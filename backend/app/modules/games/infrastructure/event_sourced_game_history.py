"""``GameHistoryQuery`` and ``GameDirectory`` over the event log.

**Everything here folds the aggregate.** A game's line-up moves in exactly two
told ways and the fold carries both (``docs/adr/0162``), so today's court is the
court as it stands and the fold is the whole answer. **Every read answers about
the people on the court now**: the streams read finds everybody a court has ever
seated, and the folded line-up is what says who is still on it — a leaver is
nobody's attendee, and their list no longer holds the game.

**Nothing is projected.** Every fact these reads publish — played or missed,
counted, confirmed, won or lost — is folded from the record against the caller's
clock, so a game past a deadline has moved in this answer whether or not anything
swept it. A projection storing the standing would be right until a deadline
passed, wrong until something rebuilt it, and believed throughout.

**One clock per read, taken from the caller.** Every read here takes ``now``
rather than reading one, because a screen that asks two of them in one request
must get one instant's answer to both.

**Cost.** Bounded by how many games the platform has ever recorded, because a
substring match cannot use a B-tree.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Collection, Mapping, final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import EventCodec
from app.kernel import Instant, Sport
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind
from app.modules.games.domain.ports import (
    RECENT_RESULTS,
    Attendance,
    CountedResult,
    OpponentVariety,
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

    async def recent_results_in(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> tuple[CountedResult, ...]:
        """This player's last few counted results in one sport, oldest to newest.

        **Filtered before it is trimmed**: trimmed to five across every sport
        first, a caller filtering afterwards would show three results to somebody
        who has played thirty in the sport asked about.
        """

        rows = [
            one
            for one in await self._counted_results(player_id, now=now)
            if one.sport is sport
        ]
        return tuple(rows[-RECENT_RESULTS:])

    async def _counted_results(
        self, player_id: UUID, *, now: Instant
    ) -> list[CountedResult]:
        """Every confirmed counted result for this player, **oldest first.**

        Untrimmed, because the read above narrows to a sport first — a helper
        that had already cut to five would be the bug it exists to prevent.
        """

        found: list[CountedResult] = []
        for game in await self._games_of(player_id):
            if game.kind is not GameKind.COUNTED:
                continue
            if game.standing_at(now) is not GameStanding.CONFIRMED:
                continue
            outcome = game.outcome_for(player_id, now=now)
            if outcome is None:
                continue
            found.append(
                CountedResult(
                    game_id=game.id,
                    sport=game.sport,
                    outcome=outcome,
                    played_at=game.played_at or game.planned_at,
                )
            )
        found.sort(key=lambda one: (one.played_at, one.game_id))
        return found

    async def attendance_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, Attendance]:
        """What became of each of these people's arrangements — played, or missed.

        **Counted per person and never per pair**: a four played once is one
        evening and three counterparts, so a *shows up* strand summed pair by
        pair would charge a doubles player three times for turning up once.

        **Absent rather than a measured zero.** A person nothing was ever
        arranged for has not failed to come, and a ``0/0`` published here would
        say they had.

        **A booked game somebody did not come to is read per player** (#547):
        a report that stood its day is a miss for the player it named — which
        with the broken booked game on *keeps plans* makes it the strongest
        mark on a record — and a game played for everybody else on the court,
        who came. **It is the only miss left**: a full court nobody recorded is
        played for all of it (#655; ``docs/adr/0195`` §2).
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        played: dict[UUID, int] = defaultdict(int)
        missed: dict[UUID, int] = defaultdict(int)
        latest: dict[UUID, Instant] = {}
        for game in await self._games_among(wanted):
            if game.standing_at(now) is GameStanding.NO_SHOW:
                # **Per player, not per game** (#547): whoever a report stood
                # against did not come — a miss — and everybody else did.
                absent = game.confirmed_no_shows_at(now)
                at = game.became_history_at(now) or game.planned_at
                for player_id in game.line_up.players & wanted:
                    if player_id in absent:
                        missed[player_id] += 1
                    else:
                        played[player_id] += 1
                    latest[player_id] = max(at, latest.get(player_id, at))
                continue
            moment = _played_for_the_record_at(game, now)
            if moment is None:
                continue
            for player_id in game.line_up.players & wanted:
                played[player_id] += 1
                latest[player_id] = max(moment, latest.get(player_id, moment))

        return {
            player_id: Attendance(
                played=played[player_id],
                missed=missed[player_id],
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
        below: a friendly and a game nobody played put nobody in either half,
        so a face can never enter the count without an evening under it.

        **Nothing is trimmed and nothing is windowed.** The whole record is the
        statistic: this caller asked for a career.
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
    because a game called off or started short is not an evening. A game with
    no agreed score passes both — disputed, or a full court nobody recorded
    (*Played · no score*, #655) — because it is an evening and it is not
    evidence, and those are two questions.

    Written once and read by the variety fold, so both halves of the pair a
    record prints come from one idea of what a counted game is.
    """

    return game.kind is GameKind.COUNTED and game.was_played_at(now)


def _played_for_the_record_at(game: Game, now: Instant) -> Instant | None:
    """When this game became an evening the people on its court played, or
    ``None`` while it says nothing about them.

    A game whose entry window is still open says **nothing yet**, and is left
    out rather than filed as played. **A game called off or started short says
    nothing at all, for good** (``docs/adr/0163`` §3, #544): it is not an
    evening, and filing it against the people who stayed would price somebody
    else's departure through them, which #411 rule 7 refuses. **A full court
    nobody recorded is played** once its window closes (#655): there is no
    ghost any more, and silence costs nobody anything.

    The moment is when the *opportunity closed* — the entry, or a window
    closing on nobody — and never when the game was booked, which would age a
    record faster than the record aged.
    """

    if not game.was_played_at(now):
        return None
    # The moment is the aggregate's own fold — one date for one game, wherever
    # it is read — and it is set for every played standing, so the narrowing is
    # stated rather than asserted.
    return game.became_history_at(now) or game.planned_at


__all__ = ["EventSourcedGameHistory"]
