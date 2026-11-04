"""What an invitation does to a User — **done here, on the User's own stream**.

The Administrators context decides *when* an account is opened or its password
cleared (``docs/adr/0184`` §2, §6); this context is the only one that writes a
User, so it does the writing, each change appended to the stream and projected
onto the row in the caller's transaction, exactly as the naming and *Forgot
password?* are. A password **set** goes through ``UserPasswordAccounts``, the
same as a reset's. Nothing here commits.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, final
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import Instant
from app.modules.users.application.user_stream import USER_AGGREGATE, replay_user
from app.modules.users.domain.events import AccountOpenedByInvitation, PasswordCleared
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import Email, HashedPassword
from app.shared.ids import new_uuid


@final
@dataclass(frozen=True, slots=True)
class InvitedAccount:
    """The account behind an address: which one, and whether anything signs
    in to it — false only between the club clearing its password and a new one
    being set."""

    id: UUID
    has_password: bool


class InvitationAccounts:
    def __init__(
        self,
        *,
        users: UserRepository,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._users = users
        self._event_store = event_store
        self._events = events

    async def holder_of(self, email: Email) -> Optional[InvitedAccount]:
        user = await self._users.get_by_email(email.value)
        if user is None:
            return None
        return InvitedAccount(id=user.id, has_password=user.has_password)

    async def open(self, *, email: Email, password_hash: str, at: Instant) -> UUID:
        """Open the account, holding **no player name**: the name the club typed
        stays on the Administrator (``docs/adr/0199`` §4)."""

        user = User.open_by_invitation(
            user_id=new_uuid(),
            email=email,
            password_hash=HashedPassword(password_hash),
            occurred_at=at,
        )
        pending = user.pull_events()
        opened = pending[0]
        if not isinstance(opened, AccountOpenedByInvitation):
            raise RuntimeError("an invitation's account must open with its event")
        await self._event_store.append(
            aggregate_type=USER_AGGREGATE,
            aggregate_id=user.id,
            expected_version=0,
            events=pending,
        )
        await self._users.project_opened_by_invitation(opened)
        await self._events.publish_many(pending)
        return user.id

    async def clear_password(self, account_id: UUID, *, at: Instant) -> None:
        user = await _the_user(self._event_store, account_id)
        expected_version = user.version
        user.clear_password(occurred_at=at)
        pending = user.pull_events()
        cleared = pending[0]
        if not isinstance(cleared, PasswordCleared):
            raise RuntimeError("clearing a password must record PasswordCleared")
        await self._event_store.append(
            aggregate_type=USER_AGGREGATE,
            aggregate_id=user.id,
            expected_version=expected_version,
            events=pending,
        )
        await self._users.project_password_cleared(cleared)
        await self._events.publish_many(pending)

    async def adult_attested(self, account_id: UUID) -> bool:
        """Read off the stream, the only place it is kept."""

        return bool((await _the_user(self._event_store, account_id)).adult_attested)


async def _the_user(event_store: DomainEventStore, account_id: UUID) -> User:
    user = await replay_user(event_store, account_id)
    if user is None:
        # An administratorship names the account it was taken up by, and
        # nothing deletes a User: one with no stream is a broken store.
        raise RuntimeError(f"user {account_id} has no stream")
    return user
