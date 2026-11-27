"""How many Social tags a player must hold: the floor, the ceiling, and the rule.

The two numbers are written out here rather than read from the module: a change
to what every client's picker allows and what the commit accepts should have to
be argued with, not absorbed. Unlike a
tag id they are *tunable* — nothing persists a bound — so reddening this file is
a prompt to think, not a refusal. It reddened on 2026-11-22, when ADR-0207 §7
raised the ceiling from six to eight (#829).
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.player_profile.domain.errors import SocialTagSelectionOutOfBounds
from app.modules.player_profile.domain.social_tags import (
    SOCIAL_TAG_SELECTION_BOUNDS,
    SocialTag,
    SocialTagSelection,
    SocialTagSelectionBounds,
)

#: Nine of the tags, in the vocabulary's order, so a slice is a selection.
NINE = (
    SocialTag.STAYS_FOR_A_DRINK,
    SocialTag.STAYS_FOR_A_COFFEE,
    SocialTag.PLAYS_TO_WIN,
    SocialTag.LAUGHS_OFF_MISTAKES,
    SocialTag.PATIENT_WITH_BEGINNERS,
    SocialTag.BRINGS_THE_ENERGY,
    SocialTag.HERE_TO_IMPROVE,
    SocialTag.HERE_TO_MEET_PLAYERS,
    SocialTag.NEW_IN_TOWN,
)


def test_a_player_holds_between_two_and_eight_tags():
    assert SOCIAL_TAG_SELECTION_BOUNDS.minimum_tags == 2
    assert SOCIAL_TAG_SELECTION_BOUNDS.maximum_tags == 8


@pytest.mark.parametrize("tag_count", [2, 3, 4, 5, 6, 7, 8])
def test_a_selection_inside_the_range_is_allowed(tag_count):
    assert SOCIAL_TAG_SELECTION_BOUNDS.contains(tag_count)


@pytest.mark.parametrize("tag_count", [0, 1, 9, 27])
def test_a_selection_outside_the_range_is_refused(tag_count):
    assert not SOCIAL_TAG_SELECTION_BOUNDS.contains(tag_count)


def test_a_player_may_choose_eight_tags():
    assert len(SocialTagSelection.chosen(NINE[:8])) == 8


@pytest.mark.parametrize("tag_count", [1, 9])
def test_a_choice_of_one_tag_or_nine_is_refused(tag_count):
    with pytest.raises(SocialTagSelectionOutOfBounds):
        SocialTagSelection.chosen(NINE[:tag_count])


def test_six_tags_on_a_stream_from_before_the_eight_still_replay():
    # The ceiling was six when a selection like this was written, from the
    # nineteen that stood then. Raising it refuses nothing already recorded,
    # and six is still a number a player may choose.
    six = tuple(
        tag.value
        for tag in (
            SocialTag.STAYS_FOR_A_DRINK,
            SocialTag.SHARES_A_LIFT,
            SocialTag.PLAYS_TO_WIN,
            SocialTag.WARMS_UP_PROPERLY,
            SocialTag.HERE_TO_IMPROVE,
            SocialTag.OPEN_TO_MEET_SOMEONE,
        )
    )

    assert SocialTagSelection.recorded(six).ids == six
    assert SocialTagSelection.from_ids(six).ids == six


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
