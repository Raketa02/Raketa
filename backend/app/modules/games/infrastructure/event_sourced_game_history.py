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

**One clock per read, taken from the caller.** All four reads take ``now``
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
from app.kernel import Instant, Minutes, Sport
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind
from app.modules.games.domain.ports import (
    PLAYED_COUNTERPART_BOUND,
    RECENT_RESULTS,
    Attendance,
    CountedResult,
    GameCounterpart,
    PlayedOutcome,
    PlayedTally,
)
from app.modules.games.domain.standing import GameStanding
from app.modules.games.domain.windows import entry_closes_at
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

        found = await self._counted_results(wanted, now=now)
        return {
            player_id: tuple(rows[-RECENT_RESULTS:])
            for player_id, rows in found.items()
        }

    async def recent_results_in(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> tuple[CountedResult, ...]:
        """This player's last few counted results in one sport, oldest to newest.

        **Filtered before it is trimmed**, and that order is the whole reason
        this cannot be built out of the read above: that one answers at most five
        across every sport, so a caller filtering afterwards would show three
        results to somebody who has played thirty in the sport asked about.
        """

        found = await self._counted_results({player_id}, now=now)
        rows = [one for one in found.get(player_id, []) if one.sport is sport]
        return tuple(rows[-RECENT_RESULTS:])

    async def _counted_results(
        self, wanted: set[UUID], *, now: Instant
    ) -> dict[UUID, list[CountedResult]]:
        """Every confirmed counted result for these people, **oldest first.**

        The fold both reads above are trims of, written once so the two cannot
        come to two answers about what a counted result is. Untrimmed, because
        the two trim differently and one of them narrows first — a shared helper
        that had already cut to five would be the bug it exists to prevent.

        A player with none is **absent**, which is what lets the mapping read
        above keep one spelling for *nothing to show*.
        """

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
        for rows in found.values():
            # Sorted here rather than at each caller, so *oldest to newest* is
            # the fold's promise and not two of them.
            rows.sort(key=lambda one: (one.played_at, one.game_id))
        return found

    async def attendance_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, Attendance]:
        """What became of each of these people's arrangements — played, or ghosted.

        **The same fold as the pairwise read, counted per person instead of per
        pair**, and that is the whole difference between them: a four played once
        is one evening and three counterparts, so a *shows up* strand summed off
        ``played_counterparts`` would charge a doubles player three times for
        turning up once.

        **Absent rather than a measured zero**, unlike ``counted_games_for``
        above. A person nothing was ever arranged for has not failed to come, and
        a ``0/0`` published here would say they had.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        played: dict[UUID, int] = defaultdict(int)
        ghosts: dict[UUID, int] = defaultdict(int)
        latest: dict[UUID, Instant] = {}
        for game in await self._games_among(wanted):
            settled = _settled_arrangement(game, now)
            if settled is None:
                continue
            outcome, at = settled
            for player_id in game.line_up.players & wanted:
                if outcome is PlayedOutcome.PLAYED:
                    played[player_id] += 1
                else:
                    ghosts[player_id] += 1
                latest[player_id] = max(at, latest.get(player_id, at))

        return {
            player_id: Attendance(
                played=played[player_id],
                ghosts=ghosts[player_id],
                last_at=at,
            )
            for player_id, at in latest.items()
        }

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


def _settled_arrangement(
    game: Game, now: Instant
) -> tuple[PlayedOutcome, Instant] | None:
    """The same three answers, **with the moment the arrangement settled.**

    The pairwise read needs the outcome and dates it from the game; the strand
    needs the moment the *opportunity closed*, and for a ghost those are not the
    same instant — the plan was made a week before the entry window shut on it.
    Dating a ghost from its plan would age a record faster than the record aged,
    which the matcher's horizon reads directly.

    It is written beside ``_pairwise_outcome`` rather than replacing it because
    the two callers want different halves and a shape carrying both would leave
    every pairwise row holding a moment nothing reads.
    """

    outcome = _pairwise_outcome(game, now)
    if outcome is None:
        return None
    if outcome is PlayedOutcome.PLAYED:
        # ``played_at`` is set for every standing in ``PLAYED`` — the entry that
        # records *we played* is the only thing that can set it — so the fallback
        # is unreachable and is stated rather than asserted, because a read is a
        # bad place to raise about a stream somebody else wrote.
        return outcome, game.played_at or game.planned_at
    return outcome, entry_closes_at(game.planned_at)


__all__ = ["EventSourcedGameHistory"]
