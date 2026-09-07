"""The bounding box and the distance — and why one is not the other.

**The box is the only spatial truth**, and it is a cheap over-approximation the
radius gate then corrects. The two claims worth holding are that the box never
rejects somebody the ring would have admitted (a false negative there is a person
who silently does not exist), and that it *does* admit its own corners (which is
why the gate is still needed).
"""

from __future__ import annotations

from math import cos, radians

import pytest

from app.modules.matchmaking.domain.areas import area_code_of
from app.modules.matchmaking.domain.geography import (
    KM_PER_DEGREE_OF_LATITUDE,
    Point,
    bounding_box,
    distance_km,
    whole_kilometres,
)

LONDON = Point(latitude=51.51, longitude=-0.13)


def test_a_point_is_no_distance_from_itself():
    assert distance_km(LONDON, LONDON) == pytest.approx(0.0, abs=1e-9)


def test_a_degree_of_latitude_is_the_constant_the_box_reads():
    north = Point(latitude=LONDON.latitude + 1.0, longitude=LONDON.longitude)
    assert distance_km(LONDON, north) == pytest.approx(
        KM_PER_DEGREE_OF_LATITUDE, rel=1e-3
    )


def test_a_degree_of_longitude_shrinks_with_the_latitude():
    """Which is why the box is not a square, and why the same offset in degrees
    is a different distance in Warsaw and on the equator."""

    east = Point(latitude=LONDON.latitude, longitude=LONDON.longitude + 1.0)
    expected = KM_PER_DEGREE_OF_LATITUDE * cos(radians(LONDON.latitude))
    assert distance_km(LONDON, east) == pytest.approx(expected, rel=1e-2)


@pytest.mark.parametrize("bearing_degrees", range(0, 360, 15))
def test_the_box_never_rejects_somebody_inside_the_ring(bearing_degrees):
    """The one failure a cheap pre-filter may not have.

    A candidate the box drops is a candidate nothing downstream can rescue: they
    are not gated, not counted and not near — they simply do not exist for that
    search.
    """

    from math import cos as _cos, radians as _radians, sin

    radius_km = 10.0
    box = bounding_box(LONDON, radius_km)
    bearing = _radians(bearing_degrees)
    # Just inside the ring, in every direction round it.
    north_km = 9.99 * _cos(bearing)
    east_km = 9.99 * sin(bearing)
    inside = Point(
        latitude=LONDON.latitude + north_km / KM_PER_DEGREE_OF_LATITUDE,
        longitude=LONDON.longitude
        + east_km
        / (KM_PER_DEGREE_OF_LATITUDE * _cos(_radians(LONDON.latitude))),
    )

    assert distance_km(LONDON, inside) <= radius_km + 0.05
    assert box.contains(inside)


def test_the_box_admits_its_own_corners_which_is_why_the_gate_exists():
    """A search that stopped at the box would quietly widen every radius by up to
    41% — the corner of a square around a circle."""

    box = bounding_box(LONDON, 10.0)
    corner = Point(
        latitude=box.maximum_latitude - 1e-6, longitude=box.maximum_longitude - 1e-6
    )

    assert box.contains(corner)
    assert distance_km(LONDON, corner) > 10.0


def test_a_box_that_has_run_round_the_world_admits_everybody():
    """Near a pole the longitude span is the whole circle, and the only answer
    that cannot exclude somebody genuinely near is *everybody*."""

    box = bounding_box(Point(latitude=89.99, longitude=0.0), 10.0)
    assert box.contains(Point(latitude=89.99, longitude=179.0))


def test_the_box_wraps_the_antimeridian():
    box = bounding_box(Point(latitude=0.0, longitude=179.99), 10.0)
    assert box.contains(Point(latitude=0.0, longitude=-179.99))


def test_whole_kilometres_never_round_up():
    """A card saying *3 km* under a 3 km radius must not be a row the radius gate
    excluded, so the printed figure is never larger than the measurement."""

    assert whole_kilometres(3.9) == 3
    assert whole_kilometres(0.0) == 0


def test_an_area_code_is_stable_and_names_nothing_finer_than_the_platform_holds():
    """The same square answers the same code for ever, and two players in one
    square share it — which is exactly what makes *they are in your area* a
    comparison the client can make."""

    assert area_code_of(LONDON) == area_code_of(Point(51.51, -0.13))
    assert area_code_of(LONDON) != area_code_of(Point(51.52, -0.13))
    assert "51.51" not in area_code_of(LONDON), "a code, not a coordinate pair"


def test_an_area_code_is_fixed_width_and_signed_in_both_hemispheres():
    """A code whose leading character depended on the hemisphere is a code
    somebody eventually parses by position and gets wrong off the coast of
    Africa."""

    codes = {
        area_code_of(Point(51.51, -0.13)),
        area_code_of(Point(-33.87, 151.21)),
        area_code_of(Point(0.0, 0.0)),
    }
    assert len({len(code) for code in codes}) == 1
