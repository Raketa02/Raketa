import pytest


async def _signup_and_login(client, payload):
    await client.post("/api/v1/users", json=payload)
    login = await client.post(
        "/api/v1/users/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return login.json()


@pytest.mark.asyncio
async def test_refresh_success_rotates_tokens(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    resp = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200, resp.text
    new_tokens = resp.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert new_tokens["access_token"]
    assert new_tokens["expires_in"] >= 60


@pytest.mark.asyncio
async def test_refresh_rejects_invalid_token(client):
    resp = await client.post("/auth/refresh", json={"refresh_token": "not-a-jwt"})
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rejects_revoked_token(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    # First refresh rotates → original refresh becomes invalid.
    first = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first.status_code == 200
    again = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert again.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    resp = await client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    assert resp.json()["message"]

    refresh = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_logout_is_idempotent(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    first = await client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    second = await client.post(
        "/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first.status_code == 200 and second.status_code == 200


@pytest.mark.asyncio
async def test_access_token_rejected_at_refresh(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    resp = await client.post(
        "/auth/refresh", json={"refresh_token": tokens["access_token"]}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_token_rejected_at_me(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    resp = await client.get(
        "/api/v1/users/me",
        headers={"Authorization": f"Bearer {tokens['refresh_token']}"},
    )
    assert resp.status_code == 401
