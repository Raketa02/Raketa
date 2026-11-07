"""The chip and the gap line, read the way the player app reads them (#769;
``docs/adr/0203`` §4, §6; the rankings mechanics §6–§7).

**Every Level is moved through the rating's own aggregate** (``moves_to``),
which records the same ``rating.moved_on_result`` a settled game does, on the
same outbox — the move folds the row and appends the level history — and every
claim is read off ``GET /rankings/padel``, moving the clock.

**One win in padel at σ 0,30 moves a Level a hundredth** — the engine's own
rule for an even game, whose stake of 0,0149 leaves the Level 0,01 up
(``test_what_one_even_win_moves_a_level``). Every gap below is priced against
it: 0,01 is one win, 0,04 about four, and 0,31 more than five.
"""

from __future__ import annotations

from datetime import timedelta

import pytest
from sqlalchemy import delete

from app.bootstrap.composition import build_rebuild_the_rankings
from app.kernel import instant
from app.modules.rankings.infrastructure.ranking_model import (
    LevelPointORM,
    RankingRowORM,
)
from tests.api import players_world as players
from tests.api.rankings_world import (
    chips,
    moves_to,
    ranking,
    results_at,
    stored_points,
)

UP_1 = {"kind": "UP", "places": 1}
DOWN_1 = {"kind": "DOWN", "places": 1}
DOWN_2 = {"kind": "DOWN", "places": 2}
SAME = {"kind": "SAME", "places": None}
NEW = {"kind": "NEW", "places": None}


@pytest.fixture
async def five(client) -> dict[str, dict]:
    """Five padel players, each rated through a real questionnaire."""

    return {
        name: await players.a_rated_player(client, name)
        for name in ("tomek", "karol", "zofia", "ines", "ewa")
    }


async def listed_a_while_ago(session_factory, clock, *levels: tuple) -> None:
    """Each player's five results at the Level paired with them, then the clock
    moved past the chip's week — so every one of them is listed, and none is
    *New*."""

    for player, level in levels:
        await results_at(session_factory, player, [level] * 5, clock)
    clock.move(timedelta(days=8))


def forward_to(clock, when) -> None:
    """The clock moved on to ``when`` — never back."""

    assert when >= clock.now()
    clock.move(when - clock.now())


async def now(session_factory, player: dict, level: float, clock) -> None:
    """One result moving the player to ``level``, settled this instant."""

    await moves_to(session_factory, player, level, at=instant(clock.now()))


# --------------------------------------------------------------------------- #
# The chip
# --------------------------------------------------------------------------- #


async def test_a_newcomer_moves_nobody(client, session_factory, clock, five):
    """Tuesday: Ewa plays her 5th game and enters 3rd. Seven days ago she stood
    there too, by her Level then, so nobody below her reads ▼ — and she reads
    *New*."""

    tomek, karol, zofia, ines, ewa = five.values()
    await listed_a_while_ago(
        session_factory,
        clock,
        (ines, 3.40),
        (karol, 2.75),
        (tomek, 2.71),
        (zofia, 2.69),
    )
    await results_at(session_factory, ewa, [2.72] * 4, clock)
    clock.move(timedelta(days=8))
    before = await ranking(client, tomek)

    await now(session_factory, ewa, 2.73, clock)
    after = await ranking(client, tomek)

    assert [row["nickname"] for row in after["rows"]] == [
        "ines",
        "karol",
        "ewa",
        "tomek",
        "zofia",
    ]
    assert (before["card"]["place"], after["card"]["place"]) == (3, 4)
    assert chips(after) == {
        "ines": SAME,
        "karol": SAME,
        "ewa": NEW,
        "tomek": SAME,
        "zofia": SAME,
    }
    assert after["card"]["chip"] == SAME


async def test_an_overtake_reads_down_one_and_up_one(
    client, session_factory, clock, five
):
    """Monday: Karol, just below Tomek, wins twice and overtakes him."""

    tomek, karol, zofia, ines, _ = five.values()
    await listed_a_while_ago(
        session_factory,
        clock,
        (ines, 3.40),
        (tomek, 2.71),
        (karol, 2.70),
        (zofia, 2.69),
    )

    await now(session_factory, karol, 2.73, clock)
    clock.move(timedelta(hours=2))
    await now(session_factory, karol, 2.75, clock)
    tomeks = await ranking(client, tomek)

    assert tomeks["card"]["chip"] == DOWN_1
    assert chips(tomeks) == {
        "ines": SAME,
        "karol": UP_1,
        "tomek": DOWN_1,
        "zofia": SAME,
    }
    assert (await ranking(client, karol))["card"]["chip"] == UP_1


async def test_new_lasts_seven_days_and_then_the_chip_is_real(
    client, session_factory, clock, five
):
    """Ewa enters between Karol and Tomek, and passes Karol the next day. For
    the week she reads *New*; then her chip counts from where she entered."""

    tomek, karol, zofia, _, ewa = five.values()
    await listed_a_while_ago(
        session_factory, clock, (karol, 2.75), (tomek, 2.71), (zofia, 2.69)
    )
    await results_at(session_factory, ewa, [2.70] * 4, clock)
    clock.move(timedelta(days=8))
    await now(session_factory, ewa, 2.72, clock)
    entered = clock.now()
    clock.move(timedelta(days=1))
    await now(session_factory, ewa, 2.77, clock)

    forward_to(clock, entered + timedelta(days=7) - timedelta(minutes=1))
    still_new = await ranking(client, ewa)
    forward_to(clock, entered + timedelta(days=7))
    a_week_on = await ranking(client, ewa)

    assert still_new["card"]["chip"] == NEW
    assert a_week_on["card"]["chip"] == UP_1
    assert chips(a_week_on) == {
        "ewa": UP_1,
        "karol": DOWN_1,
        "tomek": SAME,
        "zofia": SAME,
    }


async def test_the_window_rolls_day_by_day(client, session_factory, clock, five):
    """Karol passes Tomek on day 0, Zofia passes them both on day 3. Tomek's
    chip counts what moved in the 7 days behind each read, and no more."""

    tomek, karol, zofia, _, _ = five.values()
    await listed_a_while_ago(
        session_factory, clock, (tomek, 2.75), (karol, 2.71), (zofia, 2.69)
    )
    day_0 = clock.now()

    read: dict[int, dict] = {}
    for day in range(11):
        forward_to(clock, day_0 + timedelta(days=day))
        if day == 0:
            await now(session_factory, karol, 2.77, clock)
        if day == 3:
            await now(session_factory, zofia, 2.78, clock)
        clock.move(timedelta(hours=1))
        read[day] = (await ranking(client, tomek))["card"]["chip"]

    assert read == {
        **{day: DOWN_1 for day in (0, 1, 2)},
        **{day: DOWN_2 for day in (3, 4, 5, 6)},
        # Karol's pass is older than a week from day 7; Zofia's from day 10.
        **{day: DOWN_1 for day in (7, 8, 9)},
        10: SAME,
    }


async def test_a_comeback_after_ninety_days_gets_a_real_chip(
    client, session_factory, clock, five
):
    """Inés stops at the bottom, drops off the list, and comes back with a win
    that puts her on top: her Level a week ago is known, so she reads ▲ 3, not
    *New*."""

    tomek, karol, zofia, ines, _ = five.values()
    await listed_a_while_ago(
        session_factory,
        clock,
        (ines, 2.60),
        (karol, 2.75),
        (tomek, 2.71),
        (zofia, 2.69),
    )
    clock.move(timedelta(days=52))
    for player, level in ((karol, 2.75), (tomek, 2.71), (zofia, 2.69)):
        await results_at(session_factory, player, [level], clock)
    clock.move(timedelta(days=35))
    gone = await ranking(client, tomek)
    assert "ines" not in chips(gone)

    await now(session_factory, ines, 2.80, clock)
    back = await ranking(client, ines)

    assert back["card"]["place"] == 1
    assert back["card"]["chip"] == {"kind": "UP", "places": 3}
    assert chips(back) == {
        "ines": {"kind": "UP", "places": 3},
        "karol": DOWN_1,
        "tomek": DOWN_1,
        "zofia": DOWN_1,
    }


async def test_a_player_rated_inside_the_week_is_ordered_by_their_first_level(
    client, session_factory, clock, five
):
    """Ewa answers the questionnaire, then plays five games in a week. With no
    Level a week ago, she stands where her first Level put her — above Tomek —
    so finishing below him reads ▲ 1 on Tomek's chip, and *New* on hers."""

    tomek, karol, *_ = five.values()
    await listed_a_while_ago(session_factory, clock, (karol, 4.90), (tomek, 1.10))
    ewa = await players.a_rated_player(client, "ewa_newcomer")
    assert 1.10 < ewa["mu"] < 4.90

    await results_at(session_factory, ewa, [1.05] * 5, clock)
    read = await ranking(client, tomek)

    assert chips(read) == {"karol": SAME, "tomek": UP_1, "ewa_newcomer": NEW}


# --------------------------------------------------------------------------- #
# The gap line
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    "karols, gap, wins",
    [
        # *0,01 behind Karol · one win closes it*
        (2.72, 0.01, 1),
        # *0,04 behind Karol · about 4 wins close it*
        (2.75, 0.04, 4),
        # *0,31 behind Karol* — more than five, the count left out.
        (3.02, 0.31, None),
    ],
)
async def test_the_gap_line_names_the_player_above_and_the_wins_and_the_player_below(
    client, session_factory, clock, five, karols, gap, wins
):
    tomek, karol, zofia, _, _ = five.values()
    await listed_a_while_ago(
        session_factory, clock, (karol, karols), (tomek, 2.71), (zofia, 2.69)
    )

    card = (await ranking(client, tomek))["card"]

    assert card["gap_line"] == {
        "above": {"nickname": "karol", "gap": gap, "wins": wins, "tied": False},
        "below": {"nickname": "zofia", "gap": 0.02},
        "top_of_the_list": False,
    }


async def test_a_settled_padel_player_is_told_no_count(
    client, session_factory, clock, five
):
    """At σ 0,15 an even padel win is under half a hundredth, so it never moves
    the Level: the line names Karol, 0,01 ahead, and promises no count."""

    tomek, karol, *_ = five.values()
    await listed_a_while_ago(session_factory, clock, (karol, 2.72))
    for _ in range(5):
        await moves_to(
            session_factory, tomek, 2.71, at=instant(clock.now()), sigma=0.15
        )
        clock.move(timedelta(hours=1))

    card = (await ranking(client, tomek))["card"]

    assert card["gap_line"]["above"] == {
        "nickname": "karol",
        "gap": 0.01,
        "wins": None,
        "tied": False,
    }


async def test_level_with_the_player_above_is_a_tie(
    client, session_factory, clock, five
):
    """Ewa and Tomek both at 2,71; Ewa has played one more, so she is above:
    *Level with Ewa · one win puts you ahead*."""

    tomek, _, zofia, _, ewa = five.values()
    await listed_a_while_ago(session_factory, clock, (tomek, 2.71), (zofia, 2.71))
    await results_at(session_factory, ewa, [2.71] * 6, clock)

    card = (await ranking(client, tomek))["card"]

    assert card["gap_line"] == {
        "above": {"nickname": "ewa", "gap": 0.0, "wins": None, "tied": True},
        # *Zofia is level with you* — level, and below on the tie rule.
        "below": {"nickname": "zofia", "gap": 0.0},
        "top_of_the_list": False,
    }


async def test_the_top_of_the_list_is_the_whole_line(
    client, session_factory, clock, five
):
    tomek, karol, *_ = five.values()
    await listed_a_while_ago(session_factory, clock, (tomek, 2.90), (karol, 2.71))

    card = (await ranking(client, tomek))["card"]

    assert card["place"] == 1
    assert card["gap_line"] == {
        "above": None,
        "below": None,
        "top_of_the_list": True,
    }


async def test_last_place_reads_only_the_player_above(
    client, session_factory, clock, five
):
    tomek, karol, *_ = five.values()
    await listed_a_while_ago(session_factory, clock, (karol, 2.72), (tomek, 2.71))

    card = (await ranking(client, tomek))["card"]

    assert card["gap_line"] == {
        "above": {"nickname": "karol", "gap": 0.01, "wins": 1, "tied": False},
        "below": None,
        "top_of_the_list": False,
    }


async def test_a_reader_off_the_list_has_no_chip_and_no_gap_line(
    client, session_factory, clock, five
):
    tomek, karol, *_ = five.values()
    await listed_a_while_ago(session_factory, clock, (karol, 2.72))
    await results_at(session_factory, tomek, [2.71] * 4, clock)

    card = (await ranking(client, tomek))["card"]

    assert (card["state"], card["chip"], card["gap_line"]) == (
        "NEEDS_RESULTS",
        None,
        None,
    )


# --------------------------------------------------------------------------- #
# The level history
# --------------------------------------------------------------------------- #


async def test_the_rebuild_fills_the_history_and_running_it_twice_changes_nothing(
    client, session_factory, clock, five
):
    """Today's players, before the ranking shipped: neither a row nor a point.
    The rebuild folds both from the rating streams, and the chips read the same
    week live delivery did."""

    tomek, karol, zofia, ines, _ = five.values()
    await listed_a_while_ago(
        session_factory,
        clock,
        (ines, 3.40),
        (tomek, 2.71),
        (karol, 2.70),
        (zofia, 2.69),
    )
    await now(session_factory, karol, 2.75, clock)
    live = await stored_points(session_factory)
    live_read = await ranking(client, tomek)
    assert live_read["card"]["chip"] == DOWN_1
    # The opening and five results for three; six results for Karol.
    assert len(live) == 3 * 6 + 7

    async with session_factory() as session:
        await session.execute(delete(LevelPointORM))
        await session.execute(delete(RankingRowORM))
        await session.commit()
    assert await stored_points(session_factory) == []

    async with session_factory() as session:
        first = await build_rebuild_the_rankings(session).execute()
    async with session_factory() as session:
        second = await build_rebuild_the_rankings(session).execute()

    assert (first.rows, first.points, second.points) == (4, len(live), 0)
    assert await stored_points(session_factory) == live
    assert await ranking(client, tomek) == live_read


async def test_a_stream_the_history_never_had_is_filled_on_its_next_result(
    client, session_factory, clock, five
):
    """A store whose history was never filled: the next result's delivery
    hands the history every point of the player's stream."""

    tomek, karol, *_ = five.values()
    await listed_a_while_ago(session_factory, clock, (tomek, 2.71), (karol, 2.70))
    async with session_factory() as session:
        await session.execute(delete(LevelPointORM))
        await session.commit()

    await now(session_factory, karol, 2.75, clock)

    points = await stored_points(session_factory)

    # Karol's whole stream — the opening and six results — and nobody else's:
    # Tomek played nothing since, so his week stands where he stands now.
    assert {point[1] for point in points} == {karol["id"]}
    assert sorted(point[5] for point in points) == [0, 1, 2, 3, 4, 5, 6]
    assert (await ranking(client, tomek))["card"]["chip"] == DOWN_1
