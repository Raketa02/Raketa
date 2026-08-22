"""``CourtHolds`` over the Courts context's own claim and release.

The one file in Matches that knows a court kept aside is a ``Reservation`` whose
holder is ``MatchHeld``, that a claimed interval is a played one widened by the
club's turnaround, and that giving a court back is a write rather than a delete.
Everything above it asks in Matches' words and is told yes or no.

**It takes ``ClaimCourt`` rather than reassembling the scan.** ADR-0035's whole
central path — ask for a category and a window, let the database refuse the
loser, re-ask with that court removed, and report *nothing was free* only when
nothing is — lives in that use case, and it has a ``claim`` that deliberately
does not commit *"for one reason, and it is ADR-0035's: a seat payment that earns
a court, and the court it earns, are one event or they are a bug."* A second
implementation of the loop here would be a second answer to *which court*, and
the two would disagree on the day one of them was fixed.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Instant, Minutes

from app.modules.courts.application.claim_court import ClaimCourt
from app.modules.courts.domain.errors import InventoryLost
from app.modules.courts.domain.ports import ReservationRepository
from app.modules.courts.domain.reservation import MatchHeld
from app.modules.courts.domain.time_range import span
from app.modules.matches.domain.ports import CourtHolds


class CourtHoldsThroughReservations(CourtHolds):
    """A match's court, kept aside as a reservation and given back as a release."""

    def __init__(
        self, claim: ClaimCourt, reservations: ReservationRepository
    ) -> None:
        self._claim = claim
        self._reservations = reservations

    async def keep_aside(
        self,
        *,
        match_id: UUID,
        club_id: UUID,
        category_id: UUID,
        start: Instant,
        duration: Minutes,
    ) -> bool:
        # Asked before claiming rather than trusted not to happen. The ladder
        # grants once, but a court kept aside twice for one match would take two
        # courts off the club's inventory for one game, and the second would
        # never be given back — `give_back` releases the one live row it finds.
        if await self._reservations.for_match(match_id) is not None:
            return True

        try:
            await self._claim.claim(
                club_id=club_id,
                category_id=category_id,
                played=span(start, duration),
                holder=MatchHeld(match_id=match_id),
            )
        except InventoryLost:
            # *Nothing was free.* The one story ADR-0035 promises a player, and
            # here it is a fact the ladder has to decide about rather than an
            # error anybody upstream can do anything with.
            return False
        return True

    async def give_back(self, *, match_id: UUID, at: Instant) -> None:
        reservation = await self._reservations.for_match(match_id)
        if reservation is None:
            return
        reservation.release(at=at)
        await self._reservations.save(reservation)
