"""Whom the gap line names, at the read's own seam (#769; the mechanics §7.3):
**only rows the reader can see** — here, a row somebody can name — so a nameless
neighbour is skipped and the line reads against the nearest named one, and a
neighbour off the first page is asked about on its own.

Every port is a hand-written stub implementing the ``Protocol``.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from uuid import UUID

from app.kernel import Instant, Sport, instant
from app.modules.rankings.application.reads import ReadRanking
from app.modules.rankings.domain.ports import RankedFace
from app.modules.rankings.domain.ranking import (
    PAGE_SIZE,
    LevelPoint,
    Outcome,
    RankingRow,
)
from app.shared.ids import new_uuid
from tests.unit.fake_clock import MovableClock

NOW = instant(datetime(2026, 11, 1, 18, 0, tzinfo=timezone.utc))
ENTERED = instant(NOW - timedelta(days=30))


def a_row(hundredths: int) -> RankingRow:
    return RankingRow(
        player_id=new_uuid(),
        sport=Sport.PADEL,
        hundredths=hundredths,
        sigma=0.30,
        results=5,
        last_result_at=ENTERED,
        level_reached_at=ENTERED,
        general_entered_at=ENTERED,
        friends_entered_at=ENTERED,
        form=(Outcome.WIN,) * 5,
    )


class Rows:
    def __init__(self, listed: Sequence[RankingRow]) -> None:
        self._listed = tuple(listed)

    async def save(self, row: RankingRow) -> None:
        raise AssertionError("a read writes nothing")

    async def of_player(self, player_id: UUID) -> tuple[RankingRow, ...]:
        return tuple(row for row in self._listed if row.player_id == player_id)

    async def listed(
        self, sport: Sport, *, at_least: int, since: Instant
    ) -> tuple[RankingRow, ...]:
        return self._listed


class NoHistory:
    async def append(self, points: Sequence[LevelPoint]) -> int:
        raise AssertionError("a read writes nothing")

    async def points_at(
        self, sport: Sport, at: Instant, player_ids: Collection[UUID]
    ) -> Mapping[UUID, LevelPoint]:
        return {}


class Faces:
    """Names whoever ``names`` holds and nobody else, and remembers each
    question."""

    def __init__(self, names: Mapping[UUID, str]) -> None:
        self._names = names
        self.asked: list[set[UUID]] = []

    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, RankedFace]:
        self.asked.append(set(player_ids))
        return {
            player_id: RankedFace(
                player_id=player_id, nickname=self._names.get(player_id)
            )
            for player_id in player_ids
        }


class Rated:
    async def holds_a_level(self, player_id: UUID, sport: Sport) -> bool:
        return True


def a_read(listed: Sequence[RankingRow], faces: Faces) -> ReadRanking:
    return ReadRanking(
        rows=Rows(listed),
        level_history=NoHistory(),
        faces=faces,
        levels=Rated(),
        clock=MovableClock(NOW),
    )


async def test_a_neighbour_nobody_can_name_is_skipped_for_the_nearest_named_one():
    karol, nameless, tomek, other, zofia = (a_row(h) for h in (275, 273, 271, 270, 269))
    faces = Faces(
        {karol.player_id: "karol", tomek.player_id: "tomek", zofia.player_id: "zofia"}
    )

    card = (
        await a_read([karol, nameless, tomek, other, zofia], faces).execute(
            tomek.player_id, Sport.PADEL
        )
    ).card

    assert card.gap_line is not None
    above, below = card.gap_line.above, card.gap_line.below
    # Measured against the rows named, so closing the gap passes the nameless
    # rows too: 0,04 to Karol, 0,02 down to Zofia.
    assert above is not None and (above.nickname, above.gap) == ("karol", 4)
    assert below is not None and (below.nickname, below.gap) == ("zofia", 2)
    # The places stay true: Tomek is 3rd, with the nameless row above him.
    assert card.place == 3


async def test_a_neighbour_off_the_first_page_is_asked_about_on_its_own():
    listed = [a_row(400 - place) for place in range(PAGE_SIZE + 10)]
    reader = listed[PAGE_SIZE + 4]
    above, below = listed[PAGE_SIZE + 3], listed[PAGE_SIZE + 5]
    faces = Faces({row.player_id: f"p{place}" for place, row in enumerate(listed)})

    card = (await a_read(listed, faces).execute(reader.player_id, Sport.PADEL)).card

    assert card.place == PAGE_SIZE + 5
    assert card.gap_line is not None
    assert card.gap_line.above is not None and card.gap_line.below is not None
    assert (card.gap_line.above.nickname, card.gap_line.below.nickname) == (
        f"p{PAGE_SIZE + 3}",
        f"p{PAGE_SIZE + 5}",
    )
    # The page in one question, then each neighbour once — never the list.
    assert faces.asked == [
        {row.player_id for row in listed[:PAGE_SIZE]},
        {above.player_id},
        {below.player_id},
    ]
