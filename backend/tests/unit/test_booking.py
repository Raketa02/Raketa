"""A Booking holds a Reservation and is not one — asserted as an *absence*.

ADR-0035 answers root `CONTEXT.md`'s open question — *is a Booking owned by the
Court, the Club, or standing alone* — with **none of the three**. The content of
that answer is negative: a booking has no court and no time range. So the test
for it has to be negative too, and it is the whole of this file's first half.

A positive test cannot state it. A booking that happens to agree with its
reservation about the hour passes just as happily whether the hour is stored
twice or once — and the failure it would miss arrives on the day a court is
reassigned and one of the two copies moves.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.kernel import CourtPrice, instant, zloty
from app.modules.courts.domain.booking import Booking
from app.modules.courts.infrastructure.sqlalchemy_court_models import (
    BookingORM,
    ReservationORM,
)

#: What a reservation carries about the court and the clock. Read off the
#: reservation itself rather than written out, so a fifth column added there is
#: covered here on the day it exists.
COURT_AND_CLOCK = {
    "court_id",
    "played_from",
    "played_to",
    "claimed_from",
    "claimed_to",
}


def at(hour: int):
    return instant(datetime(2026, 9, 1, hour, tzinfo=timezone.utc))


def a_booking(**kw) -> Booking:
    return Booking(
        **{
            "id": uuid4(),
            "club_id": uuid4(),
            "player_id": uuid4(),
            "reservation_id": uuid4(),
            "price": CourtPrice(zloty(120)),
            "booked_at": at(12),
            **kw,
        }
    )


# --- the absence ------------------------------------------------------------


def test_a_booking_holds_a_reservation_and_carries_no_court():
    assert "reservation_id" in Booking.__dataclass_fields__
    for field in ("court_id", "category_id"):
        assert field not in Booking.__dataclass_fields__


def test_a_booking_carries_no_interval_of_its_own():
    for field in Booking.__dataclass_fields__:
        assert "played" not in field
        assert "claimed" not in field


def test_the_booking_table_carries_neither_either():
    """The domain having no copy is worth nothing if the row has one."""

    columns = {column.name for column in BookingORM.__table__.columns}
    reservation_columns = {
        column.name for column in ReservationORM.__table__.columns
    }

    assert COURT_AND_CLOCK <= reservation_columns
    assert not (COURT_AND_CLOCK & columns)


def test_one_booking_per_reservation_is_the_databases_half_of_the_rule():
    """Two bookings against one claim would sell one court twice by a route
    that never touches the exclusion constraint."""

    assert BookingORM.__table__.c.reservation_id.unique is True


# --- what it does carry -----------------------------------------------------


def test_the_price_is_copied_and_the_booking_owns_it():
    booking = a_booking(price=CourtPrice(zloty(96)))

    assert int(booking.price) == 9600


def test_a_new_booking_is_live_and_never_moves_its_own_version():
    booking = a_booking()

    assert booking.is_live
    assert booking.version == 0


def test_cancelling_records_the_instant_and_leaves_the_row():
    booking = a_booking()

    booking.cancel(at=at(13))

    assert not booking.is_live
    assert booking.cancelled_at == at(13)


def test_cancelling_twice_keeps_the_first_instant():
    """A second cancellation is a caller that has lost track, not a new fact.

    Unlike a reservation's release, which refuses: releasing twice would move
    the instant a *court* stopped being claimed, and something else is waiting
    on that. Nothing waits on a booking's cancellation instant, so the honest
    answer is the first one.
    """

    booking = a_booking()
    booking.cancel(at=at(13))
    booking.cancel(at=at(14))

    assert booking.cancelled_at == at(13)
