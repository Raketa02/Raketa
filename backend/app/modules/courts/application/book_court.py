"""A player buys a court outright: one Booking, one Reservation, one transaction.

The Booking and the claim it holds are written together and committed once. Not
for tidiness: a booking whose reservation failed is a player who has bought
nothing and been told otherwise, and a reservation whose booking failed is a
court held for nobody. Neither state has a card in the model.

This is also the smaller, in-context rehearsal of ADR-0035's harder rule — *"a
seat payment that earns a court, and the court it earns, are one event or they
are a bug"* — which `Raketa02/Raketa#70` will write across three contexts. The
mechanism is the same one used here: ``ClaimCourt.claim`` does not commit, so a
caller with its own write joins it.

**The price is quoted here and copied onto the booking.** ``court_price``
compounds the club's multipliers in exact rationals and rounds once to whole
złoty (`app/kernel/money.py`), and the result is stored — so reassigning the
court cannot move it, and a discount the club publishes tomorrow cannot either.
That is *"the price cannot change"* made structural.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, court_price, instant

from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.courts.application.claim_court import ClaimCourt
from app.modules.courts.application.commands import BookCourtCommand
from app.modules.courts.domain.booking import Booking
from app.modules.courts.domain.ports import BookingRepository
from app.modules.courts.domain.reservation import BookingHeld
from app.shared.ids import new_uuid


class BookCourt:
    def __init__(
        self,
        clubs: ClubRepository,
        bookings: BookingRepository,
        claim_court: ClaimCourt,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._clubs = clubs
        self._bookings = bookings
        self._claim_court = claim_court
        self._uow = uow
        self._clock = clock

    async def execute(self, command: BookCourtCommand) -> Booking:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()
        category = club.category(command.category_id)

        # The booking's id is minted before the claim, because the claim's
        # holder *is* the booking: a reservation held by "a booking that will
        # exist shortly" is the nullable-holder state this union exists to
        # refuse.
        booking_id = new_uuid()
        reservation = await self._claim_court.claim(
            club_id=command.club_id,
            category_id=command.category_id,
            played=command.played,
            holder=BookingHeld(booking_id),
        )

        booking = await self._bookings.add(
            Booking(
                id=booking_id,
                club_id=command.club_id,
                player_id=command.player_id,
                reservation_id=reservation.id,
                price=court_price(
                    category.rate,
                    club.pricing.price_multiplier,
                    club.pricing.slot_discount,
                ),
                booked_at=instant(self._clock.now()),
            )
        )
        await self._uow.commit()
        return booking
