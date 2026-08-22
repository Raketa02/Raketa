"""A Booking: a player buying a court outright. It **holds** a reservation.

ADR-0035 answers root `CONTEXT.md`'s open question — *is a Booking owned by the
Court, the Club, or standing alone* — with **none of the three**: a Booking holds
a Reservation, and the tenancy spine is `Club → Court`.

**So this record carries no court and no interval.** Not because they would be
inconvenient here, but because a copy of them is a second answer to *when is this
booked and where*, and the day it disagrees with the reservation nobody can say
which one the club believed. Everything about the court and the clock is read
through ``reservation_id``; `tests/unit/test_booking.py` asserts the absence,
because it is the whole content of *"a Booking is not a Reservation"*.

**What it does carry that a reservation cannot** is who bought it and what they
were quoted. The price is a ``CourtPrice`` — after every club multiplier, rounded
once to whole złoty (`app/kernel/money.py`) — **copied at booking time**, so
reassigning the court cannot move it and a club discount published afterwards
cannot either. That is ADR-0035's *"the price cannot change"* made structural
rather than remembered.

On the private split-share path a Booking exists **before any share is paid**,
which is why nothing here is conditional on money having arrived. Whose money
arrived is Money's record, not this one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import CourtPrice, Instant


@final
@dataclass
class Booking:
    """One player, one reservation, one price — and the version that guards it."""

    id: UUID
    club_id: UUID
    player_id: UUID
    #: The claim this booking holds. The only route to the court and the clock.
    reservation_id: UUID
    #: What the player was quoted, at the moment they were quoted it.
    price: CourtPrice
    booked_at: Instant
    cancelled_at: Instant | None = None
    version: int = 0

    @property
    def is_live(self) -> bool:
        return self.cancelled_at is None

    def cancel(self, *, at: Instant) -> None:
        """Cancel the booking. Releasing the court is the reservation's own act.

        Two writes, deliberately not one: a booking that is cancelled and a
        court that is given back are different facts about different records,
        and `ClaimCourt`'s caller is entitled to cancel a booking while the
        club keeps the slot. The use case does both in one transaction; the
        aggregate does not reach across.
        """

        if self.cancelled_at is None:
            self.cancelled_at = at
