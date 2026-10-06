"""The Location area: where a player plays, held coarsely and only coarsely.

The glossary is explicit that *"the precise fix that produced it is never a
shareable value"* (``../../../../CONTEXT.md``). This module is where that stops
being a wish. A client hands over whatever its device gave it; **the coarsening
happens on the way in**, before an event is recorded, so the precise fix never
reaches the event store at all and there is no later step anybody can forget.

**Why coarsening rather than access control.** A precise fix that is stored and
guarded is one query, one export or one bug away from leaving; a fix that was
never stored cannot. It is the same argument ADR-0091 makes for re-encoding a
photo rather than scrubbing its EXIF: the honest way to not hold something is to
not hold it.

The precision is two decimal places — a bit over a kilometre of latitude, less of
longitude away from the equator. Every reader measures distance in whole
kilometres, so a finer location would be precision no consumer can use.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.kernel import invariant

#: Decimal places kept. Two is ≈1.1 km of latitude — the resolution distance is
#: read in, and deliberately not one place better than it.
LOCATION_PRECISION_DP: Final = 2

MINIMUM_LATITUDE: Final = -90.0
MAXIMUM_LATITUDE: Final = 90.0
MINIMUM_LONGITUDE: Final = -180.0
MAXIMUM_LONGITUDE: Final = 180.0


@dataclass(frozen=True, slots=True)
class LocationArea:
    """A coarse place, and the only place this platform keeps.

    Construct it with ``around``, which is the coarsening. The constructor is
    left reachable because replay has to rebuild one from what a stream already
    holds, and re-coarsening an already-coarse pair is a no-op — but every path
    that starts from a *device* goes through ``around``.
    """

    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        invariant(
            MINIMUM_LATITUDE <= self.latitude <= MAXIMUM_LATITUDE,
            f"latitude: {self.latitude}",
        )
        invariant(
            MINIMUM_LONGITUDE <= self.longitude <= MAXIMUM_LONGITUDE,
            f"longitude: {self.longitude}",
        )

    @classmethod
    def around(cls, latitude: float, longitude: float) -> "LocationArea":
        """The area a precise fix falls in. The fix itself is discarded here."""

        return cls(
            latitude=round(latitude, LOCATION_PRECISION_DP),
            longitude=round(longitude, LOCATION_PRECISION_DP),
        )
