"""``CourtHours``, ``CourtKinds``, ``ClubNames`` and ``ClubTerms``, over what
the Club context publishes.

**The share and the book-by are read, never derived here**: each sellable hour
already carries both (``clubs/domain/sellable.py``), so a proposal and the club
cannot disagree about the price or the deadline. A club that is not live is
absent from the offer, and a **paused** one is answered with
``taking_new_cards=False`` — no new card is built on its courts (the mechanics
§16.15), which is the answer here.

**Every hour a club sells, counted in courts**, is read off the same offer for
the proposer: one per sport and hour, with how many courts are free then — a
paused club's too, since its cards keep their court while it deals no new one.
And **every hour it still holds a court for**, read off the offer as it stood
before any deadline in the window: a card keeps the book-by it was made with,
so a club that lengthens its release lead has not taken a card's court away.

**The kind of court a card promises is read off the same offer, as it stood
before any deadline** (#671; the mechanics §5.2, Q122): the free courts of the
card's sport at its club and hour are the courts it could be booked on, and
the card says *Indoor* or *Outdoor* only when every one of them is of that
kind — a club with both kinds free at the hour promises neither, since the
first free court in the club's order is the one booked and a court may be
taken meanwhile.

**A club's terms are read off the same offer**, so *which clubs sell* has one
answer for a card and for the hour it was made at: a live club is answered,
paused or not, with the cut-off its settings hold now — a card is not booked
yet, so the terms in force are the ones it will be booked with. The offer is
asked for **an empty window**: its terms, and none of its hours, since a card's
hour was read when the card was made.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from datetime import timedelta
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.clubs.domain.ports import (
    ClubDirectory,
    SellableCourtHours,
)
from app.modules.clubs.domain.rakieta_terms import before_any_deadline
from app.modules.clubs.domain.sellable import ClubOffer, SellableCourtHour
from app.modules.proposals.domain.deck import SellingTerms
from app.modules.proposals.domain.ports import CourtHourKey, OfferedCourtHour
from app.modules.proposals.domain.proposer import CourtHourOnSale, CourtOnSale

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

    async def on_sale(
        self,
        club_ids: Collection[UUID],
        *,
        start: Instant,
        end: Instant,
        now: Instant,
    ) -> Sequence[CourtHourOnSale]:
        offers = await self._sellable.between(
            list(dict.fromkeys(club_ids)), start=start, end=end, now=now
        )
        on_sale: list[CourtHourOnSale] = []
        for club_id, offer in offers.items():
            # One court per sellable hour: counted per sport and start, since a
            # card promises a court at a club at an hour and never a number.
            courts: dict[tuple[Sport, Instant], list[SellableCourtHour]] = {}
            for hour in offer.hours:
                courts.setdefault((hour.sport, hour.start), []).append(hour)
            for (sport, at), free in courts.items():
                on_sale.append(
                    CourtHourOnSale(
                        club_id=club_id,
                        sport=sport,
                        start=at,
                        courts=len(free),
                        # Every court of a sport at an hour is priced alike,
                        # and its book-by is the club's.
                        share_grosze=free[0].share_grosze,
                        book_by=free[0].book_by,
                        taking_new_cards=offer.taking_new_cards,
                        # In the club's order, which the offer is in.
                        free=tuple(
                            CourtOnSale(
                                court_id=hour.court_id,
                                name=hour.court_name,
                                indoor=hour.indoor,
                            )
                            for hour in free
                        ),
                    )
                )
        return on_sale

    async def held(
        self, club_ids: Collection[UUID], *, start: Instant, end: Instant
    ) -> Collection[tuple[UUID, Sport, Instant]]:
        offers = await _held_offers(self._sellable, club_ids, start=start, end=end)
        return {
            (club_id, hour.sport, hour.start)
            for club_id, offer in offers.items()
            for hour in offer.hours
        }


async def _held_offers(
    sellable: SellableCourtHours,
    club_ids: Collection[UUID],
    *,
    start: Instant,
    end: Instant,
) -> Mapping[UUID, ClubOffer]:
    """The offer as it stood before any hour in the window could have closed:
    what the club still has, bookings, exceptions and hours taken off it, and
    no deadline — a card's own book-by is the card's."""

    return await sellable.between(
        list(dict.fromkeys(club_ids)),
        start=start,
        end=end,
        now=before_any_deadline(start),
    )


@final
class SellableCourtKinds:
    """``CourtKinds`` over ``SellableCourtHours``."""

    def __init__(self, sellable: SellableCourtHours) -> None:
        self._sellable = sellable

    async def of(self, hours: Collection[CourtHourKey]) -> Mapping[CourtHourKey, bool]:
        if not hours:
            return {}
        starts = [start for _, _, start in hours]
        offers = await _held_offers(
            self._sellable,
            [club_id for club_id, _, _ in hours],
            start=min(starts),
            end=max(starts) + _A_GAME,
        )
        kinds: dict[CourtHourKey, set[bool]] = {}
        for club_id, offer in offers.items():
            for hour in offer.hours:
                key = (club_id, hour.sport, hour.start)
                if key in hours:
                    kinds.setdefault(key, set()).add(hour.indoor)
        return {
            key: next(iter(found)) for key, found in kinds.items() if len(found) == 1
        }


@final
class DirectoryClubNames:
    def __init__(self, directory: ClubDirectory) -> None:
        self._directory = directory

    async def names_of(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        listed = await self._directory.listed(club_ids)
        return {club_id: listing.name for club_id, listing in listed.items()}


@final
class SellableClubTerms:
    def __init__(self, sellable: SellableCourtHours) -> None:
        self._sellable = sellable

    async def of(
        self, club_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, SellingTerms]:
        if not club_ids:
            return {}
        offers = await self._sellable.between(
            sorted(set(club_ids)), start=now, end=now, now=now
        )
        return {
            club_id: SellingTerms(cut_off_hours=offer.settings.cut_off_hours)
            for club_id, offer in offers.items()
        }
