"""What ``proposals`` demands of the rest of the platform for Home and a game's
details (#542), run against every registered implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/proposal_demands.py`` is
enrolled here automatically, so a second one either satisfies the demand or
turns the build red.

**Each provider's record is built the way it is built**: a booking through its
aggregate and repository, a game through its own, and a player and a club
through the routes a person and a desk use — because a demand is a claim about
another context's record, and a stub that agreed with it would prove nothing.
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
    build_game_repository,
)
from app.bootstrap.proposal_demands import (
    PROPOSAL_DEMANDS,
    PROPOSAL_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.proposals.domain.home import ResultStage
from app.modules.proposals.domain.ports import (
    BookableCourt,
    ClubDistances,
    ClubRequests,
    GameResults,
    GameToAsk,
    PlayerBookings,
    PlayerNames,
)
from app.modules.proposals.domain.proposal import ClubAnswer
from app.kernel import minutes
from app.shared.ids import new_uuid
from tests.api import matchmaking_world as world
from tests.api.administration_world import club_signs_up

OLA, KUBA, EWA, TOMEK = (new_uuid() for _ in range(4))


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _at(hours: int = 0) -> Instant:
    return instant(
        datetime(2026, 10, 5, 6, tzinfo=timezone.utc) + timedelta(hours=hours)
    )


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_declared_demand_has_at_least_one_implementation():
    unregistered = [
        port.__name__ for port in PROPOSAL_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_answers_a_declared_demand():
    declared = set(PROPOSAL_DEMANDS)

    assert all(one.port in declared for one in PROPOSAL_IMPLEMENTATIONS)


# --------------------------------------------------------------------------- #
# PlayerBookings — a player's booked games, and each seat's code
# --------------------------------------------------------------------------- #


async def _booked(session, *, start: Instant, court: str = "Court 1") -> Booking:
    booking = Booking.confirmed(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name=court),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=start,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=start - timedelta(hours=24),
        game_id=new_uuid(),
        at=_at(),
    )
    repository = build_booking_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    await repository.save(booking)
    await session.commit()
    return booking


@pytest.mark.parametrize("implementation", registered(PlayerBookings))
async def test_a_player_s_booked_games_come_soonest_first_as_booked(
    implementation, session
):
    later = await _booked(session, start=_at(120), court="Court 2")
    sooner = await _booked(session, start=_at(48))
    bookings: PlayerBookings = implementation.build(session)

    found = await bookings.of_player(EWA)

    assert [game.booking_id for game in found] == [
        sooner.booking_id,
        later.booking_id,
    ]
    game = found[1]
    assert game.court_name == "Court 2"
    assert (game.first_side, game.second_side) == ((OLA, KUBA), (EWA, TOMEK))
    assert (game.start, game.cut_off) == (later.start, later.cut_off)
    assert (game.share_grosze, game.game_id) == (30_00, later.game_id)
    assert (game.sport, game.kind) == (Sport.PADEL, SearchMode.COMPETITIVE)
    assert await bookings.of_player(new_uuid()) == []


@pytest.mark.parametrize("implementation", registered(PlayerBookings))
async def test_a_booking_is_found_by_its_id_and_an_unknown_one_is_not(
    implementation, session
):
    booking = await _booked(session, start=_at(48))
    bookings: PlayerBookings = implementation.build(session)

    found = await bookings.find(booking.booking_id)

    assert found is not None
    assert found.club_id == booking.club_id
    assert await bookings.find(new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(PlayerBookings))
async def test_a_seat_s_code_is_the_same_on_every_read_and_its_own(
    implementation, session
):
    booking = await _booked(session, start=_at(48))
    bookings: PlayerBookings = implementation.build(session)

    ola = bookings.check_in(booking.booking_id, OLA)

    assert bookings.check_in(booking.booking_id, OLA) == ola
    assert bookings.check_in(booking.booking_id, KUBA).short_code != ola.short_code
    assert str(booking.booking_id) in ola.qr_payload


# --------------------------------------------------------------------------- #
# GameResults — where a booked game's result stands, for one of its players
# --------------------------------------------------------------------------- #


def _a_booked_game() -> Game:
    """Ola and Kuba against Ewa and Tomek, at a booked hour."""

    return Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=GameKind.COUNTED,
        window=None,
        line_up=LineUp.of(
            (
                Seating(side=GameSide.A, player_id=OLA),
                Seating(side=GameSide.A, player_id=KUBA),
                Seating(side=GameSide.B, player_id=EWA),
                Seating(side=GameSide.B, player_id=TOMEK),
            )
        ),
        occurred_at=_at(),
        starts_at=_at(48),
    )


async def _saved(session, game: Game) -> Game:
    repository = build_game_repository(
        session=session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    await repository.save(game)
    await session.commit()
    return game


@pytest.mark.parametrize("implementation", registered(GameResults))
async def test_a_game_nobody_said_happened_is_open_for_its_entry(
    implementation, session
):
    game = await _saved(session, _a_booked_game())
    results: GameResults = implementation.build(session)

    found = await results.of([game.game_id, new_uuid()], reader=OLA, now=_at(50))

    assert list(found) == [game.game_id]
    assert found[game.game_id].stage is ResultStage.ENTRY_OPEN
    assert found[game.game_id].awaits_your_agreement is False


@pytest.mark.parametrize("implementation", registered(GameResults))
async def test_a_score_waits_on_the_other_side_s_agreement(implementation, session):
    game = _a_booked_game()
    game.state_result(
        by=OLA,
        score=Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3))),
        occurred_at=_at(50),
    )
    await _saved(session, game)
    results: GameResults = implementation.build(session)

    theirs = await results.of([game.game_id], reader=EWA, now=_at(51))
    ours = await results.of([game.game_id], reader=KUBA, now=_at(51))

    assert theirs[game.game_id].stage is ResultStage.SCORE_TO_ANSWER
    assert theirs[game.game_id].awaits_your_agreement is True
    assert ours[game.game_id].awaits_your_agreement is False


# --------------------------------------------------------------------------- #
# ClubDistances — how far a club is from a player
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ClubDistances))
async def test_a_club_is_as_far_as_every_distance_is_printed(
    implementation, client, session
):
    """From the player's Location area to the club's point: 0,03° of latitude
    in Kraków, printed to one decimal."""

    player_id, token = await world.register(client, "ola")
    await world.commit_profile(
        client, token, location={"latitude": 50.03, "longitude": 19.95}
    )
    club_id, _ = await club_signs_up(client, point=(50.06, 19.95))
    distances: ClubDistances = implementation.build(session)

    found = await distances.from_player(player_id, [UUID(club_id), new_uuid()])

    assert found == {UUID(club_id): 3.3}


@pytest.mark.parametrize("implementation", registered(ClubDistances))
async def test_a_player_with_no_location_area_is_nowhere(
    implementation, client, session
):
    club_id, _ = await club_signs_up(client, point=(50.06, 19.95))
    distances: ClubDistances = implementation.build(session)

    assert await distances.from_player(new_uuid(), [UUID(club_id)]) == {}


# --------------------------------------------------------------------------- #
# ClubRequests — a full game put to its On request club, and its answer (#543)
# --------------------------------------------------------------------------- #


def _a_game_to_ask(club_id: UUID, *, start: Instant, at: Instant) -> GameToAsk:
    return GameToAsk(
        proposal_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=club_id,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=start,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        court=BookableCourt(
            court_id=new_uuid(),
            name="Court 1",
            cut_off=start - timedelta(hours=24),
            time_to_confirm=minutes(30),
        ),
        answer_by=at + timedelta(minutes=30),
    )


@pytest.mark.parametrize("implementation", registered(ClubRequests))
async def test_a_request_waits_at_its_club_until_its_answer_is_due(
    implementation, session
):
    club_id = new_uuid()
    game = _a_game_to_ask(club_id, start=_at(48), at=_at())
    requests: ClubRequests = implementation.build(session)

    await requests.ask(game, at=_at())
    await session.commit()

    found = await requests.find(game.proposal_id)
    assert found is not None and found.waiting is True
    assert (found.club_id, found.court_name, found.answer_by) == (
        club_id,
        "Court 1",
        game.answer_by,
    )
    assert found.players == (OLA, KUBA, EWA, TOMEK)
    assert [r.booking_id for r in await requests.waiting_at(club_id)] == [
        game.proposal_id
    ]
    assert await requests.waiting_at(new_uuid()) == []
    assert await requests.unanswered(now=_at()) == []
    assert await requests.unanswered(now=game.answer_by) == [game.proposal_id]
    assert await requests.find(new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(ClubRequests))
async def test_a_request_is_answered_once_and_a_withdrawn_one_asked_again(
    implementation, session
):
    club_id = new_uuid()
    refused = _a_game_to_ask(club_id, start=_at(48), at=_at())
    accepted = _a_game_to_ask(club_id, start=_at(72), at=_at())
    requests: ClubRequests = implementation.build(session)
    await requests.ask(refused, at=_at())
    await requests.ask(accepted, at=_at())

    await requests.turn_down(
        refused.proposal_id, answer=ClubAnswer.REFUSED, reason=None, at=_at()
    )
    assert await requests.withdraw(accepted.proposal_id, player_ids=(KUBA,), at=_at())
    await requests.ask(accepted, at=_at())
    game_id = await requests.accept(accepted.proposal_id, at=_at())
    await session.commit()

    gone = await requests.find(refused.proposal_id)
    booked = await requests.find(accepted.proposal_id)
    assert gone is not None and gone.waiting is False
    assert booked is not None and booked.waiting is False
    assert game_id is not None
    assert await requests.waiting_at(club_id) == []
    assert not await requests.withdraw(refused.proposal_id, player_ids=(OLA,), at=_at())


# --------------------------------------------------------------------------- #
# PlayerNames — what the club sees of a player
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(PlayerNames))
async def test_a_player_is_named_by_their_name_and_a_stranger_not_at_all(
    implementation, client, session
):
    player_id, _ = await world.register(client, "ola")
    names: PlayerNames = implementation.build(session)

    assert await names.names_of([player_id, new_uuid()]) == {player_id: "ola"}
    assert await names.names_of([]) == {}
