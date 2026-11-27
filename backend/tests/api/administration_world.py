"""Ogrody 33's desk, Marta who is new to Rakieta, and Tomek who already plays —
the people ``docs/adr/0184`` is told through, and the few moves every test of
administrators and invitations makes.

**Every assertion reads what a person reads**: an answer on the club surface or
the player surface, and an email out of the recording mailer once the queues
have drained, its link and code read off the text.
"""

from __future__ import annotations

import re

CLUB_SIGN_UP = "/api/v1/club/sign-up"
CLUB_SIGN_IN = "/api/v1/club/auth/login"
ADMINISTRATORS = "/api/v1/club/administrators"

SIGN_UP = "/api/v1/users"
SIGN_IN = "/api/v1/auth/login"
ME = "/api/v1/users/me"
NAME_ME = "/api/v1/users/me/name"
ATTEST = "/api/v1/users/me/adult-attestation"
CLAIM = "/api/v1/invitations/claim"
PASSWORD = "/api/v1/invitations/password"
BY_TOKEN = "/api/v1/invitations/by-token"
PROFILE_PATH = "/api/v1/profile/commit"

DESK = "desk@ogrody33.pl"
DESK_PASSWORD = "ogrody-desk-33"
MARTA = "marta@ogrody33.pl"
TOMEK = "tomek@example.com"
TOMEK_PASSWORD = "padel-tomek-1"
MARTA_PASSWORD = "ogrody-marta-1"

#: The alphabet a code is written in, spelled here rather than imported: the
#: test's claim is that a person can read the code.
CODE = re.compile(r"^([ABCDEFGHJKMNPQRSTUVWXYZ23456789]{8})$", re.MULTILINE)


def bearer(tokens: dict) -> dict:
    return {"Authorization": f"Bearer {tokens['access_token']}"}


def accept_path(administrator_id: str) -> str:
    return f"/api/v1/invitations/{administrator_id}/acceptance"


def profile_at(club_id: str) -> str:
    return f"/api/v1/administrator/clubs/{club_id}"


async def club_signs_up(
    client,
    *,
    name: str = "Ogrody 33",
    email: str = DESK,
    sports=("PADEL", "TENNIS"),
    point: tuple[float, float] = (50.06, 19.95),
) -> tuple[str, dict]:
    """The club's id, and a club-audience session for its desk — in Kraków's
    centre unless told otherwise."""

    signed_up = await client.post(
        CLUB_SIGN_UP,
        json={
            "name": name,
            "district": "Grzegórzki",
            "city": "Kraków",
            "sports": list(sports),
            "point": {"latitude": point[0], "longitude": point[1]},
            "email": email,
            "password": DESK_PASSWORD,
        },
    )
    assert signed_up.status_code == 201, signed_up.text
    signed_in = await client.post(
        CLUB_SIGN_IN, json={"email": email, "password": DESK_PASSWORD}
    )
    assert signed_in.status_code == 200, signed_in.text
    return signed_up.json()["id"], bearer(signed_in.json())


async def player_signs_up(
    client, email: str = TOMEK, password: str = TOMEK_PASSWORD
) -> dict:
    """A player's player-app session."""

    created = await client.post(
        SIGN_UP,
        json={
            "email": email,
            "password1": password,
            "password2": password,
            "adult_attested": True,
        },
    )
    assert created.status_code == 201, created.text
    return await signs_in(client, email, password)


async def signs_in(client, email: str, password: str) -> dict:
    signed_in = await client.post(SIGN_IN, json={"email": email, "password": password})
    assert signed_in.status_code == 200, signed_in.text
    return bearer(signed_in.json())


async def invites(client, desk: dict, *, name: str, email: str) -> dict:
    invited = await client.post(
        ADMINISTRATORS, headers=desk, json={"name": name, "email": email}
    )
    assert invited.status_code == 201, invited.text
    return invited.json()


async def listed(client, desk: dict) -> list[dict]:
    read = await client.get(ADMINISTRATORS, headers=desk)
    assert read.status_code == 200, read.text
    return read.json()["administrators"]


def link_in(email) -> str:
    found = re.search(r"(https?://\S+/invite/\S+)", email.text)
    assert found, email.text
    return found.group(1)


def token_in(email) -> str:
    return link_in(email).rsplit("/invite/", 1)[1]


def code_in(email) -> str:
    found = CODE.search(email.text)
    assert found, email.text
    return found.group(1)


async def the_email_to(mailbox, address: str):
    return (await mailbox.to(address))[-1]


async def marta_sets_her_password(client, mailbox, password: str = MARTA_PASSWORD):
    """Marta opens the invitation's link and sets her password — the first way
    in — and is signed in."""

    email = await the_email_to(mailbox, MARTA)
    set_ = await client.post(
        PASSWORD, json={"token": token_in(email), "password": password}
    )
    assert set_.status_code == 200, set_.text
    return bearer(set_.json())


async def me(client, session: dict) -> dict:
    read = await client.get(ME, headers=session)
    assert read.status_code == 200, read.text
    return read.json()
