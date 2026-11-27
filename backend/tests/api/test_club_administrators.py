"""Ogrody 33 makes people administrators, on the club surface (``docs/adr/0184``).

The desk invites Marta, who is new to Raketa, and Tomek, who already plays. It
watches each of them go from *invited* to *active*, resends, resets Marta's
password — only because her account holds nothing but administrator profiles —
and removes either of them. Every route here is the club website's, under
``/api/v1/club``, and takes a club-audience token.
"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.core.config import get_settings
from tests.api.administration_world import (
    ADMINISTRATORS,
    ATTEST,
    CLAIM,
    CODE,
    MARTA,
    MARTA_PASSWORD,
    ME,
    PASSWORD,
    TOMEK,
    accept_path,
    club_signs_up,
    code_in,
    invites,
    link_in,
    listed,
    marta_sets_her_password,
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


def row_for(rows: list[dict], email: str) -> dict:
    (row,) = [row for row in rows if row["email"] == email]
    return row


# ---------------------------------------------------------------------------
# Invite
# ---------------------------------------------------------------------------


async def test_inviting_a_new_person_lists_them_invited_for_72_hours(
    client, desk, clock
):
    row = await invites(
        client, desk, name="  Marta   Wójcik ", email="Marta@Ogrody33.pl"
    )

    assert row["name"] == "Marta Wójcik"
    assert row["email"] == MARTA
    assert row["status"] == "INVITED"
    assert row["groups"] == []
    assert row["last_used_at"] is None
    assert row["can_reset_password"] is False
    rows = await listed(client, desk)
    assert [r["email"] for r in rows] == [MARTA]
    expires = rows[0]["expires_at"]
    assert expires.startswith((clock.now() + timedelta(hours=72)).isoformat()[:16]), (
        expires
    )


async def test_a_new_person_is_emailed_a_button_to_the_public_site_and_a_code(
    client, desk, mailbox
):
    await invites(client, desk, name="Marta Wójcik", email=MARTA)

    email = await the_email_to(mailbox, MARTA)
    public_site = get_settings().PUBLIC_SITE_URL.rstrip("/")
    assert link_in(email).startswith(f"{public_site}/invite/")
    assert len(code_in(email)) == 8
    assert "Ogrody 33" in email.subject
    assert "Marta Wójcik" in email.text
    assert f'href="{link_in(email)}"' in email.html
    assert code_in(email) in email.html


async def test_the_way_to_the_code_box_makes_the_app_s_labels_stand_out(
    client, desk, mailbox
):
    """*Have an invitation code?* under *Sign in* is two labels inside one
    sentence, and the first ends in a question mark. They are what she has to
    find on the screen, so they are bold in the HTML and quoted in the plain
    text, which has no bold (#529 I2)."""

    await invites(client, desk, name="Marta Wójcik", email=MARTA)

    email = await the_email_to(mailbox, MARTA)
    assert (
        "tap <strong>Have an invitation code?</strong> under "
        "<strong>Sign in</strong>, and enter this code:" in email.html
    )
    assert (
        "tap “Have an invitation code?” under “Sign in”, and enter this code:"
        in email.text
    )


async def test_an_invitation_says_groups_and_never_whatsapp(client, desk, mailbox):
    """Where a club's players talk is the club's business: the invitation is to
    run its groups (#529 I4)."""

    await player_signs_up(client)
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await invites(client, desk, name="Tomek Kowalski", email=TOMEK)

    for address in (MARTA, TOMEK):
        email = await the_email_to(mailbox, address)
        assert "run its groups on Raketa" in email.text
        assert "WhatsApp" not in email.text
        assert "WhatsApp" not in email.html


async def test_an_existing_account_is_asked_to_accept_in_the_app_with_no_code(
    client, desk, mailbox
):
    await player_signs_up(client)

    await invites(client, desk, name="Tomek Kowalski", email=TOMEK)

    email = await the_email_to(mailbox, TOMEK)
    assert email.subject == "Ogrody 33 wants to make you an administrator"
    assert "/invite/" not in email.text
    assert code_in_nothing(email)
    # The button opens the app, on the scheme the app declares (#896).
    assert 'href="rakieta://"' in email.html


def code_in_nothing(email) -> bool:
    from tests.api.administration_world import CODE

    return CODE.search(email.text) is None


@pytest.mark.parametrize(
    ("payload", "code", "field"),
    [
        ({"name": "M", "email": MARTA}, "administrator_name_invalid", "name"),
        ({"name": "Marta", "email": "not-an-email"}, "email_invalid", "email"),
    ],
)
async def test_a_field_the_desk_has_to_correct_is_refused_under_it(
    client, desk, payload, code, field
):
    refused = await client.post(ADMINISTRATORS, headers=desk, json=payload)

    assert refused.status_code == 400, refused.text
    assert refused.json()["code"] == code
    assert refused.json()["details"] == {"field": field}


async def test_an_email_already_invited_here_is_refused_on_the_spot(
    client, desk, mailbox
):
    await invites(client, desk, name="Marta Wójcik", email=MARTA)

    again = await client.post(
        ADMINISTRATORS,
        headers=desk,
        json={"name": "Marta", "email": "MARTA@ogrody33.pl"},
    )

    assert again.status_code == 409
    assert again.json()["code"] == "administrator_already_invited"
    assert again.json()["details"] == {"field": "email"}
    assert len(await mailbox.to(MARTA)) == 1


async def test_an_email_already_active_here_is_refused_on_the_spot(
    client, desk, mailbox
):
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)

    again = await client.post(
        ADMINISTRATORS, headers=desk, json={"name": "Marta", "email": MARTA}
    )

    assert again.status_code == 409
    assert again.json()["code"] == "administrator_already_active"


async def test_another_club_may_invite_the_same_person(client, desk, mailbox):
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    _, bonarka = await club_signs_up(
        client, name="Bonarka Arena", email="desk@bonarka.pl"
    )

    assert (await invites(client, bonarka, name="Marta", email=MARTA))["status"] == (
        "INVITED"
    )
    assert [r["email"] for r in await listed(client, desk)] == [MARTA]


async def test_a_player_token_is_refused_on_the_club_surface(client, desk):
    player = await player_signs_up(client)

    refused = await client.get(ADMINISTRATORS, headers=player)

    assert refused.status_code == 401


# ---------------------------------------------------------------------------
# The list: invited, expired, active
# ---------------------------------------------------------------------------


async def test_the_list_reads_expired_once_the_72_hours_have_passed(
    client, desk, clock
):
    await invites(client, desk, name="Marta Wójcik", email=MARTA)

    clock.move(timedelta(hours=72, minutes=1))

    row = row_for(await listed(client, desk), MARTA)
    assert row["status"] == "EXPIRED"
    assert row["expires_at"] is not None


async def test_the_desk_watches_both_of_them_go_from_invited_to_active(
    client, desk, club_id, mailbox, clock
):
    tomek = await player_signs_up(client)
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    tomek_row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)

    await marta_sets_her_password(client, mailbox)
    accepted = await client.post(accept_path(tomek_row["id"]), headers=tomek)
    assert accepted.status_code == 200, accepted.text

    rows = await listed(client, desk)
    assert [(r["name"], r["status"]) for r in rows] == [
        ("Marta Wójcik", "ACTIVE"),
        ("Tomek Kowalski", "ACTIVE"),
    ]
    assert all(r["last_used_at"] is not None for r in rows)
    assert all(r["expires_at"] is None for r in rows)


async def test_last_used_moves_with_an_administrator_request_at_most_hourly(
    client, desk, club_id, mailbox, clock
):
    await invites(client, desk, name="Marta Wójcik", email=MARTA)
    marta = await marta_sets_her_password(client, mailbox)
    first = row_for(await listed(client, desk), MARTA)["last_used_at"]

    clock.move(timedelta(minutes=30))
    assert (await client.get(profile_at(club_id), headers=marta)).status_code == 200
    unchanged = row_for(await listed(client, desk), MARTA)["last_used_at"]

    clock.move(timedelta(hours=2))
    assert (await client.get(profile_at(club_id), headers=marta)).status_code == 200
    moved = row_for(await listed(client, desk), MARTA)["last_used_at"]

    assert unchanged == first
    assert moved > first


# ---------------------------------------------------------------------------
# Resend
# ---------------------------------------------------------------------------


async def test_resending_an_expired_invitation_opens_a_fresh_72_hours(
    client, desk, mailbox, clock
):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    old = await the_email_to(mailbox, MARTA)
    clock.move(timedelta(days=4))

    resent = await client.post(f"{ADMINISTRATORS}/{row['id']}/invitation", headers=desk)

    assert resent.status_code == 200, resent.text
    assert resent.json()["status"] == "INVITED"
    new = await the_email_to(mailbox, MARTA)
    assert token_in(new) != token_in(old)
    # The newest works, and the old one reads expired.
    stale = await client.post(
        PASSWORD, json={"token": token_in(old), "password": MARTA_PASSWORD}
    )
    assert stale.status_code == 409
    assert stale.json()["code"] == "credential_expired"


async def test_resending_to_somebody_already_active_is_refused(client, desk, mailbox):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)

    refused = await client.post(
        f"{ADMINISTRATORS}/{row['id']}/invitation", headers=desk
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "administrator_already_active"


async def test_another_club_s_administrator_is_not_found_here(client, desk):
    _, bonarka = await club_signs_up(
        client, name="Bonarka Arena", email="desk@bonarka.pl"
    )
    theirs = await invites(client, bonarka, name="Marta", email=MARTA)

    for refused in (
        await client.post(f"{ADMINISTRATORS}/{theirs['id']}/invitation", headers=desk),
        await client.post(
            f"{ADMINISTRATORS}/{theirs['id']}/password-reset", headers=desk
        ),
        await client.delete(f"{ADMINISTRATORS}/{theirs['id']}", headers=desk),
    ):
        assert refused.status_code == 404, refused.text
        assert refused.json()["code"] == "administrator_not_found"


# ---------------------------------------------------------------------------
# Reset password
# ---------------------------------------------------------------------------


async def test_an_administrator_only_account_can_be_reset(client, desk, mailbox, clock):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    marta = await marta_sets_her_password(client, mailbox)
    assert row_for(await listed(client, desk), MARTA)["can_reset_password"] is True
    clock.move(timedelta(minutes=1))

    reset = await client.post(
        f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk
    )

    assert reset.status_code == 200, reset.text
    assert reset.json()["status"] == "INVITED"
    # Signed out everywhere, and the old password opens nothing.
    assert (await client.get(ME, headers=marta)).status_code == 401
    old = await client.post(
        "/api/v1/auth/login", json={"email": MARTA, "password": MARTA_PASSWORD}
    )
    assert old.status_code == 401
    # A fresh 72 hours on the invitation's own page, with a code.
    email = await the_email_to(mailbox, MARTA)
    assert "/invite/" in link_in(email)
    assert len(code_in(email)) == 8
    clock.move(timedelta(minutes=1))
    again = await client.post(
        PASSWORD, json={"token": token_in(email), "password": "ogrody-marta-2"}
    )
    assert again.status_code == 200, again.text
    assert row_for(await listed(client, desk), MARTA)["status"] == "ACTIVE"
    assert await signs_in(client, MARTA, "ogrody-marta-2")


async def test_the_reset_is_refused_for_an_account_that_also_plays(
    client, desk, mailbox
):
    tomek = await player_signs_up(client)
    row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)
    await client.post(accept_path(row["id"]), headers=tomek)
    assert row_for(await listed(client, desk), TOMEK)["can_reset_password"] is False

    refused = await client.post(
        f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "administrator_also_plays"
    # Nothing moved: Tomek is still signed in and still active.
    assert (await client.get(ME, headers=tomek)).status_code == 200
    assert row_for(await listed(client, desk), TOMEK)["status"] == "ACTIVE"


async def test_the_reset_is_refused_once_an_administrator_has_started_playing(
    client, desk, mailbox
):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    marta = await marta_sets_her_password(client, mailbox)
    attested = await client.post(ATTEST, headers=marta, json={"adult_attested": True})
    assert attested.status_code == 204, attested.text

    refused = await client.post(
        f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "administrator_also_plays"


async def test_somebody_who_never_set_a_password_has_no_account_to_reset(client, desk):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)

    refused = await client.post(
        f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk
    )

    assert refused.status_code == 409
    assert refused.json()["code"] == "administrator_has_no_account"


async def test_resending_after_a_reset_retires_the_first_reset_s_link(
    client, desk, mailbox, clock
):
    """After the reset, the newest email is the only way in: the reset's own
    first email, still sitting in the inbox, opens nothing."""

    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)
    await client.post(f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk)
    first_reset = await the_email_to(mailbox, MARTA)

    await client.post(f"{ADMINISTRATORS}/{row['id']}/invitation", headers=desk)
    resent = await the_email_to(mailbox, MARTA)

    assert token_in(resent) != token_in(first_reset)
    stale = await client.post(
        PASSWORD, json={"token": token_in(first_reset), "password": "ogrody-marta-3"}
    )
    assert stale.json()["code"] == "credential_expired"


# ---------------------------------------------------------------------------
# Remove
# ---------------------------------------------------------------------------


async def test_removing_ends_the_administratorship_on_the_next_request(
    client, desk, club_id, mailbox
):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    marta = await marta_sets_her_password(client, mailbox)
    assert (await client.get(profile_at(club_id), headers=marta)).status_code == 200

    removed = await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    assert removed.status_code == 204
    guarded = await client.get(profile_at(club_id), headers=marta)
    assert guarded.status_code == 403
    assert guarded.json()["code"] == "not_an_administrator"
    assert await listed(client, desk) == []
    # The account stays, signed in: it simply holds no profile now.
    account = await me(client, marta)
    assert account["profiles"]["administers"] == []


async def test_removing_leaves_the_player_side_and_its_sessions_alone(
    client, desk, club_id
):
    tomek = await player_signs_up(client)
    row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)
    await client.post(accept_path(row["id"]), headers=tomek)

    await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    account = await me(client, tomek)
    assert account["profiles"]["acts_as_player"] is True
    assert account["profiles"]["administers"] == []
    assert (await client.get(profile_at(club_id), headers=tomek)).json()["code"] == (
        "not_an_administrator"
    )


async def test_removing_an_invited_person_retires_their_link(client, desk, mailbox):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    email = await the_email_to(mailbox, MARTA)

    await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    by_link = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )
    by_code = await client.post(CLAIM, json={"email": MARTA, "code": code_in(email)})
    assert by_link.json()["code"] == "credential_expired"
    assert by_code.json()["code"] == "credential_expired"


async def test_removing_an_administrator_emails_them_to_say_so(client, desk, mailbox):
    """The app hears a removal only on its next administrator request, and only
    while it is open: whoever is away would find out by their groups vanishing.
    So the email says it, and what stays (#529 N4)."""

    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)

    await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    email = await the_email_to(mailbox, MARTA)
    assert email.subject == "Ogrody 33 removed you as an administrator"
    assert "Hi Marta Wójcik" in email.text
    assert "You no longer run Ogrody 33's groups on Raketa" in email.text
    assert "Your Raketa account stays" in email.text
    assert "ask Ogrody 33 about it" in email.text
    # Nothing to open and nothing to type: it tells, and asks for nothing.
    assert "http" not in email.text
    assert "<a " not in email.html
    assert CODE.search(email.text) is None


async def test_removing_somebody_who_also_plays_emails_them_too(client, desk, mailbox):
    tomek = await player_signs_up(client)
    row = await invites(client, desk, name="Tomek Kowalski", email=TOMEK)
    await client.post(accept_path(row["id"]), headers=tomek)

    await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    email = await the_email_to(mailbox, TOMEK)
    assert email.subject == "Ogrody 33 removed you as an administrator"
    assert "anything you do on it as a player" in email.text


async def test_removing_somebody_whose_password_the_club_reset_says_removed(
    client, desk, mailbox
):
    """A reset puts her back to *invited*, but she ran its groups: what ends is
    an administratorship, not an invitation she never took up."""

    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)
    await client.post(f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk)

    await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    email = await the_email_to(mailbox, MARTA)
    assert email.subject == "Ogrody 33 removed you as an administrator"


async def test_removing_an_invited_person_tells_them_the_invitation_is_withdrawn(
    client, desk, mailbox
):
    """Their link would otherwise read *expired, ask the club to send a new
    one* — and the club is who withdrew it."""

    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)

    await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    email = await the_email_to(mailbox, MARTA)
    assert email.subject == "Ogrody 33 withdrew its invitation"
    assert "Hi Marta Wójcik" in email.text
    assert "no longer wants you to run its groups on Raketa" in email.text
    assert "The invitation it sent you no longer works." in email.text
    assert "http" not in email.text
    assert CODE.search(email.text) is None


async def test_a_removed_person_can_be_invited_again(client, desk, mailbox):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    await marta_sets_her_password(client, mailbox)
    await client.delete(f"{ADMINISTRATORS}/{row['id']}", headers=desk)

    again = await invites(client, desk, name="Marta W.", email=MARTA)

    assert again["id"] == row["id"]
    assert again["status"] == "INVITED"
    # Her account already exists, so this time the app is where she accepts.
    email = await the_email_to(mailbox, MARTA)
    assert email.subject == "Ogrody 33 wants to make you an administrator"


async def test_resending_a_still_open_invitation_moves_its_window(
    client, desk, mailbox, clock
):
    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    clock.move(timedelta(hours=10))

    resent = await client.post(f"{ADMINISTRATORS}/{row['id']}/invitation", headers=desk)

    assert resent.status_code == 200, resent.text
    assert resent.json()["status"] == "INVITED"
    assert resent.json()["expires_at"] > row["expires_at"]
    assert len(await mailbox.to(MARTA)) == 2


async def test_the_reset_ends_the_player_app_sessions_it_signs_out(
    client, desk, mailbox, clock
):
    """Signing out everywhere is both halves: the access token refused and the
    refresh token revoked, so nothing renews the session either."""

    row = await invites(client, desk, name="Marta Wójcik", email=MARTA)
    email = await the_email_to(mailbox, MARTA)
    set_ = await client.post(
        PASSWORD, json={"token": token_in(email), "password": MARTA_PASSWORD}
    )
    refresh_token = set_.json()["refresh_token"]
    clock.move(timedelta(minutes=1))

    await client.post(f"{ADMINISTRATORS}/{row['id']}/password-reset", headers=desk)

    renewed = await client.post(
        "/api/v1/auth/refresh", json={"refresh_token": refresh_token}
    )
    assert renewed.status_code == 401
    assert renewed.json()["code"] == "refresh_token_revoked"
