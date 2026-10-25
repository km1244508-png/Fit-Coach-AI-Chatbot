import asyncio

from tests.conftest import register

FAKE_ID = "507f1f77bcf86cd799439011"


async def test_create_list_rename_delete(client):
    await register(client)
    a = (await client.post("/api/conversations")).json()
    b = (await client.post("/api/conversations", json={"title": "  Leg   day plan "})).json()
    assert a["id"] != b["id"] and a["title"] == "New Chat" and b["title"] == "Leg day plan"

    listing = (await client.get("/api/conversations")).json()
    assert listing["total"] == 2 and len(listing["items"]) == 2

    r = await client.patch(f"/api/conversations/{a['id']}", json={"title": "Meal prep"})
    assert r.status_code == 200 and r.json()["title"] == "Meal prep"
    assert (await client.patch(f"/api/conversations/{a['id']}", json={"title": "   "})).status_code == 422

    assert (await client.delete(f"/api/conversations/{a['id']}")).status_code == 204
    assert (await client.get(f"/api/conversations/{a['id']}")).status_code == 404  # old ID is dead
    assert (await client.get("/api/conversations")).json()["total"] == 1


async def test_list_is_newest_activity_first_and_paginated(client):
    await register(client)
    ids = []
    for _ in range(3):
        ids.append((await client.post("/api/conversations")).json()["id"])
        await asyncio.sleep(0.01)
    await client.post(f"/api/conversations/{ids[0]}/messages", json={"content": "bump the oldest"})
    items = (await client.get("/api/conversations")).json()["items"]
    assert items[0]["id"] == ids[0]  # moved to the top by new activity
    page = (await client.get("/api/conversations?limit=2&skip=2")).json()
    assert len(page["items"]) == 1 and page["total"] == 3
    assert (await client.get("/api/conversations?limit=1000")).status_code == 422


async def test_user_cannot_touch_another_users_conversation(client, other_client):
    await register(client, email="alice@example.com")
    await register(other_client, email="bob@example.com", name="Bob Ali")
    conv = (await client.post("/api/conversations")).json()
    await client.post(f"/api/conversations/{conv['id']}/messages", json={"content": "alice private message"})
    cid = conv["id"]

    assert (await other_client.get(f"/api/conversations/{cid}")).status_code == 404
    assert (await other_client.patch(f"/api/conversations/{cid}", json={"title": "hacked"})).status_code == 404
    assert (await other_client.post(f"/api/conversations/{cid}/messages", json={"content": "hi"})).status_code == 404
    assert (await other_client.delete(f"/api/conversations/{cid}")).status_code == 404
    assert (await other_client.get("/api/conversations")).json()["total"] == 0

    still = (await client.get(f"/api/conversations/{cid}")).json()
    assert still["conversation"]["title"] != "hacked" and len(still["messages"]) == 2


async def test_invalid_and_unknown_ids_return_404(client):
    await register(client)
    for bad in ["abc", "123", "zzzzzzzzzzzzzzzzzzzzzzzz", FAKE_ID, "$ne"]:
        assert (await client.get(f"/api/conversations/{bad}")).status_code == 404
        assert (await client.delete(f"/api/conversations/{bad}")).status_code == 404
