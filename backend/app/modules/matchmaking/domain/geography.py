"""How far apart two coarse areas are, and the box a radius draws around one.

**The box is the only spatial truth** (``docs/adr/0101``). Generation is
``sport ∧ box ∧ gates``; there is no geo cell, no shard key and no derived
spatial structure, because a bounding-box rejection costs 18.5 ns against 1.00 µs
per surviving candidate and a bucket map buys nothing at any population this
platform will see for years (``scale-posture.md``).

**Two readings, and the order between them is load-bearing.** The box is a cheap
over-approximation — a rectangle in degrees around a centroid — and the radius
gate is the exact circle inside it. A search runs the box first because it is the
one that can reject without arithmetic, and then the gate, because a rectangle is
not a ring and a candidate in the corner of the box is further away than the
searcher asked for. Using the box alone would quietly widen every radius by up to
41%.

**Everything here reads the coarse centroid and nothing finer exists.**
``LocationArea.around`` discards the device fix at the boundary
(``player_profile/domain/location.py``), so a distance computed here is a
distance between two ≈1.1 km squares — and that is the distance the term reads
and the radius gate applies, cell to cell.

**What is printed is measured between two drawn spots** (``docs/adr/0174`` §2).
A player is drawn at one fixed point inside their own cell — the centre, offset
by an amount and a direction derived from a stable digest of who they are —
which is what lets a radar draw a bearing and every card print *1,9 km* rather
than *2 km* without the platform holding anything finer than the cell. The spot
is a **print and never a measurement**: it reaches no term, no gate and no
artifact, and the named cost of keeping the two apart is that a player at the
very edge may print *10,3 km* inside a 10 km reach.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt, tau
from typing import final
from uuid import UUID

from app.kernel import invariant
from app.modules.player_profile.domain.location import LOCATION_PRECISION_DP

#: The earth, as one number. A sphere and not an ellipsoid: the input is already
#: rounded to two decimal places of latitude, so the ~0.3% a spheroidal model
#: would recover is an order of magnitude below the coarsening that has already
#: happened.
EARTH_RADIUS_KM = 6371.0088

#: Kilometres per degree of latitude. Constant everywhere; longitude's shrinks
#: with the cosine of the latitude, which is why the box below is not a square.
KM_PER_DEGREE_OF_LATITUDE = EARTH_RADIUS_KM * radians(1.0)

#: How close to a pole the longitude span stops being computable. At the pole
#: every longitude is the same place and the span is the whole circle; rather
#: than divide by a cosine approaching zero, the box opens to the full range.
_POLE_EPSILON = 1e-9

#: Half a cell, in degrees, on either axis. A location is rounded to
#: ``LOCATION_PRECISION_DP`` places on the way in, so the cell a stored centroid
#: names is the square of half a unit in the last place around it — derived from
#: the platform's own precision rather than written as ``0.005``, for the reason
#: ``areas.py`` derives the code's scale: a change to how coarsely a location is
#: kept moves the cell with it.
HALF_CELL_DEGREES = 0.5 / 10**LOCATION_PRECISION_DP

#: The one decimal a printed distance keeps, and the smallest it prints. Never
#: *0,0*: two people in one cell are a kilometre apart for all the platform
#: knows, and a zero would claim it knows they share a building.
_PRINTED_PLACES = 1
_SMALLEST_PRINTED_KM = 0.1


@final
@dataclass(frozen=True, slots=True)
class Point:
    """A coarse centroid, as this module reads one.

    A structural echo of ``LocationArea`` and ``IndexedArea`` rather than an
    import of either, because both of those are *facts a player published* and
    this is the measurement over them. It carries no precision claim of its own:
    what it is given is what the platform kept.
    """

    latitude: float
    longitude: float


@final
@dataclass(frozen=True, slots=True)
class BoundingBox:
    """The rectangle in degrees a radius draws around a centroid.

    **An over-approximation on purpose.** It admits the corners, which are
    further than the radius, and the exact ring is applied afterwards by the
    radius gate. A box that tried to be the circle would be the circle, computed
    per row, which is the cost this shape exists to avoid.

    The longitude bounds are **not wrapped** across the antimeridian and the
    latitude bounds are **not clamped** past the poles: ``contains`` handles a
    span that has run round the world by widening to everything, which is the
    only answer that cannot exclude somebody who is genuinely near.
    """

    minimum_latitude: float
    maximum_latitude: float
    minimum_longitude: float
    maximum_longitude: float

    def contains(self, point: Point) -> bool:
        """Whether this point survives the cheap rejection."""

        if not (
            self.minimum_latitude <= point.latitude <= self.maximum_latitude
        ):
            return False
        if self.maximum_longitude - self.minimum_longitude >= 360.0:
            return True
        return _longitude_within(
            point.longitude, self.minimum_longitude, self.maximum_longitude
        )


def bounding_box(centre: Point, radius_km: float) -> BoundingBox:
    """The box a search of this radius reads, around this centroid."""

    invariant(radius_km > 0.0, f"a bounding box of {radius_km} km")
    latitude_span = radius_km / KM_PER_DEGREE_OF_LATITUDE
    shrink = cos(radians(centre.latitude))
    if abs(shrink) < _POLE_EPSILON:
        longitude_span = 180.0
    else:
        longitude_span = min(180.0, latitude_span / abs(shrink))
    return BoundingBox(
        minimum_latitude=centre.latitude - latitude_span,
        maximum_latitude=centre.latitude + latitude_span,
        minimum_longitude=centre.longitude - longitude_span,
        maximum_longitude=centre.longitude + longitude_span,
    )


def distance_km(first: Point, second: Point) -> float:
    """Great-circle kilometres between two coarse centroids.

    Haversine rather than the equirectangular approximation the box uses: the box
    may over-admit and be corrected afterwards, while this number is printed on a
    card and read by the distance term, and a term reading an approximation would
    be the product explaining itself with arithmetic it does not believe.
    """

    first_latitude = radians(first.latitude)
    second_latitude = radians(second.latitude)
    delta_latitude = second_latitude - first_latitude
    delta_longitude = radians(second.longitude - first.longitude)
    chord = (
        sin(delta_latitude / 2.0) ** 2
        + cos(first_latitude) * cos(second_latitude) * sin(delta_longitude / 2.0) ** 2
    )
    return 2.0 * EARTH_RADIUS_KM * asin(min(1.0, sqrt(chord)))


def drawn_spot(player_id: UUID, cell: Point) -> Point:
    """Where this player is drawn: one fixed point inside their own cell.

    The cell's centre, offset by an **amount** and a **direction** both read off
    a stable digest of the player's id — SHA-256 over the id's bytes, never the
    process hash, which ``docs/adr/0105`` forbids for anything that must agree
    across two workers. The direction is a bearing round the full circle and the
    amount is a fraction of the way from the centre to the cell's edge *along
    that bearing*, so the spot is inside the square by construction rather than
    by clamping.

    Three properties follow and each is asserted. **It never leaves the cell**,
    so it claims nothing finer than the area the player published. **It is the
    same for every viewer**, so it cannot be averaged away by two people
    comparing what they were served. **It moves only when the cell does**: the
    offset is the id's alone, so a player who moves carries it into the new
    cell. *Neighbourhood-true, building-false* — the direction to the cell is
    real; where inside it the spot sits says nothing about where the player is.

    Worked in degrees rather than kilometres deliberately: the cell is a square
    in degrees and a rectangle on the ground, and *inside the cell* is the
    promise.
    """

    digest = hashlib.sha256(player_id.bytes).digest()
    direction = tau * _unit_fraction(digest[:8])
    amount = _unit_fraction(digest[8:16])
    north, east = cos(direction), sin(direction)
    # The distance from the centre to the square's edge along this bearing —
    # the nearer of the two walls the ray meets.
    to_the_edge = HALF_CELL_DEGREES / max(abs(north), abs(east))
    return Point(
        latitude=cell.latitude + amount * to_the_edge * north,
        longitude=cell.longitude + amount * to_the_edge * east,
    )


def shown_kilometres(measured: float) -> float:
    """What the wire carries: **one decimal, and never below a tenth.**

    Measured between two drawn spots and rounded to the place the radar's
    rings are read at — Python's ``round``, which is **half to even on the
    binary value** (``round(0.25, 1)`` is ``0.2``), named here so a client
    never argues with a print that lands on a tie. The floor is the honest
    print for somebody in the same cell: *0,1 km* says *very near*, where
    *0,0* would say the platform knows two people share a building, which it
    does not.
    """

    invariant(measured >= 0.0, f"a negative distance: {measured} km")
    return max(_SMALLEST_PRINTED_KM, round(measured, _PRINTED_PLACES))


#: How many bits of a digest become one fraction: a double's mantissa, so the
#: quotient below is exact and the largest value is ``(2**53 - 1) / 2**53``,
#: which is strictly below one. Eight whole bytes divided by ``2**64`` would
#: round the top values *to* ``1.0`` and put a spot on the cell's edge.
_FRACTION_BITS = 53


def _unit_fraction(octets: bytes) -> float:
    """``[0, 1)`` from eight bytes of a digest, big-endian, so the reading is the
    same on every architecture — and strictly below one, see ``_FRACTION_BITS``."""

    invariant(len(octets) == 8, f"a fraction from {len(octets)} bytes")
    top = int.from_bytes(octets, "big") >> (64 - _FRACTION_BITS)
    return top / float(1 << _FRACTION_BITS)


def _longitude_within(longitude: float, lower: float, upper: float) -> bool:
    """Whether a longitude lies in ``[lower, upper]``, allowing for a wrap.

    The bounds may run past ±180 because :func:`bounding_box` does not wrap them,
    so the comparison is made on the offset from the lower bound taken modulo the
    circle. A point 359° *after* the lower bound is 1° *before* it, and reading
    the raw inequality would drop the whole span on the far side of the
    antimeridian.
    """

    return (longitude - lower) % 360.0 <= upper - lower
