from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.modules.users.domain.errors import InactiveUserCannotBePromoted
from app.modules.users.domain.events import (
    UserDisabled,
    UserPromotedToAdmin,
    UserRegistered,
)
from app.modules.users.domain.value_objects import (
    AdultAttestation,
    Authority,
    Email,
    HashedPassword,
    Nickname,
)
from app.shared.domain import DomainEvent, EventRecorder


@dataclass
class User:
    """Event-sourced user aggregate — no SQLAlchemy, no Pydantic, no HTTP.

    State changes are represented as domain events. New events are applied
    immediately and collected until the application layer appends them to the
    event store.
    """

    id: UUID
    email: Email
    nickname: Nickname
    password_hash: HashedPassword
    authority: Authority = Authority.USER
    is_admin: bool = False
    is_active: bool = True
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    version: int = 0

    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "User":
        user = cls._empty()
        for event in events:
            user._apply(event)
        return user

    @classmethod
    def register(
        cls,
        *,
        user_id: UUID,
        email: Email,
        nickname: Nickname,
        password_hash: HashedPassword,
        attestation: AdultAttestation,
        occurred_at: datetime,
    ) -> "User":
        """Open an account, which is the one moment the age rule is enforced.

        The attestation arrives as a type that cannot be constructed from a
        missing or negative answer, so there is no branch here to forget: a
        registration either has one or was never built (``docs/adr/0124``).
        """

        user = cls._empty()
        user._record_that(
            UserRegistered(
                user_id=user_id,
                email=email.value,
                nickname=nickname.value,
                password_hash=password_hash.value,
                authority=Authority.USER.value,
                is_admin=False,
                is_active=True,
                occurred_at=occurred_at,
                adult_attested=attestation.value,
            )
        )
        return user

    @classmethod
    def _empty(cls) -> "User":
        user = cls.__new__(cls)
        user._events = EventRecorder()
        user.version = 0
        return user

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, UserRegistered):
            self.id = event.user_id
            self.email = Email(event.email)
            self.nickname = Nickname(event.nickname)
            self.password_hash = HashedPassword(event.password_hash)
            self.authority = Authority(event.authority)
            self.is_admin = event.is_admin
            self.is_active = event.is_active
            # ``adult_attested`` is deliberately not folded into state. It is a
            # precondition of the account existing, answered once and never
            # asked again — no later command reads it, and no rule anywhere
            # varies by it (``docs/adr/0124``). Holding it here would also make
            # it a field ``_to_domain`` cannot fill, because the projection has
            # no column for it: a ``User`` read back from the read model would
            # report *nobody attested* about a player who did. The stream is the
            # record, and the stream keeps it.
            self.created_at = None
            self.updated_at = None
            self.version += 1
            return
        if isinstance(event, UserDisabled):
            self.is_active = False
            self.version += 1
            return
        if isinstance(event, UserPromotedToAdmin):
            self.is_admin = True
            self.authority = Authority.ADMIN
            self.version += 1
            return
        raise TypeError(f"Unsupported user event {event!r}")

    def _ensure_registered(self) -> None:
        if not hasattr(self, "id"):
            raise RuntimeError("user aggregate is not registered")

    def disable(self, *, occurred_at: datetime) -> None:
        self._ensure_registered()
        if not self.is_active:
            return
        self._record_that(UserDisabled(user_id=self.id, occurred_at=occurred_at))

    def promote_to_admin(self, *, occurred_at: datetime) -> None:
        self._ensure_registered()
        if not self.is_active:
            raise InactiveUserCannotBePromoted()
        if self.authority == Authority.ADMIN:
            return
        self._record_that(
            UserPromotedToAdmin(
                user_id=self.id,
                occurred_at=occurred_at,
            )
        )
