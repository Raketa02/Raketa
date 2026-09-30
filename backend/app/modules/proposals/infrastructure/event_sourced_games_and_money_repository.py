"""A player's Games & money: one stream per player, filed under their own id.

The same shape as the other aggregate repositories — the aggregate type spelled
once, state rebuilt by replay, the version remembered from the load and expected
by the append (``docs/adr/0018``). **``load`` answers the defaults for a stream
never written**, as a Payment method's and a club's courts' do: a player who
never opened the screen has chosen nothing, and two games a week with every card
shown is what nothing means.

**No projection**: the deck reads one player's settings, and a stream read is
one query.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.proposals.domain.games_and_money import GamesAndMoney

GAMES_AND_MONEY_AGGREGATE = "games_and_money"


@final
class EventSourcedGamesAndMoneyRepository:
    """``GamesAndMoneyRepository`` over ``DomainEventStore``."""

    def __init__(
        self, *, event_store: DomainEventStore, events: DomainEventPublisher
    ) -> None:
        self._event_store = event_store
        self._events = events
        self._versions: dict[UUID, int] = {}

    async def load(self, player_id: UUID) -> GamesAndMoney:
        stored = await self._event_store.load_stream(
            aggregate_type=GAMES_AND_MONEY_AGGREGATE, aggregate_id=player_id
        )
        settings = GamesAndMoney.from_history(
            player_id, (record.event for record in stored)
        )
        self._versions[player_id] = settings.version
        return settings

    async def save(self, settings: GamesAndMoney) -> None:
        pending = settings.pull_events()
        if not pending:
            return
        await self._event_store.append(
            aggregate_type=GAMES_AND_MONEY_AGGREGATE,
            aggregate_id=settings.player_id,
            expected_version=self._versions.get(settings.player_id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's.
        self._versions[settings.player_id] = settings.version
