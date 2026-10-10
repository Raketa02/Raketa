"""What ``proposals`` demands of the rest of the platform for Home and a game's
details (#542), On request (#543), leaving and the cut-off (#544), rescues
(#545), posting (#546) and the club running its bookings (#547), run against
every registered implementation.

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
    build_clock,
    build_domain_event_store,
    build_event_publisher,
    build_game_opening,
    build_game_repository,
    build_seat_charge_repository,
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
from app.modules.payments.domain.provider import Payment, PaymentStatus
from app.modules.payments.domain.seat_charge import SeatCharge, SeatChargeStatus
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.proposals.domain.home import BookingStage, ResultStage
from app.modules.proposals.domain.club_bookings import CodeAtTheDesk
from app.modules.proposals.domain.home import ClubCancelReason
from app.modules.proposals.domain.ports import (
    BookableCourt,
    BookedGameChanges,
    BookingTakings,
    CardFees,
    ClubBookings,
    ClubDistances,
    ClubRequests,
    DeskCheckIns,
    GameResults,
    GameToAsk,
    HeldShares,
    PlayerBookings,
    PlayerFit,
    PlayerNames,
    PlayersInPlay,
    PoolOrigins,
    RefundReason,
    SeatRefunds,
)
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.post import LevelRange
from app.modules.proposals.domain.proposal import ClubAnswer
from app.kernel import minutes
from app.shared.ids import new_uuid
from tests.api import players_world as players
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


def registered_build(port, session):
    """The first registered implementation of ``port`` — to read back what the
    one under test wrote."""

    [first, *_] = implementations_of(port)
    return first.build(session)


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


async def _booked(
    session,
    *,
    start: Instant,
    court: str = "Court 1",
    left_by: UUID | None = None,
) -> Booking:
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
    if left_by is not None:
        booking.leave(left_by, at=_at())
    return await _saved_booking(session, booking)


async def _waiting(
    session, *, start: Instant, taken_back_from: UUID | None = None
) -> Booking:
    """A full game its On request club has not answered: no Game yet — or,
    ``taken_back_from`` a player whose seat opened while it waited, a game
    filling again (#624)."""

    booking = Booking.requested(
        booking_id=new_uuid(),
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=start,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=start - timedelta(hours=24),
        answer_by=_at(1),
        filled_by=None,
        at=_at(),
    )
    if taken_back_from is not None:
        booking.withdraw_request(
            (taken_back_from,), left=(taken_back_from,), at=_at()
        )
    return await _saved_booking(session, booking)


async def _saved_booking(session, booking: Booking) -> Booking:
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

    found = await bookings.of_player(EWA, since=None)

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
    assert await bookings.of_player(new_uuid(), since=None) == []


@pytest.mark.parametrize("implementation", registered(PlayerBookings))
async def test_a_request_taken_back_is_a_game_filling_again_to_those_still_in(
    implementation, session
):
    """Kuba's seat opened while the club decided (#624, Q106): the others keep
    their places, and he no longer has one."""

    booking = await _waiting(session, start=_at(48), taken_back_from=KUBA)
    bookings: PlayerBookings = implementation.build(session)

    [game] = await bookings.of_player(EWA, since=None)

    assert game.booking_id == booking.booking_id
    assert (game.stage, game.called_off) == (BookingStage.FILLING_AGAIN, None)
    assert (game.first_side, game.second_side) == ((OLA,), (EWA, TOMEK))
    assert await bookings.of_player(KUBA, since=None) == []
    found = await bookings.find(booking.booking_id)
    assert found is not None and found.filling_again


@pytest.mark.parametrize("implementation", registered(ClubBookings))
async def test_a_request_taken_back_is_no_booking_of_the_club_s(
    implementation, session
):
    booking = await _waiting(session, start=_at(48), taken_back_from=KUBA)
    club: ClubBookings = implementation.build(session)

    assert (
        await club.on_day(booking.club_id, start=_at(47), end=_at(49))
    ) == []


@pytest.mark.parametrize("implementation", registered(PlayerBookings))
async def test_a_player_s_booked_games_are_read_from_an_hour_on(
    implementation, session
):
    """Home's bound (#613): a game whose hour started before ``since`` is not
    read at all, so how many are loaded no longer grows with old games."""

    await _booked(session, start=_at(48))
    later = await _booked(session, start=_at(120))
    bookings: PlayerBookings = implementation.build(session)

    from_its_hour = await bookings.of_player(EWA, since=_at(120))
    after_it = await bookings.of_player(EWA, since=_at(121))

    assert [game.booking_id for game in from_its_hour] == [later.booking_id]
    assert after_it == []


@pytest.mark.parametrize("implementation", registered(PlayerBookings))
async def test_the_games_of_a_player_s_older_bookings_are_named_unread(
    implementation, session
):
    """Each Game a player's booking opened before an hour, to its booking —
    never one with no Game yet, and never one whose seat they left."""

    older = await _booked(session, start=_at(48))
    await _booked(session, start=_at(120))
    await _booked(session, start=_at(49), left_by=EWA)
    await _waiting(session, start=_at(50))
    bookings: PlayerBookings = implementation.build(session)

    found = await bookings.games_before(EWA, before=_at(120))

    assert found == {older.game_id: older.booking_id}
    assert await bookings.games_before(new_uuid(), before=_at(200)) == {}


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


A_SCORE = Score.of((SetScore(a=6, b=4), SetScore(a=6, b=3)))
ANOTHER_SCORE = Score.of((SetScore(a=6, b=4), SetScore(a=7, b=5)))


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


@pytest.mark.parametrize("implementation", registered(GameResults))
async def test_the_games_a_score_may_still_wait_on_are_named(implementation, session):
    """Home's look at games older than it reads (#613): a correction re-dates
    its side's score, so a game played long ago may still wait on its reader —
    for a day from the last score put on its table."""

    scored = _a_booked_game()
    scored.state_result(by=OLA, score=A_SCORE, occurred_at=_at(50))
    scored.state_result(by=KUBA, score=ANOTHER_SCORE, occurred_at=_at(70))
    await _saved(session, scored)
    unscored = await _saved(session, _a_booked_game())
    asked = [scored.game_id, unscored.game_id, new_uuid()]
    results: GameResults = implementation.build(session)

    assert await results.waiting_among(asked, now=_at(93)) == {scored.game_id}
    assert await results.waiting_among(asked, now=_at(95)) == set()
    assert await results.waiting_among([], now=_at(0)) == set()


# --------------------------------------------------------------------------- #
# ClubDistances — how far a club is from a player
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ClubDistances))
async def test_a_club_is_as_far_as_every_distance_is_printed(
    implementation, client, session
):
    """From the player's Location area to the club's point: 0,03° of latitude
    in Kraków, printed to one decimal."""

    player_id, token = await players.register(client, "ola")
    await players.commit_profile(
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
        filled_by=TOMEK,
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
    assert await requests.withdraw(
        accepted.proposal_id, player_ids=(KUBA,), left=(KUBA,), at=_at()
    )
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


@pytest.mark.parametrize("implementation", registered(ClubRequests))
async def test_a_club_s_yes_waits_on_a_payment_then_books_or_is_called_off(
    implementation, session
):
    """#626: a share refused at the club's yes keeps the yes and its court
    until the payment's time; paid, the club's yes books it, not asked again —
    not paid, it is called off, and a request no longer the club's records
    nothing."""

    club_id = new_uuid()
    paid = _a_game_to_ask(club_id, start=_at(48), at=_at())
    lapsed = _a_game_to_ask(club_id, start=_at(72), at=_at())
    requests: ClubRequests = implementation.build(session)
    for game in (paid, lapsed):
        await requests.ask(game, at=_at())
        await requests.await_a_payment(
            game.proposal_id, player_ids=(TOMEK,), until=_at(1), at=_at()
        )

    awaiting = await requests.find(paid.proposal_id)
    assert awaiting is not None
    assert (awaiting.waiting, awaiting.pay_by) == (False, _at(1))
    assert await requests.waiting_at(club_id) == []
    assert await requests.unanswered(now=_at(48)) == []
    assert await requests.accept(paid.proposal_id, at=_at()) is not None
    assert await requests.payment_not_in_time(
        lapsed.proposal_id, player_ids=(TOMEK,), for_good=False, at=_at(1)
    )
    assert not await requests.payment_not_in_time(
        lapsed.proposal_id, player_ids=(TOMEK,), for_good=False, at=_at(1)
    )
    await session.commit()

    booked = await requests.find(paid.proposal_id)
    called_off = await requests.find(lapsed.proposal_id)
    assert booked is not None and booked.pay_by is None
    assert called_off is not None and called_off.waiting is False


# --------------------------------------------------------------------------- #
# PlayerNames — what the club sees of a player
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(PlayerNames))
async def test_a_player_is_named_by_their_name_and_a_stranger_not_at_all(
    implementation, client, session
):
    player_id, _ = await players.register(client, "ola")
    names: PlayerNames = implementation.build(session)

    assert await names.names_of([player_id, new_uuid()]) == {player_id: "ola"}
    assert await names.names_of([]) == {}


# --------------------------------------------------------------------------- #
# BookedGameChanges — leaving a booked game, and the cut-off (#544)
# --------------------------------------------------------------------------- #


async def _booked_with_its_game(session, *, start: Instant) -> Booking:
    """A booking, and the ordinary Game it opened — as the fill makes both."""

    game_id = await build_game_opening(session).open(
        booking_id=(booking_id := new_uuid()),
        sport=Sport.PADEL,
        counted=True,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        starts_at=start,
        at=_at(),
    )
    booking = Booking.confirmed(
        booking_id=booking_id,
        pool_id=new_uuid(),
        club_id=new_uuid(),
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=start,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=start - timedelta(hours=24),
        game_id=game_id,
        at=_at(),
    )
    await build_booking_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(booking)
    await session.commit()
    return booking


@pytest.mark.parametrize("implementation", registered(BookedGameChanges))
async def test_a_seat_left_before_the_cut_off_calls_the_game_off_at_it(
    implementation, session
):
    changes: BookedGameChanges = implementation.build(session)
    start = _at(5 * 24)
    booking = await _booked_with_its_game(session, start=start)

    await changes.leave(booking.booking_id, KUBA, at=_at(1))
    await session.commit()
    cut_off = start - timedelta(hours=24)

    assert booking.booking_id not in await changes.short_at_the_cut_off(
        now=cut_off - timedelta(minutes=1)
    )
    assert booking.booking_id in await changes.short_at_the_cut_off(now=cut_off)
    still_in = await changes.call_off_at_the_cut_off(booking.booking_id, at=cut_off)
    await session.commit()
    assert still_in == (OLA, EWA, TOMEK)
    assert booking.booking_id not in await changes.short_at_the_cut_off(now=cut_off)


@pytest.mark.parametrize("implementation", registered(BookedGameChanges))
async def test_a_rescue_takes_the_seat_that_opened_first_and_a_no_is_kept(
    implementation, session
):
    """#545: the first seat to open is the one taken, on its side, and the game
    is whole again when the last is; a no to its card is recorded once."""

    changes: BookedGameChanges = implementation.build(session)
    start = _at(5 * 24)
    booking = await _booked_with_its_game(session, start=start)
    zosia, marek = new_uuid(), new_uuid()
    await changes.leave(booking.booking_id, EWA, at=_at(1))
    await changes.leave(booking.booking_id, KUBA, at=_at(2))

    first = await changes.rescue(booking.booking_id, zosia, at=_at(3))
    said_no = await changes.say_no_to_the_seat(booking.booking_id, marek, at=_at(4))
    again = await changes.say_no_to_the_seat(booking.booking_id, marek, at=_at(5))
    await session.commit()

    assert (first.left_by, first.side, first.left_at) == (EWA, "B", _at(1))
    assert (said_no, again) == (True, False)
    bookings = registered_build(PlayerBookings, session)
    game = await bookings.find(booking.booking_id)
    assert game is not None
    assert game.second_side == (TOMEK, zosia)
    assert [seat.left_by for seat in game.open] == [KUBA]
    assert game.said_no == frozenset({marek})
    assert game.leavers == frozenset({EWA, KUBA})
    second = await changes.rescue(booking.booking_id, marek, at=_at(6))
    await session.commit()
    assert second.left_by == KUBA
    whole = await bookings.find(booking.booking_id)
    assert whole is not None and whole.open_seats == 0 and whole.open == ()


@pytest.mark.parametrize("implementation", registered(PlayerBookings))
async def test_a_pool_s_rescues_are_its_games_with_a_seat_open_soonest_first(
    implementation, session
):
    bookings: PlayerBookings = implementation.build(session)
    changes = registered_build(BookedGameChanges, session)
    later = await _booked_with_its_game(session, start=_at(6 * 24))
    sooner = await _booked_with_its_game(session, start=_at(5 * 24))
    whole = await _booked_with_its_game(session, start=_at(4 * 24))
    for booking in (later, sooner):
        await changes.leave(booking.booking_id, KUBA, at=_at(1))
    await session.commit()

    found = [
        await bookings.rescues_in(booking.pool_id, sport=Sport.PADEL, now=_at(2))
        for booking in (later, sooner, whole)
    ]
    assert [[game.booking_id for game in games] for games in found] == [
        [later.booking_id],
        [sooner.booking_id],
        [],
    ]
    assert await bookings.rescues_in(
        sooner.pool_id, sport=Sport.TENNIS, now=_at(2)
    ) == []
    # Its hour come, a game is nobody's rescue.
    assert await bookings.rescues_in(
        sooner.pool_id, sport=Sport.PADEL, now=sooner.start
    ) == []


@pytest.mark.parametrize("implementation", registered(BookedGameChanges))
async def test_a_seat_left_after_the_cut_off_calls_nothing_off(implementation, session):
    changes: BookedGameChanges = implementation.build(session)
    start = _at(5 * 24)
    booking = await _booked_with_its_game(session, start=start)

    await changes.leave(booking.booking_id, KUBA, at=start - timedelta(hours=2))
    await session.commit()

    assert await changes.short_at_the_cut_off(now=start) == []
    assert await changes.call_off_at_the_cut_off(booking.booking_id, at=start) is None


# --------------------------------------------------------------------------- #
# SeatRefunds and CardFees — a paid share given back, and the fee on one (#544)
# --------------------------------------------------------------------------- #


async def _a_paid_share(session, *, game_id: UUID, player_id: UUID) -> SeatCharge:
    charge = SeatCharge.held(
        charge_id=new_uuid(),
        player_id=player_id,
        game_id=game_id,
        club_id=new_uuid(),
        account_id="acct_fake_club",
        payment=Payment(
            payment_id="pi_fake_3000g_x",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=30_00,
        ),
        sport=Sport.PADEL,
        starts_at=_at(5 * 24),
        at=_at(),
    )
    charge.take(booking_id=game_id, at=_at())
    charge.captured(at=_at())
    await _charges(session).save(charge)
    await session.commit()
    return charge


def _charges(session):
    return build_seat_charge_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


@pytest.mark.parametrize("implementation", registered(SeatRefunds))
async def test_a_leaver_s_share_taken_before_the_cut_off_comes_back_whole(
    implementation, session
):
    """Leaving before the cut-off costs nothing (#637, Q113): a share taken
    that early — only #639's fallback takes one — is given back in full."""

    refunds: SeatRefunds = implementation.build(session)
    game_id = new_uuid()
    kubas = await _a_paid_share(session, game_id=game_id, player_id=KUBA)
    olas = await _a_paid_share(session, game_id=game_id, player_id=OLA)

    await refunds.refund(
        game_id, [KUBA], reason=RefundReason.LEFT_BEFORE_THE_CUT_OFF, at=_at(1)
    )
    await session.commit()

    kuba_now = await _charges(session).load(kubas.charge_id)
    ola_now = await _charges(session).load(olas.charge_id)
    assert kuba_now is not None and kuba_now.refund_withholds_fee is False
    assert ola_now is not None and ola_now.refund_withholds_fee is None


@pytest.mark.parametrize("implementation", registered(SeatRefunds))
async def test_a_game_called_off_gives_everybody_still_in_everything_back(
    implementation, session
):
    refunds: SeatRefunds = implementation.build(session)
    game_id = new_uuid()
    olas = await _a_paid_share(session, game_id=game_id, player_id=OLA)

    await refunds.refund(
        game_id, [OLA], reason=RefundReason.CALLED_OFF_AT_THE_CUT_OFF, at=_at(1)
    )
    await refunds.refund(
        game_id, [OLA], reason=RefundReason.CALLED_OFF_AT_THE_CUT_OFF, at=_at(2)
    )
    await session.commit()

    ola_now = await _charges(session).load(olas.charge_id)
    assert ola_now is not None and ola_now.refund_withholds_fee is False
    assert ola_now.refund_decided_at == _at(1)


@pytest.mark.parametrize("implementation", registered(SeatRefunds))
async def test_a_leaver_whose_seat_was_taken_is_given_back_less_the_card_fee(
    implementation, session
):
    """#545: left after the cut-off, refunded only when somebody took the
    seat — and, as before it, less the card fee."""

    refunds: SeatRefunds = implementation.build(session)
    game_id = new_uuid()
    kubas = await _a_paid_share(session, game_id=game_id, player_id=KUBA)

    await refunds.refund(game_id, [KUBA], reason=RefundReason.SEAT_TAKEN, at=_at(1))
    await session.commit()

    kuba_now = await _charges(session).load(kubas.charge_id)
    assert kuba_now is not None and kuba_now.refund_withholds_fee is True


@pytest.mark.parametrize("implementation", registered(SeatRefunds))
async def test_a_game_its_club_cancelled_gives_everybody_everything_back(
    implementation, session
):
    """#547: the club's own rule, so the club bears the fees."""

    refunds: SeatRefunds = implementation.build(session)
    game_id = new_uuid()
    olas = await _a_paid_share(session, game_id=game_id, player_id=OLA)

    await refunds.refund(
        game_id,
        [OLA],
        reason=RefundReason.CANCELLED_BY_THE_CLUB,
        because=ClubCancelReason.WEATHER,
        at=_at(1),
    )
    await session.commit()

    ola_now = await _charges(session).load(olas.charge_id)
    assert ola_now is not None and ola_now.refund_withholds_fee is False


async def _a_held_share(
    session, *, game_id: UUID, player_id: UUID, until: Instant
) -> SeatCharge:
    """A share held for the booked game until ``until``, its cut-off (#637)."""

    charge = SeatCharge.held(
        charge_id=new_uuid(),
        player_id=player_id,
        game_id=game_id,
        club_id=new_uuid(),
        account_id="acct_fake_club",
        payment=Payment(
            payment_id="pi_fake_3000g_y",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=30_00,
        ),
        sport=Sport.PADEL,
        starts_at=until + timedelta(hours=24),
        at=_at(),
    )
    charge.keep(booking_id=game_id, until=until, at=_at())
    await _charges(session).save(charge)
    await session.commit()
    return charge


@pytest.mark.parametrize("implementation", registered(SeatRefunds))
@pytest.mark.parametrize(
    "reason",
    [
        RefundReason.LEFT_BEFORE_THE_CUT_OFF,
        RefundReason.CALLED_OFF_AT_THE_CUT_OFF,
        RefundReason.CANCELLED_BY_THE_CLUB,
    ],
)
async def test_a_share_only_held_is_let_go_and_never_refunded(
    implementation, session, reason
):
    """#637: nothing was taken before the cut-off, so giving the share back
    lets the hold go — nothing to refund, no fee for anybody."""

    refunds: SeatRefunds = implementation.build(session)
    game_id = new_uuid()
    kubas = await _a_held_share(
        session, game_id=game_id, player_id=KUBA, until=_at(4 * 24)
    )

    await refunds.refund(
        game_id,
        [KUBA],
        reason=reason,
        because=(
            ClubCancelReason.WEATHER
            if reason is RefundReason.CANCELLED_BY_THE_CLUB
            else None
        ),
        at=_at(1),
    )
    await session.commit()

    kuba_now = await _charges(session).load(kubas.charge_id)
    assert kuba_now is not None
    assert kuba_now.status is SeatChargeStatus.RELEASING
    assert kuba_now.refund_withholds_fee is None


@pytest.mark.parametrize("implementation", registered(HeldShares))
async def test_the_shares_held_for_a_game_are_due_at_its_cut_off_and_taken_then(
    implementation, session
):
    held: HeldShares = implementation.build(session)
    game_id, later_game = new_uuid(), new_uuid()
    cut_off = _at(4 * 24)
    olas = await _a_held_share(session, game_id=game_id, player_id=OLA, until=cut_off)
    kubas = await _a_held_share(session, game_id=game_id, player_id=KUBA, until=cut_off)
    await _a_held_share(
        session, game_id=later_game, player_id=EWA, until=cut_off + timedelta(hours=1)
    )

    assert await held.due(at=cut_off - timedelta(seconds=1)) == ()
    assert list(await held.due(at=cut_off)) == [game_id]
    assert await held.take(game_id, at=cut_off) == 2
    await session.commit()

    for charge in (olas, kubas):
        now = await _charges(session).load(charge.charge_id)
        assert now is not None and now.status is SeatChargeStatus.TAKING
    assert list(await held.due(at=cut_off + timedelta(hours=1))) == [later_game]
    assert await held.take(game_id, at=cut_off) == 0


@pytest.mark.parametrize("implementation", registered(CardFees))
def test_the_card_fee_on_a_share_is_the_provider_s_standard_price(implementation):
    fees: CardFees = implementation.build(None)

    # The mechanics §12.3: about 1,60 zł on a 40 zł share.
    assert fees.card_fee_on(40_00) == 1_60
    assert fees.card_fee_on(30_00) == 1_45


# --------------------------------------------------------------------------- #
# PlayerFit — whether two people may share a court, and a player's window
# --------------------------------------------------------------------------- #


async def _rated(client, session_factory, name: str, *, mu: float, **profile) -> UUID:
    player_id, token = await players.register(client, name)
    await players.commit_profile(client, token, **profile)
    await players.rate_in(session_factory, player_id, Sport.PADEL, mu=mu)
    return player_id


@pytest.mark.parametrize("implementation", registered(PlayerFit))
async def test_two_people_fit_by_the_matchers_own_pair_rule(
    implementation, client, session_factory, session
):
    """Levels inside the kind's window fit; a gap past it, a preference that
    excludes, and somebody unrated in the sport do not."""

    ola = await _rated(client, session_factory, "ola", mu=2.5)
    ewa = await _rated(client, session_factory, "ewa", mu=2.9)
    far = await _rated(client, session_factory, "zosia", mu=3.4)
    picky = await _rated(
        client, session_factory, "ania", mu=2.5, gender_preference="MEN_ONLY"
    )
    unrated, token = await players.register(client, "kuba")
    await players.commit_profile(client, token)
    fit: PlayerFit = implementation.build(session)

    unfit = await fit.unfit_pairs(
        [ola, ewa, far, picky, unrated],
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        at=_at(),
    )

    assert frozenset((ola, ewa)) not in unfit
    assert frozenset((ola, far)) in unfit
    assert frozenset((ola, picky)) in unfit
    assert frozenset((ola, unrated)) in unfit


@pytest.mark.parametrize("implementation", registered(PlayerFit))
async def test_a_players_window_is_the_kinds_tolerance_around_their_level(
    implementation, client, session_factory, session
):
    """The competitive window, 0,55 either side, rounded inward — and nothing
    for somebody unrated in the sport (#546)."""

    ola = await _rated(client, session_factory, "ola", mu=2.5)
    unrated, token = await players.register(client, "kuba")
    await players.commit_profile(client, token)
    fit: PlayerFit = implementation.build(session)

    window = await fit.level_window(
        ola, sport=Sport.PADEL, kind=SearchMode.COMPETITIVE, at=_at()
    )
    nothing = await fit.level_window(
        unrated, sport=Sport.PADEL, kind=SearchMode.COMPETITIVE, at=_at()
    )

    assert window == LevelRange(low=1.95, high=3.05)
    assert nothing is None


@pytest.mark.parametrize("implementation", registered(PlayerFit))
async def test_a_players_window_narrows_to_the_competitive_one_while_they_are_new(
    implementation, client, session_factory, session
):
    """For fun is 0,9 either side once settled, and the competitive 0,55 while
    the player is new — the pair gate's own rule (``docs/adr/0113``)."""

    ola = await _rated(client, session_factory, "ola", mu=2.5)
    fit: PlayerFit = implementation.build(session)
    today = instant(build_clock().now())

    new = await fit.level_window(
        ola, sport=Sport.PADEL, kind=SearchMode.FOR_FUN, at=today
    )
    settled = await fit.level_window(
        ola, sport=Sport.PADEL, kind=SearchMode.FOR_FUN, at=today + timedelta(days=60)
    )

    assert new == LevelRange(low=1.95, high=3.05)
    assert settled == LevelRange(low=1.6, high=3.4)


# --------------------------------------------------------------------------- #
# PlayersInPlay — a member's Level, week, gender and preference
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(PlayersInPlay))
async def test_a_member_in_play_is_their_level_week_gender_and_preference(
    implementation, client, session_factory, session
):
    ola = await _rated(
        client,
        session_factory,
        "ola",
        mu=2.75,
        gender="MAN",
        gender_preference="ANY",
        weekly_hours=[{"day": 6, "hour": 18}],
    )
    nobody = new_uuid()
    players: PlayersInPlay = implementation.build(session)

    read = await players.of([ola, nobody], sport=Sport.PADEL)

    assert read[ola].level is not None and read[ola].level.mu == 2.75
    assert read[ola].week == WeeklyHours.of_cells([(6, 18)])
    assert (read[ola].gender, read[ola].preference) == (
        Gender.MAN,
        GenderPreference.ANY,
    )
    assert read[nobody].level is None
    assert read[nobody].week == WeeklyHours.blank()
    assert (read[nobody].gender, read[nobody].preference) == (None, None)



# --------------------------------------------------------------------------- #
# The club runs its bookings (#547)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ClubBookings))
async def test_a_club_s_day_is_its_bookings_and_its_cancel_says_whom_it_owes(
    implementation, session
):
    club: ClubBookings = implementation.build(session)
    start = _at(5 * 24)
    booking = await _booked_with_its_game(session, start=start)
    day_opens, day_closes = start - timedelta(hours=1), start + timedelta(hours=14)

    [game] = await club.on_day(booking.club_id, start=day_opens, end=day_closes)
    assert game.booking_id == booking.booking_id
    assert await club.on_day(new_uuid(), start=day_opens, end=day_closes) == []
    # No club sells this court, so it is no court to move to.
    assert await club.free_courts(booking.booking_id) == []
    assert await club.move(booking.booking_id, new_uuid(), at=_at(1)) is None

    cut_off = start - timedelta(hours=24)
    changes: BookedGameChanges = registered_build(BookedGameChanges, session)
    await changes.leave(booking.booking_id, KUBA, at=cut_off + timedelta(hours=1))
    cancelled = await club.cancel(
        booking.booking_id,
        because=ClubCancelReason.REPAIR,
        at=cut_off + timedelta(hours=2),
    )
    await session.commit()

    assert cancelled.still_in == (OLA, EWA, TOMEK)
    assert set(cancelled.refunded) == {OLA, KUBA, EWA, TOMEK}
    [after] = await club.on_day(booking.club_id, start=day_opens, end=day_closes)
    assert after.cancel_reason is ClubCancelReason.REPAIR


@pytest.mark.parametrize("implementation", registered(ClubBookings))
async def test_a_code_is_placed_at_its_club_and_day_and_checked_in(
    implementation, session
):
    from app.bootstrap.composition import build_check_in_codes
    from app.core.config import get_settings

    club: ClubBookings = implementation.build(session)
    start = _at(5 * 24)
    booking = await _booked_with_its_game(session, start=start)
    code = build_check_in_codes(get_settings()).code_for(booking.booking_id, EWA)
    on_the_day = start - timedelta(minutes=10)

    here = await club.seat_for(code.short_code, club_id=booking.club_id, now=on_the_day)
    scanned = await club.seat_for(code.qr_payload, club_id=new_uuid(), now=on_the_day)
    early = await club.seat_for(
        code.short_code, club_id=booking.club_id, now=_at(1)
    )
    nobody = await club.seat_for("ZZZZZZ", club_id=booking.club_id, now=on_the_day)

    assert (here.where, here.booking_id, here.player_id) == (
        CodeAtTheDesk.HERE_TODAY,
        booking.booking_id,
        EWA,
    )
    assert scanned.where is CodeAtTheDesk.ANOTHER_CLUB
    assert early.where is CodeAtTheDesk.ANOTHER_DAY
    assert nobody.where is CodeAtTheDesk.UNKNOWN
    await club.check_in(booking.booking_id, EWA, at=on_the_day)
    await session.commit()
    [game] = await club.on_day(
        booking.club_id,
        start=start - timedelta(hours=1),
        end=start + timedelta(hours=1),
    )
    assert game.checked_in == {EWA: on_the_day}


@pytest.mark.parametrize("implementation", registered(BookingTakings))
async def test_a_booking_s_takings_are_what_was_paid_and_given_back(
    implementation, session
):
    takings: BookingTakings = implementation.build(session)
    game_id = new_uuid()
    await _a_paid_share(session, game_id=game_id, player_id=OLA)
    kubas = await _a_paid_share(session, game_id=game_id, player_id=KUBA)
    charges = _charges(session)
    kuba_now = await charges.load(kubas.charge_id)
    assert kuba_now is not None and kuba_now.refund(withhold_fee=False, at=_at(1))
    await charges.save(kuba_now)
    await session.commit()

    found = await takings.of([game_id, new_uuid()])

    assert list(found) == [game_id]
    assert found[game_id].paid == frozenset({OLA, KUBA})
    assert (found[game_id].collected_grosze, found[game_id].refunded_grosze) == (
        60_00,
        30_00,
    )


@pytest.mark.parametrize("implementation", registered(PoolOrigins))
async def test_a_pool_is_the_group_it_is_filed_under(
    implementation, client, session, payments
):
    from tests.api.proposals_world import a_group, a_player

    club_id, _ = await club_signs_up(client, name="Bonarka Arena", email="d@b.pl")
    owner = await a_player(client, payments, "ola", card=False)
    group_id = await a_group(client, owner, club_id)
    origins: PoolOrigins = implementation.build(session)

    found = await origins.of([group_id, new_uuid()])

    assert list(found) == [group_id]
    assert (found[group_id].name, found[group_id].official) == ("Sobotni padel", False)


@pytest.mark.parametrize("implementation", registered(DeskCheckIns))
async def test_a_club_checks_its_players_in_only_once_it_says_so(
    implementation, client, session
):
    from tests.api.proposals_world import a_club_and_its_desk

    checking, _ = await a_club_and_its_desk(client, check_in=True)
    silent, _ = await club_signs_up(client, name="Ogrody 33", email="d@o.pl")
    settings: DeskCheckIns = implementation.build(session)

    assert await settings.checks_players_in(UUID(checking)) is True
    assert await settings.checks_players_in(UUID(silent)) is False
