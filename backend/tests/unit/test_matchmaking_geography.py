"""The bounding box, the distance, the drawn spot — and why none is another.

**The box is the only spatial truth**, and it is a cheap over-approximation the
radius gate then corrects. The two claims worth holding are that the box never
rejects somebody the ring would have admitted (a false negative there is a person
who silently does not exist), and that it *does* admit its own corners (which is
why the gate is still needed).

**The drawn spot is a print and never a measurement** (``docs/adr/0174`` §2). It
is one fixed point inside a player's cell, derived from a stable digest of who
they are, and the three claims below are the whole of what makes it safe to
serve: it never leaves the cell, it is the same on every process (carried by
``shortlist_determinism_probe``, which prints it under two hash seeds), and it
moves only when the cell does.
"""

from __future__ import annotations

from math import cos, radians
from pathlib import Path
from uuid import UUID, uuid5

import pytest

from app.kernel import InvariantViolated
from app.modules.matchmaking.domain.areas import area_code_of
from app.modules.matchmaking.domain.geography import (
    HALF_CELL_DEGREES,
    KM_PER_DEGREE_OF_LATITUDE,
    Point,
    bounding_box,
    distance_km,
    drawn_spot,
    shown_kilometres,
)

LONDON = Point(latitude=51.51, longitude=-0.13)

#: `backend/`, which the source walk below reads from.
ROOT = Path(__file__).resolve().parents[2]

ANIA = UUID("11111111-1111-1111-1111-111111111111")

#: Enough ids to make a claim about *every* player rather than about one, drawn
#: under a namespace so the list is the same on every run.
MANY = tuple(uuid5(ANIA, f"player-{n}") for n in range(400))


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


def test_the_printed_distance_is_one_decimal_and_never_below_a_tenth():
    """*1,9 km* where the card said *2 km*, and *0,1 km* for somebody in the same
    cell — never *0,0*, which would claim the platform knows two people share a
    building."""

    assert shown_kilometres(1.94) == 1.9
    assert shown_kilometres(10.26) == 10.3
    assert shown_kilometres(0.0) == 0.1
    assert shown_kilometres(0.04) == 0.1
    assert shown_kilometres(0.05) == pytest.approx(0.1)


def test_a_negative_distance_is_a_broken_precondition_and_not_a_print():
    with pytest.raises(InvariantViolated):
        shown_kilometres(-0.1)


def test_a_drawn_spot_never_leaves_the_cell():
    """The whole privacy argument: *neighbourhood-true, building-false*. A spot
    outside the cell would be a claim about a place the platform never held."""

    for player_id in MANY:
        spot = drawn_spot(player_id, LONDON)
        assert abs(spot.latitude - LONDON.latitude) < HALF_CELL_DEGREES, player_id
        assert abs(spot.longitude - LONDON.longitude) < HALF_CELL_DEGREES, player_id


def test_the_digest_can_never_put_a_spot_on_the_cells_edge():
    """*Inside by construction* has to survive the digest's worst case. A
    fraction read as ``int / 2**64`` rounds its top values to exactly ``1.0``
    — a double has 53 bits — and a spot at the edge is a spot in two cells."""

    from app.modules.matchmaking.domain.geography import _unit_fraction

    assert _unit_fraction(b"\xff" * 8) < 1.0
    assert _unit_fraction(b"\x00" * 8) == 0.0


def test_a_cell_is_the_square_the_location_rounds_into():
    """Half a cell is half of the last decimal place the platform keeps —
    ``0.005°`` at two places — so a spot cannot be read back into anything
    finer than the area a player published. Pinned as the number, so that a
    change to the derivation shows up here rather than in a radar that draws
    people across a cell boundary."""

    assert HALF_CELL_DEGREES == 0.005


def test_a_drawn_spot_is_the_same_for_every_viewer_and_moves_only_with_the_cell():
    """Fixed per player: two viewers cannot average it away, and a player who
    moves to another cell carries the same offset into it."""

    here = drawn_spot(ANIA, LONDON)
    again = drawn_spot(ANIA, Point(latitude=51.51, longitude=-0.13))
    elsewhere = drawn_spot(ANIA, Point(latitude=52.23, longitude=21.01))

    assert here == again
    assert elsewhere.latitude - 52.23 == pytest.approx(here.latitude - 51.51)
    assert elsewhere.longitude - 21.01 == pytest.approx(here.longitude - -0.13)


def test_two_players_in_one_cell_are_drawn_apart():
    """Which is what lets *Closest* tell them apart at all — and the reason the
    print is a fiction inside the cell and a truth between cells."""

    spots = {drawn_spot(player_id, LONDON) for player_id in MANY}

    assert len(spots) == len(MANY)


def test_the_spot_is_spread_over_the_cell_and_not_pinned_to_its_middle():
    """A digest that produced a corner for everybody would be a code for the
    cell, not a spot in it. Every quadrant is reached and the amount varies."""

    quadrants = set()
    reach = set()
    for player_id in MANY:
        spot = drawn_spot(player_id, LONDON)
        north = spot.latitude - LONDON.latitude
        east = spot.longitude - LONDON.longitude
        quadrants.add((north >= 0, east >= 0))
        reach.add(round(max(abs(north), abs(east)) / HALF_CELL_DEGREES, 1))

    assert len(quadrants) == 4
    assert len(reach) > 5


def test_the_geography_reads_no_process_hash():
    """``docs/adr/0105``: the offset comes from a stable digest and never from
    ``hash()``. Asserted structurally, because the behavioural check cannot
    catch the substitution it names — a ``UUID``'s ``hash()`` is its integer
    and agrees across seeds — so the two-seed run that carries the print is the
    shortlist determinism probe, and this walk is what guards the source."""

    source = (
        ROOT / "app" / "modules" / "matchmaking" / "domain" / "geography.py"
    ).read_text()

    assert "hash(" not in source
    assert "hashlib" in source


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
