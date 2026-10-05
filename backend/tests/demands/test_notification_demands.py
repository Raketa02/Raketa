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
from app.modules.payments.domain.provider import Payment, PaymentStatus
from app.modules.payments.domain.seat_charge import RefundReason, SeatCharge
from app.modules.proposals.domain.pool import Pool, PoolKind
from app.modules.proposals.domain.proposal import Origin, Proposal
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
async def test_no_such_game_is_nothing(implementation, session):
    games: GameBriefs = implementation.build(session)

    assert await games.about(new_uuid(), at=NOW) is None


# --------------------------------------------------------------------------- #
# PaidShares — what a refund gives back
# --------------------------------------------------------------------------- #


async def _a_paid_share(session, *, withhold_fee: bool) -> SeatCharge:
    game_id = new_uuid()
    charge = SeatCharge.held(
        charge_id=new_uuid(),
        player_id=KUBA,
        game_id=game_id,
        club_id=new_uuid(),
        account_id="acct_fake_club",
        payment=Payment(
            payment_id="pi_fake_3000g_x",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=30_00,
        ),
        sport=Sport.PADEL,
        starts_at=START,
        at=NOW,
    )
    charge.take(booking_id=game_id, at=NOW)
    charge.captured(at=NOW)
    charge.refund(withhold_fee=withhold_fee, at=NOW, reason=RefundReason.SEAT_TAKEN)
    await build_seat_charge_repository(session, **_store(session)).save(charge)
    await session.commit()
    return charge


@pytest.mark.parametrize("implementation", registered(PaidShares))
async def test_a_share_given_back_less_the_card_fee_or_whole(implementation, session):
    shares: PaidShares = implementation.build(session)
    less = await _a_paid_share(session, withhold_fee=True)
    whole = await _a_paid_share(session, withhold_fee=False)

    given_less = await shares.of(less.charge_id)
    given_whole = await shares.of(whole.charge_id)

    # 30 zł less Stripe's EEA card fee: 1.5 % and 1 zł.
    assert given_less is not None and given_less.refunded_grosze == 28_55
    assert given_less.game_id == less.game_id
    assert given_whole is not None and given_whole.refunded_grosze == 30_00
    assert await shares.of(new_uuid()) is None


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
