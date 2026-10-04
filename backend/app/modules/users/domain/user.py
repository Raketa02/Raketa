from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.modules.users.domain.errors import InactiveUserCannotBePromoted
from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    AdultAttested,
    PasswordChanged,
    PasswordCleared,
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
    #: ``None`` once the club's *Reset password* has cleared it
    #: (``docs/adr/0184`` §6): nothing signs in until a new one is set.
    password_hash: Optional[HashedPassword]
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
    #: Whether this account has given the **Adult attestation**
    #: (``docs/adr/0185`` §5), **as its stream tells it** — and ``None`` on a
    #: ``User`` read from the projection, which has no column for it. ``None``
    #: says *this read did not learn it*, never *nobody attested*: the one
    #: reader that needs it, ``/me``, replays the stream.
    adult_attested: Optional[bool] = None
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
    def open_by_invitation(
        cls,
        *,
        user_id: UUID,
        email: Email,
        name: Name,
        password_hash: HashedPassword,
        occurred_at: datetime,
    ) -> "User":
        """Open the account an Invitation is for, as its person sets a password
        (``docs/adr/0184`` §2).

        **Named by the club and holding nothing else**: the Name is the one the
        club typed, there is no Nickname, and there is no Adult attestation —
        running a club's groups asks nobody's age (``docs/adr/0185`` §5). The
        attestation is asked at *Start playing*, before anything player-side.
        Whether the address already has an account is the caller's question,
        asked before this is reached.
        """

        user = cls._empty()
        user._record_that(
            AccountOpenedByInvitation(
                user_id=user_id,
                email=email.value,
                password_hash=password_hash.value,
                name=name.value,
                occurred_at=occurred_at,
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
            # Folded since ``docs/adr/0185`` §5 made the attestation something
            # an account can give later, and *Start playing* asks whether it
            # has. **Only ``True`` is an attestation**: ``None`` is an account
            # registered before the question existed, which was never asked and
            # so is asked the first time it acts as a player — reading it as a
            # claim would be the backfill ``docs/adr/0124`` forbids. The
            # projection still has no column for it, which is why a ``User``
            # read from the row carries ``None`` there rather than a guess.
            self.adult_attested = event.adult_attested is True
            self.created_at = None
            self.updated_at = None
            self.version += 1
            return
        if isinstance(event, AccountOpenedByInvitation):
            self.id = event.user_id
            self.email = Email(event.email)
            self.name = Name(event.name)
            self.nickname = None
            self.password_hash = HashedPassword(event.password_hash)
            self.authority = Authority.USER
            self.is_admin = False
            self.is_active = True
            self.is_tester = False
            self.credentials_changed_at = None
            self.adult_attested = False
            self.created_at = None
            self.updated_at = None
            self.version += 1
            return
        if isinstance(event, AdultAttested):
            self.adult_attested = True
            self.version += 1
            return
        if isinstance(event, PasswordCleared):
            self.password_hash = None
            self.credentials_changed_at = event.occurred_at
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

    @property
    def has_password(self) -> bool:
        """Whether anything can sign in to this account — false only between
        the club clearing it and a new one being set."""

        return self.password_hash is not None

    def attest_adult(self, *, occurred_at: datetime) -> None:
        """The Adult attestation, given after the account was opened
        (``docs/adr/0185`` §5). The claim itself is the caller's to have built
        — an :class:`AdultAttestation`, which cannot be built from a *no*.

        **Once**: an account that has attested — at sign-up or here — records
        nothing, as a second ``disable`` does. ``adult_attested`` is only known
        on an aggregate replayed from its stream.
        """

        self._ensure_registered()
        if self.adult_attested is None:
            # Read from the projection, which does not know: attesting on that
            # would record a second attestation for an account that gave one.
            raise RuntimeError("the attestation is only known on a replayed stream")
        if self.adult_attested:
            return
        self._record_that(AdultAttested(user_id=self.id, occurred_at=occurred_at))

    def clear_password(self, *, occurred_at: datetime) -> None:
        """The club's *Reset password* (``docs/adr/0184`` §6): no password at
        all, and **signed out everywhere** from ``occurred_at``. Whether this
        account may be cleared — only one holding nothing but administrator
        profiles — is the caller's question, asked before this is reached.
        Always recorded, as a password change is: clearing again still ends
        whatever sessions were opened since."""

        self._ensure_registered()
        self._record_that(PasswordCleared(user_id=self.id, occurred_at=occurred_at))

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
