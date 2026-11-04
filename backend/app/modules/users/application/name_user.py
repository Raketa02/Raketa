"""The naming — one act that says how people should see a player.

``PUT /api/v1/users/me/name`` with a **Nickname** and nothing else, for the
authenticated player, **repeatable**: a later change is the same act, and
keeping the nickname you already hold is admitted (``docs/adr/0199`` §3). The
one refusal that is this context's own is ``NicknameAlreadyTaken``, read
against the projection before anything is recorded.

**The projection is written in the same transaction as the event**, so the
nickname is taken the instant the commit lands and the next naming that asks
for it is refused — and a nickname given up is free the same instant.
"""

from __future__ import annotations

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.kernel import Clock
from app.modules.users.application.commands import NameUserCommand
from app.modules.users.application.user_stream import USER_AGGREGATE, replay_user
from app.modules.users.domain.errors import NicknameAlreadyTaken
from app.modules.users.domain.events import UserNamed
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.value_objects import Nickname


class NameUser:
    def __init__(
        self,
        users: UserRepository,
        event_store: DomainEventStore,
        uow: UnitOfWork,
        clock: Clock,
        events: DomainEventPublisher,
    ) -> None:
        self._users = users
        self._event_store = event_store
        self._uow = uow
        self._clock = clock
        self._events = events

    async def execute(self, command: NameUserCommand) -> Nickname:
        """The nickname this player is seen by once the act has landed,
        which is what the client shows back."""

        nickname = Nickname(command.nickname)

        holder = await self._users.get_by_nickname(nickname.value)
        if holder is not None and holder.id != command.user_id:
            raise NicknameAlreadyTaken()

        user = await replay_user(self._event_store, command.user_id)
        if user is None:
            # The route resolved this player from the projection a moment ago;
            # a projection row with no stream behind it is a broken precondition
            # and not a state a player can be in.
            raise RuntimeError(f"user {command.user_id} has no stream to name on")
        expected_version = user.version

        user.name_as(nickname=nickname, occurred_at=self._clock.now())
        pending = user.pull_events()
        if pending:
            named = pending[0]
            if not isinstance(named, UserNamed):
                raise RuntimeError("the naming must record UserNamed")
            await self._event_store.append(
                aggregate_type=USER_AGGREGATE,
                aggregate_id=user.id,
                expected_version=expected_version,
                events=pending,
            )
            await self._users.project_named(named)
            await self._events.publish_many(pending)
            await self._uow.commit()
        # Re-submitted unchanged, nothing was recorded and the answer is the
        # same: the nickname as it stands.
        return nickname
