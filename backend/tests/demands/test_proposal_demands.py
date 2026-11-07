"""What ``proposals`` demands of the rest of the platform for Home and a game's
details (#542), leaving and the cut-off (#544), rescues (#545), posting (#546)
and the club running its bookings (#547), run against every registered
implementation.

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
from app.modules.payments.domain.seat_charge import (
    FailureReason,
    SeatCharge,
    SeatChargeStatus,
)
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score, SetScore
from app.modules.proposals.domain.club_bookings import (
    ClubCancellation,
    CourtToMoveTo,
)
from app.modules.proposals.domain.home import ResultStage
from app.modules.proposals.domain.home import ClubCancelReason, LateRefund
from app.modules.friends.domain.relation import FriendRelation
from app.modules.proposals.domain.ports import (
    FriendRequestsOnHome,
    ReaderRelations,
    PaymentRefusal,
    RefusedPayment,
    BookedGameChanges,
    BookingTakings,
    CourtHours,
    CourtKinds,
    LateRefunds,
    ClubBookings,
    ClubDistances,
    GameResults,
    CardsToFix,
    CheckedShares,
    HeldShares,
    HoldingTimes,
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
from app.modules.proposals.domain.proposal import TimeTo
from app.shared.ids import new_uuid
from tests.api import players_world as players
from tests.api.administration_world import club_signs_up
from tests.api.club_courts_world import adds_a_court, court_path, sets_hours
from tests.api.proposals_world import (
    SATURDAY_FIVE,
    a_club_and_its_desk,
    every_hour_of_the_week,
)
from tests.api.reliability_world import NEW_AT_50, SERGIO_AT_65, a_history
from tests.demands import friends_world

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
        court=BookedCourt(court_id=new_uuid(), name=court, indoor=True),
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
    never one whose seat they left."""

    older = await _booked(session, start=_at(48))
    await _booked(session, start=_at(120))
    await _booked(session, start=_at(49), left_by=EWA)
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


async def _booked_with_its_game(
    session,
    *,
    start: Instant,
    club_id: UUID | None = None,
    court: BookedCourt | None = None,
) -> Booking:
    """A booking, and the ordinary Game it opened — as the fill makes both. At
    a club nobody sells, unless told which club and court."""

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
        club_id=new_uuid() if club_id is None else club_id,
        court=(
            BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True)
            if court is None
            else court
        ),
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


@pytest.mark.parametrize("implementation", registered(BookedGameChanges))
async def test_a_refused_holding_s_card_is_fixed_in_time_or_its_seat_opens(
    implementation, session
):
    """#639: a player whose holding was refused keeps their seat on the booked
    game until their time to fix the card ends; fixed, it is simply theirs;
    run out, it opens as a leaver's."""

    changes: BookedGameChanges = implementation.build(session)
    start = _at(5 * 24)
    booking = await _booked_with_its_game(session, start=start)
    fix_by = _at(1) + timedelta(minutes=30)
    for player in (KUBA, EWA):
        await changes.card_to_fix(
            booking.booking_id,
            player,
            until=fix_by,
            refused=RefusedPayment(
                seat_charge_id=new_uuid(), refusal=PaymentRefusal.DECLINED
            ),
            at=_at(1),
        )
    await session.commit()

    assert set(await changes.cards_to_fix_of(KUBA)) == {booking.booking_id}
    assert await changes.cards_to_fix_past(now=fix_by - timedelta(seconds=1)) == ()
    assert list(await changes.cards_to_fix_past(now=fix_by)) == [booking.booking_id]
    assert await changes.card_fixed(booking.booking_id, KUBA, at=_at(1))
    assert not await changes.card_not_fixed(booking.booking_id, EWA, at=_at(1))
    assert await changes.card_not_fixed(booking.booking_id, EWA, at=fix_by)
    await session.commit()

    assert await changes.cards_to_fix_of(KUBA) == ()
    assert await changes.cards_to_fix_past(now=fix_by) == ()
    game = await registered_build(PlayerBookings, session).find(booking.booking_id)
    assert game is not None
    assert game.leavers == frozenset({EWA}) and game.cards_to_fix == {}


@pytest.mark.parametrize("implementation", registered(BookedGameChanges))
async def test_a_refused_rescuer_s_kept_seat_is_taken_or_runs_out_once(
    implementation, session
):
    """#640: a seat kept for a refused rescuer is theirs until their time
    ends — read off the clock, the rest offered to anybody — taken once they
    pay; run out, it is offered again and never kept for them again, its
    refused payment still known while the game is theirs to take."""

    changes: BookedGameChanges = implementation.build(session)
    bookings = registered_build(PlayerBookings, session)
    start = _at(5 * 24)
    booking = await _booked_with_its_game(session, start=start)
    zosia, marek = new_uuid(), new_uuid()
    await changes.leave(booking.booking_id, EWA, at=_at(1))
    await changes.leave(booking.booking_id, KUBA, at=_at(1))
    until = _at(2) + timedelta(minutes=30)
    for player in (zosia, marek):
        await changes.keep_the_seat(
            booking.booking_id,
            player,
            until=until,
            refused=RefusedPayment(
                seat_charge_id=new_uuid(), refusal=PaymentRefusal.DECLINED
            ),
            time_to=TimeTo.FIX_THE_CARD,
            at=_at(2),
        )
    await session.commit()

    assert list(await changes.kept_for(zosia)) == [booking.booking_id]
    assert await changes.keeps_past(now=until - timedelta(seconds=1)) == ()
    assert list(await changes.keeps_past(now=until)) == [booking.booking_id]
    game = await bookings.find(booking.booking_id)
    assert game is not None
    kept = game.kept_for(zosia, now=_at(2))
    assert kept is not None and (kept.until, kept.time_to) == (
        until,
        TimeTo.FIX_THE_CARD,
    )
    assert game.seats_kept(now=_at(2)) == 2
    assert game.seats_kept(now=_at(2), but=zosia) == 1
    assert game.seats_kept(now=until) == 0

    await changes.rescue(booking.booking_id, zosia, at=_at(2))
    assert not await changes.kept_seat_ran_out(booking.booking_id, marek, at=_at(2))
    assert await changes.kept_seat_ran_out(booking.booking_id, marek, at=until)
    await session.commit()

    assert await changes.kept_for(zosia) == ()
    assert list(await changes.kept_for(marek)) == [booking.booking_id]
    assert await changes.keeps_past(now=until) == ()
    game = await bookings.find(booking.booking_id)
    assert game is not None
    assert set(game.kept) == {marek} and game.keeps_ran_out == frozenset({marek})
    assert game.kept_for(marek, now=until) is None


# --------------------------------------------------------------------------- #
# SeatRefunds and LateRefunds — a paid share given back (#544), and what a
# leaver after the cut-off would get back (#641)
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


async def _a_checked_share(
    session, *, game_id: UUID, player_id: UUID, cut_off: Instant
) -> SeatCharge:
    """A share checked at its game's fill, held again four days before
    ``cut_off`` (#639)."""

    charge = SeatCharge.held(
        charge_id=new_uuid(),
        player_id=player_id,
        game_id=game_id,
        club_id=new_uuid(),
        account_id="acct_fake_club",
        payment=Payment(
            payment_id=f"pi_fake_3000g_{new_uuid().hex[:8]}",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=30_00,
        ),
        sport=Sport.PADEL,
        starts_at=cut_off + timedelta(hours=24),
        at=_at(),
    )
    charge.check(
        booking_id=game_id,
        until=cut_off,
        hold_at=cut_off - timedelta(days=4),
        at=_at(),
    )
    await _charges(session).save(charge)
    await session.commit()
    return charge


@pytest.mark.parametrize("implementation", registered(CheckedShares))
async def test_a_checked_share_is_due_at_its_holding_time(implementation, session):
    checked: CheckedShares = implementation.build(session)
    game_id = new_uuid()
    cut_off = _at(7 * 24)
    await _a_checked_share(session, game_id=game_id, player_id=OLA, cut_off=cut_off)
    holding = cut_off - timedelta(days=4)

    assert await checked.due(at=holding - timedelta(seconds=1)) == ()
    assert list(await checked.due(at=holding)) == [game_id]
    # A game with nothing due holds nothing, and asks nobody.
    nothing = await checked.hold(
        new_uuid(), fix_by=_at(1), fixing_until={}, at=holding
    )
    assert (nothing.held, dict(nothing.refused)) == (frozenset(), {})


@pytest.mark.parametrize("implementation", registered(HoldingTimes))
async def test_a_checked_share_says_when_it_is_held(implementation, session):
    times: HoldingTimes = implementation.build(session)
    checked_game, held_game = new_uuid(), new_uuid()
    cut_off = _at(7 * 24)
    await _a_checked_share(
        session, game_id=checked_game, player_id=OLA, cut_off=cut_off
    )
    await _a_held_share(session, game_id=held_game, player_id=OLA, until=cut_off)

    assert await times.of(OLA, [checked_game, held_game]) == {
        checked_game: cut_off - timedelta(days=4)
    }
    assert await times.of(KUBA, [checked_game]) == {}


@pytest.mark.parametrize("implementation", registered(CardsToFix))
async def test_a_refused_holding_is_kept_once_fixed_or_let_go(implementation, session):
    cards: CardsToFix = implementation.build(session)
    game_id = new_uuid()
    cut_off = _at(7 * 24)
    holding = cut_off - timedelta(days=4)
    olas = await _a_checked_share(
        session, game_id=game_id, player_id=OLA, cut_off=cut_off
    )
    kubas = await _a_checked_share(
        session, game_id=game_id, player_id=KUBA, cut_off=cut_off
    )
    repository = _charges(session)
    for charge in (olas, kubas):
        refused = await repository.load(charge.charge_id)
        assert refused is not None
        refused.holding_refused(
            FailureReason.AUTHENTICATION_REQUIRED,
            payment=Payment(
                payment_id=f"pi_fake_3000g_{new_uuid().hex[:8]}",
                status=PaymentStatus.AUTHENTICATION_REQUIRED,
                amount_grosze=30_00,
            ),
            at=holding,
        )
        await repository.save(refused)
    await session.commit()
    confirmed = await repository.load(olas.charge_id)
    assert confirmed is not None
    confirmed.confirm(at=holding + timedelta(minutes=5))
    await repository.save(confirmed)
    await session.commit()

    assert await cards.keep_fixed(olas.charge_id, at=holding + timedelta(minutes=5))
    await cards.let_go_unfixed(game_id, KUBA, at=holding + timedelta(minutes=30))
    await session.commit()

    ola_now = await _charges(session).load(olas.charge_id)
    kuba_now = await _charges(session).load(kubas.charge_id)
    assert ola_now is not None and ola_now.status is SeatChargeStatus.HELD
    assert kuba_now is not None and kuba_now.status is SeatChargeStatus.RELEASING
    # A share no refused holding: nothing kept.
    assert not await cards.keep_fixed(kubas.charge_id, at=holding)


async def _a_share_taken(
    session, *, game_id: UUID, player_id: UUID, fee_grosze: int | None
) -> SeatCharge:
    charge = SeatCharge.held(
        charge_id=new_uuid(),
        player_id=player_id,
        game_id=game_id,
        club_id=new_uuid(),
        account_id="acct_fake_club",
        payment=Payment(
            payment_id="pi_fake_4000g_x",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=40_00,
        ),
        sport=Sport.PADEL,
        starts_at=_at(5 * 24),
        at=_at(),
    )
    charge.keep(booking_id=game_id, until=_at(4 * 24), at=_at())
    charge.take(booking_id=game_id, at=_at(4 * 24))
    charge.captured(at=_at(4 * 24), fee_grosze=fee_grosze)
    await _charges(session).save(charge)
    await session.commit()
    return charge


@pytest.mark.parametrize("implementation", registered(SeatRefunds))
async def test_a_leaver_after_the_cut_off_is_given_nothing_back_yet(
    implementation, session
):
    """Leaving after the cut-off moves no money (#641): the share stays paid
    until somebody takes the seat — the leaver is only told what would come
    back."""

    refunds: SeatRefunds = implementation.build(session)
    game_id = new_uuid()
    kubas = await _a_share_taken(
        session, game_id=game_id, player_id=KUBA, fee_grosze=1_76
    )

    await refunds.left_after_the_cut_off(game_id, KUBA, at=_at(4 * 24 + 1))
    await session.commit()

    kuba_now = await _charges(session).load(kubas.charge_id)
    assert kuba_now is not None
    assert kuba_now.status is SeatChargeStatus.CAPTURED
    assert kuba_now.refund_withholds_fee is None


@pytest.mark.parametrize("implementation", registered(LateRefunds))
async def test_a_late_leaver_would_get_the_share_less_exactly_the_fee_kept(
    implementation, session
):
    """*If someone takes your seat, you get 38,24 zł back (40 zł less the 1,76
    zł kept on your payment)* — the fee kept on the reader's own payment, never
    an estimate (#641, Q113)."""

    refunds: LateRefunds = implementation.build(session)
    game_id = new_uuid()
    await _a_share_taken(session, game_id=game_id, player_id=KUBA, fee_grosze=1_76)
    await _a_share_taken(session, game_id=game_id, player_id=OLA, fee_grosze=2_30)

    assert await refunds.of(game_id, KUBA) == LateRefund(
        refund_grosze=38_24, fee_kept_grosze=1_76
    )
    assert await refunds.of(game_id, OLA) == LateRefund(
        refund_grosze=37_70, fee_kept_grosze=2_30
    )


@pytest.mark.parametrize("implementation", registered(LateRefunds))
async def test_nothing_is_said_while_the_fee_kept_is_not_yet_known(
    implementation, session
):
    refunds: LateRefunds = implementation.build(session)
    game_id = new_uuid()
    await _a_share_taken(session, game_id=game_id, player_id=KUBA, fee_grosze=None)

    assert await refunds.of(game_id, KUBA) is None
    # Nor for a player with no share taken on the game.
    assert await refunds.of(game_id, OLA) is None


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
async def test_a_reliability_filter_keeps_a_pair_apart_both_ways_and_new_passes(
    implementation, client, session_factory, session
):
    """Marta's *at least High* (#661): Sergio at 65 — Medium, not New — does
    not fit her, whoever is asked about first; Nerea at 50, New, does. A yes
    already given is asked without the filter."""

    marta, token = await players.register(client, "marta")
    await players.commit_profile(client, token)
    await players.rate_in(session_factory, marta, Sport.PADEL, mu=2.5)
    sergio = await _rated(client, session_factory, "sergio", mu=2.5)
    nerea = await _rated(client, session_factory, "nerea", mu=2.5)
    await a_history(session_factory, sergio, SERGIO_AT_65)
    await a_history(session_factory, nerea, NEW_AT_50)
    switched = await client.put(
        "/api/v1/players/me/reliability-filter",
        json={"minimum": "HIGH"},
        headers=players.auth(token),
    )
    assert switched.status_code == 204, switched.text
    fit: PlayerFit = implementation.build(session)
    asked = dict(sport=Sport.PADEL, kind=SearchMode.COMPETITIVE, at=_at())

    unfit = await fit.unfit_pairs([sergio, marta, nerea], **asked)
    given = await fit.unfit_pairs([marta, sergio], **asked, reliability_filter=False)

    assert unfit == {frozenset((marta, sergio))}
    assert given == frozenset()


@pytest.mark.parametrize("implementation", registered(PlayerFit))
async def test_every_kind_over_one_reading_answers_as_each_kind_alone(
    implementation, client, session_factory, session
):
    """A deal asks every kind at once (#661): 2,5 and 3,4 are too far apart
    for a competitive game and close enough for fun, as asking each alone
    says."""

    ola = await _rated(client, session_factory, "ola", mu=2.5)
    far = await _rated(client, session_factory, "zosia", mu=3.3)
    fit: PlayerFit = implementation.build(session)
    people = [ola, far]
    # Two months on, so neither is new and For fun's window is its own.
    settled = instant(build_clock().now()) + timedelta(days=60)

    by_kind = await fit.unfit_pairs_by_kind(
        people, sport=Sport.PADEL, kinds=list(SearchMode), at=settled
    )

    for kind in SearchMode:
        assert by_kind[kind] == await fit.unfit_pairs(
            people, sport=Sport.PADEL, kind=kind, at=settled
        )
    assert by_kind[SearchMode.COMPETITIVE] == {frozenset((ola, far))}
    assert by_kind[SearchMode.FOR_FUN] == frozenset()


@pytest.mark.parametrize("implementation", registered(PlayerFit))
async def test_the_block_mask_alone_is_every_blocked_pair_either_way(
    implementation, client, session_factory, session
):
    """The friends card's question (#750): a block either way round keeps a
    pair apart, and nothing else the pair rule reads does — 2,5 and 3,4 are
    far past the competitive window, and somebody unrated is asked about too."""

    ola = await _rated(client, session_factory, "ola", mu=2.5)
    far = await _rated(client, session_factory, "zosia", mu=3.4)
    ewa = await _rated(client, session_factory, "ewa", mu=2.5)
    unrated, token = await players.register(client, "kuba")
    await players.commit_profile(client, token)
    await friends_world.blocks(session, ewa, ola)
    await friends_world.blocks(session, unrated, far)
    fit: PlayerFit = implementation.build(session)

    blocked = await fit.blocked_pairs([ola, far, ewa, unrated])

    assert blocked == {frozenset((ola, ewa)), frozenset((far, unrated))}
    assert await fit.blocked_pairs([ola, far]) == frozenset()
    assert await fit.blocked_pairs([ola]) == frozenset()


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
    # No court absorbs the cancel: it calls the game off (#672).
    assert (
        await club.absorbing_court(booking.booking_id, because=ClubCancelReason.REPAIR)
        is None
    )
    cancelled = await club.cancel(
        booking.booking_id,
        because=ClubCancelReason.REPAIR,
        anyway=False,
        at=cut_off + timedelta(hours=2),
    )
    await session.commit()

    assert isinstance(cancelled, ClubCancellation)
    assert cancelled.still_in == (OLA, EWA, TOMEK)
    assert set(cancelled.refunded) == {OLA, KUBA, EWA, TOMEK}
    [after] = await club.on_day(booking.club_id, start=day_opens, end=day_closes)
    assert after.cancel_reason is ClubCancelReason.REPAIR


@pytest.mark.parametrize("implementation", registered(ClubBookings))
async def test_a_club_s_cancel_a_free_court_absorbs_moves_the_game(
    implementation, client, session
):
    """#672 (Q122): Court 3, indoor like Court 1 and sold at the game's share,
    absorbs a cancel — the preview names it, and the cancel moves the game
    there, owing nobody anything; *anyway* calls the game off all the same."""

    club_id, desk = await a_club_and_its_desk(client)
    courts = (await client.get("/api/v1/club/courts", headers=desk)).json()["courts"]
    court_1 = next(one for one in courts if one["name"] == "Court 1")
    court_3 = await adds_a_court(client, desk, name="Court 3", sport="PADEL")
    await sets_hours(client, desk, [court_3["id"]], every_hour_of_the_week())
    booking = await _booked_with_its_game(
        session,
        start=instant(SATURDAY_FIVE),
        club_id=UUID(club_id),
        court=BookedCourt(court_id=UUID(court_1["id"]), name="Court 1", indoor=True),
    )
    club: ClubBookings = implementation.build(session)
    to_court_3 = CourtToMoveTo(
        court_id=UUID(court_3["id"]), name="Court 3", indoor=True
    )

    assert (
        await club.absorbing_court(booking.booking_id, because=ClubCancelReason.WEATHER)
        == to_court_3
    )
    moved = await club.cancel(
        booking.booking_id,
        because=ClubCancelReason.WEATHER,
        anyway=False,
        at=_at(1),
    )
    await session.commit()

    assert moved == to_court_3
    [game] = await club.on_day(
        booking.club_id,
        start=SATURDAY_FIVE - timedelta(hours=1),
        end=SATURDAY_FIVE + timedelta(hours=1),
    )
    assert (game.court_name, game.cancel_reason) == ("Court 3", None)
    # Court 1 is free again and would take it; *anyway* calls it off all the
    # same.
    cancelled = await club.cancel(
        booking.booking_id,
        because=ClubCancelReason.OTHER,
        anyway=True,
        at=_at(2),
    )
    await session.commit()
    assert isinstance(cancelled, ClubCancellation)
    assert cancelled.still_in == (OLA, KUBA, EWA, TOMEK)


@pytest.mark.parametrize("implementation", registered(CourtKinds))
async def test_the_kind_of_court_a_card_promises_is_certain_or_nothing(
    implementation, client, session
):
    """#671 (Q122): indoor or outdoor when every free court of the sport at the
    club and hour is of that kind; absent when they are mixed, and where no
    court is held."""

    club_id, desk = await a_club_and_its_desk(client)
    kinds: CourtKinds = implementation.build(session)
    padel = (UUID(club_id), Sport.PADEL, SATURDAY_FIVE)
    squash = (UUID(club_id), Sport.SQUASH, SATURDAY_FIVE)
    nowhere = (new_uuid(), Sport.PADEL, SATURDAY_FIVE)

    assert await kinds.of([padel, squash, nowhere]) == {padel: True}
    assert await kinds.of([]) == {}

    outdoor = await adds_a_court(
        client, desk, name="Court 4", sport="PADEL", indoor=False
    )
    await sets_hours(client, desk, [outdoor["id"]], every_hour_of_the_week())
    assert await kinds.of([padel]) == {}

    courts = (await client.get("/api/v1/club/courts", headers=desk)).json()["courts"]
    court_1 = next(one for one in courts if one["name"] == "Court 1")
    off = await client.put(
        court_path(court_1["id"]),
        json={"name": "Court 1", "sport": "PADEL", "indoor": True, "offered": False},
        headers=desk,
    )
    assert off.status_code == 200, off.text
    assert await kinds.of([padel]) == {padel: False}


@pytest.mark.parametrize("implementation", registered(CourtHours))
async def test_every_hour_a_club_sells_counts_and_names_its_free_courts_in_order(
    implementation, client, session
):
    """One row per club, sport and hour, its courts counted — and, for the
    friends card (#750), named in the club's own order, the first being the
    one a booking then is given. A court the desk takes off Raketa is neither."""

    club_id, desk = await a_club_and_its_desk(client)
    outdoor = await adds_a_court(
        client, desk, name="Court 3", sport="PADEL", indoor=False
    )
    await sets_hours(client, desk, [outdoor["id"]], every_hour_of_the_week())
    hours: CourtHours = implementation.build(session)
    asked = dict(start=SATURDAY_FIVE, end=SATURDAY_FIVE + timedelta(hours=1), now=_at())

    padel, tennis = sorted(
        await hours.on_sale([UUID(club_id), new_uuid()], **asked),
        key=lambda hour: hour.sport.value,
    )

    assert (padel.club_id, padel.sport, padel.start) == (
        UUID(club_id),
        Sport.PADEL,
        SATURDAY_FIVE,
    )
    assert padel.courts == 2
    assert [(court.name, court.indoor) for court in padel.free] == [
        ("Court 1", True),
        ("Court 3", False),
    ]
    assert padel.free[1].court_id == UUID(outdoor["id"])
    assert [court.name for court in tennis.free] == ["Court 2"]

    taken_off = await client.put(
        court_path(outdoor["id"]),
        json={"name": "Court 3", "sport": "PADEL", "indoor": False, "offered": False},
        headers=desk,
    )
    assert taken_off.status_code == 200, taken_off.text
    [padel] = [
        hour
        for hour in await hours.on_sale([UUID(club_id)], **asked)
        if hour.sport is Sport.PADEL
    ]
    assert (padel.courts, [court.name for court in padel.free]) == (1, ["Court 1"])


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
    # Neither share's fee was said on its capture: not yet known, never an
    # estimate (#641) — and so neither is what is the club's.
    assert (found[game_id].card_fees_grosze, found[game_id].net_grosze) == (None, None)


@pytest.mark.parametrize("implementation", registered(BookingTakings))
async def test_a_booking_s_card_fees_are_the_ones_the_provider_kept(
    implementation, session
):
    takings: BookingTakings = implementation.build(session)
    game_id = new_uuid()
    await _a_share_taken(session, game_id=game_id, player_id=OLA, fee_grosze=1_76)
    await _a_share_taken(session, game_id=game_id, player_id=KUBA, fee_grosze=2_30)

    found = (await takings.of([game_id]))[game_id]

    assert (found.collected_grosze, found.card_fees_grosze, found.net_grosze) == (
        80_00,
        4_06,
        75_94,
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


# --------------------------------------------------------------------------- #
# ReaderRelations and FriendRequestsOnHome — the faces' tag and Home's row
# (#745). What Home draws of a card is driven whole over HTTP in
# ``tests/api/test_friends_on_every_face.py``: a card needs a named account,
# which this suite's arrangements do not make.
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(ReaderRelations))
async def test_only_the_readers_own_relations_are_answered(implementation, session):
    from tests.demands.friends_world import asks, befriends

    reader, friend, asked, asker, stranger = (new_uuid() for _ in range(5))
    await befriends(session, reader, friend)
    await asks(session, reader, asked)
    await asks(session, asker, reader)
    await befriends(session, friend, stranger)
    relations: ReaderRelations = implementation.build(session)

    everyone = [reader, friend, asked, asker, stranger]
    assert await relations.friends_among(reader, everyone) == frozenset({friend})
    assert await relations.relations_of(reader, everyone) == {
        reader: FriendRelation.NONE,
        friend: FriendRelation.FRIEND,
        asked: FriendRelation.SENT,
        asker: FriendRelation.ASKED_YOU,
        stranger: FriendRelation.NONE,
    }


@pytest.mark.parametrize("implementation", registered(ReaderRelations))
async def test_a_request_from_somebody_the_reader_blocked_reads_none(
    implementation, session
):
    from tests.demands.friends_world import asks, blocks

    reader, blocked = new_uuid(), new_uuid()
    await blocks(session, reader, blocked)
    await asks(session, blocked, reader)
    relations: ReaderRelations = implementation.build(session)

    assert (await relations.relations_of(reader, [blocked]))[blocked] is (
        FriendRelation.NONE
    )
    assert (await relations.relations_of(blocked, [reader]))[reader] is (
        FriendRelation.SENT
    )


@pytest.mark.parametrize("implementation", registered(FriendRequestsOnHome))
async def test_nobody_asked_and_nobody_nameable_draw_no_card(implementation, session):
    from tests.demands.friends_world import asks

    reader, unnamed = new_uuid(), new_uuid()
    requests: FriendRequestsOnHome = implementation.build(session)
    assert await requests.of(reader) == ()

    await asks(session, unnamed, reader)

    assert await requests.of(reader) == ()
