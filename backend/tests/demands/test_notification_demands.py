"""What ``notifications`` demands of other contexts (#549), run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident**
(``docs/adr/0098``). Every implementation registered in
``app/bootstrap/notification_demands.py`` is enrolled here automatically.
**Every game is arranged through its aggregates** — a Proposal, a Booking, a
Seat charge — saved by their own repositories, never an ``INSERT``.
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
    build_group_repository,
    build_proposal_repository,
    build_seat_charge_repository,
)
from app.bootstrap.notification_demands import (
    NOTIFICATION_DEMANDS,
    NOTIFICATION_IMPLEMENTATIONS,
    implementations_of,
)
from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.bookings.domain.booking import BookedCourt, Booking, CancelReason
from app.modules.games.domain.attendance import ClubVerdict
from app.modules.games.domain.game import Game
from app.modules.games.domain.lineup import GameKind, GameSide, LineUp, Seating
from app.modules.games.domain.results import Score
from app.modules.notifications.domain.ports import (
    GameCourts,
    Decks,
    EndedHours,
    GameBriefs,
    GroupJoiners,
    Names,
    PaidShares,
    RatedAccounts,
    SeatOffers,
)
from app.modules.groups.domain.group import Group, JoinPolicy
from app.modules.groups.domain.value_objects import GroupCode, GroupName
from app.modules.payments.domain.provider import (
    Payment,
    PaymentStatus,
    Refund,
    RefundStatus,
)
from app.modules.payments.domain.seat_charge import RefundReason, SeatCharge
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.proposal import (
    Origin,
    Proposal,
    ReopenReason,
    TimeTo,
)
from app.shared.ids import new_uuid
from tests.api.club_courts_world import adds_a_court, sets_hours
from tests.api.proposals_world import a_club_and_its_desk, every_hour_of_the_week
from tests.demands.test_player_record_demands import _a_club, _a_rating

OLA, KUBA, EWA, TOMEK, ZOSIA = (new_uuid() for _ in range(5))
NOW = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
START = NOW + timedelta(days=5)


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


def _store(session):
    return {
        "event_store": build_domain_event_store(session),
        "events": build_event_publisher(session),
    }


async def _a_proposal(
    session, *, poster: UUID | None = None, club_id: UUID | None = None
) -> Proposal:
    proposal = Proposal.make(
        proposal_id=new_uuid(),
        pool=Pool(id=new_uuid(), kind=PoolKind.GROUP),
        origin=Origin.POST if poster else Origin.PICK,
        poster_id=poster,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=club_id or new_uuid(),
        start=START,
        share_grosze=30_00,
        book_by=START - timedelta(hours=2),
        at=NOW,
    )
    proposal.deal([p for p in (OLA, KUBA, EWA, TOMEK) if p != poster], at=NOW)
    return proposal


async def _saved(session, proposal: Proposal) -> Proposal:
    await build_proposal_repository(session, **_store(session)).save(proposal)
    await session.commit()
    return proposal


def _booked(proposal: Proposal, *, at: Instant) -> Booking:
    return Booking.confirmed(
        booking_id=proposal.proposal_id,
        pool_id=proposal.pool.id,
        club_id=proposal.club_id,
        court=BookedCourt(court_id=new_uuid(), name="Court 1", indoor=True),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=START,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=START - timedelta(hours=24),
        game_id=new_uuid(),
        at=at,
    )


# --------------------------------------------------------------------------- #
# The register itself
# --------------------------------------------------------------------------- #


def test_every_demand_has_at_least_one_implementation():
    assert [p.__name__ for p in NOTIFICATION_DEMANDS if not implementations_of(p)] == []


def test_every_registered_implementation_is_of_a_demand():
    assert all(one.port in NOTIFICATION_DEMANDS for one in NOTIFICATION_IMPLEMENTATIONS)


# --------------------------------------------------------------------------- #
# GameBriefs — a game as it stands
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_game_still_filling_is_its_people_in_and_its_seats_open(
    implementation, session
):
    games: GameBriefs = implementation.build(session)
    proposal = await _a_proposal(session)
    proposal.say_yes(OLA, at=NOW)
    proposal.say_yes(KUBA, at=NOW)
    proposal.withdraw_yes(KUBA, at=NOW)
    proposal.say_yes(EWA, at=NOW)
    await _saved(session, proposal)

    brief = await games.about(proposal.proposal_id, at=NOW)

    assert brief is not None
    assert (brief.filling, brief.booked) == (True, False)
    assert (brief.in_, brief.withdrawn, brief.open_seats) == ((OLA, EWA), (KUBA,), 2)
    assert (brief.undecided, brief.named) == ((TOMEK,), (TOMEK,))
    assert (brief.share_grosze, brief.posted_by, brief.starts_at) == (
        30_00,
        None,
        START,
    )


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_next_best_fit_dealt_after_a_no_is_undecided_and_never_named(
    implementation, session
):
    games: GameBriefs = implementation.build(session)
    proposal = await _a_proposal(session)
    proposal.say_no(TOMEK, at=NOW)
    proposal.deal([ZOSIA], at=NOW, into=1)
    await _saved(session, proposal)

    brief = await games.about(proposal.proposal_id, at=NOW)

    assert brief is not None
    assert set(brief.undecided) == {OLA, KUBA, EWA, ZOSIA}
    assert set(brief.named) == {OLA, KUBA, EWA}


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_game_past_its_book_by_is_filling_no_more(implementation, session):
    games: GameBriefs = implementation.build(session)
    proposal = await _saved(session, await _a_proposal(session, poster=OLA))

    brief = await games.about(proposal.proposal_id, at=START - timedelta(hours=1))

    assert brief is not None
    assert (brief.filling, brief.posted_by, brief.in_) == (False, OLA, (OLA,))


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_booked_game_is_who_holds_a_seat_and_who_took_one(
    implementation, session
):
    games: GameBriefs = implementation.build(session)
    proposal = await _saved(session, await _a_proposal(session))
    booking = _booked(proposal, at=NOW)
    booking.leave(KUBA, at=NOW + timedelta(hours=1))
    booking.rescue(ZOSIA, at=NOW + timedelta(hours=2))
    await build_booking_repository(session, **_store(session)).save(booking)
    await session.commit()

    brief = await games.about(proposal.proposal_id, at=NOW + timedelta(hours=3))

    assert brief is not None
    assert (brief.booked, brief.cancel_reason) == (True, None)
    assert set(brief.seated) == {OLA, EWA, TOMEK, ZOSIA}
    assert brief.seats_taken == {KUBA: ZOSIA}


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_booked_game_says_whose_own_yes_filled_it(implementation, session):
    games: GameBriefs = implementation.build(session)
    filled = await _a_proposal(session)
    for player in (OLA, KUBA, EWA, TOMEK):
        filled.say_yes(player, at=NOW)
    filled.fill(first_side=(OLA, KUBA), second_side=(EWA, TOMEK), by=TOMEK, at=NOW)
    await _saved(session, filled)
    by_nobody = await _a_proposal(session)
    for player in (OLA, KUBA, EWA, TOMEK):
        by_nobody.say_yes(player, at=NOW)
    by_nobody.fill(first_side=(OLA, KUBA), second_side=(EWA, TOMEK), by=None, at=NOW)
    await _saved(session, by_nobody)
    still_filling = await _saved(session, await _a_proposal(session))

    later = NOW + timedelta(hours=1)
    assert (await games.about(filled.proposal_id, at=later)).filled_by == TOMEK
    assert (await games.about(by_nobody.proposal_id, at=later)).filled_by is None
    assert (await games.about(still_filling.proposal_id, at=later)).filled_by is None


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_game_the_club_cancelled_says_why(implementation, session):
    games: GameBriefs = implementation.build(session)
    proposal = await _saved(session, await _a_proposal(session))
    booking = _booked(proposal, at=NOW)
    booking.cancel(CancelReason.REPAIR, at=NOW + timedelta(hours=1))
    await build_booking_repository(session, **_store(session)).save(booking)
    await session.commit()

    brief = await games.about(proposal.proposal_id, at=NOW + timedelta(hours=2))

    assert brief is not None
    assert (brief.booked, brief.cancel_reason) == (False, "REPAIR")


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_full_game_gone_back_to_filling_says_since_when(
    implementation, session
):
    """Kuba left while the game waited for Tomek's payment: it is filling
    again (Q106), Tomek's time running on."""

    games: GameBriefs = implementation.build(session)
    proposal = await _a_proposal(session)
    for player in (OLA, KUBA, EWA, TOMEK):
        proposal.say_yes(player, at=NOW)
    proposal.give_time_to_pay(
        TOMEK,
        reason=ReopenReason.AUTHENTICATION_REQUIRED,
        seat_charge_id=new_uuid(),
        until=NOW + timedelta(minutes=30),
        time_to=TimeTo.FIX_THE_CARD,
        filled_by=TOMEK,
        at=NOW,
    )
    proposal.withdraw_yes(KUBA, at=NOW + timedelta(minutes=5))
    await _saved(session, proposal)
    later = NOW + timedelta(minutes=10)

    brief = await games.about(proposal.proposal_id, at=later)

    assert brief is not None
    assert (brief.fell_back, brief.fell_back_at) == (True, NOW + timedelta(minutes=5))
    assert (brief.filling, brief.book_by) == (True, START - timedelta(hours=2))
    assert brief.in_ == (OLA, EWA, TOMEK)
    assert brief.waiting_for_a_payment is False
    booked = await _saved(session, await _a_proposal(session))
    await build_booking_repository(session, **_store(session)).save(
        _booked(booked, at=NOW)
    )
    await session.commit()
    assert (await games.about(booked.proposal_id, at=later)).fell_back is False


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_game_waiting_for_a_payment_says_whose_and_until_when(
    implementation, session
):
    """Tomek's share was refused as the game filled (#625): it waits for his
    payment until then — and, out of time, has fallen back to filling, the
    moment said; booked on a payment in time, it says so (Q110)."""

    games: GameBriefs = implementation.build(session)
    pay_by = NOW + timedelta(minutes=30)
    waiting = await _a_proposal(session)
    paid = await _a_proposal(session)
    for proposal in (waiting, paid):
        for player in (OLA, KUBA, EWA, TOMEK):
            proposal.say_yes(player, at=NOW)
        proposal.give_time_to_pay(
            TOMEK,
            reason=ReopenReason.AUTHENTICATION_REQUIRED,
            seat_charge_id=new_uuid(),
            until=pay_by,
            time_to=TimeTo.FIX_THE_CARD,
            filled_by=TOMEK,
            at=NOW,
        )
    paid.fill(first_side=(OLA, KUBA), second_side=(EWA, TOMEK), by=TOMEK, at=NOW)
    await _saved(session, waiting)
    await _saved(session, paid)

    brief = await games.about(waiting.proposal_id, at=NOW + timedelta(minutes=5))
    booked = await games.about(paid.proposal_id, at=NOW + timedelta(minutes=5))

    assert brief is not None and booked is not None
    assert (brief.waiting_for_a_payment, brief.paying) == (True, {TOMEK: pay_by})
    # His time is to fix his card (#638).
    assert brief.fixing == {TOMEK}
    assert brief.fell_back is False
    assert (booked.booked_on_a_payment, booked.paying) == (True, {})
    assert booked.fixing == frozenset()
    proposals = build_proposal_repository(session, **_store(session))
    lapsing = await proposals.load(waiting.proposal_id)
    assert lapsing is not None and lapsing.run_out_of_time(at=pay_by) == (TOMEK,)
    await proposals.save(lapsing)
    await session.commit()
    ran_out = await games.about(waiting.proposal_id, at=pay_by)
    assert ran_out is not None
    assert (ran_out.waiting_for_a_payment, ran_out.fell_back_at) == (False, pay_by)
    assert ran_out.in_ == (OLA, KUBA, EWA)


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_game_called_off_at_its_cut_off_names_whose_empty_seat_did_it(
    implementation, session
):
    """Kuba and Ewa left before the cut-off; Zosia took the seat that opened
    first, Kuba's. Ewa's empty seat called it off."""

    games: GameBriefs = implementation.build(session)
    proposal = await _saved(session, await _a_proposal(session))
    booking = _booked(proposal, at=NOW)
    booking.leave(KUBA, at=NOW + timedelta(hours=1))
    booking.leave(EWA, at=NOW + timedelta(hours=2))
    booking.rescue(ZOSIA, at=NOW + timedelta(hours=3))
    cut_off = START - timedelta(hours=24)
    booking.call_off_at_the_cut_off(at=cut_off)
    await build_booking_repository(session, **_store(session)).save(booking)
    await session.commit()

    brief = await games.about(proposal.proposal_id, at=cut_off)

    assert brief is not None
    assert brief.left_it_short == (EWA,)


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_no_such_game_is_nothing(implementation, session):
    games: GameBriefs = implementation.build(session)

    assert await games.about(new_uuid(), at=NOW) is None


# --------------------------------------------------------------------------- #
# GameCourts — a booked game's court, and what it waits on (#663)
# --------------------------------------------------------------------------- #

#: At the club, as an attendance tap's verdict hands it to the Game.
HERE = ClubVerdict(at_the_club=True, club_name="Bonarka Arena")


async def _a_court(
    session, *, kind: GameKind = GameKind.COUNTED, act=lambda game: None
) -> Game:
    """Ola and Kuba against Ewa and Tomek on Saturday at 17:00, opened for a
    booking — and whatever ``act`` does to it, through the Game's own acts."""

    game = Game.planned(
        game_id=new_uuid(),
        challenge_id=new_uuid(),
        sport=Sport.PADEL,
        kind=kind,
        window=None,
        line_up=LineUp.of(
            [
                Seating(side=GameSide.A, player_id=OLA),
                Seating(side=GameSide.A, player_id=KUBA),
                Seating(side=GameSide.B, player_id=EWA),
                Seating(side=GameSide.B, player_id=TOMEK),
            ]
        ),
        occurred_at=NOW,
        starts_at=START,
    )
    act(game)
    await build_game_repository(session=session, **_store(session)).save(game)
    await session.commit()
    return game


@pytest.mark.parametrize("implementation", registered(GameCourts))
async def test_a_court_is_its_booking_its_sides_and_its_hour(implementation, session):
    courts: GameCourts = implementation.build(session)
    game = await _a_court(session)
    after = START + timedelta(hours=1)

    by_game = await courts.of_game(game.game_id, at=after)
    by_booking = await courts.of_booking(game.challenge_id, at=after)

    assert by_game is not None and by_game == by_booking
    assert (by_game.booking_id, by_game.competitive, by_game.hour_ends_at) == (
        game.challenge_id,
        True,
        START + timedelta(hours=1),
    )
    assert by_game.sides == {OLA: "A", KUBA: "A", EWA: "B", TOMEK: "B"}
    # Nobody said they played: it waits for its score, and nothing else.
    assert by_game.awaiting_a_score
    assert (by_game.awaited, by_game.to_agree, by_game.claimed) == (
        frozenset(),
        frozenset(),
        frozenset(),
    )
    assert by_game.settles_at is None
    assert by_game.vouching == {OLA, KUBA, EWA, TOMEK}


@pytest.mark.parametrize("implementation", registered(GameCourts))
async def test_a_player_tapped_is_awaited_until_they_arrive(implementation, session):
    courts: GameCourts = implementation.build(session)
    tapped = START + timedelta(minutes=5)
    game = await _a_court(
        session,
        act=lambda game: game.note_absent(
            by=OLA, absent=EWA, where=HERE, occurred_at=tapped
        ),
    )

    awaited = await courts.of_game(game.game_id, at=tapped)

    assert awaited is not None
    assert (awaited.awaited, awaited.noted_by) == ({EWA}, {EWA: OLA})
    # Nothing takes a score while somebody is awaited, and the awaited player
    # vouches for nobody.
    assert not awaited.awaiting_a_score
    assert awaited.vouching == {OLA, KUBA, TOMEK}

    arrives = START + timedelta(minutes=20)
    games = build_game_repository(session=session, **_store(session))
    again = await games.load(game.game_id)
    assert again is not None
    again.note_arrival(by=EWA, arrived=EWA, where=HERE, occurred_at=arrives)
    await games.save(again)
    await session.commit()
    arrived = await courts.of_game(game.game_id, at=arrives)

    assert arrived is not None
    assert (arrived.awaited, arrived.noted_by) == (frozenset(), {EWA: OLA})


@pytest.mark.parametrize("implementation", registered(GameCourts))
async def test_a_score_waits_on_the_other_side_until_its_day_is_up(
    implementation, session
):
    courts: GameCourts = implementation.build(session)
    stated = START + timedelta(hours=1, minutes=5)
    game = await _a_court(
        session,
        act=lambda game: game.state_result(
            by=OLA, score=Score.from_code("6-4,6-3"), occurred_at=stated
        ),
    )

    court = await courts.of_game(game.game_id, at=stated)

    assert court is not None
    assert court.to_agree == {EWA, TOMEK}
    assert court.settles_at == stated + timedelta(hours=24)
    assert not court.awaiting_a_score


@pytest.mark.parametrize("implementation", registered(GameCourts))
async def test_a_claim_waits_on_a_confirmation_from_somebody_who_came(
    implementation, session
):
    courts: GameCourts = implementation.build(session)
    claimed = START + timedelta(hours=16)

    def ewa_never_came_and_says_she_did(game: Game) -> None:
        game.note_absent(
            by=OLA, absent=EWA, where=HERE, occurred_at=START + timedelta(minutes=5)
        )
        game.claim_presence(by=EWA, occurred_at=claimed)

    game = await _a_court(session, act=ewa_never_came_and_says_she_did)

    court = await courts.of_game(game.game_id, at=claimed)

    assert court is not None
    assert court.claimed == {EWA}
    assert court.vouching == {OLA, KUBA, TOMEK}
    assert court.claims_close_at == START + timedelta(minutes=30, hours=24)


@pytest.mark.parametrize("implementation", registered(GameCourts))
async def test_a_for_fun_court_is_not_competitive(implementation, session):
    courts: GameCourts = implementation.build(session)
    game = await _a_court(session, kind=GameKind.FRIENDLY)

    court = await courts.of_game(game.game_id, at=START)

    assert court is not None and not court.competitive


@pytest.mark.parametrize("implementation", registered(GameCourts))
async def test_no_such_game_has_no_court(implementation, session):
    courts: GameCourts = implementation.build(session)

    assert await courts.of_game(new_uuid(), at=NOW) is None
    assert await courts.of_booking(new_uuid(), at=NOW) is None


# --------------------------------------------------------------------------- #
# EndedHours — the booked games whose hour has just ended (#663)
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(EndedHours))
async def test_a_booked_hour_is_found_once_it_has_ended(implementation, session):
    hours: EndedHours = implementation.build(session)
    proposal = await _saved(session, await _a_proposal(session))
    booking = _booked(proposal, at=NOW)
    await build_booking_repository(session, **_store(session)).save(booking)
    await session.commit()
    ends = START + timedelta(hours=1)

    assert await hours.ended(after=ends - timedelta(minutes=1), by=ends) == [
        booking.booking_id
    ]
    # Not before its end, and not twice: the window is after one, by the other.
    assert await hours.ended(after=START, by=ends - timedelta(seconds=1)) == []
    assert await hours.ended(after=ends, by=ends + timedelta(minutes=1)) == []


@pytest.mark.parametrize("implementation", registered(EndedHours))
async def test_a_game_with_a_seat_open_has_no_hour_to_end(implementation, session):
    hours: EndedHours = implementation.build(session)
    proposal = await _saved(session, await _a_proposal(session))
    booking = _booked(proposal, at=NOW)
    booking.leave(KUBA, at=NOW + timedelta(hours=1))
    await build_booking_repository(session, **_store(session)).save(booking)
    await session.commit()
    ends = START + timedelta(hours=1)

    assert await hours.ended(after=ends - timedelta(minutes=1), by=ends) == []


# --------------------------------------------------------------------------- #
# PaidShares — what a refund gives back
# --------------------------------------------------------------------------- #


async def _a_paid_share(
    session,
    *,
    withhold_fee: bool,
    fee_grosze: int | None = 1_76,
    given: bool = False,
) -> SeatCharge:
    game_id = new_uuid()
    charge = SeatCharge.held(
        charge_id=new_uuid(),
        player_id=KUBA,
        game_id=game_id,
        club_id=new_uuid(),
        account_id="acct_fake_club",
        payment=Payment(
            payment_id="pi_fake_4000g_x",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=40_00,
        ),
        sport=Sport.PADEL,
        starts_at=START,
        at=NOW,
    )
    charge.take(booking_id=game_id, at=NOW)
    charge.captured(at=NOW, fee_grosze=fee_grosze)
    charge.refund(withhold_fee=withhold_fee, at=NOW, reason=RefundReason.SEAT_TAKEN)
    if given:
        amount = charge.refund_to_ask_grosze
        assert amount is not None
        charge.refunded(
            Refund(
                refund_id="re_1", status=RefundStatus.SUCCEEDED, amount_grosze=amount
            ),
            at=NOW,
        )
    await build_seat_charge_repository(session, **_store(session)).save(charge)
    await session.commit()
    return charge


@pytest.mark.parametrize("implementation", registered(PaidShares))
async def test_a_share_given_back_less_the_fee_kept_on_it_or_whole(
    implementation, session
):
    """Never an estimate (#641): a business card kept 1,76 zł on a 40 zł
    share, so 38,24 zł goes back — and once it has, what was kept is said."""

    shares: PaidShares = implementation.build(session)
    less = await _a_paid_share(session, withhold_fee=True)
    given = await _a_paid_share(session, withhold_fee=True, given=True)
    whole = await _a_paid_share(session, withhold_fee=False)

    given_less = await shares.of(less.charge_id)
    made = await shares.of(given.charge_id)
    given_whole = await shares.of(whole.charge_id)

    assert given_less is not None and given_less.refunded_grosze == 38_24
    assert given_less.game_id == less.game_id
    assert given_less.seat_taken
    assert made is not None
    assert (made.refunded_grosze, made.kept_grosze) == (38_24, 1_76)
    assert given_whole is not None and given_whole.refunded_grosze == 40_00
    assert await shares.of(new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(PaidShares))
async def test_a_refund_less_a_fee_not_yet_known_says_no_sum(implementation, session):
    shares: PaidShares = implementation.build(session)
    waiting = await _a_paid_share(session, withhold_fee=True, fee_grosze=None)

    found = await shares.of(waiting.charge_id)

    assert found is not None and found.refunded_grosze is None


@pytest.mark.parametrize("implementation", registered(PaidShares))
async def test_a_player_s_share_of_a_game_is_found_by_the_game(implementation, session):
    shares: PaidShares = implementation.build(session)
    less = await _a_paid_share(session, withhold_fee=True)

    given = await shares.of_player(less.game_id, KUBA)

    assert given is not None and given.refunded_grosze == 38_24
    assert await shares.of_player(less.game_id, OLA) is None
    assert await shares.of_player(new_uuid(), KUBA) is None


@pytest.mark.parametrize("implementation", registered(PaidShares))
async def test_a_player_charged_for_a_game_is_known_whatever_the_charge_s_state(
    implementation, session
):
    """#711: the club's cancel tells the players with **no** charge at all — a
    held share, a paid one and a player never charged must read differently."""

    shares: PaidShares = implementation.build(session)
    paid = await _a_paid_share(session, withhold_fee=True)
    held_game = new_uuid()
    held = SeatCharge.held(
        charge_id=new_uuid(),
        player_id=OLA,
        game_id=held_game,
        club_id=new_uuid(),
        account_id="acct_fake_club",
        payment=Payment(
            payment_id="pi_fake_4000g_held",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=40_00,
        ),
        sport=Sport.PADEL,
        starts_at=START,
        at=NOW,
    )
    await build_seat_charge_repository(session, **_store(session)).save(held)
    await session.commit()

    assert await shares.has_a_charge(paid.game_id, KUBA)
    assert await shares.has_a_charge(held_game, OLA)
    assert not await shares.has_a_charge(paid.game_id, OLA)
    assert not await shares.has_a_charge(new_uuid(), KUBA)


# --------------------------------------------------------------------------- #
# SeatOffers and Names — the questions with nothing to ask about
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("implementation", registered(SeatOffers))
async def test_a_game_that_is_not_there_has_no_pool_and_no_seat_offered(
    implementation, session
):
    offers: SeatOffers = implementation.build(session)

    assert await offers.pool_of(new_uuid()) == ()
    assert await offers.offered_among(new_uuid(), [OLA], at=NOW) == ()


@pytest.mark.parametrize("implementation", registered(Decks))
async def test_a_card_is_shown_to_nobody_outside_its_pool(implementation, session):
    decks: Decks = implementation.build(session)
    # A pool no group is: nobody is in it, so no deck shows its card.
    proposal = await _saved(session, await _a_proposal(session))

    assert await decks.showing(proposal.proposal_id, [OLA, KUBA], at=NOW) == ()
    assert await decks.showing(new_uuid(), [OLA], at=NOW) == ()


@pytest.mark.parametrize("implementation", registered(Decks))
async def test_a_card_promises_a_kind_of_court_only_when_its_courts_are_one_kind(
    implementation, client, session
):
    """What *Your new game* names at the club and hour a cancel took (#673): the
    kind the card promises, as the deck shows it (Q122)."""

    club_id, desk = await a_club_and_its_desk(client)
    decks: Decks = implementation.build(session)
    card = await _saved(session, await _a_proposal(session, club_id=UUID(club_id)))

    # Court 1 is the club's one padel court, and indoor.
    assert await decks.kind_of_court(card.proposal_id) is True
    outdoor = await adds_a_court(client, desk, name="Court 4", indoor=False)
    await sets_hours(client, desk, [outdoor["id"]], every_hour_of_the_week())
    assert await decks.kind_of_court(card.proposal_id) is None
    assert await decks.kind_of_court(new_uuid()) is None


@pytest.mark.parametrize("implementation", registered(Names))
async def test_nobody_and_no_club_is_called_anything(implementation, session):
    names: Names = implementation.build(session)

    assert await names.of_people([new_uuid()]) == {}
    assert await names.of_clubs([new_uuid()]) == {}


# --------------------------------------------------------------------------- #
# GroupJoiners and RatedAccounts — Get your level's two questions (#727)
# --------------------------------------------------------------------------- #


async def _a_group_joined(
    session, owner: UUID, *, at: Instant, joins: dict[UUID, Instant], code: str
) -> Group:
    """A player group its Owner made at ``at``, and each of ``joins`` joining at
    their own instant — through the aggregate, saved by its repository."""

    group = Group.create_player_group(
        group_id=new_uuid(),
        name=GroupName("Wednesday padel"),
        home_club_id=await _a_club(session),
        join_policy=JoinPolicy.ANYONE,
        owner_id=owner,
        code=GroupCode(code),
        occurred_at=at,
    )
    for player, joined_at in joins.items():
        group.join(player, occurred_at=joined_at)
    await build_group_repository(session, **_store(session)).save(group)
    await session.commit()
    return group


async def _leave(session, group: Group, *players: UUID, at: Instant) -> None:
    """``players`` leave the group, loaded and saved through its repository."""

    groups = build_group_repository(session, **_store(session))
    loaded = await groups.load(group.id)
    assert loaded is not None
    for player in players:
        loaded.leave(player, occurred_at=at)
    await groups.save(loaded)
    await session.commit()


@pytest.mark.parametrize("implementation", registered(GroupJoiners))
async def test_each_account_is_counted_from_its_earliest_join_in_the_window(
    implementation, session
):
    """Ola made the group four days ago; Kuba joined two days ago and Ewa an
    hour ago. Asked for the joins between three days and one day ago, only Kuba
    is a candidate — Ola joined before the window, Ewa after it."""

    joiners: GroupJoiners = implementation.build(session)
    await _a_group_joined(
        session,
        OLA,
        at=instant(NOW - timedelta(days=4)),
        joins={
            KUBA: instant(NOW - timedelta(days=2)),
            EWA: instant(NOW - timedelta(hours=1)),
        },
        code="k7pq2mxa",
    )

    first = await joiners.first_joined(
        after=instant(NOW - timedelta(days=3)), by=instant(NOW - timedelta(days=1))
    )

    assert first == {KUBA: instant(NOW - timedelta(days=2))}


@pytest.mark.parametrize("implementation", registered(GroupJoiners))
async def test_an_account_is_counted_from_the_groups_it_is_in_now(
    implementation, session
):
    """Tomek joined the first group four days ago and the second two days ago;
    he left the first, so his earliest join is the second's. Zosia left the one
    group she was in, and is in none."""

    joiners: GroupJoiners = implementation.build(session)
    first_group = await _a_group_joined(
        session,
        OLA,
        at=instant(NOW - timedelta(days=5)),
        joins={
            TOMEK: instant(NOW - timedelta(days=4)),
            ZOSIA: instant(NOW - timedelta(days=4)),
        },
        code="k7pq2mxa",
    )
    await _a_group_joined(
        session,
        KUBA,
        at=instant(NOW - timedelta(days=3)),
        joins={TOMEK: instant(NOW - timedelta(days=2))},
        code="m3nq8rtw",
    )
    await _leave(
        session, first_group, TOMEK, ZOSIA, at=instant(NOW - timedelta(days=1))
    )

    first = await joiners.first_joined(after=instant(NOW - timedelta(days=10)), by=NOW)

    assert first[TOMEK] == instant(NOW - timedelta(days=2))
    assert ZOSIA not in first


@pytest.mark.parametrize("implementation", registered(RatedAccounts))
async def test_a_rating_in_any_sport_counts_and_none_does_not(implementation, session):
    ratings: RatedAccounts = implementation.build(session)
    await _a_rating(session, OLA, sport=Sport.PADEL, mu=2.5)
    await _a_rating(session, KUBA, sport=Sport.SQUASH, mu=3.0)
    await session.commit()

    assert await ratings.rated_among([OLA, KUBA, EWA]) == {OLA, KUBA}
    assert await ratings.rated_among([]) == frozenset()
