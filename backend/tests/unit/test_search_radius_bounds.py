"""The Search radius bounds, and the question they exist to answer.

The served numbers are written out here rather than read from the module, for
the reason the tag ids are: a change to what every client's slider offers should
have to be argued with, not absorbed. Unlike a tag id these are *tunable* — a
radius is not persisted-forever vocabulary — so reddening this file is a prompt
to think, not a refusal.
"""

from __future__ import annotations

import pytest

from app.kernel import InvariantViolated
from app.modules.player_profile.domain.search_radius import (
    SEARCH_RADIUS_BOUNDS,
    SearchRadiusBounds,
)


def test_the_served_bounds_are_whole_kilometres_from_one_to_fifty():
    assert SEARCH_RADIUS_BOUNDS.minimum_km == 1
    assert SEARCH_RADIUS_BOUNDS.maximum_km == 50
    assert SEARCH_RADIUS_BOUNDS.step_km == 1
    assert SEARCH_RADIUS_BOUNDS.default_km == 10


def test_the_step_can_be_passed_without_a_decision():
    # The default is a value the control can open at, which means it has to be
    # one the commit would accept.
    assert SEARCH_RADIUS_BOUNDS.contains(SEARCH_RADIUS_BOUNDS.default_km)


@pytest.mark.parametrize("radius_km", [1, 2, 10, 49, 50])
def test_a_radius_inside_the_range_is_held(radius_km):
    assert SEARCH_RADIUS_BOUNDS.contains(radius_km)


@pytest.mark.parametrize("radius_km", [0, -1, 51, 500])
def test_a_radius_outside_the_range_is_refused(radius_km):
    assert not SEARCH_RADIUS_BOUNDS.contains(radius_km)


def test_both_ends_of_the_range_are_included():
    assert SEARCH_RADIUS_BOUNDS.contains(SEARCH_RADIUS_BOUNDS.minimum_km)
    assert SEARCH_RADIUS_BOUNDS.contains(SEARCH_RADIUS_BOUNDS.maximum_km)


def test_a_value_off_the_step_is_refused():
    coarse = SearchRadiusBounds(minimum_km=5, maximum_km=25, step_km=5, default_km=10)
    assert coarse.contains(15)
    assert not coarse.contains(16)


def test_bounds_whose_default_sits_outside_them_cannot_be_declared():
    with pytest.raises(InvariantViolated):
        SearchRadiusBounds(minimum_km=1, maximum_km=50, step_km=1, default_km=99)


def test_bounds_whose_default_misses_the_step_cannot_be_declared():
    with pytest.raises(InvariantViolated):
        SearchRadiusBounds(minimum_km=5, maximum_km=25, step_km=5, default_km=12)


def test_an_inverted_range_cannot_be_declared():
    with pytest.raises(InvariantViolated):
        SearchRadiusBounds(minimum_km=50, maximum_km=1, step_km=1, default_km=10)


def test_a_step_of_zero_cannot_be_declared():
    with pytest.raises(InvariantViolated):
        SearchRadiusBounds(minimum_km=1, maximum_km=50, step_km=0, default_km=10)
