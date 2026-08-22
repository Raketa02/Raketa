"""Bookings, in and out of one table. A record, and a version on the way out.

Nothing about a court or a clock is read or written here, because the row has
neither: a booking holds a reservation, and the reservation is where *when* and
*where* live. The unique index on ``reservation_id`` is the database's half of
*one booking, one claim* — a second booking against one reservation would be two
players sold one court by a route that never touches the exclusion constraint.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Sequence, cast
from uuid import UUID

from sqlalchemy import Select, select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import CourtPrice, Instant, instant, zloty

from app.modules.courts.domain.booking import Booking
from app.modules.courts.domain.errors import ConcurrentBookingModification
from app.modules.courts.infrastructure.sqlalchemy_court_models import BookingORM


def _as_instant(value: datetime) -> Instant:
    return instant(value if value.tzinfo else value.replace(tzinfo=timezone.utc))


def _optional_instant(value: datetime | None) -> Instant | None:
    return None if value is None else _as_instant(value)


def _price_of(amount: int) -> CourtPrice:
    """Back through the brand, refusing anything that is not whole złoty.

    A `CourtPrice` means *after every multiplier, rounded once to whole złoty*
    (`app/kernel/money.py`). Reading a stored figure straight into the brand
    would let a hand-edited row become a price the money layer believes is
    already rounded — so the constructor is `zloty`, and a grosze figure that
    is not a whole number of złoty is refused here rather than three contexts
    later.
    """

    whole, remainder = divmod(amount, 100)
    if remainder:
        raise ValueError(f"a stored court price that is not whole złoty: {amount}")
    return CourtPrice(zloty(whole))


def _booking_of(row: BookingORM) -> Booking:
    return Booking(
        id=row.id,
        club_id=row.club_id,
        player_id=row.player_id,
        reservation_id=row.reservation_id,
        price=_price_of(row.price_grosze),
        booked_at=_as_instant(row.booked_at),
        cancelled_at=_optional_instant(row.cancelled_at),
        version=row.version,
    )


class SqlAlchemyBookingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get(self, booking_id: UUID) -> Booking | None:
        row = (
            await self._session.execute(
                select(BookingORM).where(BookingORM.id == booking_id)
            )
        ).scalar_one_or_none()
        return None if row is None else _booking_of(row)

    async def for_reservation(self, reservation_id: UUID) -> Booking | None:
        row = (
            await self._session.execute(
                select(BookingORM).where(
                    BookingORM.reservation_id == reservation_id
                )
            )
        ).scalar_one_or_none()
        return None if row is None else _booking_of(row)

    async def for_player(self, player_id: UUID) -> list[Booking]:
        rows = await self._all(
            select(BookingORM)
            .where(BookingORM.player_id == player_id)
            .order_by(BookingORM.booked_at.desc(), BookingORM.id)
        )
        return [_booking_of(row) for row in rows]

    async def _all(self, statement: Select[Any]) -> Sequence[Any]:
        return (await self._session.execute(statement)).scalars().all()

    async def add(self, booking: Booking) -> Booking:
        self._session.add(
            BookingORM(
                id=booking.id,
                club_id=booking.club_id,
                player_id=booking.player_id,
                reservation_id=booking.reservation_id,
                version=0,
                **self._columns(booking),
            )
        )
        await self._session.flush()
        booking.version = 0
        return booking

    async def save(self, booking: Booking) -> Booking:
        result = await self._session.execute(
            update(BookingORM)
            .where(
                BookingORM.id == booking.id,
                BookingORM.version == booking.version,
            )
            .values(**self._columns(booking), version=booking.version + 1)
        )
        if cast(CursorResult[Any], result).rowcount != 1:
            raise ConcurrentBookingModification()
        booking.version += 1
        return booking

    def _columns(self, booking: Booking) -> dict[str, Any]:
        return {
            "price_grosze": int(booking.price),
            "booked_at": booking.booked_at,
            "cancelled_at": booking.cancelled_at,
        }
