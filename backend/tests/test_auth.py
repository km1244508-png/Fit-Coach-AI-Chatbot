from tests.conftest import register, user_payload


async def test_register_logs_in_and_hides_secrets(client, db):
    r = await client.post("/api/auth/register", json=user_payload())
    assert r.status_code == 201
    body = r.json()
    assert body["user"]["email"] == "alice@example.com"
    assert "password" not in r.text.lower() or "password_hash" not in r.text
    assert "set-cookie" in r.headers and "httponly" in r.headers["set-cookie"].lower()
    stored = await db.users.find_one({"email": "alice@example.com"})
    assert stored["password_hash"].startswith("$2") and stored["password_hash"] != "Strong123"
    me = await client.get("/api/auth/me")
    assert me.status_code == 200 and me.json()["name"] == "Alice Khan"


async def test_duplicate_email_rejected_case_insensitive(client):
    await register(client)
    r = await client.post("/api/auth/register", json=user_payload(email="  ALICE@Example.com "))
    assert r.status_code == 409
    assert r.json()["code"] == "email_taken"


async def test_validation_errors_do_not_echo_password(client):
    bad = user_payload()
    bad["confirm_password"] = "Different123"
    r = await client.post("/api/auth/register", json=bad)
    assert r.status_code == 422
    assert {"field": "confirm_password", "message": "Passwords do not match"} in r.json()["errors"]
    assert "Strong123" not in r.text and "Different123" not in r.text

    weak = user_payload(password="short")
    assert (await client.post("/api/auth/register", json=weak)).status_code == 422
    nodigit = user_payload(password="onlyletters")
    assert (await client.post("/api/auth/register", json=nodigit)).status_code == 422
    bad_email = user_payload(email="not-an-email")
    assert (await client.post("/api/auth/register", json=bad_email)).status_code == 422


async def test_login_success_and_failures(client):
    await register(client)
    client.cookies.clear()
    ok = await client.post("/api/auth/login", json={"email": "ALICE@example.com", "password": "Strong123"})
    assert ok.status_code == 200 and ok.json()["user"]["email"] == "alice@example.com"
    wrong = await client.post("/api/auth/login", json={"email": "alice@example.com", "password": "Wrong1234"})
    unknown = await client.post("/api/auth/login", json={"email": "nobody@example.com", "password": "Strong123"})
    assert wrong.status_code == unknown.status_code == 401
    assert wrong.json()["detail"] == unknown.json()["detail"]  # no user enumeration


async def test_protected_endpoints_reject_unauthenticated(client):
    for method, url in [
        ("get", "/api/auth/me"), ("get", "/api/conversations"), ("post", "/api/conversations"),
        ("get", "/api/conversations/507f1f77bcf86cd799439011"), ("patch", "/api/conversations/507f1f77bcf86cd799439011"),
        ("delete", "/api/conversations/507f1f77bcf86cd799439011"), ("post", "/api/conversations/507f1f77bcf86cd799439011/messages"),
    ]:
        r = await getattr(client, method)(url, **({"json": {"title": "x", "content": "hi"}} if method in ("post", "patch") else {}))
        assert r.status_code == 401, (method, url, r.status_code)


async def test_logout_revokes_session(client):
    await register(client)
    stolen = client.cookies.get("access_token")
    assert (await client.post("/api/auth/logout")).status_code == 200
    assert (await client.get("/api/auth/me")).status_code == 401
    client.cookies.set("access_token", stolen)  # replaying the old token must fail too
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_tampered_token_rejected(client):
    await register(client)
    client.cookies.set("access_token", "not.a.jwt")
    assert (await client.get("/api/auth/me")).status_code == 401


async def test_foreign_origin_blocked_on_state_changes(client):
    r = await client.post("/api/auth/login", json={"email": "a@example.com", "password": "x"}, headers={"Origin": "http://evil.example"})
    assert r.status_code == 403
