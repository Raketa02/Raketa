"""*Forgot password?* on the club surface: Ogrody 33's desk gets back in.

The same three acts as the player's (``tests/api/test_forgot_password.py``),
built for the club audience: the link opens the **club website's** own *Set a
new password* page, and setting one signs every other browser the desk is
signed in on out (``docs/adr/0185`` §7).

**One email, two identities** (``docs/adr/0182`` §3): the desk's address may be
the address of somebody at the desk who also plays, with a different password.
A reset on either surface recovers that surface's account and touches nothing
on the other.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.config import get_settings
from tests.api.test_clubs import DETAILS, SIGN_UP, bearer, ogrody_33
from tests.api.test_forgot_password import (
    code_in,
    everything_recorded,
    link_in,
    token_in,
)

FORGOT = "/api/v1/club/auth/forgot-password"
CLAIM = "/api/v1/club/auth/forgot-password/claim"
NEW_PASSWORD = "/api/v1/club/auth/forgot-password/new-password"
SIGN_IN = "/api/v1/club/auth/login"
REFRESH = "/api/v1/club/auth/refresh"

PLAYER_FORGOT = "/api/v1/auth/forgot-password"
PLAYER_CLAIM = "/api/v1/auth/forgot-password/claim"
PLAYER_NEW_PASSWORD = "/api/v1/auth/forgot-password/new-password"
PLAYER_SIGN_IN = "/api/v1/auth/login"
PLAYER_ME = "/api/v1/users/me"

DESK = "desk@ogrody33.pl"
DESK_PASSWORD = "ogrody-desk-33"
NEW = "ogrody-desk-34"
PLAYER_PASSWORD = "my-own-padel-1"


@pytest.fixture
async def ogrody(client) -> None:
    assert (await client.post(SIGN_UP, json=ogrody_33())).status_code == 201


async def sign_in(client, password: str = DESK_PASSWORD):
    return await client.post(SIGN_IN, json={"email": DESK, "password": password})


async def the_reset_email(client, mailbox):
    asked = await client.post(FORGOT, json={"email": DESK})
    assert asked.status_code == 202, asked.text
    return (await mailbox.to(DESK))[-1]


async def test_the_desk_is_emailed_a_link_to_the_club_website_and_a_code(
    client, ogrody, mailbox
):
    unknown = await client.post(FORGOT, json={"email": "nobody@ogrody33.pl"})
    email = await the_reset_email(client, mailbox)

    club_website = get_settings().CLUB_WEBSITE_URL.rstrip("/")
    assert link_in(email).startswith(f"{club_website}/reset/")
    assert len(code_in(email)) == 8
    assert unknown.status_code == 202 and unknown.content == b""
    assert await mailbox.to("nobody@ogrody33.pl") == []


async def test_the_desk_sets_a_new_password_by_code_and_is_signed_in(
    client, ogrody, mailbox
):
    email = await the_reset_email(client, mailbox)
    claimed = await client.post(CLAIM, json={"email": DESK, "code": code_in(email)})
    assert claimed.status_code == 200, claimed.text

    set_ = await client.post(
        NEW_PASSWORD, json={"ticket": claimed.json()["ticket"], "password": NEW}
    )

    assert set_.status_code == 200, set_.text
    assert (await client.get(DETAILS, headers=bearer(set_.json()))).status_code == 200
    assert (await sign_in(client, password=NEW)).status_code == 200
    assert (await sign_in(client)).status_code == 401


async def test_after_an_hour_the_club_link_has_expired(client, ogrody, mailbox, clock):
    email = await the_reset_email(client, mailbox)

    clock.move(timedelta(hours=1))

    late = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
    )
    assert late.status_code == 409
    assert late.json()["code"] == "credential_expired"


async def test_no_club_link_code_or_ticket_ever_enters_an_event(
    client, ogrody, mailbox, session_factory
):
    """``docs/adr/0184`` §4 on the club surface: its password change and its
    revoked sessions are recorded, and nothing that opened them is."""

    await sign_in(client)
    email = await the_reset_email(client, mailbox)
    token, code = token_in(email), code_in(email)
    ticket = (await client.post(CLAIM, json={"email": DESK, "code": code})).json()[
        "ticket"
    ]
    set_ = await client.post(NEW_PASSWORD, json={"ticket": ticket, "password": NEW})
    assert set_.status_code == 200
    await mailbox.drain()

    recorded = await everything_recorded(session_factory)
    assert "password_hash" in recorded
    for secret in (token, code, ticket):
        assert secret not in recorded


async def test_a_club_reset_signs_every_other_browser_out(
    client, ogrody, mailbox, clock
):
    other_browser = (await sign_in(client)).json()
    email = await the_reset_email(client, mailbox)
    clock.move(timedelta(minutes=2))

    this_browser = (
        await client.post(
            NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
        )
    ).json()

    refused = await client.get(DETAILS, headers=bearer(other_browser))
    assert refused.status_code == 401
    assert refused.json()["code"] == "access_token_revoked"
    renewed = await client.post(
        REFRESH, json={"refresh_token": other_browser["refresh_token"]}
    )
    assert renewed.status_code == 401
    assert renewed.json()["code"] == "refresh_token_revoked"
    assert (await client.get(DETAILS, headers=bearer(this_browser))).status_code == 200


# ---------------------------------------------------------------------------
# One email, two identities
# ---------------------------------------------------------------------------


@pytest.fixture
async def the_person_at_the_desk_plays(client, ogrody) -> dict:
    signed_up = await client.post(
        "/api/v1/users",
        json={
            "email": DESK,
            "password1": PLAYER_PASSWORD,
            "password2": PLAYER_PASSWORD,
            "adult_attested": True,
        },
    )
    assert signed_up.status_code == 201, signed_up.text
    signed_in = await client.post(
        PLAYER_SIGN_IN, json={"email": DESK, "password": PLAYER_PASSWORD}
    )
    assert signed_in.status_code == 200
    return signed_in.json()


async def test_a_club_reset_leaves_the_player_with_the_same_email_alone(
    client, the_person_at_the_desk_plays, mailbox, clock
):
    player = the_person_at_the_desk_plays
    email = await the_reset_email(client, mailbox)
    clock.move(timedelta(minutes=2))

    set_ = await client.post(
        NEW_PASSWORD, json={"token": token_in(email), "password": NEW}
    )

    assert set_.status_code == 200, set_.text
    assert (await client.get(PLAYER_ME, headers=bearer(player))).status_code == 200
    still = await client.post(
        PLAYER_SIGN_IN, json={"email": DESK, "password": PLAYER_PASSWORD}
    )
    assert still.status_code == 200


async def test_a_players_reset_opens_nothing_on_the_club_surface(
    client, the_person_at_the_desk_plays, mailbox
):
    asked = await client.post(PLAYER_FORGOT, json={"email": DESK})
    assert asked.status_code == 202
    (player_email,) = await mailbox.to(DESK)

    by_code = await client.post(
        CLAIM, json={"email": DESK, "code": code_in(player_email)}
    )
    by_link = await client.post(
        NEW_PASSWORD, json={"token": token_in(player_email), "password": NEW}
    )

    assert by_code.status_code == 400
    assert by_code.json()["code"] == "code_incorrect"
    assert by_link.status_code == 404
    assert by_link.json()["code"] == "credential_not_found"
    assert (await sign_in(client)).status_code == 200


async def test_a_clubs_reset_opens_nothing_on_the_player_surface(
    client, the_person_at_the_desk_plays, mailbox
):
    club_email = await the_reset_email(client, mailbox)

    by_code = await client.post(
        PLAYER_CLAIM, json={"email": DESK, "code": code_in(club_email)}
    )
    by_link = await client.post(
        PLAYER_NEW_PASSWORD, json={"token": token_in(club_email), "password": NEW}
    )

    assert by_code.json()["code"] == "code_incorrect"
    assert by_link.json()["code"] == "credential_not_found"


async def test_each_surface_sends_its_own_email_for_one_address(
    client, the_person_at_the_desk_plays, mailbox
):
    await client.post(FORGOT, json={"email": DESK})
    await client.post(PLAYER_FORGOT, json={"email": DESK})

    kinds = sorted(message.kind for message in await mailbox.to(DESK))

    assert kinds == ["forgot_password.club", "forgot_password.player"]
