"""``PublishedScoreQuery`` over the two contexts that keep a record of anything.

**Named for the fact it asserts, not for what it wraps** — the rule
``docs/adr/0095`` set for the null objects. *Points from the record* says what
it publishes since #659: Player reliability in points (``docs/adr/0195`` §1),
folded from what ``games`` says each booked game was for each player and from
what ``bookings`` says became of each seat they held. It was *three strands
from the record* while the figure was a weighted blend of ratios.

**It reads each provider's own published port and never their streams.** A
``select`` over ``event_store`` written here would make ``player_score`` a second
reader of two other contexts' schemas and, worse, a second author of what
*Didn't come*, *Came late* and *a broken booked game* mean — and the second copy
is always the one that gets believed. What crosses each seam is the provider's
own vocabulary — ``games``' ``Turnout``, ``bookings``' ``Broken`` — mapped here
onto this context's ``Happened``; the prices, the six months and the order they
are taken in are ``domain/points.py``'s, and are the only thing here that is not
somebody else's fact.

**Two reads and never one per player.** Every provider answers about a whole
set, because a group's Members list asks about everybody it draws in one call,
and the reliability filter will ask about a whole deal (#661).

**Everybody asked is answered.** A player neither provider has a line for reads
*100 · New* — everyone starts at a hundred — so the absence a provider spells by
leaving somebody out of its answer is, here, simply no lines.
"""

from __future__ import annotations

from typing import Collection, Iterator, Mapping, final
from uuid import UUID

from app.kernel import Instant
from app.modules.bookings.domain.keeping import Broken, Keeping
from app.modules.bookings.domain.ports import BookingHistoryQuery
from app.modules.games.domain.ports import GameHistoryQuery, GameOnTheRecord, Turnout
from app.modules.player_score.domain.points import (
    Happened,
    Line,
    PlayerScore,
    score_of,
)

#: ``games``' word for what a game said about somebody, in this context's.
_TURNOUT: Mapping[Turnout, Happened] = {
    Turnout.PLAYED_THROUGH: Happened.PLAYED_THROUGH,
    Turnout.TURNED_UP_UNCOUNTED: Happened.TURNED_UP_UNCOUNTED,
    Turnout.CAME_LATE: Happened.CAME_LATE,
    Turnout.DIDNT_COME: Happened.DIDNT_COME,
}

#: ``bookings``' word for how a seat was given up, in this context's.
_BROKEN: Mapping[Broken, Happened] = {
    Broken.LEFT_AFTER_THE_CUT_OFF: Happened.LEFT_AFTER_THE_CUT_OFF,
    Broken.CALLED_OFF_BY_LEAVING: Happened.CALLED_OFF_BY_LEAVING,
}


@final
class PointsFromTheRecord:
    """``PublishedScoreQuery`` over ``games`` and ``bookings``."""

    def __init__(
        self, *, games: GameHistoryQuery, bookings: BookingHistoryQuery
    ) -> None:
        self._games = games
        self._bookings = bookings

    async def scores_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, PlayerScore]:
        """Every one of these people's reliability, at one instant.

        **One instant for both halves.** A game is played through only once
        somebody says so or its entry window has closed, and a booked game is
        kept only once its hour has come, so two clocks here would let one
        figure be computed from two different presents.
        """

        wanted = set(player_ids)
        if not wanted:
            return {}

        # One after another, because they share the request's session: an
        # `AsyncSession` is not safe to use concurrently and both of these fold
        # streams through it, so gathering them would be a race rather than a
        # speed-up.
        games = await self._games.games_on_the_record_for(wanted, now=now)
        keeping = await self._bookings.keeping_for(wanted, now=now)

        return {
            player_id: score_of(
                [
                    *_game_lines(games.get(player_id, ())),
                    *_keeping_lines(keeping.get(player_id, ())),
                ],
                now=now,
            )
            for player_id in wanted
        }


def _game_lines(games: tuple[GameOnTheRecord, ...]) -> Iterator[Line]:
    """A line per game, dated by its hour — and a second, priced at nothing,
    for each game they left in dispute."""

    for game in games:
        yield Line(happened=_TURNOUT[game.turnout], at=game.at)
        if game.left_in_dispute:
            yield Line(happened=Happened.LEFT_IN_DISPUTE, at=game.at)


def _keeping_lines(keeping: tuple[Keeping, ...]) -> Iterator[Line]:
    """A line per settled booked game, dated when it was settled."""

    for one in keeping:
        happened = Happened.KEPT if one.broken is None else _BROKEN[one.broken]
        yield Line(happened=happened, at=one.at)


__all__ = ["PointsFromTheRecord"]
