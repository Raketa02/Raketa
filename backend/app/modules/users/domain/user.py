from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from uuid import UUID

from app.modules.users.domain.errors import InactiveUserCannotBePromoted
from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    AccountOpenedByInvitationV1,
    AdultAttested,
    PasswordChanged,
    PasswordCleared,
    UserDisabled,
    UserNamed,
    UserNamedV1,
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

    **An account can exist without a nickname** (``docs/adr/0199`` §3).
    Sign-up creates one with credentials only, and so does an Invitation
    (§4), and ``nickname`` is ``None`` until the naming. **No account holds a
    player name**: the Name is retired, and a stored event that carried one is
    read with it ignored (§6). The only read where the nickname may be null is
    the player's own ``/me``; every other surface that names a player is
    reached through a gate that holds such an account at the naming step.
    """

    id: UUID
    email: Email
    #: ``None`` once the club's *Reset password* has cleared it
    #: (``docs/adr/0184`` §6): nothing signs in until a new one is set.
    password_hash: Optional[HashedPassword]
    nickname: Optional[Nickname] = None
    authority: Authority = Authority.USER
    is_admin: bool = False
    is_active: bool = True
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

        **Credentials only.** The nickname arrives with :meth:`name_as`, in
        onboarding, and a fresh account has none (``docs/adr/0199`` §3).
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
        password_hash: HashedPassword,
        occurred_at: datetime,
    ) -> "User":
        """Open the account an Invitation is for, as its person sets a password
        (``docs/adr/0184`` §2).

        **Credentials and nothing else**: no player name — the name the club
        typed is the Administrator's (``docs/adr/0199`` §4) — no nickname, and no
        Adult attestation, because running a club's groups asks nobody's age
        (``docs/adr/0185`` §5). The attestation and the nickname are asked at
        *Start playing*, before anything player-side. Whether the address
        already has an account is the caller's question, asked before this is
        reached.
        """

        user = cls._empty()
        user._record_that(
            AccountOpenedByInvitation(
                user_id=user_id,
                email=email.value,
                password_hash=password_hash.value,
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
            self.nickname = None
            self.password_hash = HashedPassword(event.password_hash)
            self.authority = Authority(event.authority)
            self.is_admin = event.is_admin
            self.is_active = event.is_active
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
        # A first-version row carried the name the club typed, and it is read
        # with that name ignored (``docs/adr/0199`` §6).
        if isinstance(event, (AccountOpenedByInvitation, AccountOpenedByInvitationV1)):
            self.id = event.user_id
            self.email = Email(event.email)
            self.nickname = None
            self.password_hash = HashedPassword(event.password_hash)
            self.authority = Authority.USER
            self.is_admin = False
            self.is_active = True
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
        # A first-version naming carried a Name beside the nickname, and it is
        # read with the name ignored (``docs/adr/0199`` §6).
        if isinstance(event, (UserNamed, UserNamedV1)):
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

    def name_as(self, *, nickname: Nickname, occurred_at: datetime) -> None:
        """The naming: the nickname people see this player by
        (``docs/adr/0199`` §3).

        **Repeatable** — a later change is the same act, and the fold keeps the
        latest. Re-submitting the step unchanged is admitted and records
        nothing, as a second ``disable`` does: the stream records acts. The
        nickname's uniqueness is not this aggregate's to know: the use case
        reads it against the projection and refuses before this is reached.
        """

        self._ensure_registered()
        if self.nickname == nickname:
            return
        self._record_that(
            UserNamed(
                user_id=self.id,
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
