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
from app.modules.notifications.domain.ports import (
    Decks,
    GameBriefs,
    Names,
    PaidShares,
    SeatOffers,
)
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


async def _a_proposal(session, *, poster: UUID | None = None) -> Proposal:
    proposal = Proposal.make(
        proposal_id=new_uuid(),
        pool=Pool(id=new_uuid(), kind=PoolKind.GROUP),
        origin=Origin.POST if poster else Origin.PICK,
        poster_id=poster,
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        club_id=new_uuid(),
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


def _requested(proposal: Proposal, *, at: Instant) -> Booking:
    return Booking.requested(
        booking_id=proposal.proposal_id,
        pool_id=proposal.pool.id,
        club_id=proposal.club_id,
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=START,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=START - timedelta(hours=24),
        answer_by=at + timedelta(minutes=30),
        filled_by=TOMEK,
        at=at,
    )


def _booked(proposal: Proposal, *, at: Instant) -> Booking:
    return Booking.confirmed(
        booking_id=proposal.proposal_id,
        pool_id=proposal.pool.id,
        club_id=proposal.club_id,
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
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
    assert (brief.filling, brief.booked, brief.waiting_for_the_club) == (
        True,
        False,
        False,
    )
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
    assert (brief.booked, brief.asked_the_club, brief.cancel_reason) == (
        True,
        False,
        None,
    )
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
    by_the_club = await _a_proposal(session)
    for player in (OLA, KUBA, EWA, TOMEK):
        by_the_club.say_yes(player, at=NOW)
    by_the_club.fill(first_side=(OLA, KUBA), second_side=(EWA, TOMEK), by=None, at=NOW)
    await _saved(session, by_the_club)
    still_filling = await _saved(session, await _a_proposal(session))

    later = NOW + timedelta(hours=1)
    assert (await games.about(filled.proposal_id, at=later)).filled_by == TOMEK
    assert (await games.about(by_the_club.proposal_id, at=later)).filled_by is None
    assert (await games.about(still_filling.proposal_id, at=later)).filled_by is None


@pytest.mark.parametrize("implementation", registered(GameBriefs))
async def test_a_game_waiting_for_its_club_says_by_when_it_answers(
    implementation, session
):
    """Only while it waits: refused, it says no deadline — nor does a game
    still filling, or one booked at once."""

    games: GameBriefs = implementation.build(session)
    proposal = await _a_proposal(session)
    for player in (OLA, KUBA, EWA, TOMEK):
        proposal.say_yes(player, at=NOW)
    await _saved(session, proposal)
    answer_by = NOW + timedelta(minutes=30)
    booking = Booking.requested(
        booking_id=proposal.proposal_id,
        pool_id=proposal.pool.id,
        club_id=proposal.club_id,
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        sport=Sport.PADEL,
        kind=SearchMode.COMPETITIVE,
        start=START,
        share_grosze=30_00,
        first_side=(OLA, KUBA),
        second_side=(EWA, TOMEK),
        cut_off=START - timedelta(hours=24),
        answer_by=answer_by,
        filled_by=TOMEK,
        at=NOW,
    )
    bookings = build_booking_repository(session, **_store(session))
    await bookings.save(booking)
    await session.commit()
    later = NOW + timedelta(minutes=5)

    waiting = await games.about(proposal.proposal_id, at=later)

    assert waiting is not None
    assert (waiting.waiting_for_the_club, waiting.answer_by) == (True, answer_by)
    booking.refuse(reason=None, at=later)
    await bookings.save(booking)
    await session.commit()
    assert (await games.about(proposal.proposal_id, at=later)).answer_by is None
    filling = await _saved(session, await _a_proposal(session))
    assert (await games.about(filling.proposal_id, at=later)).answer_by is None
    booked = await _saved(session, await _a_proposal(session))
    await bookings.save(_booked(booked, at=NOW))
    await session.commit()
    assert (await games.about(booked.proposal_id, at=later)).answer_by is None


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
    """Kuba left while the club decided: the request was taken back, and the
    game is filling again (Q106) — until it is asked again."""

    games: GameBriefs = implementation.build(session)
    proposal = await _a_proposal(session)
    for player in (OLA, KUBA, EWA, TOMEK):
        proposal.say_yes(player, at=NOW)
    proposal.withdraw_yes(KUBA, at=NOW + timedelta(minutes=5))
    await _saved(session, proposal)
    booking = _requested(proposal, at=NOW)
    booking.withdraw_request((KUBA,), left=(KUBA,), at=NOW + timedelta(minutes=5))
    bookings = build_booking_repository(session, **_store(session))
    await bookings.save(booking)
    await session.commit()
    later = NOW + timedelta(minutes=10)

    brief = await games.about(proposal.proposal_id, at=later)

    assert brief is not None
    assert (brief.fell_back, brief.fell_back_at) == (True, NOW + timedelta(minutes=5))
    assert (brief.filling, brief.book_by) == (True, START - timedelta(hours=2))
    assert brief.in_ == (OLA, EWA, TOMEK)
    booking.request_again(
        court=BookedCourt(court_id=new_uuid(), name="Court 1"),
        first_side=(OLA, ZOSIA),
        second_side=(EWA, TOMEK),
        cut_off=START - timedelta(hours=24),
        answer_by=later + timedelta(minutes=30),
        filled_by=ZOSIA,
        at=later,
    )
    await bookings.save(booking)
    await session.commit()
    assert (await games.about(proposal.proposal_id, at=later)).fell_back is False
    booked = await _saved(session, await _a_proposal(session))
    await bookings.save(_booked(booked, at=NOW))
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
    assert (brief.waiting_for_the_club, brief.fell_back) == (False, False)
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


@pytest.mark.parametrize("implementation", registered(Names))
async def test_nobody_and_no_club_is_called_anything(implementation, session):
    names: Names = implementation.build(session)

    assert await names.of_people([new_uuid()]) == {}
    assert await names.of_clubs([new_uuid()]) == {}
