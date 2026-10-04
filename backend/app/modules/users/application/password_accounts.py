"""``PasswordAccounts`` for the player app: a recoverable password is a User's.

Answered here, beside ``UserSessionHolders``, because what *may still sign in*
means for a User is this context's to say — an active account — and the change
is an event on the User's own stream (``docs/adr/0185`` §7), projected onto the
row every player-surface request reads.
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import Instant
from app.modules.auth.domain.errors import AccountDisabled
from app.modules.auth.domain.ports import PasswordAccount
from app.modules.users.application.user_stream import USER_AGGREGATE, replay_user
from app.modules.users.domain.events import PasswordChanged
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.value_objects import HashedPassword


class UserPasswordAccounts:
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

    async def recoverable(self, email: str) -> Optional[PasswordAccount]:
        user = await self._users.get_by_email(email)
        if user is None or not user.is_active:
            return None
        return PasswordAccount(id=user.id, email=user.email.value)

    async def set_password(
        self, account_id: UUID, *, password_hash: str, at: Instant
    ) -> None:
        user = await replay_user(self._event_store, account_id)
        if user is None:
            # A credential names the account it was issued for, and nothing
            # deletes a User; a credential with no account behind it is a
            # broken precondition rather than a state a person can be in.
            raise RuntimeError(f"user {account_id} has no stream to set a password on")
        if not user.is_active:
            # Disabled after the email went out: refused exactly as the
            # sign-in this would otherwise open is.
            raise AccountDisabled()
        expected_version = user.version
        user.change_password(
            password_hash=HashedPassword(password_hash), occurred_at=at
        )
        pending = user.pull_events()
        changed = pending[0]
        if not isinstance(changed, PasswordChanged):
            raise RuntimeError("a password change must record PasswordChanged")
        await self._event_store.append(
            aggregate_type=USER_AGGREGATE,
            aggregate_id=user.id,
            expected_version=expected_version,
            events=pending,
        )
        await self._users.project_password_changed(changed)
        await self._events.publish_many(pending)
