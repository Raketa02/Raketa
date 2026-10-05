"""``SellableCourtHours`` over each club's stream and what bookings hold.

One stream read and one bookings read per club asked about, then the pure
derivation (``domain/sellable.py``). **No projection of hours exists to read
instead**, and that is the rule rather than a shortcut: a stored hour would be
a copy that a booking, an exception or a clock could leave stale.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.clubs.domain.ports import ClubCourtsRepository, CourtBookings
from app.modules.clubs.domain.sellable import ClubOffer, offer_of


@final
class ClubCourtsSellableHours:
    def __init__(
        self, *, courts: ClubCourtsRepository, bookings: CourtBookings
    ) -> None:
        self._courts = courts
        self._bookings = bookings

    async def between(
        self,
        club_ids: Collection[UUID],
        *,
        start: Instant,
        end: Instant,
        now: Instant,
    ) -> Mapping[UUID, ClubOffer]:
        offers: dict[UUID, ClubOffer] = {}
        for club_id in dict.fromkeys(club_ids):
            taken = await self._bookings.taken(club_id, start=start, end=end)
            offer = offer_of(
                await self._courts.load(club_id),
                start=start,
                end=end,
                now=now,
                taken={(hour.court_id, hour.start) for hour in taken},
            )
            if offer is not None:
                offers[club_id] = offer
        return offers
