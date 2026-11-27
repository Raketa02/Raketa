"""Tomek opens his reset link on a laptop, and the public page sets his password.

*Forgot password?* in the app emails a button to the public site's
``/reset/<token>`` (``docs/adr/0184`` §5). The page reads whether the link
still works, and sets the new password by **the same rules as Forgot
password** — the password rule, the four refusals, and every phone signed out —
but signs nobody in: the public site holds no session (``docs/adr/0187`` §4),
so Tomek then signs in to Rakieta with the new password.

The refusals are asserted **on both surfaces at once**, parametrised, so the
claim that they are the same rules is a claim a test makes rather than a
sentence. An administrator is an account like a player's (``docs/adr/0185``),
so their reset is this page too.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from tests.api.administration_world import (
    MARTA,
    MARTA_PASSWORD,
    club_signs_up,
    invites,
    marta_sets_her_password,
)
from tests.api.administration_world import token_in as invitation_token_in
from tests.api.test_club_forgot_password import FORGOT as CLUB_FORGOT
from tests.api.test_clubs import SIGN_UP as CLUB_SIGN_UP
from tests.api.test_clubs import ogrody_33
from tests.api.test_forgot_password import (
    CLAIM,
    FORGOT,
    ME,
    NEW,
    NEW_PASSWORD,
    OLD_PASSWORD,
    REFRESH,
    TOMEK,
    bearer,
    code_in,
    sign_in,
    sign_up,
    the_reset_email,
    token_in,
)

PUBLIC_READ = "/api/v1/public/password-resets/by-token"
PUBLIC_PASSWORD = "/api/v1/public/password-resets/password"

#: Where the new password is set: in the app, and on the public page.
SURFACES = {"player": NEW_PASSWORD, "public": PUBLIC_PASSWORD}


@pytest.fixture
async def tomek(client) -> None:
    await sign_up(client)


@pytest.fixture
async def ogrody(client) -> None:
    assert (await client.post(CLUB_SIGN_UP, json=ogrody_33())).status_code == 201


async def read(client, token: str):
    return await client.post(PUBLIC_READ, json={"token": token})


# ---------------------------------------------------------------------------
# Reading the link
# ---------------------------------------------------------------------------


async def test_a_fresh_link_reads_valid_and_says_nothing_else(client, tomek, mailbox):
    email = await the_reset_email(client, mailbox)

    page = await read(client, token_in(email))

    assert page.status_code == 200, page.text
    assert page.json() == {"state": "valid"}


async def test_after_an_hour_the_link_reads_expired(client, tomek, mailbox, clock):
    email = await the_reset_email(client, mailbox)
    clock.move(timedelta(hours=1))

    assert (await read(client, token_in(email))).json() == {"state": "expired"}


async def test_a_newer_email_leaves_the_older_link_reading_expired(
    client, tomek, mailbox
):
    first = await the_reset_email(client, mailbox)
    await the_reset_email(client, mailbox)

    assert (await read(client, token_in(first))).json() == {"state": "expired"}


async def test_a_spent_link_reads_used(client, tomek, mailbox):
    email = await the_reset_email(client, mailbox)
    await client.post(PUBLIC_PASSWORD, json={"token": token_in(email), "password": NEW})

    assert (await read(client, token_in(email))).json() == {"state": "used"}


async def test_five_wrong_codes_leave_the_link_reading_locked(client, tomek, mailbox):
    email = await the_reset_email(client, mailbox)
    for _ in range(5):
        await client.post(CLAIM, json={"email": TOMEK, "code": "AAAAAAAA"})

    assert (await read(client, token_in(email))).json() == {"state": "locked"}


async def test_a_link_never_issued_is_not_found(client):
    missing = await read(client, "not-a-token-anybody-was-sent")

    assert missing.status_code == 404, missing.text
    assert missing.json()["code"] == "credential_not_found"


async def test_a_club_s_reset_link_is_not_this_page_s(client, ogrody, mailbox):
    """A club's link opens the club website's own page, and nothing here."""

    await client.post(CLUB_FORGOT, json={"email": "desk@ogrody33.pl"})
    email = (await mailbox.to("desk@ogrody33.pl"))[-1]

    missing = await read(client, token_in(email))

    assert missing.status_code == 404, missing.text
    assert missing.json()["code"] == "credential_not_found"


async def test_an_invitation_link_is_not_a_reset_link(client, mailbox):
    _, desk = await club_signs_up(client)
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    invitation = (await mailbox.to(MARTA))[-1]

    missing = await read(client, invitation_token_in(invitation))

    assert missing.status_code == 404, missing.text
    assert missing.json()["code"] == "credential_not_found"


# ---------------------------------------------------------------------------
# Setting the new password on the page
# ---------------------------------------------------------------------------


async def test_the_page_sets_the_password_and_signs_nobody_in(client, tomek, mailbox):
    email = await the_reset_email(client, mailbox)

    set_ = await client.post(
        PUBLIC_PASSWORD, json={"token": token_in(email), "password": NEW}
    )

    assert set_.status_code == 204, set_.text
    assert set_.content == b""
    assert (await sign_in(client, password=NEW)).status_code == 200
    assert (await sign_in(client, password=OLD_PASSWORD)).status_code == 401


async def test_the_page_signs_every_phone_out(client, tomek, mailbox, clock):
    phone = (await sign_in(client)).json()
    email = await the_reset_email(client, mailbox)
    clock.move(timedelta(minutes=2))

    await client.post(PUBLIC_PASSWORD, json={"token": token_in(email), "password": NEW})

    refused = await client.get(ME, headers=bearer(phone))
    assert refused.status_code == 401
    assert refused.json()["code"] == "access_token_revoked"
    renewed = await client.post(REFRESH, json={"refresh_token": phone["refresh_token"]})
    assert renewed.status_code == 401
    assert renewed.json()["code"] == "refresh_token_revoked"


async def test_an_administrator_resets_on_the_same_page(client, mailbox):
    _, desk = await club_signs_up(client)
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)
    await client.post(FORGOT, json={"email": MARTA})
    email = (await mailbox.to(MARTA))[-1]

    set_ = await client.post(
        PUBLIC_PASSWORD, json={"token": token_in(email), "password": "ogrody-marta-9"}
    )

    assert set_.status_code == 204, set_.text
    assert (
        await client.post(
            "/api/v1/auth/login",
            json={"email": MARTA, "password": "ogrody-marta-9"},
        )
    ).status_code == 200
    assert (
        await client.post(
            "/api/v1/auth/login", json={"email": MARTA, "password": MARTA_PASSWORD}
        )
    ).status_code == 401


# ---------------------------------------------------------------------------
# The same refusals, wherever it is set
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_a_weak_password_is_refused_and_spends_nothing(
    client, tomek, mailbox, surface
):
    email = await the_reset_email(client, mailbox)

    weak = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": "lettersonly"}
    )

    assert weak.status_code == 400
    assert weak.json()["code"] == "password_too_weak"
    assert weak.json()["details"] == {"field": "password"}
    assert (await read(client, token_in(email))).json() == {"state": "valid"}


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_an_expired_link_is_refused(client, tomek, mailbox, clock, surface):
    email = await the_reset_email(client, mailbox)
    clock.move(timedelta(hours=1))

    refused = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": NEW}
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "credential_expired"


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_a_spent_link_never_reopens(client, tomek, mailbox, surface):
    email = await the_reset_email(client, mailbox)
    await client.post(PUBLIC_PASSWORD, json={"token": token_in(email), "password": NEW})

    again = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": "padel-tomek-3"}
    )

    assert again.status_code == 409
    assert again.json()["code"] == "credential_used"
    assert (await sign_in(client, password=NEW)).status_code == 200


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_a_locked_link_is_refused(client, tomek, mailbox, surface):
    email = await the_reset_email(client, mailbox)
    for _ in range(5):
        await client.post(CLAIM, json={"email": TOMEK, "code": "AAAAAAAA"})

    refused = await client.post(
        SURFACES[surface], json={"token": token_in(email), "password": NEW}
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "credential_locked"


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_a_link_never_issued_is_refused(client, surface):
    refused = await client.post(
        SURFACES[surface], json={"token": "never-sent", "password": NEW}
    )

    assert refused.status_code == 404
    assert refused.json()["code"] == "credential_not_found"


@pytest.mark.parametrize("surface", sorted(SURFACES))
async def test_an_invitation_link_sets_no_reset_password(client, mailbox, surface):
    _, desk = await club_signs_up(client)
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    invitation = (await mailbox.to(MARTA))[-1]

    refused = await client.post(
        SURFACES[surface],
        json={"token": invitation_token_in(invitation), "password": NEW},
    )

    assert refused.status_code == 404
    assert refused.json()["code"] == "credential_not_found"


async def test_the_page_takes_the_link_and_never_a_ticket(client, tomek, mailbox):
    """The page holds the link; a claimed code's ticket is the app's."""

    email = await the_reset_email(client, mailbox)
    claimed = await client.post(CLAIM, json={"email": TOMEK, "code": code_in(email)})

    refused = await client.post(
        PUBLIC_PASSWORD, json={"ticket": claimed.json()["ticket"], "password": NEW}
    )

    assert refused.status_code == 422
