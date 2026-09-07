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
distance between two ≈1.1 km squares. That is why the wire carries **whole
kilometres**: a decimal would claim a precision the input does not hold.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import asin, cos, radians, sin, sqrt
from typing import final

from app.kernel import invariant

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


def whole_kilometres(measured: float) -> int:
    """What the wire carries. **Rounded down, never up.**

    A card saying *3 km* under a 3 km radius must not be a row the radius gate
    excluded, so the printed figure is never larger than the measurement. Rounding
    to nearest would let 3.5 km print as 4 and sit inside a 4 km ring it does not
    belong in.
    """

    invariant(measured >= 0.0, f"a negative distance: {measured} km")
    return int(measured)


def _longitude_within(longitude: float, lower: float, upper: float) -> bool:
    """Whether a longitude lies in ``[lower, upper]``, allowing for a wrap.

    The bounds may run past ±180 because :func:`bounding_box` does not wrap them,
    so the comparison is made on the offset from the lower bound taken modulo the
    circle. A point 359° *after* the lower bound is 1° *before* it, and reading
    the raw inequality would drop the whole span on the far side of the
    antimeridian.
    """

    return (longitude - lower) % 360.0 <= upper - lower
