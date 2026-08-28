"""The machine code a coarse area crosses the wire under.

``IndexedArea`` holds two degrees and **no code**, and its docstring says why:
the human-readable area a player card prints *"has no producer in this repository
yet"*, and deriving one there would be inventing a naming scheme nobody has
calibrated. That refusal stands. What the contract still needs is an
**identifier** — ``player_card.area_code`` and the distance evidence both carry
one — and an identifier is not a name.

So the code here is the coarse centroid itself, spelled as a stable string. It
names nothing the platform does not already hold: two decimal places is the
resolution ``LocationArea.around`` rounds to on the way in, so a code cannot be
read back into anything finer than the ≈1.1 km square the player published. It is
deliberately **not** a neighbourhood, a district or a city — the day a gazetteer
exists, this is the one function that changes, and every consumer is reading a
code rather than a sentence (``docs/adr/0022``).

**Two players in the same square share a code, and that is the whole point.** A
card saying *they are in your area* is a comparison the client makes between two
codes, which is exactly the shape ``docs/adr/0021`` licenses a client to compute.
"""

from __future__ import annotations

from app.modules.matchmaking.domain.geography import Point
from app.modules.player_profile.domain.location import LOCATION_PRECISION_DP

#: The multiplier that turns coarse degrees into the integers the code carries.
#: Derived from the platform's own precision rather than written as ``100``, so
#: that a change to how coarsely a location is kept moves the code with it rather
#: than silently truncating it.
_SCALE = 10**LOCATION_PRECISION_DP

#: What every code starts with. A letter rather than a digit so that a code is
#: never mistaken for a number by something parsing loosely, and one character so
#: the whole code stays short enough to read in a log line.
_PREFIX = "A"


def area_code_of(area: Point) -> str:
    """This coarse area's code — the same string for the same square, forever.

    Signed and zero-padded so that the code is fixed-width and sorts the way the
    coordinates do, which makes a lexical index over it a spatial one. The sign
    is always printed, because a code whose leading character depends on the
    hemisphere is a code somebody eventually parses by position and gets wrong
    off the coast of Africa.
    """

    latitude = round(area.latitude * _SCALE)
    longitude = round(area.longitude * _SCALE)
    return f"{_PREFIX}{latitude:+06d}{longitude:+07d}"
