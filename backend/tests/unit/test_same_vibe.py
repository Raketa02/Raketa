"""*Same vibe players*' pure rules (#795; the home-rows mechanics §8, §9):
the vibe %, the order and its ties, and the row of ten."""

from __future__ import annotations

from uuid import UUID

import pytest

from app.kernel import InvariantViolated
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.same_vibe import (
    GOOD_MATCH,
    RowOfTen,
    VibeKey,
    VibePlayer,
    is_fresh,
    vibe_percent,
    vibe_player,
)

MINE = frozenset({"A", "B", "C", "D", "E", "F"})


def player(n: int, *tags: str) -> VibePlayer:
    found = vibe_player(UUID(int=n), f"p{n}", None, tags, mine=MINE)
    assert found is not None
    return found


# --------------------------------------------------------------------------- #
# The vibe %
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize(
    ("shared", "percent"),
    # 7 and 8 since a player may hold eight (ADR-0207 §7): 99,22 reads 99, and
    # 99,61 reads 100 — true, since the two players' eight would be the same.
    [(1, 50), (2, 75), (3, 88), (4, 94), (5, 97), (6, 98), (7, 99), (8, 100)],
)
def test_the_vibe_percent_closes_half_of_what_is_left_with_each_tag(shared, percent):
    assert vibe_percent(shared) == percent


def test_nobody_shares_no_tag():
    with pytest.raises(InvariantViolated):
        vibe_percent(0)


# --------------------------------------------------------------------------- #
# Who, and what a card carries
# --------------------------------------------------------------------------- #


def test_somebody_sharing_no_tag_is_nobody_on_the_row():
    assert vibe_player(UUID(int=1), "x", None, ("X", "Y"), mine=MINE) is None


def test_a_card_carries_the_shared_tags_in_their_order_and_counts_the_rest():
    karol = player(1, "F", "X", "B", "Y")

    assert karol.shared_tags == ("F", "B")
    assert karol.in_common == 2
    assert karol.not_shared == 2
    assert karol.percent == 75


# --------------------------------------------------------------------------- #
# The order
# --------------------------------------------------------------------------- #


def ordered(*players: VibePlayer) -> list[int]:
    return [one.player_id.int for one in sorted(players, key=lambda p: p.key.order)]


def test_more_shared_tags_first():
    assert ordered(player(1, "A"), player(2, "A", "B", "C"), player(3, "A", "B")) == [
        2,
        3,
        1,
    ]


def test_a_tie_goes_to_fewer_tags_not_shared_then_the_player_id():
    assert ordered(
        player(3, "A", "B", "X"),
        player(1, "A", "B", "X", "Y"),
        player(2, "A", "B", "Y"),
        player(4, "A", "B"),
    ) == [4, 2, 3, 1]


def test_a_key_is_behind_every_key_before_it_in_the_order():
    first, second = player(2, "A", "B"), player(1, "A", "X")

    assert second.key.is_behind(first.key)
    assert not first.key.is_behind(second.key)
    assert not first.key.is_behind(first.key)


def test_a_key_compares_by_its_three_parts():
    one = VibeKey(in_common=3, not_shared=1, player_id=UUID(int=9))

    assert VibeKey(in_common=2, not_shared=0, player_id=UUID(int=1)).is_behind(one)
    assert VibeKey(in_common=3, not_shared=2, player_id=UUID(int=1)).is_behind(one)
    assert VibeKey(in_common=3, not_shared=1, player_id=UUID(int=10)).is_behind(one)
    assert not VibeKey(in_common=3, not_shared=1, player_id=UUID(int=8)).is_behind(one)


# --------------------------------------------------------------------------- #
# Fresh, then gaps
# --------------------------------------------------------------------------- #


def test_a_good_match_is_two_shared_tags_or_more():
    assert GOOD_MATCH == 2
    good, weaker = player(1, "A", "B"), player(2, "A")

    assert is_fresh(good.in_common, Relation.NONE, rested=False)
    assert is_fresh(good.in_common, Relation.ASKED_YOU, rested=False)
    assert not is_fresh(good.in_common, Relation.SENT, rested=False)
    assert not is_fresh(good.in_common, Relation.FRIEND, rested=False)
    assert not is_fresh(good.in_common, Relation.NONE, rested=True)
    assert not is_fresh(weaker.in_common, Relation.NONE, rested=False)


def test_fresh_good_matches_lead_and_a_friend_waits_in_a_gap():
    karol = player(1, "A", "B", "C", "D", "E", "F")
    bartek = player(2, "A", "B", "C")
    kuba = player(3, "A", "B")
    one_tag = player(4, "A")
    row = RowOfTen()
    for one, relation in (
        (karol, Relation.FRIEND),
        (bartek, Relation.NONE),
        (kuba, Relation.ASKED_YOU),
        (one_tag, Relation.NONE),
    ):
        row.take(one, relation=relation, rested=False)

    assert [one.nickname for one in row.row()] == ["p2", "p3", "p1", "p4"]


def test_ten_fresh_fill_the_row_and_nobody_else_is_on_it():
    row = RowOfTen()
    row.take(player(99, "A", "B", "C"), relation=Relation.FRIEND, rested=False)
    for n in range(1, 12):
        if row.full:
            break
        row.take(player(n, "A", "B"), relation=Relation.NONE, rested=False)

    assert row.full
    assert [one.player_id.int for one in row.row()] == list(range(1, 11))
