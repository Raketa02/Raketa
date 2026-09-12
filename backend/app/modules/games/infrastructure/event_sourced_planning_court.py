"""``PlanningCourt`` over the event log — *which games is this player arranging?*

**Its own class beside ``EventSourcedGameHistory`` rather than a third method on
it**, and the line between them is who asks. That class answers the four
questions the *platform* asks about a person's record — the pairwise history, the
counts, the run of form, the attendance — and every one of them is folded for a
consumer that already holds the person. This answers one question for one
consumer, on a **write** path, and it is the read that decides whether that write
may land.

**Nothing is projected and nothing is stored.** ``open_to_planning`` is
``AWAITING_ENTRY`` folded against the caller's own instant, exactly as every
other standing in this context is — so *are the slots frozen* has the same answer
at every instant and there is nothing for a sweep to correct.

**Cost.** One substring match over the game streams, the same as every read in
this context and for the same reason: the fold *is* the answer, and the index
that fixes it belongs with the first query that measures it.
"""

from __future__ import annotations

from typing import Mapping, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import EventCodec
from app.kernel import Instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.ports import PlannableGame
from app.modules.games.domain.standing import GameStanding
from app.modules.games.infrastructure.game_streams import streams_seating


@final
class EventSourcedPlanningCourt:
    """``PlanningCourt`` over ``event_store``."""

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    async def plannable_for(
        self, player_id: UUID, *, now: Instant
    ) -> Mapping[UUID, PlannableGame]:
        """Every game this player was on the court of, keyed by game id.

        **Open and history alike.** A plan is drawn beside a game whatever its
        standing, so filtering the frozen ones out here would make a plan vanish
        from the game screen that still reads it — and would leave the caller
        unable to tell *you are not on that court* from *that court is over*,
        which are the two different refusals it owes.
        """

        streams = await streams_seating(self._session, self._codec, {player_id})
        found: dict[UUID, PlannableGame] = {}
        for events in streams.values():
            game = Game.from_history(events)
            if player_id not in game.line_up.players:
                # A court they have since left (``docs/adr/0162``). The plan is
                # the game's, and the game is not theirs to plan any more.
                continue
            found[game.id] = PlannableGame(
                planned_at=game.planned_at,
                open_to_planning=(
                    game.standing_at(now) is GameStanding.AWAITING_ENTRY
                ),
            )
        return found
