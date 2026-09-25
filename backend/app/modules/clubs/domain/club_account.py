"""The Club account — the club's sign-in, an aggregate of its own.

**One email and one password, shared by the desk**, created with the club and
never folded into it (``docs/adr/0182`` §3): a club's facts are searched by every
player and its credentials must not sit on that stream. It is a separate
identity from every User — the same email may be an unrelated player's, with a
different password — and it signs in only on the club surface.

Its password follows **the player's rule and the player's hashing**
(``RawPassword``, ``HashedPassword``), because a second rule would be a second
thing to get wrong.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable, Optional
from uuid import UUID

from app.modules.clubs.domain.events import (
    ClubAccountOpened,
    ClubAccountPasswordChanged,
)
from app.modules.users.domain.value_objects import Email, HashedPassword
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class ClubAccount:
    """One club's sign-in, as its stream leaves it."""

    id: UUID
    club_id: UUID
    email: Email
    password_hash: HashedPassword
    #: When the password last changed (``docs/adr/0185`` §7), or ``None`` for
    #: the one it signed up with. A club access token issued before it is
    #: refused.
    credentials_changed_at: Optional[datetime] = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "ClubAccount":
        account = cls._empty()
        for event in events:
            account._apply(event)
        return account

    @classmethod
    def _empty(cls) -> "ClubAccount":
        account = cls.__new__(cls)
        account.version = 0
        account.credentials_changed_at = None
        account._events = EventRecorder()
        return account

    @classmethod
    def open(
        cls,
        *,
        account_id: UUID,
        club_id: UUID,
        email: Email,
        password_hash: HashedPassword,
        occurred_at: datetime,
    ) -> "ClubAccount":
        """Open the sign-in for a club that is signing up in the same act.

        Whether another club already signs in with this email is not this
        aggregate's to know: the use case reads the projection and refuses
        before this is reached, as ``RegisterUser`` does.
        """

        account = cls._empty()
        account._record_that(
            ClubAccountOpened(
                account_id=account_id,
                club_id=club_id,
                email=email.value,
                password_hash=password_hash.value,
                occurred_at=occurred_at,
            )
        )
        return account

    def change_password(
        self, *, password_hash: HashedPassword, occurred_at: datetime
    ) -> None:
        """A new password, and every older club session with it ended."""

        self._record_that(
            ClubAccountPasswordChanged(
                account_id=self.id,
                password_hash=password_hash.value,
                occurred_at=occurred_at,
            )
        )

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, ClubAccountOpened):
            self.id = event.account_id
            self.club_id = event.club_id
            self.email = Email(event.email)
            self.password_hash = HashedPassword(event.password_hash)
            self.version += 1
            return
        if isinstance(event, ClubAccountPasswordChanged):
            self.password_hash = HashedPassword(event.password_hash)
            self.credentials_changed_at = event.occurred_at
            self.version += 1
            return
        raise TypeError(f"Unsupported club account event {event!r}")
