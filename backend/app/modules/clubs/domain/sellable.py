"""The court hours a club can sell through Raketa — **derived, never stored
hour by hour** (``docs/adr/0189`` §5, the glossary's *Court hour*).

Its weekly pattern, **less** its exceptions, **less** what bookings hold, and
**less** every hour whose book-by has passed — which is what *after the release
time, unsold hours return to the club* and *the latest a Raketa game can book*
both mean for an hour (the mechanics §5.4, §16.3). Each hour is priced by the
band that holds it or the standard price, and carries its share and its
book-by, so whoever deals it reads both from here rather than re-deriving them.

**Only a live club sells**, because *a club's courts reach players' decks only
when all four steps are done* (§16.2). A **paused** club is still live and
still sells: its cards keep their court until their book-by and can still book
(§16.15). Pausing is what ``taking_new_cards`` says, and dealing new cards is
somebody else's decision to make from it.

**Pure**: the aggregate, the window, the moment and the taken hours in; the
hours out, by start and then by the club's order of courts.
"""

from __future__ import annotations

from collections.abc import Collection, Iterator
from dataclasses import dataclass
from datetime import timedelta
from typing import final
from uuid import UUID

from app.kernel import Instant, Sport, Zone, iso_weekday
from app.modules.clubs.domain.club_courts import ClubCourts
from app.modules.clubs.domain.court_hours import CLUB_ZONE, hour_start, local_day
from app.modules.clubs.domain.prices import share_of
from app.modules.clubs.domain.raketa_terms import RaketaSettings, book_by
from app.modules.clubs.domain.setup import checklist_of
from app.modules.player_profile.domain.weekly_hours import HOURS_OF_THE_DAY


@final
@dataclass(frozen=True, slots=True)
class SellableCourtHour:
    """One court for one hour that Raketa may sell: its court, when it
    starts, what it costs, the share one player pays, and the latest moment a
    game on it can still fill."""

    court_id: UUID
    court_name: str
    sport: Sport
    indoor: bool
    start: Instant
    price_grosze: int
    share_grosze: int
    book_by: Instant


@final
@dataclass(frozen=True, slots=True)
class ClubOffer:
    """What one live club sells through Raketa in a window, and on what terms."""

    club_id: UUID
    settings: RaketaSettings
    #: ``False`` while the club is paused: no new card may be built on its
    #: courts, while the cards already dealt keep theirs.
    taking_new_cards: bool
    #: Where the hours are wall clock — what a player's week is read in.
    zone: Zone
    hours: tuple[SellableCourtHour, ...]


def offer_of(
    club: ClubCourts,
    *,
    start: Instant,
    end: Instant,
    now: Instant,
    taken: Collection[tuple[UUID, Instant]],
) -> ClubOffer | None:
    """What ``club`` sells among the hours starting from ``start`` until
    ``end`` — ``None`` for a club that is not live. ``taken`` is every
    ``(court, start)`` a booking holds."""

    if not checklist_of(club).live:
        return None
    return ClubOffer(
        club_id=club.club_id,
        settings=club.settings,
        taking_new_cards=not club.paused,
        zone=CLUB_ZONE,
        hours=tuple(
            _sellable(
                club,
                start=start,
                end=end,
                now=now,
                taken=frozenset(taken),
            )
        ),
    )


def _sellable(
    club: ClubCourts,
    *,
    start: Instant,
    end: Instant,
    now: Instant,
    taken: frozenset[tuple[UUID, Instant]],
) -> Iterator[SellableCourtHour]:
    """Day by day, hour by hour, court by court — which is the order the
    answer is in."""

    selling = [court for court in club.selling_courts() if court.sport in club.prices]
    day, last_day = local_day(start), local_day(end)
    while day <= last_day:
        weekday = iso_weekday(day.isoweekday())
        for hour in HOURS_OF_THE_DAY:
            for court in selling:
                if not court.hours.holds(weekday, hour):
                    continue
                at = hour_start(day, hour)
                if not start <= at < end or (court.id, at) in taken:
                    continue
                deadline = book_by(at, settings=club.settings)
                if deadline <= now:
                    continue
                if any(
                    exception.covers(court.id, at)
                    for exception in club.exceptions.values()
                ):
                    continue
                price = club.prices[court.sport].price_at(weekday, hour)
                yield SellableCourtHour(
                    court_id=court.id,
                    court_name=court.name.value,
                    sport=court.sport,
                    indoor=court.indoor,
                    start=at,
                    price_grosze=price,
                    share_grosze=share_of(price, court.sport),
                    book_by=deadline,
                )
        day += timedelta(days=1)
