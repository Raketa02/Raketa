"""The Administrator aggregate — a person acting for one club (``docs/adr/0184``).

**One per (club, email)**, keyed by the email rather than the account, because
the club types an email and the account may not exist yet. A person running two
clubs' groups is two Administrators. Its stored state is one of three —
*invited*, *active*, *removed* — and a fourth reading is **derived and never
recorded**: an invitation past its window reads *expired* (§1).

**The window is the invitation credential's own lifetime**, counted from the
last time the invitation went out — the invite, a resend, or the club's reset.
A new person's email carries a credential that dies at exactly that instant;
an existing account's carries none (``docs/adr/0186`` §3), and its invitation
lapses at the same instant all the same, so there is one deadline to read.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Final, Iterable, Optional
from uuid import UUID

from app.kernel import Instant, instant
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
from app.modules.users.domain.value_objects import Email, Name
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: How long an invitation stays open: the invitation credential's lifetime,
#: read from the one place it is written rather than restated.
INVITATION_WINDOW: Final[timedelta] = LIFETIMES[CredentialPurpose.INVITATION]

#: How long the invitation the club's reset sends stays open.
RESET_WINDOW: Final[timedelta] = LIFETIMES[CredentialPurpose.CLUB_RESET]

#: How often the projection's *last used* moves at most (``docs/adr/0184`` §1):
#: *active · this week* has hour granularity, and a write on every request
#: would add one to every read.
LAST_USED_GRANULARITY: Final = timedelta(hours=1)


class AdministratorState(StrEnum):
    """What the stream records. *Expired* is not among them."""

    INVITED = "INVITED"
    ACTIVE = "ACTIVE"
    REMOVED = "REMOVED"


class AdministratorStanding(StrEnum):
    """What the club website reads, now: the state, with an invitation past its
    window read as ``EXPIRED``."""

    INVITED = "INVITED"
    EXPIRED = "EXPIRED"
    ACTIVE = "ACTIVE"
    REMOVED = "REMOVED"


def standing_of(
    state: AdministratorState, *, expires_at: Optional[Instant], now: Instant
) -> AdministratorStanding:
    """The one reading of a state at an instant — the aggregate's and the
    projection's alike, so the club's list and the rules cannot disagree about
    when an invitation expired. The same comparison a credential's deadline
    uses: at the instant itself, it has expired."""

    if state is AdministratorState.ACTIVE:
        return AdministratorStanding.ACTIVE
    if state is AdministratorState.REMOVED:
        return AdministratorStanding.REMOVED
    if expires_at is not None and now >= expires_at:
        return AdministratorStanding.EXPIRED
    return AdministratorStanding.INVITED


@dataclass
class Administrator:
    """One administratorship, as its stream leaves it."""

    id: UUID
    club_id: UUID
    email: Email
    #: The name the club typed. It becomes the account's Name when the person
    #: is new to Raketa (``docs/adr/0185`` §4), and is what the club's list says.
    name: Name
    state: AdministratorState
    #: The account this administratorship belongs to — set when the invitation
    #: is taken up, and kept through the club's reset, which recovers that
    #: account rather than replacing it.
    account_id: Optional[UUID] = None
    #: When the invitation last sent stops being answerable.
    expires_at: Optional[Instant] = None
    #: Whether what is waiting is the club's reset rather than an invitation:
    #: a resend of it is a reset email, as the original was.
    reset_pending: bool = False
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Administrator":
        administrator = cls._empty()
        for event in events:
            administrator._apply(event)
        return administrator

    @classmethod
    def _empty(cls) -> "Administrator":
        administrator = cls.__new__(cls)
        administrator.version = 0
        administrator.account_id = None
        administrator.expires_at = None
        administrator.reset_pending = False
        administrator._events = EventRecorder()
        return administrator

    @classmethod
    def invite(
        cls,
        *,
        administrator_id: UUID,
        club_id: UUID,
        email: Email,
        name: Name,
        occurred_at: datetime,
    ) -> "Administrator":
        """The club names a person (``docs/adr/0184`` §2). Whether this email
        already has an Administrator at this club is the caller's question: one
        that exists is invited again through :meth:`invite_again`."""

        administrator = cls._empty()
        administrator._record_that(
            AdministratorInvited(
                administrator_id=administrator_id,
                club_id=club_id,
                email=email.value,
                name=name.value,
                occurred_at=occurred_at,
            )
        )
        return administrator

    def standing(self, *, now: Instant) -> AdministratorStanding:
        return standing_of(self.state, expires_at=self.expires_at, now=now)

    def invite_again(self, *, name: Name, occurred_at: datetime) -> None:
        """Invite a removed person again, on the same stream (``docs/adr/0184``
        §1). Refused while they are invited — *expired* included — or active:
        the email is already here."""

        self._refuse_unless_removed()
        self._record_that(
            AdministratorInvited(
                administrator_id=self.id,
                club_id=self.club_id,
                email=self.email.value,
                name=name.value,
                occurred_at=occurred_at,
            )
        )

    def resend(self, *, occurred_at: datetime) -> None:
        """Send the invitation again, with a fresh window — *invited* and
        *expired* alike (``docs/adr/0184`` §2)."""

        if self.state is AdministratorState.ACTIVE:
            raise AdministratorAlreadyActive()
        if self.state is AdministratorState.REMOVED:
            raise InvitationNotPending()
        self._record_that(
            InvitationResent(administrator_id=self.id, occurred_at=occurred_at)
        )

    def accept(self, *, account_id: UUID, now: Instant) -> None:
        """The invitation taken up by ``account_id``: the Administrator is
        **active**. Accepting again on the same account records nothing."""

        if self.state is AdministratorState.ACTIVE and self.account_id == account_id:
            return
        if self.state is not AdministratorState.INVITED:
            raise InvitationNotPending()
        if self.standing(now=now) is AdministratorStanding.EXPIRED:
            raise InvitationExpired()
        self._record_that(
            InvitationAccepted(
                administrator_id=self.id, account_id=account_id, occurred_at=now
            )
        )

    def reset_password(self, *, occurred_at: datetime) -> None:
        """The club's *Reset password* (``docs/adr/0184`` §6), recorded here as
        the Administrator going back to *invited*. **Whether the account may be
        reset** — only one holding nothing but administrator profiles — is a
        fact about the account, and the caller's to have asked; this refuses
        only what the stream itself can see: nobody has an account yet."""

        if self.state is AdministratorState.REMOVED:
            raise InvitationNotPending()
        if self.account_id is None:
            raise AdministratorHasNoAccount()
        self._record_that(
            AdministratorPasswordReset(
                administrator_id=self.id, occurred_at=occurred_at
            )
        )

    def remove(self, *, occurred_at: datetime) -> None:
        """End the administratorship (``docs/adr/0184`` §7). Removing a
        removed one records nothing."""

        if self.state is AdministratorState.REMOVED:
            return
        self._record_that(
            AdministratorRemoved(administrator_id=self.id, occurred_at=occurred_at)
        )

    def _refuse_unless_removed(self) -> None:
        if self.state is AdministratorState.ACTIVE:
            raise AdministratorAlreadyActive()
        if self.state is AdministratorState.INVITED:
            raise AdministratorAlreadyInvited()

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, AdministratorInvited):
            self.id = event.administrator_id
            self.club_id = event.club_id
            self.email = Email(event.email)
            self.name = Name(event.name)
            self.state = AdministratorState.INVITED
            self.account_id = None
            self.expires_at = _window_from(event.occurred_at, INVITATION_WINDOW)
            self.reset_pending = False
        elif isinstance(event, InvitationResent):
            window = RESET_WINDOW if self.reset_pending else INVITATION_WINDOW
            self.expires_at = _window_from(event.occurred_at, window)
        elif isinstance(event, InvitationAccepted):
            self.state = AdministratorState.ACTIVE
            self.account_id = event.account_id
            self.reset_pending = False
        elif isinstance(event, AdministratorPasswordReset):
            self.state = AdministratorState.INVITED
            self.expires_at = _window_from(event.occurred_at, RESET_WINDOW)
            self.reset_pending = True
        elif isinstance(event, AdministratorRemoved):
            self.state = AdministratorState.REMOVED
            self.reset_pending = False
        else:
            raise TypeError(f"Unsupported administrator event {event!r}")
        self.version += 1


def _window_from(sent_at: datetime, window: timedelta) -> Instant:
    return instant(sent_at + window)
