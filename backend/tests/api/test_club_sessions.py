"""The club's session, and the fence between the two audiences.

A club signs in, refreshes and signs out on the club surface, and each pair it
is issued names the **club** audience; a player's names the **player app**
(``docs/adr/0185`` §6). Neither surface accepts the other's tokens — access or
refresh — even for one email held by both identities, and a token issued before
audiences existed is still a player's.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone

import jwt
import pytest
from sqlalchemy import select

from app.core.config import get_settings
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_model import (
    RefreshTokenORM,
)
from tests.api.test_clubs import DETAILS, SIGN_IN, SIGN_UP, bearer, ogrody_33

CLUB_REFRESH = "/api/v1/club/auth/refresh"
CLUB_SIGN_OUT = "/api/v1/club/auth/logout"
PLAYER_SIGN_IN = "/api/v1/auth/login"
PLAYER_REFRESH = "/api/v1/auth/refresh"
PLAYER_ME = "/api/v1/users/me"

#: One address, two identities: Ogrody 33's desk, and the person at the desk,
#: who also plays — with a different password (``docs/adr/0182`` §3).
SHARED_EMAIL = "desk@ogrody33.pl"
CLUB_PASSWORD = "ogrody-desk-33"
PLAYER_PASSWORD = "my-own-padel-1"


@pytest.fixture
async def club_tokens(client) -> dict:
    assert (await client.post(SIGN_UP, json=ogrody_33())).status_code == 201
    resp = await client.post(
        SIGN_IN, json={"email": SHARED_EMAIL, "password": CLUB_PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


@pytest.fixture
async def player_tokens(client) -> dict:
    signed_up = await client.post(
        "/api/v1/users",
        json={
            "email": SHARED_EMAIL,
            "password1": PLAYER_PASSWORD,
            "password2": PLAYER_PASSWORD,
            "adult_attested": True,
        },
    )
    assert signed_up.status_code == 201, signed_up.text
    resp = await client.post(
        PLAYER_SIGN_IN, json={"email": SHARED_EMAIL, "password": PLAYER_PASSWORD}
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def audience_of(token: str) -> str | None:
    """The ``aud`` claim of a token as the client holds it — read, not trusted."""

    return jwt.decode(token, options={"verify_signature": False}).get("aud")


# ---------------------------------------------------------------------------
# The club's session
# ---------------------------------------------------------------------------


async def test_a_club_signs_in_and_every_token_it_holds_names_the_club(club_tokens):
    assert club_tokens["token_type"] == "bearer"
    assert club_tokens["expires_in"] >= 60
    assert audience_of(club_tokens["access_token"]) == "club"
    assert audience_of(club_tokens["refresh_token"]) == "club"


async def test_a_player_s_tokens_name_the_player_app(player_tokens):
    assert audience_of(player_tokens["access_token"]) == "player_app"
    assert audience_of(player_tokens["refresh_token"]) == "player_app"


@pytest.mark.parametrize(
    ("email", "password"),
    [(SHARED_EMAIL, "wrong-password-1"), ("nobody@ogrody33.pl", CLUB_PASSWORD)],
)
async def test_a_wrong_password_and_an_unknown_email_are_one_refusal(
    client, club_tokens, email, password
):
    resp = await client.post(SIGN_IN, json={"email": email, "password": password})

    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


async def test_a_club_refreshes_and_the_pair_stays_the_club_s(client, club_tokens):
    resp = await client.post(
        CLUB_REFRESH, json={"refresh_token": club_tokens["refresh_token"]}
    )

    assert resp.status_code == 200, resp.text
    rotated = resp.json()
    assert rotated["refresh_token"] != club_tokens["refresh_token"]
    assert audience_of(rotated["access_token"]) == "club"
    assert audience_of(rotated["refresh_token"]) == "club"
    assert (await client.get(DETAILS, headers=bearer(rotated))).status_code == 200
    # The one it replaced is spent.
    again = await client.post(
        CLUB_REFRESH, json={"refresh_token": club_tokens["refresh_token"]}
    )
    assert again.status_code == 401


async def test_a_club_signs_out_and_its_refresh_token_is_spent(client, club_tokens):
    out = await client.post(
        CLUB_SIGN_OUT, json={"refresh_token": club_tokens["refresh_token"]}
    )
    assert out.status_code == 200

    resp = await client.post(
        CLUB_REFRESH, json={"refresh_token": club_tokens["refresh_token"]}
    )

    assert resp.status_code == 401
    assert resp.json()["code"] == "refresh_token_revoked"


async def test_signing_out_twice_is_the_same_answer(client, club_tokens):
    body = {"refresh_token": club_tokens["refresh_token"]}

    first = await client.post(CLUB_SIGN_OUT, json=body)
    second = await client.post(CLUB_SIGN_OUT, json=body)

    assert first.status_code == second.status_code == 200
    assert first.json() == second.json()


# ---------------------------------------------------------------------------
# Two identities, one email
# ---------------------------------------------------------------------------


async def test_the_player_s_password_does_not_sign_the_club_in(
    client, club_tokens, player_tokens
):
    resp = await client.post(
        SIGN_IN, json={"email": SHARED_EMAIL, "password": PLAYER_PASSWORD}
    )

    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


async def test_the_club_s_password_does_not_sign_the_player_in(
    client, club_tokens, player_tokens
):
    resp = await client.post(
        PLAYER_SIGN_IN, json={"email": SHARED_EMAIL, "password": CLUB_PASSWORD}
    )

    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


async def test_a_club_account_alone_cannot_sign_in_to_the_player_app(
    client, club_tokens
):
    resp = await client.post(
        PLAYER_SIGN_IN, json={"email": SHARED_EMAIL, "password": CLUB_PASSWORD}
    )

    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_credentials"


# ---------------------------------------------------------------------------
# Neither surface takes the other's tokens
# ---------------------------------------------------------------------------


async def test_a_club_s_access_token_is_refused_on_the_player_surface(
    client, club_tokens, player_tokens
):
    resp = await client.get(PLAYER_ME, headers=bearer(club_tokens))

    assert resp.status_code == 401
    assert resp.json()["code"] == "access_token_invalid"


async def test_a_player_s_access_token_is_refused_on_the_club_surface(
    client, club_tokens, player_tokens
):
    resp = await client.get(DETAILS, headers=bearer(player_tokens))

    assert resp.status_code == 401
    assert resp.json()["code"] == "access_token_invalid"


async def test_a_club_s_refresh_token_is_refused_on_the_player_surface(
    client, club_tokens
):
    resp = await client.post(
        PLAYER_REFRESH, json={"refresh_token": club_tokens["refresh_token"]}
    )

    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_refresh_token"
    # And it was not spent by being presented in the wrong place.
    still = await client.post(
        CLUB_REFRESH, json={"refresh_token": club_tokens["refresh_token"]}
    )
    assert still.status_code == 200


async def test_a_player_s_refresh_token_is_refused_on_the_club_surface(
    client, player_tokens
):
    resp = await client.post(
        CLUB_REFRESH, json={"refresh_token": player_tokens["refresh_token"]}
    )

    assert resp.status_code == 401
    assert resp.json()["code"] == "invalid_refresh_token"


async def test_signing_the_club_out_never_ends_a_player_s_session(
    client, club_tokens, player_tokens
):
    out = await client.post(
        CLUB_SIGN_OUT, json={"refresh_token": player_tokens["refresh_token"]}
    )
    assert out.status_code == 200

    resp = await client.post(
        PLAYER_REFRESH, json={"refresh_token": player_tokens["refresh_token"]}
    )

    assert resp.status_code == 200, resp.text


# ---------------------------------------------------------------------------
# A token from before audiences, and whose a refresh token is
# ---------------------------------------------------------------------------


def a_token_from_before_audiences(account_id: str) -> str:
    """An access token as this backend minted them before ``docs/adr/0185``:
    every claim it had then, and no ``aud``."""

    settings = get_settings()
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": account_id,
            "token_type": "access",
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=5)).timestamp()),
            "iss": settings.JWT_ISSUER,
            "jti": uuid.uuid4().hex,
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


async def test_a_token_with_no_audience_is_still_a_player_s(
    client, club_tokens, player_tokens
):
    me = (await client.get(PLAYER_ME, headers=bearer(player_tokens))).json()
    club_account_id = jwt.decode(
        club_tokens["access_token"], options={"verify_signature": False}
    )["sub"]

    as_player = await client.get(
        PLAYER_ME,
        headers={"Authorization": f"Bearer {a_token_from_before_audiences(me['id'])}"},
    )
    as_club = await client.get(
        DETAILS,
        headers={
            "Authorization": f"Bearer {a_token_from_before_audiences(club_account_id)}"
        },
    )

    assert as_player.status_code == 200, as_player.text
    assert as_player.json()["id"] == me["id"]
    assert as_club.status_code == 401
    assert as_club.json()["code"] == "access_token_invalid"


async def test_every_refresh_token_records_whose_it_is(
    client, session_factory, club_tokens, player_tokens
):
    """The row a sign-out-everywhere will revoke by (``docs/adr/0185`` §7): a
    club's names its Club account and no User, and a player's the reverse."""

    club_jti = jwt.decode(
        club_tokens["refresh_token"], options={"verify_signature": False}
    )["jti"]
    player_jti = jwt.decode(
        player_tokens["refresh_token"], options={"verify_signature": False}
    )["jti"]
    club_account_id = jwt.decode(
        club_tokens["access_token"], options={"verify_signature": False}
    )["sub"]
    user_id = (await client.get(PLAYER_ME, headers=bearer(player_tokens))).json()["id"]

    async with session_factory() as session:
        rows = {
            row.jti: row
            for row in (await session.execute(select(RefreshTokenORM))).scalars()
        }

    assert str(rows[club_jti].club_account_id) == club_account_id
    assert rows[club_jti].user_id is None
    assert str(rows[player_jti].user_id) == user_id
    assert rows[player_jti].club_account_id is None
