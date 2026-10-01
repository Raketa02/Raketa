"""Who a post is for — the pure rules of *Who* and *Level* (#546; the mechanics
§9.1 steps 3–4; the screens A5.1).

**Who** is a game's own rule about everybody on it, the poster included:
*Men* and *Women* are games of one gender, *Mixed pairs* a doubles of two men
and two women standing one of each a side, and only somebody with a gender set
is counted for any of the three. Somebody whose own preference excludes the
game is never on it.

**Level** is a range the others' Levels are inside. It starts as the engine's
own window for the kind around the poster's Level, rounded inward to the
hundredth so the bounds a client prints are never wider than the window, and
it may be narrowed and never widened.
"""

from __future__ import annotations

from uuid import uuid4

import pytest

from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.proposals.domain.errors import (
    LevelRangeInverted,
    LevelRangeTooWide,
    MixedPairsOnlyInDoubles,
)
from app.modules.proposals.domain.post import (
    LevelRange,
    PostedFor,
    Who,
    stand_together,
)
from app.kernel import Sport

MAN, WOMAN, UNSAID = Gender.MAN, Gender.WOMAN, Gender.PREFER_NOT_TO_SAY
ANY, MEN_ONLY, WOMEN_ONLY = (
    GenderPreference.ANY,
    GenderPreference.MEN_ONLY,
    GenderPreference.WOMEN_ONLY,
)


# --------------------------------------------------------------------------- #
# Who
# --------------------------------------------------------------------------- #


def test_anyone_is_everybody_whatever_they_said():
    for gender in (MAN, WOMAN, UNSAID, None):
        for preference in (ANY, MEN_ONLY, WOMEN_ONLY, None):
            assert Who.ANYONE.admits(gender, preference)


@pytest.mark.parametrize(
    ("who", "gender", "preference", "admitted"),
    [
        (Who.MEN, MAN, ANY, True),
        (Who.MEN, MAN, MEN_ONLY, True),
        # Their own preference excludes a game of men only.
        (Who.MEN, MAN, WOMEN_ONLY, False),
        (Who.MEN, WOMAN, ANY, False),
        (Who.WOMEN, WOMAN, ANY, True),
        (Who.WOMEN, WOMAN, WOMEN_ONLY, True),
        (Who.WOMEN, WOMAN, MEN_ONLY, False),
        (Who.WOMEN, MAN, ANY, False),
        # Mixed pairs meets both: only a preference for anybody takes it.
        (Who.MIXED_PAIRS, MAN, ANY, True),
        (Who.MIXED_PAIRS, WOMAN, ANY, True),
        (Who.MIXED_PAIRS, MAN, MEN_ONLY, False),
        (Who.MIXED_PAIRS, WOMAN, WOMEN_ONLY, False),
    ],
)
def test_men_women_and_mixed_pairs_are_the_players_own_and_their_preference(
    who, gender, preference, admitted
):
    assert who.admits(gender, preference) is admitted


@pytest.mark.parametrize("who", [Who.MEN, Who.WOMEN, Who.MIXED_PAIRS])
def test_only_somebody_with_a_gender_set_is_counted(who):
    assert not who.admits(UNSAID, ANY)
    assert not who.admits(None, ANY)
    # An unreadable preference excludes, as the mutual gate's does.
    assert not who.admits(MAN, None)
    assert not who.admits(WOMAN, None)


def test_mixed_pairs_is_a_doubles_game_only():
    Who.MIXED_PAIRS.refuse_unless_offered_in(Sport.PADEL)
    Who.MIXED_PAIRS.refuse_unless_offered_in(Sport.BADMINTON)
    with pytest.raises(MixedPairsOnlyInDoubles):
        Who.MIXED_PAIRS.refuse_unless_offered_in(Sport.TENNIS)
    Who.MEN.refuse_unless_offered_in(Sport.SQUASH)


def test_mixed_pairs_stand_two_of_each_and_no_more():
    one, two, three, four, five = (uuid4() for _ in range(5))
    genders = {one: MAN, two: WOMAN, three: MAN, four: WOMAN, five: MAN}

    assert stand_together(Who.MIXED_PAIRS, genders, (one, two, three, four), seats=4)
    assert stand_together(Who.MIXED_PAIRS, genders, (one, three), seats=4)
    assert not stand_together(Who.MIXED_PAIRS, genders, (one, three, five), seats=4)
    # Somebody whose gender cannot be read stands with nobody on a mixed game.
    assert not stand_together(Who.MIXED_PAIRS, {one: MAN}, (one, two), seats=4)
    # Every other game stands together whoever is on it.
    assert stand_together(Who.ANYONE, genders, (one, three, five), seats=4)
    assert stand_together(None, genders, (one, three, five), seats=4)


# --------------------------------------------------------------------------- #
# Level
# --------------------------------------------------------------------------- #


def test_the_engine_s_window_is_rounded_inward_to_the_hundredth():
    window = LevelRange.around(2.7345, tolerance=0.5)

    assert window == LevelRange(low=2.24, high=3.23)


def test_a_window_on_the_hundredth_keeps_its_bounds():
    # 2.73 - 0.5 is 2.2300000000000004 in binary; it is still 2.23.
    assert LevelRange.around(2.73, tolerance=0.5) == LevelRange(low=2.23, high=3.23)


def test_a_range_admits_the_levels_inside_it_bounds_included():
    levels = LevelRange(low=2.5, high=3.0)

    assert levels.admits(2.5)
    assert levels.admits(2.75)
    assert levels.admits(3.0)
    assert not levels.admits(2.49)
    assert not levels.admits(3.01)


def test_a_narrower_range_is_taken_and_a_wider_one_refused():
    window = LevelRange(low=2.24, high=3.23)

    assert window.narrowed_to(low=2.34, high=3.13) == LevelRange(low=2.34, high=3.13)
    assert window.narrowed_to(low=None, high=None) == window
    assert window.narrowed_to(low=2.5, high=None) == LevelRange(low=2.5, high=3.23)
    with pytest.raises(LevelRangeTooWide) as wider:
        window.narrowed_to(low=2.19, high=3.23)
    assert wider.value.details == {"low": 2.24, "high": 3.23}
    with pytest.raises(LevelRangeTooWide):
        window.narrowed_to(low=None, high=3.28)
    with pytest.raises(LevelRangeInverted):
        window.narrowed_to(low=3.0, high=2.9)


def test_a_post_is_for_a_who_and_a_level_range_and_the_poster_is_not_held_to_it():
    posted_for = PostedFor(who=Who.WOMEN, levels=LevelRange(low=2.5, high=3.0))

    assert posted_for.admits(level=2.75, gender=WOMAN, preference=ANY)
    assert not posted_for.admits(level=3.25, gender=WOMAN, preference=ANY)
    assert not posted_for.admits(level=2.75, gender=MAN, preference=ANY)
    assert not posted_for.admits(level=None, gender=WOMAN, preference=ANY)
    # The poster stands on the game whatever their own Level.
    assert posted_for.includes_the_poster(gender=WOMAN, preference=ANY)
    assert not posted_for.includes_the_poster(gender=MAN, preference=ANY)
