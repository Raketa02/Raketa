"""What every kept-order store answers alike (#770), run against every adapter
registered in ``app/bootstrap/general_order_demands.py``.

**The in-memory store is what every test reads through**, so it is only as
good as its agreement with Redis's: an order kept is the order held, row for
row and place for place; a slice is the rows at those indexes; a cursor's
position counts the rows strictly ahead of it, or at it, whether or not any
row stands exactly there; a second keep replaces the first while a read
already on the first finishes on it; a forget holds nothing; and each sport is
its own. **Redis's runs over the suite's fake server**, wrapped as the
composition root wraps it.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.bootstrap.general_order_demands import (
    GENERAL_ORDER_IMPLEMENTATIONS,
    RegisteredOrderStore,
)
from app.kernel import Instant, Sport, instant
from app.modules.rankings.domain.general_order import (
    GeneralOrder,
    ListedRow,
    OrderKey,
)
from app.modules.rankings.domain.ports import GeneralOrders
from app.modules.rankings.domain.ranking import Chip, ChipKind, Outcome
from tests.unit.fake_redis import FakeRedis

NOW = instant(datetime(2026, 11, 8, 18, 0, tzinfo=timezone.utc))
REACHED = instant(datetime(2026, 10, 1, 9, 30, 15, 123456, tzinfo=timezone.utc))

FORM = (Outcome.WIN, Outcome.LOSS, Outcome.WIN, Outcome.WIN, Outcome.LOSS)
CHIPS = (
    Chip(ChipKind.UP, 2),
    Chip(ChipKind.DOWN, 11),
    Chip(ChipKind.SAME),
    Chip(ChipKind.NEW),
)


def _id(n: int) -> UUID:
    return UUID(int=n * 7919 + 1)


def an_order(size: int, *, sport: Sport = Sport.PADEL, at: Instant = NOW):
    """``size`` rows, best first: Levels falling in pairs, so two rows share
    each Level and the count of results, the day reached or the id decides
    between them — every key the order has is exercised."""

    rows = []
    for index in range(size):
        level = 520 - index // 2
        rows.append(
            dict(
                sport=sport,
                hundredths=level,
                sigma=0.1 + index / 1000,
                results=40 - index % 2 * 3,
                level_reached_at=instant(REACHED + timedelta(days=index % 3)),
                player_id=_id(index),
                form=FORM[: 5 - index % 2],
                chip=CHIPS[index % len(CHIPS)],
                # *Show me in General* off kept row for row (#772).
                hidden=index % 5 == 0,
            )
        )
    rows.sort(
        key=lambda row: (
            -row["hundredths"],
            -row["results"],
            row["level_reached_at"],
            row["player_id"],
        )
    )
    return GeneralOrder(
        sport=sport,
        worked_out_at=at,
        rows=tuple(
            ListedRow(place=place, **row) for place, row in enumerate(rows, start=1)
        ),
    )


@pytest.fixture(
    params=[pytest.param(one, id=one.name) for one in GENERAL_ORDER_IMPLEMENTATIONS]
)
def store(request) -> GeneralOrders:
    registered: RegisteredOrderStore = request.param
    return registered.build(FakeRedis())  # type: ignore[arg-type]


def test_both_adapters_are_registered():
    assert {one.name for one in GENERAL_ORDER_IMPLEMENTATIONS} == {
        "InMemoryGeneralOrders",
        "RedisGeneralOrders",
    }


async def test_nothing_is_held_before_anything_is_kept(store):
    assert await store.held(Sport.PADEL) is None


async def test_an_order_kept_is_the_order_held_row_for_row(store):
    order = an_order(120)

    await store.keep(order, forgotten=0)
    held = await store.held(Sport.PADEL)

    assert held is not None
    assert (held.worked_out_at, held.listed) == (NOW, 120)
    assert await held.rows(0, 120) == order.rows
    assert await held.rows(50, 100) == order.rows[50:100]
    assert await held.rows(110, 160) == order.rows[110:]
    assert await held.rows(120, 170) == ()


async def test_every_row_is_placed_and_nobody_else_is(store):
    order = an_order(60)
    await store.keep(order, forgotten=0)
    held = await store.held(Sport.PADEL)
    assert held is not None

    assert [await held.place_of(row.player_id) for row in order.rows] == list(
        range(1, 61)
    )
    assert await held.place_of(_id(10_000)) is None


async def test_a_cursor_counts_the_rows_ahead_of_it_and_at_it(store):
    order = an_order(30)
    await store.keep(order, forgotten=0)
    held = await store.held(Sport.PADEL)
    assert held is not None

    for index, row in enumerate(order.rows):
        assert await held.ahead_of(row.key) == index
        assert await held.up_to(row.key) == index + 1


async def test_a_cursor_no_row_stands_at_is_placed_between_rows(store):
    order = an_order(30)
    await store.keep(order, forgotten=0)
    held = await store.held(Sport.PADEL)
    assert held is not None
    tenth = order.rows[9]

    # The tenth row's key, a moment later in the day reached: behind it and
    # ahead of the eleventh, which has fewer results or a later day.
    moved = OrderKey(
        hundredths=tenth.hundredths,
        results=tenth.results,
        level_reached_at=instant(tenth.level_reached_at + timedelta(microseconds=1)),
        player_id=tenth.player_id,
    )
    best = OrderKey(hundredths=999, results=0, level_reached_at=NOW, player_id=_id(0))
    worst = OrderKey(hundredths=0, results=0, level_reached_at=NOW, player_id=_id(0))

    assert (await held.ahead_of(moved), await held.up_to(moved)) == (10, 10)
    assert (await held.ahead_of(best), await held.up_to(best)) == (0, 0)
    assert (await held.ahead_of(worst), await held.up_to(worst)) == (30, 30)


async def test_a_second_keep_replaces_the_first_and_a_read_on_the_first_finishes(
    store,
):
    first = an_order(10)
    await store.keep(first, forgotten=0)
    reading = await store.held(Sport.PADEL)
    second = an_order(4, at=instant(NOW + timedelta(seconds=30)))

    await store.keep(second, forgotten=0)
    held = await store.held(Sport.PADEL)

    assert held is not None and reading is not None
    assert (held.listed, held.worked_out_at) == (4, second.worked_out_at)
    assert await held.rows(0, 10) == second.rows
    assert await reading.rows(0, 10) == first.rows


async def test_a_forgotten_order_is_held_no_more(store):
    await store.keep(an_order(10), forgotten=0)

    await store.forget(Sport.PADEL)

    assert await store.held(Sport.PADEL) is None
    await store.forget(Sport.PADEL)  # and forgetting nothing is no error


async def test_each_sport_keeps_its_own(store):
    padel, tennis = an_order(5), an_order(7, sport=Sport.TENNIS)

    await store.keep(padel, forgotten=0)
    await store.keep(tennis, forgotten=0)
    await store.forget(Sport.PADEL)

    held = await store.held(Sport.TENNIS)
    assert await store.held(Sport.PADEL) is None
    assert held is not None and await held.rows(0, 50) == tennis.rows
    assert await store.held(Sport.SQUASH) is None


async def test_an_order_of_nobody_is_held_empty(store):
    await store.keep(an_order(0), forgotten=0)
    held = await store.held(Sport.PADEL)

    assert held is not None and held.listed == 0
    assert await held.rows(0, 50) == ()
    assert await held.place_of(_id(1)) is None
    key = OrderKey(hundredths=300, results=5, level_reached_at=NOW, player_id=_id(1))
    assert (await held.ahead_of(key), await held.up_to(key)) == (0, 0)


async def test_an_order_a_pass_began_before_a_forget_is_held_by_nobody(store):
    # A pass reads the count, then the projection; a write forgets; the pass
    # keeps what it read — after the write. Nobody holds it.
    began_at = await store.forgotten(Sport.PADEL)
    await store.forget(Sport.PADEL)
    await store.keep(an_order(10), forgotten=began_at)

    assert await store.forgotten(Sport.PADEL) == began_at + 1
    assert await store.held(Sport.PADEL) is None

    # The next pass begins after the forget, and its order is held.
    await store.keep(an_order(4), forgotten=await store.forgotten(Sport.PADEL))
    held = await store.held(Sport.PADEL)
    assert held is not None and held.listed == 4


async def test_each_sport_counts_its_own_forgets(store):
    await store.forget(Sport.PADEL)
    await store.forget(Sport.PADEL)
    await store.forget(Sport.TENNIS)

    assert [await store.forgotten(sport) for sport in Sport] == [
        {Sport.PADEL: 2, Sport.TENNIS: 1}.get(sport, 0) for sport in Sport
    ]
