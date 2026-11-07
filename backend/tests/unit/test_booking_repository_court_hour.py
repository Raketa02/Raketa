"""**Only the court hour's own index is a court taken.** The booking repository
turns the store's refusal of ``ux_bookings_court_id_start`` into ``CourtTaken``,
which a send, a fill, a move or a cancel answers as ``court_just_taken`` —
*try again*. Any other refusal is a fault, and must surface as one: for a
fortnight a foreign key written in the wrong order was read as a court taken,
and every friends game sent on Postgres told its sender to try again.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy.exc import IntegrityError

from app.bootstrap.composition import (
    build_booking_repository,
    build_domain_event_store,
    build_event_publisher,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking, PayMode
from app.modules.bookings.domain.errors import CourtTaken
from app.modules.bookings.infrastructure.booking_models import BookingORM
from app.shared.ids import new_uuid

NOW = instant(datetime(2026, 11, 9, 18, tzinfo=timezone.utc))
SATURDAY = instant(NOW + timedelta(days=5))
COURT = BookedCourt(court_id=new_uuid(), name="Court 3", indoor=True)


def _sent(*, booking_id=None, court: BookedCourt = COURT) -> Booking:
    tomek, ewa, magda, ania = (new_uuid() for _ in range(4))
    return Booking.booked_by_a_friend(
        booking_id=booking_id or new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=court,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=SATURDAY,
        share_grosze=25_00,
        sender=tomek,
        first_side=(tomek, ewa),
        second_side=(magda, ania),
        pay_mode=PayMode.SPLIT_THE_COST,
        cut_off=instant(SATURDAY - timedelta(hours=24)),
        game_id=new_uuid(),
        at=NOW,
    )


async def _saves(session_factory, booking: Booking) -> None:
    async with session_factory() as session:
        await build_booking_repository(
            session,
            event_store=build_domain_event_store(session),
            events=build_event_publisher(session),
        ).save(booking)
        await session.commit()


async def test_a_second_game_on_the_same_court_hour_is_a_court_taken(session_factory):
    await _saves(session_factory, _sent())

    with pytest.raises(CourtTaken):
        await _saves(session_factory, _sent())


async def test_any_other_refusal_is_not_a_court_taken(session_factory):
    booking = _sent()
    # A projection row already under the booking's id, at another court: the
    # store refuses the primary key, and no court hour is in question.
    async with session_factory() as session:
        session.add(
            BookingORM(
                id=booking.booking_id,
                pool_id=new_uuid(),
                club_id=new_uuid(),
                court_id=new_uuid(),
                sport=Sport.PADEL.value,
                start=SATURDAY,
                share_grosze=25_00,
                cut_off=SATURDAY - timedelta(hours=24),
                state="BOOKED",
            )
        )
        await session.commit()

    with pytest.raises(IntegrityError):
        await _saves(session_factory, booking)
