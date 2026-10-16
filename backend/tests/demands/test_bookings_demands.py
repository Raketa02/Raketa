"""What ``bookings`` publishes (#544), run against every registered
implementation.

**A demand nobody executes is a demand satisfied by accident**
(``docs/adr/0098``). Every implementation registered in
``app/bootstrap/bookings_demands.py`` is enrolled here automatically. **Every
booked game is arranged through the Booking aggregate**, saved by its own
repository — never an ``INSERT``.

**The absence rule** holds here as everywhere a record is published: a player
with no settled booked game is absent from the answer, never an empty row. What
is published is **every settled booked game**, oldest first, and how each broken
one was broken — Player reliability prices the two ways differently (#659).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.bookings_demands import (
    BOOKINGS_DEMANDS,
    BOOKINGS_IMPLEMENTATIONS,
    implementations_of,
)
from app.bootstrap.composition import (
    build_booking_repository,
    build_domain_event_store,
    build_event_publisher,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.bookings.domain.keeping import Broken, Keeping
from app.modules.bookings.domain.ports import BookingHistoryQuery
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _now() -> Instant:
    return instant(datetime.now(timezone.utc))


def _ago(**offset) -> Instant:
    return instant(datetime.now(timezone.utc) - timedelta(**offset))


async def _booked(
    session,
    players: tuple[UUID, UUID, UUID, UUID],
    *,
    starts: Instant,
    leaving: tuple[tuple[UUID, Instant], ...] = (),
) -> Booking:
    """A padel game booked five days before its hour with a 24-hour cut-off,
    and whoever left it, when."""

    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=starts,
        share_grosze=30_00,
        first_side=players[:2],
        second_side=players[2:],
        cut_off=instant(starts - timedelta(hours=24)),
        game_id=new_uuid(),
        at=instant(starts - timedelta(days=5)),
    )
    for player, at in leaving:
        booking.leave(player, at=at)
    await build_booking_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(booking)
    await session.commit()
    return booking


def _four() -> tuple[UUID, UUID, UUID, UUID]:
    return (new_uuid(), new_uuid(), new_uuid(), new_uuid())


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_published_port_has_at_least_one_implementation():
    assert [p.__name__ for p in BOOKINGS_DEMANDS if not implementations_of(p)] == []


def test_every_registered_implementation_is_of_a_published_port():
    assert all(one.port in BOOKINGS_DEMANDS for one in BOOKINGS_IMPLEMENTATIONS)


# --------------------------------------------------------------------------- #
# BookingHistoryQuery — who kept a booked game, and who broke it
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(BookingHistoryQuery))
async def test_a_player_with_no_settled_booked_game_is_absent(implementation, session):
    history: BookingHistoryQuery = implementation.build(session)
    ahead = _four()
    await _booked(session, ahead, starts=_ago(days=-2))

    assert await history.keeping_for([ahead[0], new_uuid()], now=_now()) == {}


@pytest.mark.parametrize("implementation", registered(BookingHistoryQuery))
async def test_a_game_played_whole_is_kept_and_a_leaver_nobody_replaced_broke_it(
    implementation, session
):
    history: BookingHistoryQuery = implementation.build(session)
    four = _four()
    played = _ago(days=4)
    short = _ago(days=2)
    await _booked(session, four, starts=played)
    await _booked(
        session, four, starts=short, leaving=((four[0], short - timedelta(hours=3)),)
    )

    kept = await history.keeping_for([four[0], four[1]], now=_now())

    assert kept[four[0]] == (
        Keeping(at=played),
        Keeping(at=short, broken=Broken.LEFT_AFTER_THE_CUT_OFF),
    )
    # Staying in a game that went ahead short puts nothing on the record.
    assert kept[four[1]] == (Keeping(at=played),)


@pytest.mark.parametrize("implementation", registered(BookingHistoryQuery))
async def test_a_leaver_whose_seat_called_the_game_off_broke_it_and_nobody_else(
    implementation, session
):
    history: BookingHistoryQuery = implementation.build(session)
    four = _four()
    starts = _ago(hours=6)
    await _booked(
        session, four, starts=starts, leaving=((four[0], starts - timedelta(days=2)),)
    )

    kept = await history.keeping_for(four, now=_now())

    assert kept == {
        four[0]: (
            Keeping(
                at=instant(starts - timedelta(hours=24)),
                broken=Broken.CALLED_OFF_BY_LEAVING,
            ),
        )
    }
