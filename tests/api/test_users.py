import pytest


@pytest.mark.asyncio
async def test_signup_success(client, valid_signup_payload):
    resp = await client.post("/api/v1/users", json=valid_signup_payload)
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["email"] == valid_signup_payload["email"]
    assert body["nickname"] == valid_signup_payload["nickname"]
    assert body["authority"] == "USER"
    assert body["is_admin"] is False
    assert "password" not in body and "password_hash" not in body


@pytest.mark.asyncio
async def test_signup_password_mismatch(client, valid_signup_payload):
    payload = {**valid_signup_payload, "password2": "different1!"}
    resp = await client.post("/api/v1/users", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_weak_password(client, valid_signup_payload):
    payload = {**valid_signup_payload, "password1": "weak", "password2": "weak"}
    resp = await client.post("/api/v1/users", json=payload)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_signup_duplicate_email(client, valid_signup_payload):
    assert (
        await client.post("/api/v1/users", json=valid_signup_payload)
    ).status_code == 201
    dup = {**valid_signup_payload, "nickname": "alice2"}
    resp = await client.post("/api/v1/users", json=dup)
    assert resp.status_code == 409
    assert resp.json()["error"] == "conflict"


@pytest.mark.asyncio
async def test_signup_duplicate_nickname(client, valid_signup_payload):
    assert (
        await client.post("/api/v1/users", json=valid_signup_payload)
    ).status_code == 201
    dup = {**valid_signup_payload, "email": "alice2@example.com"}
    resp = await client.post("/api/v1/users", json=dup)
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_me_requires_auth(client):
    resp = await client.get("/api/v1/users/me")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_me_with_valid_access_token(client, valid_signup_payload):
    await client.post("/api/v1/users", json=valid_signup_payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={
            "email": valid_signup_payload["email"],
            "password": valid_signup_payload["password1"],
        },
    )
    access = login.json()["access_token"]
    resp = await client.get(
        "/api/v1/users/me", headers={"Authorization": f"Bearer {access}"}
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == valid_signup_payload["email"]
