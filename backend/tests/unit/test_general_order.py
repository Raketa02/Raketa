"""A sport's General order, worked out and kept, at the domain's and the
read's own seams (#770; ``docs/adr/0203`` §10; the screens §5.3).

**The pages are slices of the order** — the first page, after and before a
cursor, around the reader held to the list's ends; **an order is read for the
minute after it was worked out**; **a kept order that disagrees with the
reader's own row is worked out again**; and **an order lost mid-read is worked
out again** rather than failing the read. The Redis wrapper is held to the
same fail-soft posture over a server that can't be reached.
"""

from __future__ import annotations

from collections.abc import Collection, Sequence
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.rankings.application.friends_table import TheFriendsTable
from app.modules.rankings.application.general_order import TheGeneralOrder
from app.modules.rankings.application.reads import ReadRanking
from app.modules.rankings.domain.general_order import (
    ORDER_KEPT_FOR,
    GeneralOrder,
    ListedRow,
    OrderKey,
    Slice,
    ListedAndThen,
    first_page,
    kept_fresh,
    page_after,
    page_around,
    page_before,
    work_out,
)
from app.modules.rankings.domain.ports import GeneralOrderLost, HeldOrder, RankedFace
from app.modules.rankings.domain.ranking import (
    PAGE_SIZE,
    ChipKind,
    LevelPoint,
    Outcome,
    RankingRow,
)
from app.modules.rankings.infrastructure.in_memory_general_orders import (
    InMemoryGeneralOrders,
)
from app.modules.rankings.infrastructure.redis_general_orders import (
    FailSoftGeneralOrders,
    RedisGeneralOrders,
)
from app.shared.ids import new_uuid
from tests.unit.fake_clock import MovableClock
from tests.unit.fake_redis import BrokenRedis, FakeRedis

NOW = instant(datetime(2026, 11, 8, 18, 0, tzinfo=timezone.utc))
ENTERED = instant(NOW - timedelta(days=30))


def a_row(hundredths: int, *, player_id: UUID | None = None) -> RankingRow:
    return RankingRow(
        player_id=player_id or new_uuid(),
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


def place_of(read) -> int | None:
    return None if read.mine is None else read.mine.place


def listed(*hundredths: int) -> list[ListedAndThen]:
    return [
        ListedAndThen(row=a_row(level), then=None, hidden=False) for level in hundredths
    ]


# --------------------------------------------------------------------------- #
# The order and its pages
# --------------------------------------------------------------------------- #


def test_the_order_places_every_row_and_works_its_chips_out_with_it():
    karol, tomek = a_row(275), a_row(271)
    # A week ago Tomek stood above Karol.
    then = {
        karol.player_id: _point(karol, 260),
        tomek.player_id: _point(tomek, 270),
    }

    order = work_out(
        Sport.PADEL,
        [
            ListedAndThen(row=row, then=then[row.player_id], hidden=False)
            for row in (karol, tomek)
        ],
        now=NOW,
    )

    assert [(row.place, row.player_id) for row in order.rows] == [
        (1, karol.player_id),
        (2, tomek.player_id),
    ]
    assert [row.chip.kind for row in order.rows] == [ChipKind.UP, ChipKind.DOWN]
    assert order.worked_out_at == NOW


def test_an_order_out_of_order_is_refused():
    # A pass that read the rows out of General's order is a broken pass.
    with pytest.raises(InvariantViolated):
        work_out(Sport.PADEL, listed(271, 275), now=NOW)


def test_an_order_is_read_for_the_minute_after_it_was_worked_out():
    assert kept_fresh(NOW, NOW)
    assert kept_fresh(NOW, instant(NOW + ORDER_KEPT_FOR - timedelta(microseconds=1)))
    assert not kept_fresh(NOW, instant(NOW + ORDER_KEPT_FOR))
    assert not kept_fresh(NOW, instant(NOW - timedelta(seconds=1)))


@pytest.mark.parametrize(
    ("place", "listed", "expected"),
    [
        (1, 480, Slice(0, 50)),
        (25, 480, Slice(0, 50)),
        (26, 480, Slice(0, 50)),
        (27, 480, Slice(1, 51)),
        (212, 480, Slice(186, 236)),
        (460, 480, Slice(430, 480)),
        (480, 480, Slice(430, 480)),
        (3, 7, Slice(0, 7)),
    ],
)
def test_around_the_reader_is_the_reader_in_the_middle_held_to_the_ends(
    place, listed, expected
):
    page = page_around(place, listed)

    assert page == expected
    if expected.stop - expected.start == PAGE_SIZE and 26 <= place <= listed - 24:
        assert place - 1 - page.start == PAGE_SIZE // 2


def test_the_pages_either_side_of_a_cursor():
    assert first_page(480) == Slice(0, 50) and first_page(3) == Slice(0, 3)
    assert page_after(100, 480) == Slice(100, 150)
    assert page_after(470, 480) == Slice(470, 480)
    assert page_after(480, 480) == Slice(480, 480)
    assert page_before(100) == Slice(50, 100)
    assert page_before(30) == Slice(0, 30)
    assert page_before(0) == Slice(0, 0)


# --------------------------------------------------------------------------- #
# The order as a read finds it
# --------------------------------------------------------------------------- #


class Rows:
    """The projection, counting the passes made over it."""

    def __init__(self, listed: Sequence[RankingRow]) -> None:
        self.listed_rows = list(listed)
        self.passes = 0

    async def save(self, row: RankingRow) -> None:
        raise AssertionError("a read writes nothing")

    async def of_player(self, player_id: UUID) -> tuple[RankingRow, ...]:
        return tuple(row for row in self.listed_rows if row.player_id == player_id)

    async def listed(
        self,
        sport: Sport,
        *,
        at_least: int,
        since: Instant,
        then: Instant,
        among: Collection[UUID] | None = None,
    ) -> tuple[ListedAndThen, ...]:
        self.passes += 1
        return tuple(
            ListedAndThen(row=row, then=None, hidden=False) for row in self.listed_rows
        )


async def test_a_fresh_order_is_read_where_it_is_kept_and_a_stale_one_again():
    tomek = a_row(271)
    rows = Rows([a_row(275), tomek])
    general = TheGeneralOrder(rows=rows, orders=InMemoryGeneralOrders())

    first = await general.read(Sport.PADEL, now=NOW, reader=tomek.player_id)
    again = await general.read(
        Sport.PADEL, now=instant(NOW + timedelta(seconds=59)), reader=tomek.player_id
    )
    assert (place_of(first), place_of(again), rows.passes) == (2, 2, 1)

    later = await general.read(
        Sport.PADEL, now=instant(NOW + ORDER_KEPT_FOR), reader=tomek.player_id
    )
    assert (place_of(later), rows.passes) == (2, 2)


async def test_an_order_that_disagrees_with_the_readers_own_row_is_worked_out_again():
    karol, tomek = a_row(275), a_row(271)
    rows = Rows([karol])
    general = TheGeneralOrder(rows=rows, orders=InMemoryGeneralOrders())
    await general.read(Sport.PADEL, now=NOW, reader=karol.player_id)

    # Tomek's fifth result committed after the order was kept: missing him,
    # it is older than his row, and is worked out again.
    rows.listed_rows.append(tomek)
    read = await general.read(Sport.PADEL, now=NOW, reader=tomek.player_id)
    assert (place_of(read), read.order.listed, rows.passes) == (2, 2, 2)

    # A kept order counting fewer of the reader's results than they have is
    # older than their last write, and is worked out again: their Level is
    # never a minute late to them.
    rows.listed_rows[1] = replace(tomek, results=6, form=(Outcome.WIN,) * 5)
    read = await general.read(Sport.PADEL, now=NOW, reader=tomek.player_id)
    assert read.mine is not None and read.mine.results == 6
    assert rows.passes == 3

    # And a kept order placing a reader with no row at all is older than
    # whatever took the row.
    rows.listed_rows.remove(karol)
    read = await general.read(Sport.PADEL, now=NOW, reader=karol.player_id)
    assert (place_of(read), read.order.listed, rows.passes) == (None, 1, 4)


async def test_a_reader_still_placed_after_their_ninety_days_is_read_as_kept():
    karol, tomek = a_row(275), a_row(271)
    rows = Rows([karol, tomek])
    general = TheGeneralOrder(rows=rows, orders=InMemoryGeneralOrders())
    await general.read(Sport.PADEL, now=NOW, reader=karol.player_id)

    # Tomek's 90 days ran out since: he drops off within the minute, not now.
    rows.listed_rows[1] = replace(
        tomek, last_result_at=instant(NOW - timedelta(days=91))
    )
    read = await general.read(Sport.PADEL, now=NOW, reader=tomek.player_id)

    assert (place_of(read), rows.passes) == (2, 1)


class LosesItsOrder:
    """A store whose kept order goes away the moment it is read."""

    def __init__(self, held: HeldOrder) -> None:
        self._held = held
        self.kept: list[GeneralOrder] = []

    async def held(self, sport: Sport) -> HeldOrder | None:
        return _Lost(self._held)

    async def forgotten(self, sport: Sport) -> int:
        return 0

    async def keep(self, order: GeneralOrder, *, forgotten: int) -> None:
        self.kept.append(order)

    async def forget(self, sport: Sport) -> None:
        return None


class _Lost:
    def __init__(self, held: HeldOrder) -> None:
        self.worked_out_at, self.listed = held.worked_out_at, held.listed

    async def rows(self, start: int, stop: int) -> tuple[ListedRow, ...]:
        raise GeneralOrderLost("gone")

    async def place_of(self, player_id: UUID) -> int | None:
        raise GeneralOrderLost("gone")

    async def ahead_of(self, key: OrderKey) -> int:
        raise GeneralOrderLost("gone")

    async def up_to(self, key: OrderKey) -> int:
        raise GeneralOrderLost("gone")


async def test_an_order_lost_mid_read_is_worked_out_again():
    tomek = a_row(271)
    rows = Rows([a_row(275), tomek])
    kept = InMemoryGeneralOrders()
    await TheGeneralOrder(rows=rows, orders=kept).read(
        Sport.PADEL, now=NOW, reader=tomek.player_id
    )
    held = await kept.held(Sport.PADEL)
    assert held is not None
    losing = LosesItsOrder(held)

    read = await TheGeneralOrder(rows=rows, orders=losing).read(
        Sport.PADEL, now=NOW, reader=tomek.player_id
    )

    assert place_of(read) == 2
    assert [row.place for row in await read.order.rows(0, 50)] == [1, 2]
    assert rows.passes == 2 and len(losing.kept) == 1


class Named:
    """Everybody has a face."""

    async def faces_of(self, player_ids):
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


class NoFriends:
    async def friends_of(self, reader: UUID) -> frozenset[UUID]:
        return frozenset()


async def test_a_card_read_across_a_lost_order_is_the_new_orders_whole():
    karol, tomek = a_row(275), a_row(271)
    rows = Rows([karol, tomek])
    kept = InMemoryGeneralOrders()
    await TheGeneralOrder(rows=rows, orders=kept).read(
        Sport.PADEL, now=NOW, reader=tomek.player_id
    )
    held = await kept.held(Sport.PADEL)
    assert held is not None
    # Since it was kept, Karol's row went: the order worked out again lists
    # Tomek first, and the card is read off that order alone.
    rows.listed_rows.remove(karol)

    ranking = await ReadRanking(
        general=TheGeneralOrder(rows=rows, orders=LosesItsOrder(held)),
        friends=TheFriendsTable(rows=rows, friends=NoFriends()),
        faces=Named(),
        levels=Rated(),
        blocks=NoBlocks(),
        clock=MovableClock(NOW),
    ).execute(tomek.player_id, Sport.PADEL)

    assert (ranking.card.place, ranking.card.of, ranking.listed_count) == (1, 1, 1)
    assert ranking.card.gap_line is not None and ranking.card.gap_line.top_of_the_list
    assert [row.place for row in ranking.rows] == [1]


# --------------------------------------------------------------------------- #
# The ephemeral store's, when it fails
# --------------------------------------------------------------------------- #


async def test_a_store_that_cannot_be_reached_holds_nothing_and_keeps_nothing(caplog):
    caplog.set_level("WARNING")
    orders = FailSoftGeneralOrders(RedisGeneralOrders(BrokenRedis()))  # type: ignore[arg-type]
    order = work_out(Sport.PADEL, listed(275, 271), now=NOW)

    await orders.keep(order, forgotten=0)
    await orders.forget(Sport.PADEL)

    assert await orders.held(Sport.PADEL) is None
    # Said once, on the way into the outage.
    assert len([r for r in caplog.records if "ephemeral store" in r.message]) == 1


class Flaky:
    """A store that is down while ``down`` says so."""

    def __init__(self) -> None:
        self.down = False

    async def held(self, sport: Sport) -> HeldOrder | None:
        if self.down:
            raise ConnectionError("down")
        return None

    async def forgotten(self, sport: Sport) -> int:
        return 0

    async def keep(self, order: GeneralOrder, *, forgotten: int) -> None:
        return None

    async def forget(self, sport: Sport) -> None:
        if self.down:
            raise ConnectionError("down")


async def test_a_long_lived_store_complains_again_after_it_recovered(caplog):
    caplog.set_level("WARNING")
    flaky = Flaky()
    # The delivery worker's: one for the life of the process.
    orders = FailSoftGeneralOrders(flaky)

    for down in (True, True, False, True):
        flaky.down = down
        await orders.forget(Sport.PADEL)

    assert len([r for r in caplog.records if "ephemeral store" in r.message]) == 2


async def test_a_generation_retired_and_gone_under_a_read_is_lost():
    store = FakeRedis()
    orders = FailSoftGeneralOrders(RedisGeneralOrders(store))  # type: ignore[arg-type]
    first = work_out(Sport.PADEL, listed(275, 271), now=NOW)
    await orders.keep(first, forgotten=0)
    reading = await orders.held(Sport.PADEL)
    assert reading is not None

    await orders.keep(work_out(Sport.PADEL, listed(280), now=NOW), forgotten=0)
    # The replaced generation stays for the reads on it...
    assert len(await reading.rows(0, 50)) == 2
    store.advance(11)

    # ...and then it is gone, and a read on it is told so.
    with pytest.raises(GeneralOrderLost):
        await reading.rows(0, 50)
    with pytest.raises(GeneralOrderLost):
        await reading.place_of(first.rows[0].player_id)
    with pytest.raises(GeneralOrderLost):
        await reading.ahead_of(first.rows[0].key)


async def test_every_key_expires_on_its_own():
    store = FakeRedis()
    orders = RedisGeneralOrders(store)  # type: ignore[arg-type]
    await orders.keep(work_out(Sport.PADEL, listed(275, 271), now=NOW), forgotten=0)

    assert all(store.ttl_of(key) is not None for key in store.keys_held())
    store.advance(181)
    assert store.keys_held() == frozenset()


def _point(row: RankingRow, hundredths: int) -> LevelPoint:
    return LevelPoint(
        event_id=new_uuid(),
        player_id=row.player_id,
        sport=row.sport,
        at=ENTERED,
        hundredths=hundredths,
        results=5,
        level_reached_at=ENTERED,
    )
