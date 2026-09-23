"""Mark a player as a Tester, or clear the mark — what ``make tester`` runs.

A **Tester** is a player whose account carries the tester mark: a real player
who may be given a feature before anyone else (``docs/adr/0180`` §9). The mark
is **the backend's and never the player's**, so there is no route that sets it:
an admin command drives this use case and nothing else does, and the player app
only reads the answer, as ``is_tester`` on its own ``GET /users/me``.

The player is named **by account id or by email, as the operator typed it**, and
:class:`AccountReference` is what reads which of the two it is — so the command
line and the tests hand over one string and ask one question. A string that is
neither, like one that is either and finds nobody, is ``UnknownPlayer``.

Written like the naming beside it: the ``User`` is replayed from its own stream
for the version the append expects, and **the projection is written in the same
transaction as the event**, because the row is what every route's ``User`` is
read from and what ``/me`` answers ``is_tester`` off. Asking for the mark a
player already holds is admitted and records nothing — the aggregate's own
idempotence — and the answer says so, so the operator is told rather than left
to wonder whether a second run did anything.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore, UnitOfWork
from app.kernel import Clock
from app.modules.users.application.commands import SetTesterMarkCommand
from app.modules.users.application.user_stream import USER_AGGREGATE, replay_user
from app.modules.users.domain.errors import UnknownPlayer
from app.modules.users.domain.events import UserMarkedAsTester, UserUnmarkedAsTester
from app.modules.users.domain.ports import UserRepository
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import AccountReference


@final
@dataclass(frozen=True, slots=True)
class TesterMark:
    """Where the mark stands once the act has landed, and whether it moved."""

    player_id: UUID
    email: str
    is_tester: bool
    #: ``False`` when the player already stood where they were asked to be, and
    #: nothing was recorded.
    changed: bool


class SetTesterMark:
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

    async def execute(self, command: SetTesterMarkCommand) -> TesterMark:
        found = await self._find(command.player)
        user = await replay_user(self._event_store, found.id)
        if user is None:
            # Found on the projection a moment ago; a row with no stream behind
            # it is a broken precondition, as it is for the naming.
            raise RuntimeError(f"user {found.id} has no stream to mark")
        expected_version = user.version

        if command.tester:
            user.mark_as_tester(occurred_at=self._clock.now())
        else:
            user.unmark_as_tester(occurred_at=self._clock.now())
        pending = user.pull_events()
        if pending:
            mark = pending[0]
            if not isinstance(mark, (UserMarkedAsTester, UserUnmarkedAsTester)):
                raise RuntimeError("the tester mark must record its own event")
            await self._event_store.append(
                aggregate_type=USER_AGGREGATE,
                aggregate_id=user.id,
                expected_version=expected_version,
                events=pending,
            )
            await self._users.project_tester_mark(mark)
            await self._events.publish_many(pending)
            await self._uow.commit()

        return TesterMark(
            player_id=user.id,
            email=user.email.value,
            is_tester=user.is_tester,
            changed=bool(pending),
        )

    async def _find(self, player: str) -> User:
        try:
            reference = AccountReference(player)
        except ValueError:
            # Neither an id nor an address: it names nobody, and to the operator
            # that is the same typo as an address nobody registered.
            raise UnknownPlayer(player) from None
        if isinstance(reference.names, UUID):
            found = await self._users.get_by_id(reference.names)
        else:
            found = await self._users.get_by_email(reference.names.value)
        if found is None:
            raise UnknownPlayer(player)
        return found
