"""Marta opens her invitation link on a laptop, and the public page reads it.

The page greets her by the name the club typed — whole, never a first name cut
out of it (``docs/adr/0171`` §4) — names the club, says whether the link still
works and — while it does — shows her code, for *after you install, open Rakieta
and enter this code* (``docs/adr/0187`` §4–§5). And she can **set her password
right there**, by exactly the rules the app's *Set your password* follows, with
exactly the same results — but the page signs nobody in: the public site holds
no session (§4), so she then opens Rakieta and signs in with it.

The refusals are asserted **on both surfaces at once**, parametrised, so the
claim that they are the same rules is a claim a test makes rather than a
sentence.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from tests.api.administration_world import (
    ADMINISTRATORS,
    CLAIM,
    MARTA,
    MARTA_PASSWORD,
    PASSWORD,
    TOMEK,
    club_signs_up,
    code_in,
    invites,
    marta_sets_her_password,
    me,
    player_signs_up,
    profile_at,
    signs_in,
    the_email_to,
    token_in,
)

PUBLIC_READ = "/api/v1/public/invitations/by-token"
PUBLIC_PASSWORD = "/api/v1/public/invitations/password"

#: Where *Set your password* is pressed: in the app, and on the public page.
SURFACES = {"player": PASSWORD, "public": PUBLIC_PASSWORD}


@pytest.fixture
async def ogrody(client):
    return await club_signs_up(client)


@pytest.fixture
def desk(ogrody):
    return ogrody[1]


@pytest.fixture
def club_id(ogrody):
    return ogrody[0]


@pytest.fixture
async def marta_invited(client, desk, mailbox):
    """Ogrody 33 has invited Marta, and her email has arrived."""

    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    return row, await the_email_to(mailbox, MARTA)


async def read(client, token: str):
    return await client.post(PUBLIC_READ, json={"token": token})


# ---------------------------------------------------------------------------
# Reading the link
# ---------------------------------------------------------------------------


async def test_the_page_greets_her_by_name_and_shows_her_code(client, marta_invited):
    _, email = marta_invited

    page = await read(client, token_in(email))

    assert page.status_code == 200, page.text
    assert page.json() == {
        "name": "Marta Wójcik",
        "club_name": "Ogrody 33",
        "state": "valid",
        # The code her email carries under the button — the same eight
        # characters, recomputed from the link she holds.
        "code": code_in(email),
    }


async def test_the_page_never_discloses_the_email(client, marta_invited):
    """The app's *Set your password* locks its field to the email; the page
    has no field to lock, and no need of it (``docs/adr/0187`` §5)."""

    _, email = marta_invited

    page = await read(client, token_in(email))

    assert "email" not in page.json()
    assert MARTA not in page.text


async def test_an_expired_link_says_so_and_shows_no_code(client, marta_invited, clock):
    _, email = marta_invited
    clock.move(timedelta(hours=72))

    page = await read(client, token_in(email))

    assert page.json()["state"] == "expired"
    assert page.json()["code"] is None


async def test_a_used_link_says_so_and_shows_no_code(client, marta_invited):
    _, email = marta_invited
    await client.post(
        PUBLIC_PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    page = await read(client, token_in(email))

    assert page.json()["state"] == "used"
    assert page.json()["code"] is None


async def test_a_locked_link_says_so_and_shows_no_code(client, marta_invited):
    _, email = marta_invited
    for _ in range(5):
        await client.post(CLAIM, json={"email": MARTA, "code": "AAAAAAAA"})

    page = await read(client, token_in(email))

    assert page.json()["state"] == "locked"
    assert page.json()["code"] is None


async def test_a_resent_invitation_leaves_the_first_link_reading_expired(
    client, desk, marta_invited
):
    row, first = marta_invited
    await client.post(f"{ADMINISTRATORS}/{row['id']}/invitation", headers=desk)

    page = await read(client, token_in(first))

    assert page.json()["state"] == "expired"
    assert page.json()["code"] is None


async def test_the_club_s_reset_opens_the_same_page(client, desk, mailbox):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)
    reset = await client.post(
        f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk
    )
    assert reset.status_code == 200, reset.text
    email = await the_email_to(mailbox, MARTA)

    page = await read(client, token_in(email))

    assert page.json() == {
        "name": "Marta Wójcik",
        "club_name": "Ogrody 33",
        "state": "valid",
        "code": code_in(email),
    }


async def test_a_link_never_issued_is_not_found(client):
    missing = await read(client, "not-a-token-anybody-was-sent")

    assert missing.status_code == 404, missing.text
    assert missing.json()["code"] == "credential_not_found"


async def test_a_forgot_password_link_is_not_an_invitation_link(client, mailbox):
    await player_signs_up(client)
    await client.post("/api/v1/auth/forgot-password", json={"email": TOMEK})
    reset = await the_email_to(mailbox, TOMEK)
    token = reset.text.split("/reset/", 1)[1].split()[0]

    missing = await read(client, token)

    assert missing.status_code == 404, missing.text
    assert missing.json()["code"] == "credential_not_found"


# ---------------------------------------------------------------------------
# Setting the password on the page
# ---------------------------------------------------------------------------


async def test_setting_it_on_the_page_opens_her_account_and_signs_nobody_in(
    client, club_id, marta_invited
):
    _, email = marta_invited

    set_ = await client.post(
        PUBLIC_PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    assert set_.status_code == 204, set_.text
    assert set_.content == b""
    # She opens Rakieta and signs in with it, and is what the app's own *Set
    # your password* would have made her: the name the club typed, and the
    # club's administrator.
    session = await signs_in(client, MARTA, MARTA_PASSWORD)
    account = await me(client, session)
    assert "name" not in account
    assert account["nickname"] is None
    assert account["adult_attested"] is False
    assert account["profiles"]["administers"] == [
        {"club_id": club_id, "club_name": "Ogrody 33"}
    ]
    assert (await client.get(profile_at(club_id), headers=session)).status_code == 200


async def test_the_club_s_reset_is_set_on_the_page_too(client, desk, club_id, mailbox):
    """The club put her back to *invited*; the page gives her account its
    password back and her administratorship with it."""

    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)
    await client.post(f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk)
    email = await the_email_to(mailbox, MARTA)

    set_ = await client.post(
        PUBLIC_PASSWORD, json={"token": token_in(email), "password": "ogrody-marta-2"}
    )

    assert set_.status_code == 204, set_.text
    session = await signs_in(client, MARTA, "ogrody-marta-2")
    assert (await client.get(profile_at(club_id), headers=session)).status_code == 200


# ---------------------------------------------------------------------------
# The same refusals, wherever it is pressed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_a_weak_password_is_refused_and_leaves_the_link_working(
    client, marta_invited, surface
):
    _, email = marta_invited

    weak = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": "lettersonly"}
    )

    assert weak.status_code == 400
    assert weak.json()["code"] == "password_too_weak"
    assert weak.json()["details"] == {"field": "password"}
    assert (await read(client, token_in(email))).json()["state"] == "valid"


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_an_expired_link_is_refused(client, marta_invited, clock, surface):
    _, email = marta_invited
    clock.move(timedelta(hours=72))

    refused = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "credential_expired"


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_a_used_link_never_reopens(client, marta_invited, surface):
    _, email = marta_invited
    await client.post(
        PUBLIC_PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    again = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": "other-pass-9"}
    )

    assert again.status_code == 409
    assert again.json()["code"] == "credential_used"
    # The first password stands.
    assert await signs_in(client, MARTA, MARTA_PASSWORD)


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_a_locked_link_is_refused(client, marta_invited, surface):
    _, email = marta_invited
    for _ in range(5):
        await client.post(CLAIM, json={"email": MARTA, "code": "AAAAAAAA"})

    refused = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "credential_locked"


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_a_link_never_issued_is_refused(client, surface):
    refused = await client.post(
        SURFACES[surface], json={"token": "never-sent", "password": MARTA_PASSWORD}
    )

    assert refused.status_code == 404
    assert refused.json()["code"] == "credential_not_found"


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_an_address_that_has_become_an_account_is_told_to_sign_in(
    client, desk, mailbox, surface
):
    """Invited while new, then signed up as a player before opening the link:
    the invitation is accepted from the app, signed in (``docs/adr/0184`` §2)."""

    await invites(client, desk, name="Tomek Kowalski", email=TOMEK)
    email = await the_email_to(mailbox, TOMEK)
    await player_signs_up(client)

    refused = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": "tomek-new-2"}
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "sign_in_to_accept"


async def test_the_page_takes_the_link_and_never_a_ticket(client, marta_invited):
    """The page holds the link; a claimed code's ticket is the app's."""

    _, email = marta_invited
    claimed = await client.post(CLAIM, json={"email": MARTA, "code": code_in(email)})

    refused = await client.post(
        PUBLIC_PASSWORD,
        json={"ticket": claimed.json()["ticket"], "password": MARTA_PASSWORD},
    )

    assert refused.status_code == 422
