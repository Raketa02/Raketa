"""The Administrator's stream (``docs/adr/0184`` §1).

**Events record *that*, never *what opens it*** (``docs/adr/0184`` §4): that an
invitation went out, went out again, was accepted, or was reset — and never the
link, the code or the ticket, which live in ``one_time_credentials`` and die
with their lifetime. Whether an invitation went to a new person with a code or
to an existing account without one is not recorded either: it is decided from
the account at the moment of sending, and no reader asks it afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AdministratorInvited:
    """The club named a person, **by name and email and nothing else**
    (``docs/adr/0184`` §2). The first event of the stream — and, after a
    removal, the event that opens it again: a person invited twice is one
    Administrator, keyed by (club, email)."""

    administrator_id: UUID
    club_id: UUID
    email: str
    name: str
    occurred_at: datetime


@dataclass(frozen=True)
class InvitationResent:
    """The club sent the invitation again: a fresh 72 hours from here."""

    administrator_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class InvitationAccepted:
    """The person took the invitation up — by setting a password through it,
    which opened or recovered their account, or by accepting it in the app on
    the account whose email it names — and the Administrator is **active**,
    linked to ``account_id``."""

    administrator_id: UUID
    account_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AdministratorPasswordReset:
    """The club's *Reset password* (``docs/adr/0184`` §6): the account's
    password is cleared, it is signed out everywhere, and the Administrator is
    **invited** again with a fresh 72 hours. The account stays linked — the
    reset recovers it rather than replacing it."""

    administrator_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class AdministratorRemoved:
    """The club ended the administratorship (``docs/adr/0184`` §7). The
    person's player side is untouched; the next administrator request is
    refused."""

    administrator_id: UUID
    occurred_at: datetime
