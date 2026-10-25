from tests.conftest import register


async def new_conv(client):
    return (await client.post("/api/conversations")).json()["id"]


async def test_message_roundtrip_persists_and_orders(client):
    await register(client)
    cid = await new_conv(client)
    r = await client.post(f"/api/conversations/{cid}/messages", json={"content": "Mujhe workout plan chahiye"})
    assert r.status_code == 201
    body = r.json()
    assert body["user_message"]["role"] == "user" and body["assistant_message"]["role"] == "assistant"
    assert body["assistant_message"]["content"].startswith("Coach reply to:")
    assert body["conversation"]["title"] == "Mujhe workout plan chahiye"  # auto title

    await client.post(f"/api/conversations/{cid}/messages", json={"content": "Second question"})
    detail = (await client.get(f"/api/conversations/{cid}")).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant", "user", "assistant"]
    assert detail["conversation"]["title"] == "Mujhe workout plan chahiye"  # not overwritten
    assert detail["has_more"] is False


async def test_persists_across_relogin_and_conversations_do_not_mix(client):
    await register(client)
    c1, c2 = await new_conv(client), await new_conv(client)
    await client.post(f"/api/conversations/{c1}/messages", json={"content": "alpha topic"})
    await client.post(f"/api/conversations/{c2}/messages", json={"content": "beta topic"})
    await client.post("/api/auth/logout")
    await client.post("/api/auth/login", json={"email": "alice@example.com", "password": "Strong123"})
    m1 = (await client.get(f"/api/conversations/{c1}")).json()["messages"]
    m2 = (await client.get(f"/api/conversations/{c2}")).json()["messages"]
    assert "alpha" in m1[0]["content"] and "beta" not in " ".join(m["content"] for m in m1)
    assert "beta" in m2[0]["content"] and "alpha" not in " ".join(m["content"] for m in m2)


async def test_rag_context_is_retrieved_and_passed_to_llm(client, fake_llm):
    await register(client)
    cid = await new_conv(client)
    r = await client.post(f"/api/conversations/{cid}/messages", json={"content": "How much protein intake for muscle gain?"})
    assert r.status_code == 201
    system = fake_llm.calls[-1]["system"]
    assert "<retrieved_context>" in system and "1.6 grams per kilogram" in system
    meta = r.json()["assistant_message"]["metadata"]["retrieval"]
    assert meta["used"] is True and meta["sources"][0]["document_id"] == "protein"


async def test_no_relevant_context_is_signalled_to_llm(client, fake_llm):
    await register(client)
    cid = await new_conv(client)
    r = await client.post(f"/api/conversations/{cid}/messages", json={"content": "xylophone quasar zebra"})
    assert r.status_code == 201
    assert "No relevant knowledge-base context was found" in fake_llm.calls[-1]["system"]
    assert r.json()["assistant_message"]["metadata"]["retrieval"] == {"used": False, "sources": []}
    assert "Mujhe iska support ya data nahi mila" in fake_llm.calls[-1]["system"]  # fallback sentence is in the prompt


async def test_llm_failure_keeps_user_message_and_retry_does_not_duplicate(client, fake_llm):
    await register(client)
    cid = await new_conv(client)
    fake_llm.fail = True
    r = await client.post(f"/api/conversations/{cid}/messages", json={"content": "Give me a diet plan"})
    assert r.status_code == 502
    saved = r.json()["user_message"]
    detail = (await client.get(f"/api/conversations/{cid}")).json()
    assert [m["role"] for m in detail["messages"]] == ["user"]  # user msg kept, NO fake assistant answer

    fake_llm.fail = False
    ok = await client.post(f"/api/conversations/{cid}/messages", json={"content": "ignored", "retry_message_id": saved["id"]})
    assert ok.status_code == 201 and ok.json()["user_message"]["id"] == saved["id"]
    detail = (await client.get(f"/api/conversations/{cid}")).json()
    assert [m["role"] for m in detail["messages"]] == ["user", "assistant"]
    assert detail["messages"][0]["content"] == "Give me a diet plan"

    again = await client.post(f"/api/conversations/{cid}/messages", json={"content": "x", "retry_message_id": saved["id"]})
    assert again.status_code == 409  # already answered


async def test_message_validation(client):
    await register(client)
    cid = await new_conv(client)
    assert (await client.post(f"/api/conversations/{cid}/messages", json={"content": "   "})).status_code == 422
    assert (await client.post(f"/api/conversations/{cid}/messages", json={"content": "a" * 501})).status_code == 422
    assert (await client.get(f"/api/conversations/{cid}")).json()["messages"] == []


async def test_message_history_pagination(client):
    await register(client)
    cid = await new_conv(client)
    for i in range(3):
        await client.post(f"/api/conversations/{cid}/messages", json={"content": f"question {i}"})
    page = (await client.get(f"/api/conversations/{cid}?limit=4")).json()
    assert len(page["messages"]) == 4 and page["has_more"] is True
    older = (await client.get(f"/api/conversations/{cid}?limit=4&before={page['messages'][0]['id']}")).json()
    assert len(older["messages"]) == 2 and older["has_more"] is False
    assert older["messages"][-1]["created_at"] <= page["messages"][0]["created_at"]


async def test_sample_knowledge_base_chunks_are_valid():
    from pathlib import Path

    from app.services.kb_ingest import MAX_CHUNK_CHARS, load_directory

    chunks = load_directory(Path(__file__).resolve().parent.parent / "data" / "knowledge_base")
    assert len(chunks) >= 20
    assert len({c["chunk_id"] for c in chunks}) == len(chunks)
    assert all(0 < len(c["text"]) <= MAX_CHUNK_CHARS + 200 for c in chunks)
