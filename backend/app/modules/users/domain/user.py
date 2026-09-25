from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.modules.users.domain.errors import InactiveUserCannotBePromoted
from app.modules.users.domain.events import (
    PasswordChanged,
    UserDisabled,
    UserMarkedAsTester,
    UserNamed,
    UserPromotedToAdmin,
    UserRegistered,
    UserUnmarkedAsTester,
)
from app.modules.users.domain.value_objects import (
    AdultAttestation,
    Authority,
    Email,
    HashedPassword,
    Name,
    Nickname,
)
from app.shared.domain import DomainEvent, EventRecorder


@dataclass
class User:
    """Event-sourced user aggregate — no SQLAlchemy, no Pydantic, no HTTP.

    State changes are represented as domain events. New events are applied
    immediately and collected until the application layer appends them to the
    event store.

    **An account can exist unnamed** (``docs/adr/0171``). Sign-up creates one
    with credentials only, and ``name`` and ``nickname`` are ``None`` until the
    naming — the one act that sets both, and the only read where either may be
    null is the player's own ``/me``. Every other surface that names a player
    is reached through a gate that holds an unnamed account at the naming step.
    """

    id: UUID
    email: Email
    password_hash: HashedPassword
    name: Optional[Name] = None
    nickname: Optional[Nickname] = None
    authority: Authority = Authority.USER
    is_admin: bool = False
    is_active: bool = True
    #: The **tester mark** (``docs/adr/0180`` §9): a Tester may be given a
    #: feature before anyone else. Beside ``authority`` and never inside it.
    is_tester: bool = False
    #: When this account's credentials last changed (``docs/adr/0185`` §7): an
    #: access token issued before it is refused. ``None`` for an account whose
    #: password is the one it registered with.
    credentials_changed_at: Optional[datetime] = None
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
        password_hash: HashedPassword,
        attestation: AdultAttestation,
        occurred_at: datetime,
    ) -> "User":
        """Open an account, which is the one moment the age rule is enforced.

        The attestation arrives as a type that cannot be constructed from a
        missing or negative answer, so there is no branch here to forget: a
        registration either has one or was never built (``docs/adr/0124``).

        **Credentials only.** Who the player is arrives with :meth:`name_as`,
        in onboarding, and a fresh account is unnamed (``docs/adr/0171`` §2).
        """

        user = cls._empty()
        user._record_that(
            UserRegistered(
                user_id=user_id,
                email=email.value,
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
            self.name = None
            self.nickname = None
            self.password_hash = HashedPassword(event.password_hash)
            self.authority = Authority(event.authority)
            self.is_admin = event.is_admin
            self.is_active = event.is_active
            self.is_tester = False
            self.credentials_changed_at = None
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
        if isinstance(event, UserNamed):
            self.name = Name(event.name)
            self.nickname = Nickname(event.nickname)
            self.version += 1
            return
        if isinstance(event, UserDisabled):
            self.is_active = False
            self.version += 1
            return
        if isinstance(event, PasswordChanged):
            self.password_hash = HashedPassword(event.password_hash)
            self.credentials_changed_at = event.occurred_at
            self.version += 1
            return
        if isinstance(event, UserPromotedToAdmin):
            self.is_admin = True
            self.authority = Authority.ADMIN
            self.version += 1
            return
        if isinstance(event, UserMarkedAsTester):
            self.is_tester = True
            self.version += 1
            return
        if isinstance(event, UserUnmarkedAsTester):
            self.is_tester = False
            self.version += 1
            return
        raise TypeError(f"Unsupported user event {event!r}")

    def _ensure_registered(self) -> None:
        if not hasattr(self, "id"):
            raise RuntimeError("user aggregate is not registered")

    def name_as(
        self, *, name: Name, nickname: Nickname, occurred_at: datetime
    ) -> None:
        """The naming: how people should see this player (``docs/adr/0171`` §2).

        **Repeatable** — a later change is the same act, and the fold keeps the
        latest. Re-submitting the step unchanged is admitted and records
        nothing, as a second ``disable`` does: the stream records acts. The
        nickname's uniqueness is not this aggregate's to know: the use case
        reads it against the projection and refuses before this is reached. The
        name is checked against nobody.
        """

        self._ensure_registered()
        if self.name == name and self.nickname == nickname:
            return
        self._record_that(
            UserNamed(
                user_id=self.id,
                name=name.value,
                nickname=nickname.value,
                occurred_at=occurred_at,
            )
        )

    def change_password(
        self, *, password_hash: HashedPassword, occurred_at: datetime
    ) -> None:
        """A new password, which **signs this account out everywhere**
        (``docs/adr/0185`` §7): ``occurred_at`` becomes the instant before which
        no access token counts. Always recorded — setting the same password
        again is still somebody saying *end my other sessions*.

        Whether a disabled account may do this is the caller's question, asked
        before a credential is spent; this records the act."""

        self._ensure_registered()
        self._record_that(
            PasswordChanged(
                user_id=self.id,
                password_hash=password_hash.value,
                occurred_at=occurred_at,
            )
        )

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

    def mark_as_tester(self, *, occurred_at: datetime) -> None:
        """Give this account the tester mark (``docs/adr/0180`` §9).

        Idempotent, as ``disable`` is: marking a Tester again records nothing,
        because the stream records acts and this one changes nothing. A disabled
        account is not refused — the mark grants nothing, and it cannot sign in
        to be shown anything by it.
        """

        self._ensure_registered()
        if self.is_tester:
            return
        self._record_that(UserMarkedAsTester(user_id=self.id, occurred_at=occurred_at))

    def unmark_as_tester(self, *, occurred_at: datetime) -> None:
        """Clear the tester mark. Idempotent, like :meth:`mark_as_tester`."""

        self._ensure_registered()
        if not self.is_tester:
            return
        self._record_that(
            UserUnmarkedAsTester(user_id=self.id, occurred_at=occurred_at)
        )
