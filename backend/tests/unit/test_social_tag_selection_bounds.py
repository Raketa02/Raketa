"""How many Social tags a player must hold: the floor, the ceiling, and the rule.

The two numbers are written out here rather than read from the module: a change
to what every client's picker allows and what the commit accepts should have to
be argued with, not absorbed. Unlike a
tag id they are *tunable* — nothing persists a bound — so reddening this file is
a prompt to think, not a refusal.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_SELECTION_BOUNDS,
    SocialTagSelectionBounds,
)


def test_a_player_holds_between_two_and_six_tags():
    assert SOCIAL_TAG_SELECTION_BOUNDS.minimum_tags == 2
    assert SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags == 6


@pytest.mark.parametrize("tag_count", [2, 3, 4, 5, 6])
def test_a_selection_inside_the_range_is_allowed(tag_count):
    assert SOCIAL_TAG_SELECTION_BOUNDS.contains(tag_count)


@pytest.mark.parametrize("tag_count", [0, 1, 7, 18])
def test_a_selection_outside_the_range_is_refused(tag_count):
    assert not SOCIAL_TAG_SELECTION_BOUNDS.contains(tag_count)


def test_both_ends_of_the_range_are_included():
    assert SOCIAL_TAG_SELECTION_BOUNDS.contains(
        SOCIAL_TAG_SELECTION_BOUNDS.minimum_tags
    )
    assert SOCIAL_TAG_SELECTION_BOUNDS.contains(
        SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags
    )


def test_a_negative_count_is_refused():
    # Not reachable from a list length, but the predicate is the one place the
    # question is answered — it should not need a caller to have sanitised.
    assert not SOCIAL_TAG_SELECTION_BOUNDS.contains(-1)


def test_the_ceiling_fits_inside_the_vocabulary():
    from app.modules.player_profile.domain.social_tags import SocialTag

    # A ceiling above the vocabulary would be a rule no player could break, and
    # a picker whose counter never reaches its own maximum.
    assert SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags <= len(SocialTag)


def test_an_inverted_range_cannot_be_declared():
    with pytest.raises(InvariantViolated):
        SocialTagSelectionBounds(minimum_tags=6, maximum_tags=2)


def test_a_negative_floor_cannot_be_declared():
    with pytest.raises(InvariantViolated):
        SocialTagSelectionBounds(minimum_tags=-1, maximum_tags=6)


def test_a_collapsed_range_is_a_rule_and_can_be_declared():
    # "Exactly three tags" is an opinion a product could hold, so the type does
    # not refuse it.
    exactly_three = SocialTagSelectionBounds(minimum_tags=3, maximum_tags=3)

    assert exactly_three.contains(3)
    assert not exactly_three.contains(2)
    assert not exactly_three.contains(4)
