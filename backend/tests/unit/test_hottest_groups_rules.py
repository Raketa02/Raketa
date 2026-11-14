"""Hottest groups' rules, on the pure function that holds them (#792; the Home
rows mechanics §5.2–§5.6, ``docs/adr/0204`` §3).

The HTTP suite (``tests/api/test_hottest_groups.py``) walks the same rules as a
player meets them, with games booked and members joined; this is the rule
itself, read off plain numbers — the heat, the two tags, the order, the six
and the bar.
"""

from __future__ import annotations

from uuid import UUID, uuid4

import pytest

from app.modules.groups.domain.hottest import (
    GroupActivity,
    HeatTag,
    faces_to_show,
    heat_of,
    hottest_groups,
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
