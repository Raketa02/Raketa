"""A For-fun table's **Social vibe** — how much of what everyone at it carries is
shared there (``docs/adr/0207`` §2, #830).

On average, each tag at the table is carried by that share of the other
players: ``Σᵢ Σ_{t∈Tᵢ} (c_t − 1)/(n − 1) ÷ Σᵢ |Tᵢ|``, as a whole percent rounded
half up. The engine is handed the tags that count — which ones don't is the
Player profile's, and is removed before it is asked — so the claims here are
the formula's: the ADR's sanity values, singles as the plain overlap, and no
value at a table of fewer than two.
"""

from __future__ import annotations

from fractions import Fraction

import pytest

from app.engines.matchfit.v1 import social_vibe, social_vibe_share


def test_four_who_share_every_tag_are_a_hundred():
    every = frozenset({"x", "y", "z"})

    assert social_vibe([every, every, every, every]) == 100


def test_two_pairs_who_share_nothing_across_the_table_are_thirty_three():
    """Everything shared with a partner and nothing across is not a perfect
    table: each tag is carried by one of the three others."""

    ours, theirs = frozenset({"x", "y", "z"}), frozenset({"p", "q", "r"})

    assert social_vibe([ours, ours, theirs, theirs]) == 33


def test_a_table_sharing_some_of_what_it_carries_is_the_adr_s_thirty():
    """(1 + 1 + ⅔ + 0) ÷ 9 carryings: 29.6, rounded half up."""

    table = [
        frozenset({"x", "y", "z"}),
        frozenset({"x", "y"}),
        frozenset({"x", "w"}),
        frozenset({"v", "u"}),
    ]

    assert social_vibe_share(table) == Fraction(8, 27)
    assert social_vibe(table) == 30


@pytest.mark.parametrize(
    ("mine", "yours", "pct"),
    [
        # Twice the tags they share, over every tag the two carry.
        ({"x", "y", "z"}, {"x", "y", "w"}, 67),
        ({"x", "y"}, {"x", "y", "z", "w"}, 67),
        ({"x", "y"}, {"z", "w"}, 0),
        ({"x", "y"}, {"y", "x"}, 100),
    ],
)
def test_in_singles_it_is_the_plain_overlap_of_the_two(mine, yours, pct):
    assert social_vibe([frozenset(mine), frozenset(yours)]) == pct
    shared = len(set(mine) & set(yours))
    assert social_vibe_share([frozenset(mine), frozenset(yours)]) == Fraction(
        2 * shared, len(mine) + len(yours)
    )


def test_a_tag_carried_by_all_four_counts_for_more_than_one_carried_by_two():
    by_two = [frozenset(tags) for tags in ({"x", "a"}, {"x", "b"}, {"c"}, {"e"})]
    by_four = [frozenset(tags) for tags in ({"x", "a"}, {"x", "b"}, {"x"}, {"x"})]

    assert social_vibe(by_four) > social_vibe(by_two)


def test_a_half_is_rounded_up():
    """⅛ of a table's carryings shared is 12.5%, which is 13 — half up, as
    the Vibe % is, never the banker's 12."""

    # Two players: 2 × 1 shared ÷ 16 carried = 12.5%.
    mine = frozenset({"x", *(f"m{index}" for index in range(7))})
    yours = frozenset({"x", *(f"y{index}" for index in range(7))})

    assert social_vibe_share([mine, yours]) == Fraction(1, 8)
    assert social_vibe([mine, yours]) == 13


@pytest.mark.parametrize("table", [[], [frozenset({"x", "y"})]])
def test_fewer_than_two_people_give_no_value(table):
    assert social_vibe(table) is None
    assert social_vibe_share(table) is None


def test_a_table_nobody_at_which_carries_a_tag_gives_no_value():
    """Nothing carried is nothing to measure — not a table that shares none.
    At a real table it never happens: everybody holds a counted tag."""

    assert social_vibe([frozenset(), frozenset()]) is None


def test_somebody_carrying_nothing_still_sits_at_the_table():
    """They share nothing, and they are one of the others each tag could be
    carried by: two who share everything and one with nothing is a half."""

    both = frozenset({"x", "y"})

    assert social_vibe([both, both, frozenset()]) == 50
