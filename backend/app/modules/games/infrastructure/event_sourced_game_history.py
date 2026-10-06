"""``GameHistoryQuery`` and ``GameDirectory`` over the event log.

**Everything here folds the aggregate.** A game's line-up moves in exactly two
told ways and the fold carries both (``docs/adr/0162``), so today's court is the
court as it stands and the fold is the whole answer. **Every read answers about
the people on the court now**: the streams read finds everybody a court has ever
seated, and the folded line-up is what says who is still on it — a leaver is
nobody's counterpart, nobody's attendee, and their list no longer holds the game.

**Nothing is projected.** Every fact these reads publish — played or a ghost,
counted, confirmed, won or lost — is folded from the record against the caller's
clock, so a game past a deadline has moved in this answer whether or not anything
swept it. A projection storing the standing would be right until a deadline
passed, wrong until something rebuilt it, and believed throughout.

**One clock per read, taken from the caller.** Every read here takes ``now``
rather than reading one, because a search that asked about counted games and
about familiarity in one request must get one instant's answer to both.

**Cost.** Bounded by how many games the platform has ever recorded, because a
substring match cannot use a B-tree.
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
    OpponentVariety,
    PlayedOutcome,
    PlayedTally,
    ResultAnswering,
)
from app.modules.games.domain.standing import GameStanding
from app.modules.games.infrastructure.game_streams import streams_seating


@final
class EventSourcedGameHistory:
    """``GameHistoryQuery``, ``GameDirectory`` and ``OpponentVarietyQuery`` over
    ``event_store``.

    **One class for three ports, because all three are one read of the log folded
    differently** and splitting them would run the same substring match twice for
    a screen that wants both. The ports stay separate, and each split is a rule
    rather than a filing decision: a caller that wants the counts has no business
    holding the aggregates, and a caller that walks twenty rows has no business
    holding an unbounded career fold.
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
            if not _counted_and_played(game, now):
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

        **A booked game somebody did not come to is read per player** (#547):
        a report that stood its day is a miss for the player it named — the
        same miss a ghost is, which with the broken booked game on *keeps
        plans* makes it the strongest mark on a record — and a game played for
        everybody else on the court, who came.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        played: dict[UUID, int] = defaultdict(int)
        ghosts: dict[UUID, int] = defaultdict(int)
        latest: dict[UUID, Instant] = {}
        for game in await self._games_among(wanted):
            if game.standing_at(now) is GameStanding.NO_SHOW:
                # **Per player, not per game** (#547): whoever a report stood
                # against did not come — a miss — and everybody else did.
                absent = game.confirmed_no_shows_at(now)
                at = game.became_history_at(now) or game.planned_at
                for player_id in game.line_up.players & wanted:
                    if player_id in absent:
                        ghosts[player_id] += 1
                    else:
                        played[player_id] += 1
                    latest[player_id] = max(at, latest.get(player_id, at))
                continue
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

    async def result_answering_for(
        self, player_ids: Collection[UUID], *, since: Instant, now: Instant
    ) -> Mapping[UUID, ResultAnswering]:
        """What became of the scores put in front of each of these people.

        **One opportunity per game at most, charged to the side that was asked**,
        so a doubles pair each carry the score their side never answered and the
        side that entered it carries nothing. That is the same per-person shape
        ``attendance_for`` takes and for a different reason: there, everybody on
        the court was in the arrangement; here, only one side was asked.

        **The window is the caller's** (``docs/adr/0160``). An opportunity that
        closed before ``since`` is not in either half — it is not a good outcome
        the player keeps for ever and not a miss they can never work off.

        **Absent rather than a measured zero**, like ``attendance_for``: nobody
        has ignored a score who was never sent one.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        answered: dict[UUID, int] = defaultdict(int)
        ignored: dict[UUID, int] = defaultdict(int)
        latest: dict[UUID, Instant] = {}
        for game in await self._games_among(wanted):
            asked = game.score_put_to_a_side_at(now)
            if asked is None or asked.closed_at < since:
                continue
            for player_id in game.line_up.players_on(asked.side) & wanted:
                if asked.answered:
                    answered[player_id] += 1
                else:
                    ignored[player_id] += 1
                latest[player_id] = max(
                    asked.closed_at, latest.get(player_id, asked.closed_at)
                )

        return {
            player_id: ResultAnswering(
                answered=answered[player_id],
                ignored=ignored[player_id],
                last_at=at,
            )
            for player_id, at in latest.items()
        }

    async def late_change_threshold(self) -> Minutes | None:
        """``None`` — **recorded, not yet scored** (``docs/adr/0162`` §8).

        A seat can be left and the game has a moment, so *late* has a referent
        now; what a departure an hour before it should cost is a judgement no
        record has made, and until one does there is no number to publish.
        Absent rather than defaulted, because a number nobody measured is a
        number somebody picked.
        """

        return None

    # -- OpponentVarietyQuery ---------------------------------------------

    async def variety_of(
        self, player_id: UUID, *, now: Instant
    ) -> OpponentVariety | None:
        """How many different people, over how many times on a court. **One pass.**

        **The denominator counts seats opposite rather than games**, and the two
        are only the same number in singles. A doubles evening puts three people
        on the court, so a game-denominated pair reported ``3 of 1``: a fraction
        whose numerator can exceed its denominator, which is not a share of
        anything. Counting the counterparts each game contributed makes both
        halves the same kind of thing, and the division honest at every court
        size.

        **Which games count is still ``_counted_and_played``'s**, written once
        below: a friendly and a ghost put nobody in either half, so a face can
        never enter the count without an evening under it.

        **Nothing is trimmed and nothing is windowed.** The whole record is the
        statistic; the sort-then-bound the pairwise read applies exists because a
        matcher asked for the *recent* few, and this caller asked for a career.
        """

        faces: set[UUID] = set()
        met = 0
        for game in await self._games_of(player_id):
            if not _counted_and_played(game, now):
                continue
            counterparts = game.line_up.counterparts_of(player_id)
            met += len(counterparts)
            faces |= counterparts
        if met == 0:
            return None
        return OpponentVariety(
            distinct_counterparts=len(faces), times_on_court=met
        )

    # -- internals --------------------------------------------------------

    async def _games_of(self, player_id: UUID) -> list[Game]:
        """Every game this player is on the court of **now**.

        The streams read answers wider than that — it finds every court that has
        ever seated them, a seat they have since left included — and the folded
        line-up narrows it. The set reads need no such narrowing because each of
        them intersects ``line_up.players`` with the people it was asked about.
        """

        return [
            game
            for game in await self._games_among({player_id})
            if player_id in game.line_up.players
        ]

    async def _games_among(self, player_ids: Collection[UUID]) -> list[Game]:
        streams = await streams_seating(self._session, self._codec, player_ids)
        return [Game.from_history(events) for events in streams.values()]


def _counted_and_played(game: Game, now: Instant) -> bool:
    """Whether this game is one *how much have they played* counts.

    **Counted rather than a friendly**, because the people who arranged a
    friendly said it was not evidence; **played rather than merely arranged**,
    because a plan nobody claimed is not an evening. An unscored game passes
    both: it is an evening and it is not evidence, and those are two questions.

    Written once and read by both the count and the variety fold, so the two
    numbers a record prints beside each other cannot come from two ideas of what
    a counted game is.
    """

    return game.kind is GameKind.COUNTED and game.was_played_at(now)


def _pairwise_outcome(game: Game, now: Instant) -> PlayedOutcome | None:
    """What this game says about the people who were on its court.

    Three answers and not two: a game whose entry window is still open says
    **nothing yet** about the pair, and is left out rather than filed as either.

    **And a called-off game says nothing at all, for good** (``docs/adr/0163``
    §3). It is not an evening — nobody played — and it is not a ghost, because a
    ghost is a window closing on silence and this was an act somebody took while
    a seat was open. Filing it as a ghost would charge the people who stayed for
    somebody else's departure, which #411 rule 7 refuses. So it is ``None`` here,
    and every read built on this — the pair, the attendance, the counts, the
    variety — leaves it out by the same line.
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
    # The moment is the aggregate's own fold — one date for one game, wherever
    # it is read — and it is set for both outcomes the line above admits, so
    # the narrowing is stated rather than asserted.
    return outcome, game.became_history_at(now) or game.planned_at


__all__ = ["EventSourcedGameHistory"]
