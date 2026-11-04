"""The Administrator, as its stream leaves it (``docs/adr/0184`` §1).

One per (club, email): *invited* — read as *expired* once its window has passed
— *active* once linked to an account, and *removed*, from which it may be
invited again on the same stream. **Expiry is derived and never recorded**: the
window is the invitation credential's own 72 hours, counted from the last time
the invitation went out.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.kernel import instant
from app.modules.administrators.domain.administrator import (
    Administrator,
    AdministratorStanding,
    INVITATION_WINDOW,
)
from app.modules.administrators.domain.errors import (
    AdministratorAlreadyActive,
    AdministratorAlreadyInvited,
    AdministratorHasNoAccount,
    InvitationExpired,
    InvitationNotPending,
)
from app.modules.administrators.domain.events import (
    AdministratorInvited,
    AdministratorPasswordReset,
    AdministratorRemoved,
    InvitationAccepted,
    InvitationResent,
)
from app.modules.auth.domain.one_time_credential import (
    LIFETIMES,
    CredentialPurpose,
)
from app.modules.administrators.domain.value_objects import Name
from app.modules.users.domain.value_objects import Email

NOW = instant(datetime(2026, 9, 25, 12, 0, tzinfo=timezone.utc))
CLUB = uuid4()
MARTA = uuid4()


def invited(at=NOW) -> Administrator:
    administrator = Administrator.invite(
        administrator_id=uuid4(),
        club_id=CLUB,
        email=Email("Marta@Ogrody33.pl"),
        name=Name("Marta  Wójcik"),
        occurred_at=at,
    )
    # Replayed, so every test starts from the stream rather than from the
    # object that recorded it.
    return Administrator.from_history(administrator.pull_events())


def test_a_club_invites_by_name_and_email_and_the_invitation_is_open_for_72_hours():
    administrator = Administrator.invite(
        administrator_id=uuid4(),
        club_id=CLUB,
        email=Email("Marta@Ogrody33.pl"),
        name=Name("Marta  Wójcik"),
        occurred_at=NOW,
    )

    (event,) = administrator.pull_events()
    assert isinstance(event, AdministratorInvited)
    assert (event.email, event.name) == ("marta@ogrody33.pl", "Marta Wójcik")
    assert administrator.standing(now=NOW) is AdministratorStanding.INVITED
    assert administrator.expires_at == NOW + timedelta(hours=72)
    assert administrator.account_id is None


def test_the_window_is_the_invitation_credential_s_own_lifetime():
    """One deadline, whether or not a credential was sent: an existing account's
    invitation carries none, and still lapses when a new person's would."""

    assert INVITATION_WINDOW == LIFETIMES[CredentialPurpose.INVITATION]


def test_an_invitation_past_its_window_reads_expired_and_nothing_was_recorded():
    administrator = invited()

    assert (
        administrator.standing(now=NOW + INVITATION_WINDOW)
        is AdministratorStanding.EXPIRED
    )
    assert administrator.pull_events() == []


def test_resending_opens_a_fresh_window_even_after_it_expired():
    administrator = invited()
    later = NOW + timedelta(days=5)

    administrator.resend(occurred_at=later)

    (event,) = administrator.pull_events()
    assert isinstance(event, InvitationResent)
    assert administrator.standing(now=later) is AdministratorStanding.INVITED
    assert administrator.expires_at == later + INVITATION_WINDOW


def test_accepting_links_the_account_and_makes_it_active():
    administrator = invited()

    administrator.accept(account_id=MARTA, now=NOW + timedelta(hours=1))

    (event,) = administrator.pull_events()
    assert isinstance(event, InvitationAccepted)
    assert event.account_id == MARTA
    assert administrator.standing(now=NOW) is AdministratorStanding.ACTIVE
    assert administrator.account_id == MARTA


def test_accepting_again_for_the_same_account_records_nothing():
    administrator = invited()
    administrator.accept(account_id=MARTA, now=NOW)
    administrator.pull_events()

    administrator.accept(account_id=MARTA, now=NOW)

    assert administrator.pull_events() == []


def test_an_expired_invitation_cannot_be_accepted():
    administrator = invited()

    with pytest.raises(InvitationExpired):
        administrator.accept(account_id=MARTA, now=NOW + INVITATION_WINDOW)


def test_a_removed_administrator_s_invitation_cannot_be_accepted():
    administrator = invited()
    administrator.remove(occurred_at=NOW)

    with pytest.raises(InvitationNotPending):
        administrator.accept(account_id=MARTA, now=NOW)


def test_an_active_administrator_is_not_resent_an_invitation():
    administrator = invited()
    administrator.accept(account_id=MARTA, now=NOW)

    with pytest.raises(AdministratorAlreadyActive):
        administrator.resend(occurred_at=NOW)


def test_the_club_s_reset_puts_an_active_administrator_back_to_invited():
    administrator = invited()
    administrator.accept(account_id=MARTA, now=NOW)
    administrator.pull_events()
    later = NOW + timedelta(days=30)

    administrator.reset_password(occurred_at=later)

    (event,) = administrator.pull_events()
    assert isinstance(event, AdministratorPasswordReset)
    assert administrator.standing(now=later) is AdministratorStanding.INVITED
    assert administrator.expires_at == later + LIFETIMES[CredentialPurpose.CLUB_RESET]
    # Still the same account's: the reset recovers it, it does not replace it.
    assert administrator.account_id == MARTA
    assert administrator.reset_pending


def test_setting_the_password_after_a_reset_makes_it_active_again():
    administrator = invited()
    administrator.accept(account_id=MARTA, now=NOW)
    administrator.reset_password(occurred_at=NOW)

    administrator.accept(account_id=MARTA, now=NOW + timedelta(hours=1))

    assert administrator.standing(now=NOW) is AdministratorStanding.ACTIVE
    assert not administrator.reset_pending


def test_an_invitation_nobody_has_answered_holds_no_account_to_reset():
    with pytest.raises(AdministratorHasNoAccount):
        invited().reset_password(occurred_at=NOW)


def test_removal_ends_it_and_a_removed_administrator_is_not_standing():
    administrator = invited()
    administrator.accept(account_id=MARTA, now=NOW)

    administrator.remove(occurred_at=NOW)

    assert isinstance(administrator.pull_events()[-1], AdministratorRemoved)
    assert administrator.standing(now=NOW) is AdministratorStanding.REMOVED


def test_a_removed_person_may_be_invited_again_on_the_same_stream():
    administrator = invited()
    administrator.accept(account_id=MARTA, now=NOW)
    administrator.remove(occurred_at=NOW)
    administrator.pull_events()
    later = NOW + timedelta(days=10)

    administrator.invite_again(name=Name("Marta W."), occurred_at=later)

    (event,) = administrator.pull_events()
    assert isinstance(event, AdministratorInvited)
    assert administrator.standing(now=later) is AdministratorStanding.INVITED
    assert administrator.name == Name("Marta W.")
    assert administrator.account_id is None


@pytest.mark.parametrize(
    ("accepted", "refusal"),
    [(False, AdministratorAlreadyInvited), (True, AdministratorAlreadyActive)],
)
def test_an_email_already_invited_or_active_here_is_not_invited_again(
    accepted, refusal
):
    administrator = invited()
    if accepted:
        administrator.accept(account_id=MARTA, now=NOW)

    with pytest.raises(refusal):
        administrator.invite_again(name=Name("Marta"), occurred_at=NOW)


def test_an_expired_invitation_is_still_invited_and_is_refused_as_one():
    """*Already invited* covers *expired*: the desk resends rather than
    inviting the same address a second time."""

    administrator = invited()

    with pytest.raises(AdministratorAlreadyInvited):
        administrator.invite_again(
            name=Name("Marta"), occurred_at=NOW + timedelta(days=9)
        )
