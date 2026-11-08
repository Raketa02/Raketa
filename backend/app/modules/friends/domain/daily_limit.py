"""The daily limit on requests to people outside the requester's groups
(#773; ``docs/adr/0203`` §9; the rankings mechanics §13.3, Q21).

**At most ten a day**, and **a day is a Warsaw day** (PRD #766 call 10): the
count resets at midnight in Warsaw. Taking the day off the UTC instant would
move the reset an hour or two every night, in the direction nobody checks.

Only a request asked of somebody the requester shares no group with **counts**
— a group-mate's never does, wherever it was made — and only a request *sent*:
crossing a request made of you is an answer, and a link's is asked by opening
it (``domain/friendship.py``).
"""

from __future__ import annotations

from typing import Final

from app.kernel import (
    Instant,
    Ok,
    Zone,
    day_offset,
    invariant,
    minute_of_day,
    slot_start,
)

#: Requests a requester may send in a Warsaw day to people they share no
#: group with (Q21). The eleventh is ``daily_request_limit``.
DAILY_REQUEST_LIMIT: Final = 10

#: The zone a request's day is read in.
REQUEST_DAY_ZONE: Final[Zone] = Zone("Europe/Warsaw")


def day_began(at: Instant) -> Instant:
    """When the Warsaw day ``at`` falls in began — its midnight. **Through
    ``slot_start``, and nowhere else.**

    The ``Err`` arm is unreachable and says so rather than being handled:
    Warsaw's clocks change at 02:00 and 03:00, never at midnight. Reaching it
    means the zone changed its rules — to be found loudly."""

    midnight = slot_start(
        anchor=at, day=day_offset(0), minute=minute_of_day(0), zone=REQUEST_DAY_ZONE
    )
    invariant(
        isinstance(midnight, Ok),
        f"a midnight that does not exist in {REQUEST_DAY_ZONE}: {at}",
    )
    assert isinstance(midnight, Ok)  # narrowed by the invariant above
    return midnight.value


__all__ = ["DAILY_REQUEST_LIMIT", "REQUEST_DAY_ZONE", "day_began"]
