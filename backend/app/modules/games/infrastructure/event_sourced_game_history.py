"""``GameHistoryQuery`` and ``GameDirectory`` over the event log.

**Everything here folds the aggregate.** A game's line-up moves in exactly two
told ways and the fold carries both (``docs/adr/0162``), so today's court is the
court as it stands and the fold is the whole answer. **Every read answers about
the people on the court now**: the streams read finds everybody a court has ever
seated, and the folded line-up is what says who is still on it — a leaver is
nobody's attendee, and their list no longer holds the game.

**Nothing is projected.** Every fact these reads publish — played through or
not come to, counted, confirmed, won or lost — is folded from the record against
the caller's clock, so a game past a deadline has moved in this answer whether or
not anything swept it. A projection storing the standing would be right until a deadline
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
    CountedResult,
    GameOnTheRecord,
    OpponentVariety,
)
from app.modules.games.domain.standing import GameStanding
from app.modules.games.infrastructure.game_streams import streams_seating


@final
class EventSourcedGameHistory:
    """``GameHistoryQuery``, ``GameDirectory``, ``OpponentVarietyQuery`` and
    ``PlayedTogetherQuery`` over ``event_store``.

    **One class for four ports, because all four are one read of the log folded
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

    async def games_on_the_record_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, tuple[GameOnTheRecord, ...]]:
        """What each game says about each of these people, oldest first.

        **Read per person and never per pair**: a four played once is one line
        on each of four records. **What a game says is the aggregate's own**
        (``Game.turnout_of``) — this walk only dates it and narrows it to the
        people asked about.

        **Absent rather than an empty row**: a person nothing final has
        happened to has no line, and is not in the answer.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        found: dict[UUID, list[GameOnTheRecord]] = defaultdict(list)
        for game in await self._games_among(wanted):
            disputed = game.left_in_dispute_by(now)
            for player_id in game.line_up.players & wanted:
                turnout = game.turnout_of(player_id, now=now)
                if turnout is None:
                    continue
                found[player_id].append(
                    GameOnTheRecord(
                        game_id=game.id,
                        # When it happened: the booked hour, which every booked
                        # game has — a stream written before bookings had none.
                        at=game.starts_at or game.planned_at,
                        turnout=turnout,
                        left_in_dispute=player_id in disputed,
                    )
                )

        return {
            player_id: tuple(sorted(rows, key=lambda row: (row.at, row.game_id)))
            for player_id, rows in found.items()
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

    # -- PlayedTogetherQuery ----------------------------------------------

    async def played_together_among(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> frozenset[frozenset[UUID]]:
        """Every pair of these people on one court played by ``now``. **One
        pass** over every stream any of them was ever seated in, narrowed to
        the court as it stands and to the people asked about."""

        wanted = set(player_ids)
        if len(wanted) < 2:
            return frozenset()
        pairs: set[frozenset[UUID]] = set()
        for game in await self._games_among(wanted):
            if not game.was_played_at(now):
                continue
            on_it = sorted(game.line_up.players & wanted, key=str)
            pairs.update(
                frozenset((one, other))
                for index, one in enumerate(on_it)
                for other in on_it[index + 1 :]
            )
        return frozenset(pairs)

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


__all__ = ["EventSourcedGameHistory"]
