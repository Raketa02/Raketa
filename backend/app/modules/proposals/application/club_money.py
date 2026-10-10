"""**The club's Money page** (#548; the mechanics §16.11; the screens B7).

**A month at a time**, by the day each game is played on at the club: every
Raketa booking that took money from its players, soonest first — the day and
the court, what was collected, what was refunded, the card fees the club pays
on it, and what is the club's — with the month's totals, and whether a payout
has carried each one's money to the club's bank. A booking that took nothing —
a request refused or never answered — is not money, and is not listed.

**The club is the seller**, so every figure is its own account's: the players'
shares were taken there, refunds come out of it, and the provider's card fee on
every share taken is the club's to pay, as at its own terminal — a game called
off and given back whole costs the club those fees. **Every fee is the real
one, or not yet known** (#641): a club on its own negotiated pricing is told
its fees after the take, and until then the figure — and what it moves, a
refund less it and the net, and the month's totals — is ``None``, never an
estimate.

Assembled here, as the Bookings page is, because a booking is the Bookings
context's and its money the Payments context's (``BookingTakings``).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.clubs.domain.court_hours import (
    DAY_CLOSES,
    DAY_OPENS,
    hour_start,
    local_day,
)
from app.modules.proposals.domain.club_bookings import (
    ClubStatus,
    Takings,
    club_status,
    known_sum,
)
from app.modules.proposals.domain.home import BookedGame
from app.modules.proposals.domain.ports import BookingTakings, ClubBookings


@final
@dataclass(frozen=True, slots=True)
class MoneyRow:
    game: BookedGame
    status: ClubStatus
    takings: Takings


@final
@dataclass(frozen=True, slots=True)
class MoneyTotals:
    collected_grosze: int
    #: Each of the three ``None`` while a booking's is not yet known (#641).
    refunded_grosze: int | None
    card_fees_grosze: int | None
    net_grosze: int | None


@final
@dataclass(frozen=True, slots=True)
class ClubMoney:
    #: The first day of the month read.
    month: date
    read_at: Instant
    rows: tuple[MoneyRow, ...]
    totals: MoneyTotals


def first_of_the_month(day: date) -> date:
    return day.replace(day=1)


def _last_of_the_month(first: date) -> date:
    following = (first + timedelta(days=32)).replace(day=1)
    return following - timedelta(days=1)


@final
class ReadClubMoney:
    def __init__(
        self, *, bookings: ClubBookings, takings: BookingTakings, clock: Clock
    ) -> None:
        self._bookings = bookings
        self._takings = takings
        self._clock = clock

    async def execute(self, club_id: UUID, *, month: date | None) -> ClubMoney:
        """``month`` is any day of the month to read — this one at the club by
        default."""

        now = instant(self._clock.now())
        first = first_of_the_month(month if month is not None else local_day(now))
        games = await self._bookings.on_day(
            club_id,
            start=hour_start(first, DAY_OPENS),
            end=hour_start(_last_of_the_month(first), DAY_CLOSES),
        )
        takings = await self._takings.of([game.booking_id for game in games])
        rows = tuple(
            MoneyRow(
                game=game,
                status=club_status(game, now=now),
                takings=takings[game.booking_id],
            )
            for game in games
            # A game whose shares are only held has collected nothing yet.
            if game.booking_id in takings and takings[game.booking_id].paid
        )
        return ClubMoney(
            month=first,
            read_at=now,
            rows=rows,
            totals=MoneyTotals(
                collected_grosze=sum(row.takings.collected_grosze for row in rows),
                refunded_grosze=known_sum(row.takings.refunded_grosze for row in rows),
                card_fees_grosze=known_sum(
                    row.takings.card_fees_grosze for row in rows
                ),
                net_grosze=known_sum(row.takings.net_grosze for row in rows),
            ),
        )
