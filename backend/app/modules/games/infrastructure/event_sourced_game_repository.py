"""The Game repository, over the event store.

The same fifteen lines the other aggregate repositories have — which aggregate
type the streams are filed under, that state is rebuilt by replaying them, and
what version the next append expects. ADR-0018 declined a generic event-sourced
base deliberately, and ``docs/adr/0137`` is this context's own answer to the
question that refusal kept open.

**Its own aggregate type**, spelled here once and nowhere else.

**One lookup by payload, and it is deliberate.** ``for_challenge`` is not *which
games is this player in* — that is a different question with a different port
(``GameDirectory``) — it is the read that makes the opening idempotent, keyed on
one challenge and answering with one game, in the transaction of the accept that
would otherwise open a second. Putting it anywhere but beside the write would
leave the invariant *one arrangement is one game* enforced by a caller.

**The version is recovered, not taken**, so this must be constructed **per
request** from the session, exactly as the event store dependency is.
"""

from __future__ import annotations

from dataclasses import fields
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.games.domain.events import GamePlanned
from app.modules.games.domain.game import Game

GAME_AGGREGATE = "game"


def _opening_key(name: str) -> str:
    """The JSON key the codec writes for the challenge, checked at import.

    ``for_challenge`` matches on a **serialized field name**, and what is
    avoidable about that coupling is it being *silent*: a renamed field makes
    this read answer ``None`` for ever, which does not look like a failure — it
    looks like *no game has been opened for this challenge yet*, and the next
    accept opens a second one. *One arrangement is one game* would stop holding
    with a green build, which is why the spelling is taken from the event class
    rather than trusted. The streams read guards its own key the same way.
    """

    if name not in {field.name for field in fields(GamePlanned)}:
        raise RuntimeError(
            f"GamePlanned has no field {name!r}: the idempotency read matches "
            "on it and would silently open a second game for one arrangement"
        )
    return name


CHALLENGE_ID_KEY = _opening_key("challenge_id")


class EventSourcedGameRepository:
    """``GameRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
        session: AsyncSession,
    ) -> None:
        self._event_store = event_store
        self._events = events
        self._session = session
        # Aggregate id -> the stream version this request has seen. Read by
        # ``save`` as the expected version.
        self._versions: dict[UUID, int] = {}

    async def load(self, game_id: UUID) -> Game | None:
        stored = await self._event_store.load_stream(
            aggregate_type=GAME_AGGREGATE,
            aggregate_id=game_id,
        )
        if not stored:
            return None
        game = Game.from_history(record.event for record in stored)
        self._remember(game)
        return game

    async def for_challenge(self, challenge_id: UUID) -> Game | None:
        """The game this challenge already opened, if it has.

        Matched on the **opening event's own scalar field**, so this is an
        equality rather than the substring the directory is reduced to: a
        challenge id is one value in one key, where a court is an array of codes.
        """

        found = await self._session.execute(
            select(EventStoreORM.aggregate_id)
            .where(
                EventStoreORM.aggregate_type == GAME_AGGREGATE,
                EventStoreORM.payload[CHALLENGE_ID_KEY].as_string()
                == str(challenge_id),
            )
            .limit(1)
        )
        game_id = found.scalars().first()
        return None if game_id is None else await self.load(game_id)

    async def save(self, game: Game) -> None:
        pending = game.pull_events()
        if not pending:
            return

        await self._event_store.append(
            aggregate_type=GAME_AGGREGATE,
            aggregate_id=game.id,
            expected_version=self._versions.get(game.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's —
        # and for the opening it is somebody else's use case entirely, because a
        # game and the acceptance that produced it commit together or not at all.
        self._remember(game)

    def _remember(self, game: Game) -> None:
        self._versions[game.id] = game.version
