import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_model import (
    RefreshTokenORM,
)
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM
from tests.unit.bcrypt_cost import BCRYPT_MINIMUM_ROUNDS, cost_of


async def _signup_and_login(client, payload):
    await client.post("/api/v1/users", json=payload)
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": payload["email"], "password": payload["password1"]},
    )
    assert login.status_code == 200, login.text
    return login.json()


@pytest.mark.asyncio
async def test_login_success(client, valid_signup_payload):
    await client.post("/api/v1/users", json=valid_signup_payload)
    resp = await client.post(
        "/api/v1/auth/login",
        json={
            "email": valid_signup_payload["email"],
            "password": valid_signup_payload["password1"],
        },
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["expires_in"] >= 60


@pytest.mark.asyncio
async def test_login_wrong_password(client, valid_signup_payload):
    await client.post("/api/v1/users", json=valid_signup_payload)
    resp = await client.post(
        "/api/v1/auth/login",
        json={"email": valid_signup_payload["email"], "password": "wrong-password1"},
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_success_rotates_tokens(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200, resp.text
    new_tokens = resp.json()
    assert new_tokens["refresh_token"] != tokens["refresh_token"]
    assert new_tokens["access_token"]
    assert new_tokens["expires_in"] >= 60


@pytest.mark.asyncio
async def test_refresh_rejects_invalid_token(client):
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": "not-a-jwt"}
    )
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_refresh_rejects_revoked_token(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    first = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first.status_code == 200
    again = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert again.status_code == 401


@pytest.mark.asyncio
async def test_logout_revokes_refresh(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    resp = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert resp.status_code == 200
    assert resp.json()["message"]

    refresh = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert refresh.status_code == 401


@pytest.mark.asyncio
async def test_logout_is_idempotent(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    first = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    second = await client.post(
        "/api/v1/auth/logout", json={"refresh_token": tokens["refresh_token"]}
    )
    assert first.status_code == 200 and second.status_code == 200


@pytest.mark.asyncio
async def test_access_token_rejected_at_refresh(client, valid_signup_payload):
    tokens = await _signup_and_login(client, valid_signup_payload)
    resp = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["access_token"]}
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


async def test_every_stored_hash_is_made_at_the_configured_work_factor(
    client, session_factory, valid_signup_payload
):
    """A password and every refresh token go through one port, so one setting
    decides the cost of both — read off the stored hashes rather than trusted from
    the wiring.

    Under test that setting is bcrypt's minimum, which `conftest.py` supplies. Were
    the wiring to drop it, nothing would fail: every sign-up, login and refresh in
    the suite would quietly go back to production's cost.
    """

    tokens = await _signup_and_login(client, valid_signup_payload)
    rotated = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": tokens["refresh_token"]}
    )
    assert rotated.status_code == 200, rotated.text

    async with session_factory() as session:
        passwords = (await session.scalars(select(UserORM.password_hash))).all()
        refresh_tokens = (
            await session.scalars(select(RefreshTokenORM.token_hash))
        ).all()

    assert len(passwords) == 1
    assert len(refresh_tokens) == 2
    assert get_settings().BCRYPT_ROUNDS == BCRYPT_MINIMUM_ROUNDS
    costs = {cost_of(h) for h in [*passwords, *refresh_tokens]}
    assert costs == {BCRYPT_MINIMUM_ROUNDS}
