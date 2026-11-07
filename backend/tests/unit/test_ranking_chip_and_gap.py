"""The level history, the chip and the gap line, at the domain's own seam (#769;
``docs/adr/0203`` §4, §6; the mechanics §6–§7)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest

from app.kernel import Instant, InvariantViolated, Sport, instant
from app.modules.rankings.domain.ranking import (
    CHIP_WINDOW,
    WINS_COUNTED,
    Chip,
    ChipKind,
    GapLine,
    LevelMove,
    LevelPoint,
    Outcome,
    PlayerAbove,
    RankingRow,
    RatingHistory,
    chips_of,
    one_win,
    player_above,
    player_below,
    points_of,
    row_of,
    wins_to_close,
)
from app.shared.ids import new_uuid

START = instant(datetime(2026, 9, 1, 18, 0, tzinfo=timezone.utc))
#: Long enough after everybody entered General that nobody is *New*.
NOW = instant(START + timedelta(days=30))


def at(hours: float) -> Instant:
    return instant(START + timedelta(hours=hours))


def a_row(
    hundredths: int,
    *,
    player_id: UUID | None = None,
    results: int = 5,
    entered: Instant = START,
    sigma: float = 0.30,
    sport: Sport = Sport.PADEL,
) -> RankingRow:
    return RankingRow(
        player_id=player_id or new_uuid(),
        sport=sport,
        hundredths=hundredths,
        sigma=sigma,
        results=results,
        last_result_at=entered,
        level_reached_at=entered,
        general_entered_at=entered if results >= 5 else None,
        friends_entered_at=entered,
        form=(Outcome.WIN,) * min(results, 5),
    )


def a_point(row: RankingRow, hundredths: int, *, results: int = 5) -> LevelPoint:
    """Where ``row``'s player stood 7 days ago."""

    return LevelPoint(
        event_id=new_uuid(),
        player_id=row.player_id,
        sport=row.sport,
        at=START,
        hundredths=hundredths,
        results=results,
        level_reached_at=START,
    )


def in_order(*rows: RankingRow) -> list[RankingRow]:
    """Today's set, in today's order — the Level alone decides in these tests."""

    return sorted(rows, key=lambda row: -row.hundredths)


# --------------------------------------------------------------------------- #
# The level history
# --------------------------------------------------------------------------- #


def a_history(*levels: float, initial: float = 2.5) -> RatingHistory:
    return RatingHistory(
        player_id=new_uuid(),
        sport=Sport.PADEL,
        initial_mu=initial,
        initialised_at=START,
        moves=tuple(
            LevelMove(
                game_id=new_uuid(),
                won=True,
                mu=mu,
                sigma=0.3,
                at=at(hour),
                event_id=new_uuid(),
            )
            for hour, mu in enumerate(levels, start=1)
        ),
        opened_by=new_uuid(),
    )


def test_no_result_makes_no_history():
    assert points_of(a_history()) == ()


def test_the_history_is_the_opening_then_a_point_per_result_keyed_by_its_event():
    history = a_history(2.55, 2.55, 2.6)

    points = points_of(history)

    assert [point.event_id for point in points] == [
        history.opened_by,
        *(move.event_id for move in history.moves),
    ]
    assert [(point.at, point.hundredths, point.results) for point in points] == [
        (START, 250, 0),
        (at(1), 255, 1),
        (at(2), 255, 2),
        (at(3), 260, 3),
    ]
    # A move that leaves the Level where it was reaches nothing new.
    assert [point.level_reached_at for point in points] == [
        START,
        at(1),
        at(1),
        at(3),
    ]


def test_the_row_is_the_historys_last_point():
    history = a_history(2.55, 2.6, 2.58, 2.6, 2.61, 2.61)

    row, last = row_of(history), points_of(history)[-1]

    assert row is not None
    assert (row.hundredths, row.results, row.level_reached_at) == (
        last.hundredths,
        last.results,
        last.level_reached_at,
    )
    assert row.general_entered_at == points_of(history)[5].at


# --------------------------------------------------------------------------- #
# The chip
# --------------------------------------------------------------------------- #


def test_an_arrival_moves_nobody():
    """Ewa enters General between Karol and Tomek; 7 days ago she stood there
    too, by her Level then — so nobody below her reads ▼."""

    karol, tomek, zofia = a_row(275), a_row(271), a_row(269)
    ewa = a_row(273, entered=instant(NOW - timedelta(days=1)))
    then = {
        karol.player_id: a_point(karol, 275),
        tomek.player_id: a_point(tomek, 271),
        zofia.player_id: a_point(zofia, 269),
        ewa.player_id: a_point(ewa, 272, results=4),
    }

    chips = chips_of(in_order(karol, tomek, zofia, ewa), then, now=NOW)

    assert chips == {
        karol.player_id: Chip(ChipKind.SAME),
        ewa.player_id: Chip(ChipKind.NEW),
        tomek.player_id: Chip(ChipKind.SAME),
        zofia.player_id: Chip(ChipKind.SAME),
    }


def test_an_overtake_moves_both():
    karol, tomek, zofia = a_row(275), a_row(271), a_row(269)
    then = {
        karol.player_id: a_point(karol, 270),
        tomek.player_id: a_point(tomek, 271),
        zofia.player_id: a_point(zofia, 269),
    }

    chips = chips_of(in_order(karol, tomek, zofia), then, now=NOW)

    assert chips == {
        karol.player_id: Chip(ChipKind.UP, 1),
        tomek.player_id: Chip(ChipKind.DOWN, 1),
        zofia.player_id: Chip(ChipKind.SAME),
    }


def test_a_climb_past_two_reads_two():
    ines, karol, tomek = a_row(340), a_row(275), a_row(271)
    then = {
        ines.player_id: a_point(ines, 260),
        karol.player_id: a_point(karol, 275),
        tomek.player_id: a_point(tomek, 271),
    }

    chips = chips_of(in_order(ines, karol, tomek), then, now=NOW)

    assert chips[ines.player_id] == Chip(ChipKind.UP, 2)
    assert chips[karol.player_id] == chips[tomek.player_id] == Chip(ChipKind.DOWN, 1)


def test_new_is_the_seven_days_after_the_fifth_result():
    entered = instant(NOW - CHIP_WINDOW)
    ewa = a_row(275, entered=instant(entered + timedelta(seconds=1)))
    seasoned = a_row(273, entered=entered)

    chips = chips_of(in_order(ewa, seasoned), {}, now=NOW)

    assert chips[ewa.player_id] == Chip(ChipKind.NEW)
    assert chips[seasoned.player_id] == Chip(ChipKind.SAME)


def test_a_row_with_no_history_stands_where_it_stands_now():
    """A store the rebuild hasn't filled: nobody's chip is invented."""

    karol, tomek = a_row(275), a_row(271)

    chips = chips_of(in_order(karol, tomek), {}, now=NOW)

    assert set(chips.values()) == {Chip(ChipKind.SAME)}


def test_a_chip_says_how_many_places_exactly_when_it_moved():
    with pytest.raises(InvariantViolated):
        Chip(ChipKind.UP)
    with pytest.raises(InvariantViolated):
        Chip(ChipKind.SAME, 1)


# --------------------------------------------------------------------------- #
# The gap line
# --------------------------------------------------------------------------- #


def test_one_win_is_the_engines_even_game_at_the_readers_own_level():
    """In hundredths, the Level the win leaves: a hundredth in padel at σ 0,30,
    six in singles, and nothing at all for a settled padel player
    (``test_what_one_even_win_moves_a_level``)."""

    assert one_win(a_row(271)) == 1
    assert one_win(a_row(271, sport=Sport.TENNIS)) == 6
    assert one_win(a_row(271, sigma=0.15)) == 0


@pytest.mark.parametrize(
    "gap, win, wins",
    [
        (1, 1, 1),
        (4, 1, 4),
        (5, 1, 5),
        (6, 1, None),
        (3, 2, 2),
        (4, 2, 2),
        (10, 2, 5),
        (11, 2, None),
        (31, 6, None),
    ],
)
def test_the_wins_are_the_gap_over_one_win_rounded_up(gap, win, wins):
    assert WINS_COUNTED == 5
    assert wins_to_close(gap, win=win) == wins


def test_a_win_that_moves_no_level_closes_no_gap():
    """However close the player above, no count of such wins reaches them —
    so the line leaves the count out rather than promise one."""

    assert wins_to_close(1, win=0) is None


def test_the_player_above_is_named_with_the_gap_and_the_wins():
    tomek, karol = a_row(271), a_row(275)

    assert player_above(tomek, karol, "karol") == PlayerAbove(
        nickname="karol", gap=4, wins=4, tied=False
    )


def test_a_tie_with_the_player_above_is_tied_with_no_count():
    tomek, ewa = a_row(271), a_row(271)

    assert player_above(tomek, ewa, "ewa") == PlayerAbove(
        nickname="ewa", gap=0, wins=None, tied=True
    )


def test_the_player_below_is_named_with_the_gap():
    tomek, zofia = a_row(271), a_row(269)

    below = player_below(tomek, zofia, "zofia")

    assert (below.nickname, below.gap) == ("zofia", 2)
    assert player_below(tomek, a_row(271), "ola").gap == 0


def test_the_top_of_the_list_is_the_whole_line():
    above = PlayerAbove(nickname="karol", gap=4, wins=4, tied=False)

    with pytest.raises(InvariantViolated):
        GapLine(above=above, below=None, top_of_the_list=True)
    with pytest.raises(InvariantViolated):
        GapLine(
            above=None,
            below=player_below(a_row(271), a_row(269), "zofia"),
            top_of_the_list=True,
        )
