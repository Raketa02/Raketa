"""*Is a court of this category free for this window* — asked, never stored.

ADR-0035: *"Availability is a projection over reservations, never a stored
number."* This is the projection. There is no counter to decrement, no cache to
invalidate and no row anywhere holding *how many are left* — the club's own
private bookings are reservations too, so they are already in the answer.

What comes back is the **courts**, not a count. A caller that wants a number
takes the length; a caller that wants to know *which* — the club console showing
a grid, a reassignment picking a target — has it without a second query. A count
alone would have to be re-derived to answer the second question, which is how
two answers to one question start.

The court identities do not leave this context in a card. What crosses to a
player is `Reservation.published`, which names the category until fifteen
minutes before play.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.courts.application.commands import CourtAvailabilityQuery
from app.modules.courts.domain.availability import free_courts
from app.modules.courts.domain.ports import ReservationRepository
from app.modules.courts.domain.reservation import Reservation


class CourtAvailability:
    def __init__(
        self, clubs: ClubRepository, reservations: ReservationRepository
    ) -> None:
        self._clubs = clubs
        self._reservations = reservations

    async def execute(self, query: CourtAvailabilityQuery) -> tuple[UUID, ...]:
        club = await self._clubs.get(query.club_id)
        if club is None:
            raise ClubNotFound()

        category = club.category(query.category_id)
        if category.is_retired:
            # A group nobody may sell has nothing free, which is the same answer
            # as a group whose every court is booked (ADR-0079).
            return ()

        courts = tuple(court.id for court in club.courts_in(query.category_id))
        overlapping = await self._reservations.overlapping(
            court_ids=courts, window=query.window
        )
        return free_courts(
            courts=courts, reservations=overlapping, window=query.window
        )


class CourtHistory:
    """Every reservation a court has ever carried, released rows included.

    The other half of *availability is a query*: if a released row could be
    deleted, this would answer *what is booked* and never *what was*. ADR-0035
    says a court's booking history is a query over reservations, and this is it.
    """

    def __init__(self, reservations: ReservationRepository) -> None:
        self._reservations = reservations

    async def execute(self, court_id: UUID) -> list[Reservation]:
        return await self._reservations.for_court(court_id)
