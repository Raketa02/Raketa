"""The Friends view at the domain's own seam and the read's (#771;
``docs/adr/0203`` §3–§4; the mechanics §4.2, §6; the screens §4.6): who enters
it, its chip's *New*, the card — listed, *just you*, *no friend listed*, and the
reader's not-listed cards above the friends' table — and the whole table, never
a page. The read's ports are hand-written stubs implementing the ``Protocol``."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import Instant, Sport, instant
from app.modules.rankings.application.friends_table import TheFriendsTable
from app.modules.rankings.application.general_order import TheGeneralOrder
from app.modules.rankings.application.reads import ReadRanking
from app.modules.rankings.domain.general_order import ListedAndThen, work_out
from app.modules.rankings.domain.ports import RankedFace
from app.modules.rankings.domain.ranking import (
    CHIP_WINDOW,
    FRIENDS_ENTRY,
    GENERAL_ENTRY,
    PAGE_SIZE,
    CardState,
    Chip,
    ChipKind,
    GapLine,
    LevelPoint,
    Outcome,
    RankingRow,
    RankingView,
    chips_of,
    friends_card_of,
)
from app.modules.rankings.infrastructure.in_memory_general_orders import (
    InMemoryGeneralOrders,
)
from app.shared.ids import new_uuid
from tests.unit.fake_clock import MovableClock

NOW = instant(datetime(2026, 11, 1, 18, 0, tzinfo=timezone.utc))
LONG_AGO = instant(NOW - timedelta(days=30))


def a_row(
    hundredths: int,
    *,
    results: int = 5,
    first: Instant = LONG_AGO,
    general: Instant | None = LONG_AGO,
) -> RankingRow:
    return RankingRow(
        player_id=new_uuid(),
        sport=Sport.PADEL,
        hundredths=hundredths,
        sigma=0.30,
        results=results,
        last_result_at=LONG_AGO,
        level_reached_at=LONG_AGO,
        general_entered_at=general if results >= GENERAL_ENTRY else None,
        friends_entered_at=first,
        form=(Outcome.WIN,) * min(results, 5),
    )


def test_friends_are_entered_from_the_first_result_and_general_from_the_fifth():
    assert (
        (RankingView.FRIENDS.entry, RankingView.GENERAL.entry)
        == (
            FRIENDS_ENTRY,
            GENERAL_ENTRY,
        )
        == (1, 5)
    )


def test_new_among_friends_is_the_seven_days_after_the_first_result():
    """Ola's first result was yesterday: *New* among friends. Karol has played
    for a month and entered General yesterday with a fifth — *New* on General,
    never among friends."""

    ola = a_row(275, results=1, first=instant(NOW - timedelta(days=1)))
    karol = a_row(271, general=instant(NOW - timedelta(days=1)))
    seasoned = a_row(269, first=instant(NOW - CHIP_WINDOW))

    friends = chips_of([ola, karol, seasoned], {}, now=NOW, view=RankingView.FRIENDS)
    general = chips_of([karol, seasoned], {}, now=NOW)

    assert friends == {
        ola.player_id: Chip(ChipKind.NEW),
        karol.player_id: Chip(ChipKind.SAME),
        seasoned.player_id: Chip(ChipKind.SAME),
    }
    assert general[karol.player_id] == Chip(ChipKind.NEW)


def test_an_overtake_among_friends_moves_both():
    karol, tomek = a_row(275), a_row(271)

    def stood(row: RankingRow, hundredths: int) -> LevelPoint:
        return LevelPoint(
            event_id=new_uuid(),
            player_id=row.player_id,
            sport=row.sport,
            at=LONG_AGO,
            hundredths=hundredths,
            results=row.results,
            level_reached_at=LONG_AGO,
        )

    chips = chips_of(
        [karol, tomek],
        {karol.player_id: stood(karol, 270), tomek.player_id: stood(tomek, 271)},
        now=NOW,
        view=RankingView.FRIENDS,
    )

    assert chips == {
        karol.player_id: Chip(ChipKind.UP, 1),
        tomek.player_id: Chip(ChipKind.DOWN, 1),
    }


def placed(row: RankingRow):
    return work_out(
        Sport.PADEL,
        [ListedAndThen(row=row, then=None, hidden=False)],
        now=NOW,
        view=RankingView.FRIENDS,
    ).rows[0]


TOP = GapLine(above=None, below=None, top_of_the_list=True)


def test_a_listed_reader_with_a_friend_listed_reads_the_place():
    tomek = a_row(271, results=2)

    card = friends_card_of(
        tomek,
        holds_a_level=True,
        of=2,
        friends_listed=1,
        placed=placed(tomek),
        gap_line=TOP,
    )

    assert (card.state, card.place, card.of, card.results) == (
        CardState.LISTED,
        1,
        2,
        2,
    )


def test_a_listed_reader_with_no_friend_listed_is_just_you():
    tomek = a_row(271, results=2)

    card = friends_card_of(
        tomek,
        holds_a_level=True,
        of=1,
        friends_listed=0,
        placed=placed(tomek),
        gap_line=TOP,
    )

    assert (card.state, card.results, card.place, card.gap_line) == (
        CardState.JUST_YOU,
        2,
        None,
        None,
    )


@pytest.mark.parametrize(
    ("row", "holds_a_level"),
    [
        (None, True),
        (a_row(271, results=7), True),
        (None, False),
    ],
    ids=["no result", "none in the 90 days", "no level"],
)
def test_nobody_listed_at_all_is_no_friend_listed(row, holds_a_level):
    """*None of your friends is ranked in padel yet* replaces the card, whatever
    the reader's own state (the screens §4.6)."""

    card = friends_card_of(row, holds_a_level=holds_a_level, of=0, friends_listed=0)

    assert card.state is CardState.NO_FRIEND_LISTED
    assert card.results == (0 if row is None else row.results)


@pytest.mark.parametrize(
    ("row", "holds_a_level", "expected"),
    [
        (None, True, CardState.NEEDS_RESULTS),
        (a_row(271, results=7), True, CardState.OFF_THE_LIST),
        (a_row(271, results=1), True, CardState.OFF_THE_LIST),
        (None, False, CardState.NO_LEVEL),
    ],
    ids=["no result", "none in the 90 days", "one, long ago", "no level"],
)
def test_a_reader_not_listed_among_listed_friends_reads_their_own_card(
    row, holds_a_level, expected
):
    """*Not ranked in padel yet — your first confirmed competitive game puts
    you on the list* is ``NEEDS_RESULTS`` with no result of the one needed."""

    card = friends_card_of(row, holds_a_level=holds_a_level, of=3, friends_listed=3)

    assert card.state is expected
    assert card.results == (0 if row is None else row.results)
    assert card.place is None


# --------------------------------------------------------------------------- #
# The read, at its seam: the whole table, never a page
# --------------------------------------------------------------------------- #


class Rows:
    """The projection: every row, filtered as ``among`` asks."""

    def __init__(self, rows: list[RankingRow]) -> None:
        self._rows = rows
        self.among: list[frozenset[UUID] | None] = []

    async def save(self, row: RankingRow) -> None:
        raise AssertionError("a read writes nothing")

    async def of_player(self, player_id: UUID) -> tuple[RankingRow, ...]:
        return tuple(row for row in self._rows if row.player_id == player_id)

    async def listed(
        self,
        sport: Sport,
        *,
        at_least: int,
        since: Instant,
        then: Instant,
        among: Collection[UUID] | None = None,
    ) -> tuple[ListedAndThen, ...]:
        self.among.append(None if among is None else frozenset(among))
        return tuple(
            ListedAndThen(row=row, then=None, hidden=False)
            for row in self._rows
            if row.results >= at_least and (among is None or row.player_id in among)
        )


class Friends:
    def __init__(self, friends: frozenset[UUID]) -> None:
        self._friends = friends

    async def friends_of(self, reader: UUID) -> frozenset[UUID]:
        return self._friends


class Named:
    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, RankedFace]:
        return {
            player_id: RankedFace(player_id=player_id, nickname=str(player_id)[:8])
            for player_id in player_ids
        }


class Rated:
    async def holds_a_level(self, player_id: UUID, sport: Sport) -> bool:
        return True


class NoBlocks:
    async def blocked_either_way(self, reader: UUID) -> frozenset[UUID]:
        return frozenset()


async def test_friends_is_the_whole_table_however_long_and_nobody_else():
    friends = [a_row(400 - n, results=1) for n in range(PAGE_SIZE + 10)]
    reader = a_row(300, results=1)
    stranger = a_row(500, results=1)
    rows = Rows([*friends, reader, stranger])
    read = ReadRanking(
        general=TheGeneralOrder(rows=rows, orders=InMemoryGeneralOrders()),
        friends=TheFriendsTable(
            rows=rows, friends=Friends(frozenset(row.player_id for row in friends))
        ),
        faces=Named(),
        levels=Rated(),
        blocks=NoBlocks(),
        clock=MovableClock(NOW),
    )

    ranking = await read.execute(
        reader.player_id, Sport.PADEL, view=RankingView.FRIENDS
    )

    assert rows.among == [
        frozenset({reader.player_id, *(row.player_id for row in friends)})
    ]
    assert (ranking.view, ranking.listed_count, ranking.next) == (
        RankingView.FRIENDS,
        PAGE_SIZE + 11,
        None,
    )
    assert [row.place for row in ranking.rows] == list(range(1, PAGE_SIZE + 12))
    assert ranking.rows[-1].is_you
    assert (ranking.card.place, ranking.card.of) == (PAGE_SIZE + 11, PAGE_SIZE + 11)
    assert ranking.card.gap_line is not None
    assert ranking.card.gap_line.below is None
    assert [row.place for row in ranking.podium] == [1, 2, 3]
