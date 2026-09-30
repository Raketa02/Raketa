"""``CourtHours`` and ``ClubNames``, over what the Club context publishes.

**The share and the book-by are read, never derived here**: each sellable hour
already carries both (``clubs/domain/sellable.py``), so a proposal and the club
cannot disagree about the price or the deadline. A club that is not live is
absent from the offer, and a **paused** one is answered with
``taking_new_cards=False`` — no new card is built on its courts (the mechanics
§16.15), which is the answer here.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping
from datetime import timedelta
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.clubs.domain.ports import ClubDirectory, SellableCourtHours
from app.modules.proposals.domain.ports import OfferedCourtHour

#: Every game is one hour, for every sport (the mechanics §2).
_A_GAME = timedelta(hours=1)


@final
class ClubCourtHours:
    def __init__(self, sellable: SellableCourtHours) -> None:
        self._sellable = sellable

    async def offered(
        self, club_id: UUID, *, sport: Sport, start: Instant, now: Instant
    ) -> OfferedCourtHour | None:
        offer = (
            await self._sellable.between(
                [club_id], start=start, end=start + _A_GAME, now=now
            )
        ).get(club_id)
        if offer is None or not offer.taking_new_cards:
            return None
        hour = next(
            (
                hour
                for hour in offer.hours
                if hour.sport is sport and hour.start == start
            ),
            None,
        )
        if hour is None:
            return None
        return OfferedCourtHour(
            club_id=club_id,
            sport=sport,
            start=hour.start,
            share_grosze=hour.share_grosze,
            book_by=hour.book_by,
        )


@final
class DirectoryClubNames:
    def __init__(self, directory: ClubDirectory) -> None:
        self._directory = directory

    async def names_of(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        listed = await self._directory.listed(club_ids)
        return {club_id: listing.name for club_id, listing in listed.items()}
