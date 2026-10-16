"""Where a booked game may be moved, for its kind (#671; the mechanics §16.4,
Q122): the same kind, or an indoor court for an outdoor game — never outdoors
from indoors, which would be a different game to the players.
"""

from __future__ import annotations

import pytest

from app.modules.bookings.domain.booking import BookedCourt
from app.shared.ids import new_uuid

INDOOR = BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True)
OUTDOOR = BookedCourt(court_id=new_uuid(), name="Court 4", indoor=False)


@pytest.mark.parametrize(
    ("played_on", "court", "allowed"),
    [
        (INDOOR, INDOOR, True),
        (OUTDOOR, OUTDOOR, True),
        (OUTDOOR, INDOOR, True),
        (INDOOR, OUTDOOR, False),
    ],
    ids=[
        "indoor to indoor",
        "outdoor to outdoor",
        "outdoor to indoor",
        "indoor to outdoor",
    ],
)
def test_a_move_keeps_the_kind_or_goes_indoors(played_on, court, allowed):
    assert played_on.may_move_to(court) is allowed
