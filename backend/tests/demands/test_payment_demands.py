"""What ``payments`` demands of other contexts (#548), run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident**
(``docs/adr/0098``). Every implementation registered in
``app/bootstrap/payment_demands.py`` is enrolled here automatically. **Every
booked game is arranged through the Booking aggregate**, saved by its own
repository — never an ``INSERT``.

**Over for good is the question**: a club is paid a game's money once nothing
can move it any more — the game played, or called off with what that gives back
decided. A game the clock reads as called off before anything recorded so has
its refunds still to come, and is not over.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.composition import (
    build_booking_repository,
    build_domain_event_store,
    build_event_publisher,
)
from app.bootstrap.payment_demands import (
    PAYMENT_DEMANDS,
    PAYMENT_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking, CancelReason
from app.modules.payments.domain.ports import GamesOver
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


def _from_now(**offset) -> Instant:
    return instant(datetime.now(timezone.utc) + timedelta(**offset))


def _booked(*, starts: Instant, made: Instant) -> Booking:
    """A padel game booked at ``made`` with a 24-hour cut-off."""

    players = (new_uuid(), new_uuid(), new_uuid(), new_uuid())
    return Booking.confirmed(
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
        at=made,
    )


async def _saved(session, booking: Booking) -> UUID:
    await build_booking_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(booking)
    await session.commit()
    return booking.booking_id


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_demand_has_at_least_one_implementation():
    assert [p.__name__ for p in PAYMENT_DEMANDS if not implementations_of(p)] == []


def test_every_registered_implementation_is_of_a_demand():
    assert all(one.port in PAYMENT_DEMANDS for one in PAYMENT_IMPLEMENTATIONS)


# --------------------------------------------------------------------------- #
# GamesOver — which games' money nothing can move any more
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(GamesOver))
async def test_a_game_played_is_over_and_one_still_ahead_is_not(
    implementation, session
):
    games: GamesOver = implementation.build(session)
    played = await _saved(
        session,
        _booked(starts=_from_now(hours=-3), made=_from_now(days=-5)),
    )
    playing = await _saved(
        session,
        _booked(starts=_from_now(minutes=-30), made=_from_now(days=-5)),
    )
    ahead = await _saved(
        session,
        _booked(starts=_from_now(days=2), made=_from_now(days=-1)),
    )

    over = await games.over([played, playing, ahead, new_uuid()], at=_now())

    assert over == {played}


@pytest.mark.parametrize("implementation", registered(GamesOver))
async def test_a_game_called_off_is_over_once_it_is_recorded_so(
    implementation, session
):
    games: GamesOver = implementation.build(session)
    cancelled = _booked(starts=_from_now(days=2), made=_from_now(days=-1))
    cancelled.cancel(CancelReason.WEATHER, at=_from_now(hours=-1))
    short = _booked(starts=_from_now(hours=-3), made=_from_now(days=-5))
    # A seat left before the cut-off and nobody took it: the game is off from
    # its cut-off — but nothing has recorded so, nor given anybody back.
    short.leave(short.players[0], at=_from_now(days=-4))
    called_off, unrecorded = (
        await _saved(session, cancelled),
        await _saved(session, short),
    )

    over = await games.over([called_off, unrecorded], at=_now())

    assert over == {called_off}
