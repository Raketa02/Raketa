"""What ``bookings`` demands of the rest of the platform (#541, #544, #673),
run against every registered implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/booking_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or
turns the build red. **Each club is built the way a desk builds it**, through
the club website's routes.
"""

from __future__ import annotations

from datetime import timedelta
from uuid import UUID

import pytest
import pytest_asyncio

from app.bootstrap.booking_demands import (
    BOOKING_DEMANDS,
    BOOKING_IMPLEMENTATIONS,
    implementations_of,
)
from app.bootstrap.composition import (
    build_club_courts_at_the_hour,
    build_domain_event_store,
    build_event_publisher,
    build_game_opening,
    build_game_repository,
)
from app.kernel import InvariantViolated, Sport, instant
from app.modules.bookings.domain.booking import CancelReason
from app.modules.bookings.domain.ports import (
    ClubCourtsAtTheHour,
    ClubDesk,
    ClubDesks,
    CourtClosures,
    GameChanges,
    GameNoShows,
    GameOpening,
)
from app.modules.games.domain.attendance import ClubVerdict
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameSide
from app.modules.games.domain.standing import GameStanding
from app.shared.ids import new_uuid
from tests.api.administration_world import club_signs_up
from tests.api.club_courts_world import adds_a_court, sets_hours
from tests.api.proposals_world import (
    MONDAY_MORNING,
    SATURDAY_FIVE,
    a_club_and_its_desk,
    every_hour_of_the_week,
)


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_declared_demand_has_at_least_one_implementation():
    unregistered = [
        port.__name__ for port in BOOKING_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_answers_a_declared_demand():
    declared = set(BOOKING_DEMANDS)

    assert all(one.port in declared for one in BOOKING_IMPLEMENTATIONS)


# --------------------------------------------------------------------------- #
# ClubCourtsAtTheHour — the first free court and its cut-off
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ClubCourtsAtTheHour))
async def test_the_first_free_court_comes_with_the_club_s_terms(
    implementation, client, session
):
    club_id, _ = await a_club_and_its_desk(client)
    courts: ClubCourtsAtTheHour = implementation.build(session)

    found = await courts.first_free(
        UUID(club_id), sport=Sport.PADEL, start=SATURDAY_FIVE
    )

    assert found is not None
    assert found.court.name == "Court 1"
    assert found.cut_off_hours == 24
    assert (
        await courts.first_free(UUID(club_id), sport=Sport.SQUASH, start=SATURDAY_FIVE)
        is None
    )


@pytest.mark.parametrize("implementation", registered(ClubCourtsAtTheHour))
async def test_the_free_courts_at_an_hour_are_the_sport_s_in_the_club_s_order(
    implementation, client, session
):
    """#547: where a booked game may be moved — each with its kind, indoor or
    outdoor, which the move keeps (#671, Q122), and the share one player pays
    for it at the hour, which a club's cancel asks of a court before it absorbs
    the game (#672)."""

    club_id, desk = await a_club_and_its_desk(client)
    outdoor = await adds_a_court(
        client, desk, name="Court 4", sport="PADEL", indoor=False
    )
    await sets_hours(client, desk, [outdoor["id"]], every_hour_of_the_week())
    courts: ClubCourtsAtTheHour = implementation.build(session)

    padel = await courts.free_courts(
        UUID(club_id), sport=Sport.PADEL, start=SATURDAY_FIVE
    )

    assert [(one.court.name, one.court.indoor, one.share_grosze) for one in padel] == [
        ("Court 1", True, 30_00),
        ("Court 4", False, 30_00),
    ]
    first = await courts.first_free(
        UUID(club_id), sport=Sport.PADEL, start=SATURDAY_FIVE
    )
    assert first is not None and first.court.indoor is True
    squash = await courts.free_courts(
        UUID(club_id), sport=Sport.SQUASH, start=SATURDAY_FIVE
    )
    assert list(squash) == []


# --------------------------------------------------------------------------- #
# CourtClosures — the court a club's cancel took, closed for the hour (#673)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(CourtClosures))
async def test_a_court_closed_by_a_cancel_is_off_sale_for_that_hour_alone(
    implementation, client, session
):
    club_id, desk = await a_club_and_its_desk(client)
    court_3 = await adds_a_court(client, desk, name="Court 3", sport="PADEL")
    await sets_hours(client, desk, [court_3["id"]], every_hour_of_the_week())
    courts = build_club_courts_at_the_hour(session)
    [court_1, _] = await courts.free_courts(
        UUID(club_id), sport=Sport.PADEL, start=SATURDAY_FIVE
    )
    closures: CourtClosures = implementation.build(session)

    await closures.close(
        UUID(club_id),
        court_1.court.court_id,
        start=SATURDAY_FIVE,
        because=CancelReason.REPAIR,
        at=MONDAY_MORNING,
    )
    await session.commit()

    def names(free) -> list[str]:
        return [one.court.name for one in free]

    assert names(
        await courts.free_courts(UUID(club_id), sport=Sport.PADEL, start=SATURDAY_FIVE)
    ) == ["Court 3"]
    an_hour_on = SATURDAY_FIVE + timedelta(hours=1)
    assert names(
        await courts.free_courts(UUID(club_id), sport=Sport.PADEL, start=an_hour_on)
    ) == ["Court 1", "Court 3"]


# --------------------------------------------------------------------------- #
# ClubDesks — whom an email to a club goes to
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ClubDesks))
async def test_a_club_s_desk_is_its_one_sign_in_and_its_name(
    implementation, client, session
):
    club_id, _ = await club_signs_up(client, name="Ogrody 33", email="desk@ogrody.pl")
    desks: ClubDesks = implementation.build(session)

    assert await desks.of(UUID(club_id)) == ClubDesk(
        email="desk@ogrody.pl", club_name="Ogrody 33"
    )
    assert await desks.of(new_uuid()) is None


# --------------------------------------------------------------------------- #
# GameOpening and GameChanges — the ordinary Game a booking opens, and what
# leaving and the cut-off do to it (#541, #544)
# --------------------------------------------------------------------------- #


OLA, KUBA, EWA, TOMEK = (new_uuid() for _ in range(4))


async def _opened(session, booking_id: UUID) -> UUID:
    game_id = await build_game_opening(session).open(
        booking_id=booking_id,
        sport=Sport.PADEL,
        counted=True,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        starts_at=SATURDAY_FIVE,
        at=MONDAY_MORNING,
    )
    await session.commit()
    return game_id


async def _game(session, booking_id: UUID) -> Game:
    game = await build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).for_challenge(booking_id)
    assert game is not None
    return game


@pytest.mark.parametrize("implementation", registered(GameOpening))
async def test_a_booking_opens_one_ordinary_game_at_its_hour(implementation, session):
    games: GameOpening = implementation.build(session)
    booking_id = new_uuid()

    game_id = await games.open(
        booking_id=booking_id,
        sport=Sport.PADEL,
        counted=True,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        starts_at=SATURDAY_FIVE,
        at=MONDAY_MORNING,
    )
    await session.commit()

    game = await _game(session, booking_id)
    assert (game.id, game.starts_at) == (game_id, SATURDAY_FIVE)
    assert game.standing_at(MONDAY_MORNING) is GameStanding.AWAITING_ENTRY
    with pytest.raises(InvariantViolated):
        await games.open(
            booking_id=booking_id,
            sport=Sport.PADEL,
            counted=True,
            first_side=(OLA, KUBA),
            second_side=(EWA, TOMEK),
            starts_at=SATURDAY_FIVE,
            at=MONDAY_MORNING,
        )


@pytest.mark.parametrize("implementation", registered(GameChanges))
async def test_a_leaver_s_seat_opens_on_the_game_and_the_cut_off_ends_it(
    implementation, session
):
    changes: GameChanges = implementation.build(session)
    booking_id = new_uuid()
    await _opened(session, booking_id)

    await changes.vacate(
        booking_id, KUBA, at=instant(MONDAY_MORNING + timedelta(hours=1))
    )
    await session.commit()
    assert KUBA not in (await _game(session, booking_id)).line_up.players

    called = instant(SATURDAY_FIVE - timedelta(hours=24))
    await changes.call_off(booking_id, at=called)
    await session.commit()
    assert (await _game(session, booking_id)).standing_at(
        called
    ) is GameStanding.CALLED_OFF


@pytest.mark.parametrize("implementation", registered(GameChanges))
async def test_a_call_off_after_the_hour_leaves_a_game_that_started_short(
    implementation, session
):
    changes: GameChanges = implementation.build(session)
    booking_id = new_uuid()
    await _opened(session, booking_id)
    await changes.vacate(
        booking_id, KUBA, at=instant(MONDAY_MORNING + timedelta(hours=1))
    )

    late = instant(SATURDAY_FIVE + timedelta(minutes=5))
    await changes.call_off(booking_id, at=late)
    await session.commit()

    assert (await _game(session, booking_id)).standing_at(
        late
    ) is GameStanding.STARTED_SHORT


@pytest.mark.parametrize("implementation", registered(GameChanges))
async def test_a_rescue_takes_the_open_seat_on_the_leaver_s_side(
    implementation, session
):
    """#545: the seat a leaver opened is taken by somebody else, on its side —
    and they are on the game's court."""

    changes: GameChanges = implementation.build(session)
    booking_id = new_uuid()
    await _opened(session, booking_id)
    await changes.vacate(
        booking_id, KUBA, at=instant(MONDAY_MORNING + timedelta(hours=1))
    )
    zosia = new_uuid()

    await changes.seat(
        booking_id, zosia, side="A", at=instant(MONDAY_MORNING + timedelta(hours=2))
    )
    await session.commit()

    game = await _game(session, booking_id)
    assert game.line_up.is_complete
    assert game.line_up.side_of(zosia) is GameSide.A


@pytest.mark.parametrize("implementation", registered(GameChanges))
async def test_the_club_s_cancel_calls_a_whole_game_off(implementation, session):
    """#547: whole or with a seat open, before its hour."""

    changes: GameChanges = implementation.build(session)
    booking_id = new_uuid()
    await _opened(session, booking_id)

    cancelled = instant(SATURDAY_FIVE - timedelta(hours=2))
    await changes.call_off_whole(booking_id, at=cancelled)
    await session.commit()

    game = await _game(session, booking_id)
    assert game.standing_at(cancelled) is GameStanding.CALLED_OFF
    assert game.called_off_by is None


# --------------------------------------------------------------------------- #
# GameNoShows — who Didn't come to a booked game (#547, #657)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(GameNoShows))
async def test_didn_t_come_counts_only_once_the_late_claim_s_day_is_over(
    implementation, session
):
    no_shows: GameNoShows = implementation.build(session)
    booking_id = new_uuid()
    await _opened(session, booking_id)
    games = build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    game = await games.for_challenge(booking_id)
    assert game is not None
    game.note_absent(
        by=OLA,
        absent=KUBA,
        where=ClubVerdict(at_the_club=True, club_name=None),
        occurred_at=instant(SATURDAY_FIVE + timedelta(minutes=10)),
    )
    await games.save(game)
    await session.commit()
    half_past = instant(SATURDAY_FIVE + timedelta(minutes=30))

    assert await no_shows.did_not_come(booking_id, now=half_past) == frozenset()
    assert await no_shows.did_not_come(
        booking_id, now=instant(half_past + timedelta(days=1))
    ) == frozenset({KUBA})
    assert await no_shows.did_not_come(new_uuid(), now=half_past) == frozenset()
