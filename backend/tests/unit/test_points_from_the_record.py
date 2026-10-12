"""Every word the two providers can say is read at the seam (#659).

``PointsFromTheRecord`` maps ``games``' ``Turnout`` and ``bookings``' ``Broken``
onto ``player_score``'s own ``Happened``. A member added to either enum without a
line here would be a ``KeyError`` on somebody's record at read time, so each is
walked through the adapter's public read, with stub providers answering one line
of every kind.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Collection, Mapping
from uuid import UUID, uuid4

import pytest

from app.kernel import Instant, instant
from app.modules.bookings.domain.keeping import Broken, Keeping
from app.modules.games.domain.ports import GameOnTheRecord, Turnout
from app.modules.player_score.infrastructure.points_from_the_record import (
    PointsFromTheRecord,
)

NOW = instant(datetime(2026, 10, 13, 18, 0, tzinfo=timezone.utc))
PLAYER = uuid4()


def _days_ago(days: int) -> Instant:
    return instant(NOW - timedelta(days=days))


class Games:
    def __init__(self, rows: tuple[GameOnTheRecord, ...] = ()) -> None:
        self.rows = rows

    async def games_on_the_record_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, tuple[GameOnTheRecord, ...]]:
        return {PLAYER: self.rows} if self.rows else {}


class Bookings:
    def __init__(self, rows: tuple[Keeping, ...] = ()) -> None:
        self.rows = rows

    async def keeping_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, tuple[Keeping, ...]]:
        return {PLAYER: self.rows} if self.rows else {}


async def _points(games: Games, bookings: Bookings) -> int:
    scores = await PointsFromTheRecord(games=games, bookings=bookings).scores_for(
        [PLAYER], now=NOW
    )
    return scores[PLAYER].points


@pytest.mark.parametrize(
    ("turnout", "points"),
    [
        (Turnout.PLAYED_THROUGH, 80),
        (Turnout.TURNED_UP_UNCOUNTED, 75),
        (Turnout.CAME_LATE, 65),
        (Turnout.DIDNT_COME, 50),
    ],
)
async def test_every_turnout_is_read_and_priced(turnout, points):
    """After a miss (75), so a price is never hidden by the clamp."""

    rows = (
        GameOnTheRecord(game_id=uuid4(), at=_days_ago(9), turnout=Turnout.DIDNT_COME),
        GameOnTheRecord(game_id=uuid4(), at=_days_ago(3), turnout=turnout),
    )

    assert await _points(Games(rows), Bookings()) == points


@pytest.mark.parametrize(
    ("broken", "points"),
    [
        (None, 100),
        (Broken.LEFT_AFTER_THE_CUT_OFF, 85),
        (Broken.CALLED_OFF_BY_LEAVING, 90),
    ],
)
async def test_every_keeping_is_read_and_priced(broken, points):
    rows = (Keeping(at=_days_ago(3), broken=broken),)

    assert await _points(Games(), Bookings(rows)) == points


def test_the_cases_above_cover_every_word_either_provider_has():
    """A word added to either provider fails here until it has a case above —
    and a line at the seam."""

    assert set(Turnout) == {
        Turnout.PLAYED_THROUGH,
        Turnout.TURNED_UP_UNCOUNTED,
        Turnout.CAME_LATE,
        Turnout.DIDNT_COME,
    }
    assert set(Broken) == {
        Broken.LEFT_AFTER_THE_CUT_OFF,
        Broken.CALLED_OFF_BY_LEAVING,
    }


async def test_a_game_left_in_dispute_is_a_count_and_no_price():
    rows = (
        GameOnTheRecord(
            game_id=uuid4(),
            at=_days_ago(3),
            turnout=Turnout.PLAYED_THROUGH,
            left_in_dispute=True,
        ),
    )

    score = (
        await PointsFromTheRecord(games=Games(rows), bookings=Bookings()).scores_for(
            [PLAYER], now=NOW
        )
    )[PLAYER]

    assert (score.points, score.counts.left_in_dispute) == (100, 1)


async def test_a_player_neither_provider_knows_reads_a_hundred_and_new():
    score = (
        await PointsFromTheRecord(games=Games(), bookings=Bookings()).scores_for(
            [PLAYER], now=NOW
        )
    )[PLAYER]

    assert (score.points, score.is_new) == (100, True)
