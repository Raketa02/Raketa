"""Hottest groups' rules, on the pure function that holds them (#792; the Home
rows mechanics §5.2–§5.6, ``docs/adr/0204`` §3).

The HTTP suite (``tests/api/test_hottest_groups.py``) walks the same rules as a
player meets them, with games booked and members joined; this is the rule
itself, read off plain numbers — the heat, the two tags, the order, the six
and the bar.
"""

from __future__ import annotations

import random
from uuid import UUID, uuid4

import pytest

from app.modules.groups.domain.hottest import (
    COUNTED_UP_TO,
    PAGE,
    GroupActivity,
    HeatTag,
    faces_to_show,
    heat_of,
    heat_order,
    hottest_groups,
    page_after,
    place_of,
    total_of,
)


def activity(
    games: int = 0, new: int = 0, players: int = 3, group_id: UUID | None = None
) -> GroupActivity:
    return GroupActivity(
        group_id=group_id or uuid4(),
        games_this_week=games,
        new_this_month=new,
        players=players,
    )


def test_the_worked_example_reads_one_hottest_one_growing_and_one_untagged():
    ogrody = activity(games=14, new=3, players=11)
    kazimierz = activity(games=11, new=4, players=10)
    podgorze = activity(games=12, new=2, players=7)

    row = hottest_groups([podgorze, kazimierz, ogrody])

    assert [(hot.activity, hot.heat, hot.tag) for hot in row] == [
        (ogrody, 48, HeatTag.HOTTEST),
        (kazimierz, 44, HeatTag.GROWING),
        (podgorze, 37, None),
    ]
    assert [hot.share for hot in row] == [1, 44 / 48, 37 / 48]


def test_players_count_up_to_twenty_in_the_heat():
    assert heat_of(activity(players=20)) == 20
    assert heat_of(activity(players=120)) == 20
    assert heat_of(activity(games=1, new=1, players=7)) == 2 + 3 + 7


def test_a_group_under_three_players_is_left_out():
    two = activity(games=9, new=2, players=2)
    three = activity(players=3)

    assert [hot.activity for hot in hottest_groups([two, three])] == [three]


def test_no_group_of_three_is_an_empty_row():
    assert hottest_groups([activity(players=2), activity(players=1)]) == ()


def test_the_top_heat_without_a_game_is_no_hottest_even_when_a_lower_one_played():
    crowd = activity(games=0, new=9, players=20)  # 47
    played = activity(games=3, new=0, players=8)  # 14

    row = hottest_groups([played, crowd])

    assert [hot.tag for hot in row] == [HeatTag.GROWING, None]
    # The bars measure against the highest heat in the row.
    assert [hot.share for hot in row] == [1, 14 / 47]


def test_with_no_hottest_no_bar_is_ever_more_than_full():
    """An untagged card can out-heat the strongest GROWING one, and comes after
    it: the bar is over the highest heat in the row, never the first card's."""

    growing = activity(games=0, new=4, players=4)  # 16
    big = activity(games=0, new=0, players=20)  # 20

    row = hottest_groups([big, growing])

    assert [(hot.activity, hot.tag) for hot in row] == [
        (growing, HeatTag.GROWING),
        (big, None),
    ]
    assert [hot.share for hot in row] == [16 / 20, 1]


def test_exactly_one_hottest_however_many_played():
    row = hottest_groups([activity(games=5, players=5), activity(games=4, players=5)])

    assert [hot.tag for hot in row] == [HeatTag.HOTTEST, None]


def test_a_tie_in_heat_goes_to_more_games_then_the_group_id():
    first, second = sorted([uuid4(), uuid4()])
    more_games = activity(games=2, new=0, players=6)  # 10
    fewer_games = activity(games=0, new=2, players=4)  # 10
    a = activity(games=1, players=4, group_id=second)  # 6
    b = activity(games=1, players=4, group_id=first)  # 6

    assert [hot.activity for hot in hottest_groups([fewer_games, more_games])] == [
        more_games,
        fewer_games,
    ]
    assert [hot.activity for hot in hottest_groups([a, b])] == [b, a]


@pytest.mark.parametrize(
    ("new", "players", "growing"),
    [
        (4, 10, True),  # 4 ≥ 2,5
        (3, 4, False),  # +3 is never growing, whatever its size
        (4, 16, True),  # exactly a quarter
        (4, 17, False),  # under a quarter
        (29, 120, False),  # a 120-player group needs +30
        (30, 120, True),
    ],
)
def test_growing_needs_four_new_and_a_quarter_of_today_s_players(new, players, growing):
    top = activity(games=50, players=20)
    other = activity(new=new, players=players)

    [_, hot] = hottest_groups([top, other])

    assert hot.tag is (HeatTag.GROWING if growing else None)


def test_the_hottest_card_is_never_also_growing():
    [hot] = hottest_groups([activity(games=1, new=9, players=9)])

    assert hot.tag is HeatTag.HOTTEST


def test_hottest_then_growing_by_heat_then_untagged_by_heat():
    hottest = activity(games=10, players=20)  # 40
    warm = activity(new=0, players=20)  # 20, untagged
    cool = activity(new=0, players=12)  # 12, untagged
    growing_small = activity(new=4, players=4)  # 16
    growing_big = activity(new=5, players=10)  # 25

    row = hottest_groups([cool, growing_small, warm, hottest, growing_big])

    assert [hot.activity for hot in row] == [
        hottest,
        growing_big,
        growing_small,
        warm,
        cool,
    ]


def test_untagged_drop_out_first_when_tagged_ones_fill_the_six():
    growing = [activity(new=4, players=4) for _ in range(6)]  # 16 each
    hotter_untagged = activity(new=0, players=20)  # 20

    row = hottest_groups([hotter_untagged, *growing])

    assert len(row) == 6
    assert {hot.activity for hot in row} == set(growing)
    assert all(hot.tag is HeatTag.GROWING for hot in row)


def test_at_most_six_cards():
    row = hottest_groups([activity(players=3 + index) for index in range(9)])

    assert [hot.activity.players for hot in row] == [11, 10, 9, 8, 7, 6]


# --------------------------------------------------------------------------- #
# The whole order, its pages and the total (#813; ADR-0205 §6, §7)
# --------------------------------------------------------------------------- #


def a_town() -> list[GroupActivity]:
    """Forty groups of every kind: a HOTTEST, GROWING ones, untagged ones, ties
    in heat and in games, and groups under three players."""

    town = [activity(games=12, new=1, players=12)]  # HOTTEST, 39
    town += [activity(games=n % 3, new=4 + n % 2, players=4 + n) for n in range(12)]
    town += [activity(games=n % 4, new=n % 3, players=3 + n % 7) for n in range(24)]
    town += [activity(games=5, players=2), activity(players=1), activity(players=0)]
    return town


def test_the_order_is_every_group_of_three_hottest_then_growing_then_untagged():
    town = a_town()

    order = heat_order(town)

    assert len(order) == 37
    ranks = [
        {HeatTag.HOTTEST: 0, HeatTag.GROWING: 1, None: 2}[hot.tag] for hot in order
    ]
    assert ranks == sorted(ranks)
    assert [hot.tag for hot in order].count(HeatTag.HOTTEST) == 1
    for tag in (HeatTag.GROWING, None):
        within = [hot for hot in order if hot.tag is tag]
        assert [
            (-hot.heat, -hot.activity.games_this_week, hot.activity.group_id)
            for hot in within
        ] == sorted(
            (-hot.heat, -hot.activity.games_this_week, hot.activity.group_id)
            for hot in within
        )
    assert all(hot.activity.players >= 3 for hot in order)


@pytest.mark.parametrize("seed", range(20))
def test_the_row_is_exactly_the_first_six_of_the_order(seed):
    draw = random.Random(seed)
    town = [
        activity(
            games=draw.choice((0, 0, 1, 2, 5)),
            new=draw.choice((0, 1, 4, 6)),
            players=draw.randint(1, 25),
        )
        for _ in range(draw.randint(0, 30))
    ]

    row = hottest_groups(town)
    order = heat_order(town)

    assert [(hot.activity, hot.tag) for hot in row] == [
        (hot.activity, hot.tag) for hot in order[:6]
    ]


def test_the_order_s_bars_are_over_the_hottest_and_never_more_than_full():
    hottest = activity(games=10, players=20)  # 40
    rest = [activity(new=4, players=4 + n) for n in range(8)]

    order = heat_order([hottest, *rest])

    assert order[0].share == 1
    assert [hot.share for hot in order[1:]] == [hot.heat / 40 for hot in order[1:]]


def test_with_no_hottest_the_order_s_bars_are_over_the_highest_heat_on_it():
    """Six GROWING groups fill the row and push a hotter untagged one off it;
    on the whole order it comes seventh, and its bar is the full one."""

    growing = [activity(new=4, players=4) for _ in range(6)]  # 16 each
    hotter_untagged = activity(new=0, players=20)  # 20

    order = heat_order([hotter_untagged, *growing])

    assert [hot.activity for hot in order][-1] == hotter_untagged
    assert [hot.share for hot in order] == [16 / 20] * 6 + [1]


def test_no_group_of_three_is_an_empty_order():
    assert heat_order([activity(players=2)]) == ()


def test_pages_of_twenty_follow_the_order_and_the_last_names_no_next():
    order = heat_order(a_town())

    first, after_first = page_after(order, None)
    second, after_second = page_after(order, after_first)

    assert PAGE == 20
    assert first == order[:20]
    assert after_first == place_of(order[19])
    assert second == order[20:]
    assert after_second is None


def test_a_page_exactly_full_at_the_end_names_no_next():
    order = heat_order([activity(players=3 + n % 5) for n in range(40)])

    _, after_first = page_after(order, None)
    second, after_second = page_after(order, after_first)

    assert len(second) == 20
    assert after_second is None


def test_a_page_reads_on_from_the_place_named_whoever_moved_meanwhile():
    """The cursor is a place in the order, not a count: a group that heated up
    past it since is not read twice, and the groups behind it don't shift."""

    town = [activity(players=3 + n) for n in range(25)]
    _, after_first = page_after(heat_order(town), None)
    # The coolest group on the first page heats up to the top; one behind the
    # cursor leaves.
    leaving = heat_order(town)[22].activity
    heated = heat_order(town)[19].activity
    later = [
        activity(games=0, new=0, players=20, group_id=heated.group_id)
        if one is heated
        else one
        for one in town
        if one is not leaving
    ]

    second, _ = page_after(heat_order(later), after_first)

    expected = [
        hot.activity for hot in heat_order(town)[20:] if hot.activity != leaving
    ]
    assert [hot.activity for hot in second] == expected


def test_a_page_past_the_end_is_empty():
    order = heat_order([activity(players=3 + n) for n in range(5)])

    assert page_after(order, place_of(order[-1])) == ((), None)


def test_the_total_counts_every_group_of_three_up_to_a_hundred():
    assert total_of(a_town()) == 37
    assert total_of([activity(players=2)]) == 0
    assert total_of([]) == 0
    assert COUNTED_UP_TO == 100
    assert total_of([activity(players=3) for _ in range(100)]) == 100
    assert total_of([activity(players=3) for _ in range(140)]) == 100


# --------------------------------------------------------------------------- #
# The faces (call 5)
# --------------------------------------------------------------------------- #

READER, ANIA, BARTEK, CELINA, DAREK, EWA, FILIP, GOSIA = (uuid4() for _ in range(8))


def test_the_reader_s_friends_first_then_the_longest_standing():
    members = (ANIA, BARTEK, CELINA, DAREK)

    assert faces_to_show(
        members, friends=frozenset({DAREK, BARTEK}), reader=READER, at_most=6
    ) == (BARTEK, DAREK, ANIA, CELINA)


def test_never_the_reader_s_own_face_and_at_most_six():
    members = (ANIA, READER, BARTEK, CELINA, DAREK, EWA, FILIP, GOSIA)

    assert faces_to_show(
        members, friends=frozenset({GOSIA}), reader=READER, at_most=6
    ) == (GOSIA, ANIA, BARTEK, CELINA, DAREK, EWA)
