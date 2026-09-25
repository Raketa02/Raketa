"""Marta and Tomek get in, on the player surface (``docs/adr/0184`` §2).

Marta is new to Raketa. Her email has a button and a code; she sets her
password with either one, and her account is created under the name the club
typed, already an administrator. Tomek already plays: there is no password step
for him — his app finds the pending invitation on ``/users/me`` and he accepts
it. Whichever way in, the administrator guard is what every administrator
request passes, and it refuses from the request after a removal.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import select

from app.infrastructure.events.event_delivery_model import EventOutboxORM
from app.infrastructure.events.event_store_model import EventStoreORM
from tests.api.administration_world import (
    ADMINISTRATORS,
    ATTEST,
    BY_TOKEN,
    CLAIM,
    MARTA,
    MARTA_PASSWORD,
    NAME_ME,
    PASSWORD,
    TOMEK,
    accept_path,
    club_signs_up,
    code_in,
    invites,
    me,
    player_signs_up,
    profile_at,
    signs_in,
    the_email_to,
    token_in,
)


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


# ---------------------------------------------------------------------------
# A new person: the link, or the code
# ---------------------------------------------------------------------------


async def test_setting_a_password_by_the_link_creates_her_account_as_the_club_named_her(
    client, club_id, marta_invited
):
    _, email = marta_invited

    set_ = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    assert set_.status_code == 200, set_.text
    session = {"Authorization": f"Bearer {set_.json()['access_token']}"}
    account = await me(client, session)
    assert account["email"] == MARTA
    assert account["name"] == "Marta Wójcik"
    assert account["nickname"] is None
    assert account["adult_attested"] is False
    assert account["has_player_profile"] is False
    assert account["profiles"] == {
        "acts_as_player": False,
        "administers": [{"club_id": club_id, "club_name": "Ogrody 33"}],
        "pending_invitations": [],
    }
    # And the password is hers from now on.
    assert await signs_in(client, MARTA, MARTA_PASSWORD)


async def test_claiming_the_code_returns_a_ticket_the_password_is_set_with(
    client, club_id, marta_invited
):
    _, email = marta_invited

    claimed = await client.post(
        CLAIM, json={"email": "Marta@Ogrody33.pl", "code": code_in(email).lower()}
    )

    assert claimed.status_code == 200, claimed.text
    assert 0 < claimed.json()["expires_in"] <= 15 * 60
    set_ = await client.post(
        PASSWORD,
        json={"ticket": claimed.json()["ticket"], "password": MARTA_PASSWORD},
    )
    assert set_.status_code == 200, set_.text
    session = {"Authorization": f"Bearer {set_.json()['access_token']}"}
    assert (await client.get(profile_at(club_id), headers=session)).json() == {
        "club_id": club_id,
        "club_name": "Ogrody 33",
    }


async def test_the_link_can_be_read_before_the_password_is_set(client, marta_invited):
    """What *Set your password* locks the email to, and greets her with."""

    _, email = marta_invited

    read = await client.post(BY_TOKEN, json={"token": token_in(email)})

    assert read.status_code == 200, read.text
    assert read.json() == {
        "email": MARTA,
        "name": "Marta Wójcik",
        "club_name": "Ogrody 33",
        "state": "valid",
    }


async def test_a_weak_password_is_refused_and_leaves_the_link_working(
    client, marta_invited
):
    _, email = marta_invited

    weak = await client.post(
        PASSWORD, json={"token": token_in(email), "password": "lettersonly"}
    )

    assert weak.status_code == 400
    assert weak.json()["code"] == "password_too_weak"
    good = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )
    assert good.status_code == 200


# ---------------------------------------------------------------------------
# The four refusals a person is shown
# ---------------------------------------------------------------------------


async def test_a_wrong_code_is_refused(client, marta_invited):
    refused = await client.post(CLAIM, json={"email": MARTA, "code": "AAAAAAAA"})

    assert refused.status_code == 400
    assert refused.json()["code"] == "code_incorrect"


async def test_an_expired_invitation_says_so_by_link_and_by_code(
    client, marta_invited, clock
):
    _, email = marta_invited
    clock.move(timedelta(hours=72))

    by_link = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )
    by_code = await client.post(CLAIM, json={"email": MARTA, "code": code_in(email)})

    assert by_link.status_code == by_code.status_code == 409
    assert by_link.json()["code"] == by_code.json()["code"] == "credential_expired"


async def test_a_used_invitation_never_reopens(client, marta_invited):
    _, email = marta_invited
    await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    again = await client.post(
        PASSWORD, json={"token": token_in(email), "password": "ogrody-marta-9"}
    )
    by_code = await client.post(CLAIM, json={"email": MARTA, "code": code_in(email)})
    read = await client.post(BY_TOKEN, json={"token": token_in(email)})

    assert again.json()["code"] == by_code.json()["code"] == "credential_used"
    assert read.json()["state"] == "used"


async def test_five_wrong_codes_lock_the_invitation_link_and_all(client, marta_invited):
    _, email = marta_invited
    for _ in range(5):
        await client.post(CLAIM, json={"email": MARTA, "code": "AAAAAAAA"})

    by_code = await client.post(CLAIM, json={"email": MARTA, "code": code_in(email)})
    by_link = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    assert by_code.json()["code"] == by_link.json()["code"] == "credential_locked"


async def test_a_forgot_password_code_is_not_an_invitation_code(client, mailbox):
    """Each code box opens its own kind: a reset code typed into *Have an
    invitation code?* is a wrong code, and says nothing more."""

    await player_signs_up(client)
    await client.post("/api/v1/auth/forgot-password", json={"email": TOMEK})
    reset = await the_email_to(mailbox, TOMEK)

    refused = await client.post(CLAIM, json={"email": TOMEK, "code": code_in(reset)})

    assert refused.json()["code"] == "code_incorrect"


# ---------------------------------------------------------------------------
# An address that became an account meanwhile: sign in to accept
# ---------------------------------------------------------------------------


async def test_a_code_for_an_email_that_now_has_an_account_says_sign_in_to_accept(
    client, marta_invited
):
    _, email = marta_invited
    marta = await player_signs_up(client, email=MARTA, password="marta-plays-1")

    by_code = await client.post(CLAIM, json={"email": MARTA, "code": code_in(email)})
    by_link = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )

    assert by_code.status_code == by_link.status_code == 409
    assert by_code.json()["code"] == by_link.json()["code"] == "sign_in_to_accept"
    # And signed in, the invitation is hers to accept.
    (pending,) = (await me(client, marta))["profiles"]["pending_invitations"]
    assert pending["club_name"] == "Ogrody 33"


# ---------------------------------------------------------------------------
# An existing account: the pending invitation, and accepting it
# ---------------------------------------------------------------------------


async def test_an_existing_player_finds_the_invitation_on_me_and_accepts_it(
    client, desk, club_id
):
    tomek = await player_signs_up(client)
    row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)

    before = (await me(client, tomek))["profiles"]
    accepted = await client.post(accept_path(row["id"]), headers=tomek)
    after = (await me(client, tomek))["profiles"]

    (pending,) = before["pending_invitations"]
    assert pending["administrator_id"] == row["id"]
    assert pending["club_id"] == club_id
    assert pending["club_name"] == "Ogrody 33"
    assert pending["expires_at"] is not None
    assert before["administers"] == []
    assert before["acts_as_player"] is True
    assert accepted.status_code == 200, accepted.text
    assert accepted.json() == after
    assert after == {
        "acts_as_player": True,
        "administers": [{"club_id": club_id, "club_name": "Ogrody 33"}],
        "pending_invitations": [],
    }
    assert (await client.get(profile_at(club_id), headers=tomek)).status_code == 200


async def test_accepting_twice_is_the_same_answer(client, desk):
    tomek = await player_signs_up(client)
    row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)
    first = await client.post(accept_path(row["id"]), headers=tomek)

    second = await client.post(accept_path(row["id"]), headers=tomek)

    assert second.status_code == 200
    assert second.json() == first.json()


async def test_an_expired_invitation_leaves_me_and_cannot_be_accepted(
    client, desk, clock
):
    tomek = await player_signs_up(client)
    row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)
    clock.move(timedelta(hours=72))

    pending = (await me(client, tomek))["profiles"]["pending_invitations"]
    refused = await client.post(accept_path(row["id"]), headers=tomek)

    assert pending == []
    assert refused.status_code == 409
    assert refused.json()["code"] == "invitation_expired"


async def test_nobody_accepts_an_invitation_addressed_to_somebody_else(client, desk):
    await player_signs_up(client)
    row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)
    ania = await player_signs_up(
        client, email="ania@example.com", password="ania-pad-1"
    )

    refused = await client.post(accept_path(row["id"]), headers=ania)

    assert refused.status_code == 404
    assert refused.json()["code"] == "invitation_not_found"
    assert (await me(client, ania))["profiles"]["pending_invitations"] == []


async def test_a_removed_invitation_cannot_be_accepted(client, desk):
    tomek = await player_signs_up(client)
    row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)
    await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    refused = await client.post(accept_path(row["id"]), headers=tomek)

    assert refused.status_code == 404
    assert refused.json()["code"] == "invitation_not_found"


# ---------------------------------------------------------------------------
# The administrator guard
# ---------------------------------------------------------------------------


async def test_the_guard_refuses_somebody_who_never_ran_the_club(client, club_id):
    tomek = await player_signs_up(client)

    refused = await client.get(profile_at(club_id), headers=tomek)

    assert refused.status_code == 403
    assert refused.json()["code"] == "not_an_administrator"


async def test_the_guard_refuses_an_invited_person_who_has_not_accepted(
    client, desk, club_id
):
    tomek = await player_signs_up(client)
    await invites(client, desk, name="Tomek Kowalski", email=TOMEK)

    refused = await client.get(profile_at(club_id), headers=tomek)

    assert refused.json()["code"] == "not_an_administrator"


async def test_the_guard_answers_each_club_for_itself(client, desk, club_id, mailbox):
    """Marta at Ogrody 33 and Marta at Bonarka Arena are two administratorships:
    removal at one leaves the other standing."""

    bonarka_id, bonarka = await club_signs_up(
        client, name="Bonarka Arena", email="desk@bonarka.pl"
    )
    ogrody_row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await invites(client, bonarka, name="Marta Wójcik", email=MARTA)
    email = (await mailbox.to(MARTA))[0]
    set_ = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )
    marta = {"Authorization": f"Bearer {set_.json()['access_token']}"}
    (bonarka_invitation,) = (await me(client, marta))["profiles"]["pending_invitations"]
    await client.post(
        accept_path(bonarka_invitation["administrator_id"]), headers=marta
    )

    await client.delete(f"{ADMINISTRATORS}/{ogrody_row['id']}", headers=desk)

    assert (await client.get(profile_at(club_id), headers=marta)).status_code == 403
    assert (await client.get(profile_at(bonarka_id), headers=marta)).status_code == 200
    assert (await me(client, marta))["profiles"]["administers"] == [
        {"club_id": bonarka_id, "club_name": "Bonarka Arena"}
    ]


# ---------------------------------------------------------------------------
# Start playing: the attestation, then a nickname
# ---------------------------------------------------------------------------


async def test_an_administrator_attests_then_names_herself_with_only_a_nickname(
    client, marta_invited
):
    _, email = marta_invited
    set_ = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )
    marta = {"Authorization": f"Bearer {set_.json()['access_token']}"}

    attested = await client.post(ATTEST, headers=marta, json={"adult_attested": True})
    again = await client.post(ATTEST, headers=marta, json={"adult_attested": True})
    account = await me(client, marta)
    named = await client.put(
        NAME_ME, headers=marta, json={"name": account["name"], "nickname": "marta"}
    )

    assert attested.status_code == again.status_code == 204
    assert account["adult_attested"] is True
    assert account["profiles"]["acts_as_player"] is True
    assert named.status_code == 200, named.text
    assert (await me(client, marta))["nickname"] == "marta"


async def test_an_attestation_that_says_no_is_refused(client, marta_invited):
    _, email = marta_invited
    set_ = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )
    marta = {"Authorization": f"Bearer {set_.json()['access_token']}"}

    refused = await client.post(ATTEST, headers=marta, json={"adult_attested": False})

    assert refused.status_code == 400
    assert refused.json()["code"] == "adult_attestation_required"
    assert (await me(client, marta))["adult_attested"] is False


async def test_a_player_who_signed_up_has_attested_already(client):
    tomek = await player_signs_up(client)

    assert (await me(client, tomek))["adult_attested"] is True


# ---------------------------------------------------------------------------
# No secret outlives its email
# ---------------------------------------------------------------------------


async def test_no_link_code_or_ticket_ever_enters_an_event(
    client, marta_invited, mailbox, session_factory
):
    """``docs/adr/0184`` §4: events record *that* an invitation was issued,
    resent, accepted — never what opens it."""

    _, email = marta_invited
    token, code = token_in(email), code_in(email)
    ticket = (await client.post(CLAIM, json={"email": MARTA, "code": code})).json()[
        "ticket"
    ]
    await client.post(PASSWORD, json={"ticket": ticket, "password": MARTA_PASSWORD})
    await mailbox.drain()

    async with session_factory() as session:
        stored = (await session.execute(select(EventStoreORM))).scalars().all()
        queued = (await session.execute(select(EventOutboxORM))).scalars().all()
    recorded = "\n".join(repr(row.payload) for row in [*stored, *queued])

    assert "invitation_accepted" in recorded or "administrator_id" in recorded
    for secret in (token, code, ticket):
        assert secret not in recorded


# ---------------------------------------------------------------------------
# No Skill rating and no Player profile without the attestation
# ---------------------------------------------------------------------------


async def test_nothing_player_side_begins_before_the_attestation(
    client, marta_invited
):
    """``docs/adr/0185`` §5: an account an invitation opened holds no
    attestation, and neither an assessment nor a Player profile can begin
    until it has given one — the invariant every sign-up used to keep by
    construction."""

    from tests.api.matchmaking_world import commit_profile

    _, email = marta_invited
    set_ = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )
    token = set_.json()["access_token"]
    marta = {"Authorization": f"Bearer {token}"}

    assessment = await client.post(
        "/api/v1/assessments", json={"sport": "PADEL"}, headers=marta
    )
    profile = await client.post(
        "/api/v1/players/me/profile",
        json={"social_tag_ids": []},
        headers={**marta, "Idempotency-Key": "before-attesting"},
    )

    assert assessment.status_code == 403, assessment.text
    assert assessment.json()["code"] == "adult_attestation_missing"
    assert profile.status_code == 403, profile.text
    assert profile.json()["code"] == "adult_attestation_missing"

    await client.post(ATTEST, headers=marta, json={"adult_attested": True})
    await client.put(
        NAME_ME, headers=marta, json={"name": "Marta Wójcik", "nickname": "marta"}
    )

    started = await client.post(
        "/api/v1/assessments", json={"sport": "PADEL"}, headers=marta
    )
    assert started.status_code == 201, started.text
    await commit_profile(client, token)
