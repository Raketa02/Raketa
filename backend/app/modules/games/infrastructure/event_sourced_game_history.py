"""``GameHistoryQuery`` and ``GameDirectory`` over the event log.

**Everything here folds the aggregate**, and that is the difference from
``challenges``' history read. There, an answer is a thing that happened *to the
court as it stood then*, so the walk carries the arrangement along with it; here
a game's line-up is **frozen at the plan** and cannot move, so today's court is
the court that played and the fold is the whole answer.

**Nothing is projected.** Every fact these reads publish — played or a ghost,
counted, confirmed, won or lost — is folded from the record against the caller's
clock, so a game past a deadline has moved in this answer whether or not anything
swept it. A projection storing the standing would be right until a deadline
passed, wrong until something rebuilt it, and believed throughout.

**One clock per read, taken from the caller.** All three reads take ``now``
rather than reading one, because a search that asked about counted games and
about familiarity in one request must get one instant's answer to both.

**Cost.** The same as ``challenges``' three reads and for the same reason:
bounded by how many games the platform has ever recorded, because a substring
match cannot use a B-tree.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Collection, Mapping, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import EventCodec
from app.kernel import Instant, Minutes
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind
from app.modules.games.domain.ports import (
    PLAYED_COUNTERPART_BOUND,
    RECENT_RESULTS,
    CountedResult,
    GameCounterpart,
    PlayedOutcome,
    PlayedTally,
)
from app.modules.games.domain.standing import GameStanding
from app.modules.games.infrastructure.game_streams import streams_seating


@final
class EventSourcedGameHistory:
    """``GameHistoryQuery`` and ``GameDirectory`` over ``event_store``.

    **One class for two ports, because both are one read of the log folded
    differently** and splitting them would run the same substring match twice for
    a screen that wants both. The ports stay separate: a caller that wants the
    counts has no business holding the aggregates.
    """

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    # -- GameDirectory ----------------------------------------------------

    async def playing(self, player_id: UUID) -> tuple[Game, ...]:
        """Every game this player was on the court of, folded whole."""

        return tuple(await self._games_of(player_id))

    # -- GameHistoryQuery -------------------------------------------------

    async def played_counterparts(
        self, player_id: UUID, *, now: Instant
    ) -> tuple[GameCounterpart, ...]:
        """Who this player has arranged games with, tallied by how they went.

        **A game is counted here whatever kind it was.** Familiarity is about two
        people having been on a court together, and a friendly puts them there
        exactly as a counted game does — it is the *Level* that a friendly leaves
        alone, not the acquaintance.

        A game still awaiting its entry is in **neither** tally: it is not a
        ghost until its window closes, and claiming it either way would publish a
        conclusion the clock has not reached.
        """

        tallies: dict[UUID, dict[PlayedOutcome, list[Instant]]] = defaultdict(
            lambda: defaultdict(list)
        )
        for game in await self._games_of(player_id):
            outcome = _pairwise_outcome(game, now)
            if outcome is None:
                continue
            at = game.played_at or game.planned_at
            for other in game.line_up.counterparts_of(player_id):
                tallies[other][outcome].append(at)

        counterparts = [
            GameCounterpart(
                player_id=other,
                outcomes={
                    outcome: PlayedTally(count=len(moments), last_at=max(moments))
                    for outcome, moments in seen.items()
                },
            )
            for other, seen in tallies.items()
        ]
        # **Newest first, then the bound** — in that order, because a bound
        # applied to an unordered list would drop an arbitrary half rather than
        # the oldest one, and the order is what makes a counterpart cut off by
        # the bound indistinguishable from one fully decayed by time.
        counterparts.sort(key=lambda one: (one.last_at, one.player_id), reverse=True)
        return tuple(counterparts[:PLAYED_COUNTERPART_BOUND])

    async def counted_games_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, int]:
        """How many counted games each of these people has played.

        **Every player asked about gets a count, and a zero is measured**: the
        games were counted and none of them was theirs. That is what separates
        this read from a Player Score, where a zero would be invented and the
        player is absent from the answer instead.
        """

        wanted = set(player_ids)
        counts = {player_id: 0 for player_id in wanted}
        if not wanted:
            return counts

        for game in await self._games_among(wanted):
            if game.kind is not GameKind.COUNTED or not game.was_played_at(now):
                continue
            for player_id in game.line_up.players & wanted:
                counts[player_id] += 1
        return counts

    async def recent_results_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, tuple[CountedResult, ...]]:
        """The last few counted results per player, oldest to newest.

        **Absent rather than empty** for a player with none, so *nothing to show*
        has one spelling. Trimmed to the newest few and then reversed, which is
        the only order that keeps *the last five* meaning the last five when
        somebody has fifty.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        found: dict[UUID, list[CountedResult]] = defaultdict(list)
        for game in await self._games_among(wanted):
            if game.kind is not GameKind.COUNTED:
                continue
            if game.standing_at(now) is not GameStanding.CONFIRMED:
                continue
            for player_id in game.line_up.players & wanted:
                outcome = game.outcome_for(player_id, now=now)
                if outcome is None:
                    continue
                found[player_id].append(
                    CountedResult(
                        game_id=game.id,
                        sport=game.sport,
                        outcome=outcome,
                        played_at=game.played_at or game.planned_at,
                    )
                )

        results: dict[UUID, tuple[CountedResult, ...]] = {}
        for player_id, rows in found.items():
            rows.sort(key=lambda one: (one.played_at, one.game_id))
            results[player_id] = tuple(rows[-RECENT_RESULTS:])
        return results

    async def late_change_threshold(self) -> Minutes | None:
        """``None``, and the reason is this context's own.

        A plan here is a line-up with a window and no time in it: an accepted seat
        cannot be withdrawn and there is nothing to move, so *late* has no
        referent and there is no number to publish. Absent rather than defaulted,
        because a number nobody measured is a number somebody picked.
        """

        return None

    # -- internals --------------------------------------------------------

    async def _games_of(self, player_id: UUID) -> list[Game]:
        return await self._games_among({player_id})

    async def _games_among(self, player_ids: Collection[UUID]) -> list[Game]:
        streams = await streams_seating(self._session, self._codec, player_ids)
        return [Game.from_history(events) for events in streams.values()]


def _pairwise_outcome(game: Game, now: Instant) -> PlayedOutcome | None:
    """What this game says about the people who were on its court.

    Three answers and not two: a game whose entry window is still open says
    **nothing yet** about the pair, and is left out rather than filed as either.
    """

    standing = game.standing_at(now)
    if standing is GameStanding.NEVER_PLAYED:
        return PlayedOutcome.PLANNED_NEVER_PLAYED
    if game.was_played_at(now):
        return PlayedOutcome.PLAYED
    return None


__all__ = ["EventSourcedGameHistory"]
