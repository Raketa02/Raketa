"""A Seat charge hears the provider **only forward** (#541; ``docs/adr/0190``
§3): notices arrive twice and out of order, so a reading the charge has
already moved past is the past arriving late and records nothing.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.kernel import Sport, instant
from app.modules.payments.domain.provider import Payment, PaymentStatus
from app.modules.payments.domain.seat_charge import (
    PAID,
    FailureReason,
    RefundReason,
    SeatCharge,
    SeatChargeStatus,
)

AT = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
GAME = instant(datetime(2026, 10, 10, 15, tzinfo=timezone.utc))


def payment(status: PaymentStatus) -> Payment:
    return Payment(payment_id="pi_1", status=status, amount_grosze=30_00)


def a_hold() -> SeatCharge:
    return SeatCharge.held(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        payment=payment(PaymentStatus.AUTHORISED),
        sport=Sport.PADEL,
        starts_at=GAME,
        at=AT,
    )


def a_refusal() -> SeatCharge:
    return SeatCharge.refused(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        amount_grosze=30_00,
        sport=Sport.PADEL,
        starts_at=GAME,
        reason=FailureReason.AUTHENTICATION_REQUIRED,
        payment=payment(PaymentStatus.AUTHENTICATION_REQUIRED),
        at=AT,
    )


def test_a_hold_heard_after_its_capture_records_nothing():
    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)
    charge.heard(payment(PaymentStatus.CAPTURED), at=AT)
    charge.pull_events()

    assert charge.heard(payment(PaymentStatus.AUTHORISED), at=AT) is False
    assert charge.status is SeatChargeStatus.CAPTURED
    assert charge.pull_events() == []


def test_a_capture_heard_twice_is_recorded_once():
    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)

    assert charge.heard(payment(PaymentStatus.CAPTURED), at=AT) is True
    assert charge.heard(payment(PaymentStatus.CAPTURED), at=AT) is False


def test_a_refused_payment_its_player_confirmed_is_held_again():
    charge = a_refusal()

    assert charge.heard(payment(PaymentStatus.AUTHORISED), at=AT) is True
    assert charge.held_now


def test_a_hold_the_provider_let_go_on_its_own_is_no_longer_held():
    """A hold the provider dropped — never decided here — must not be taken by
    the next fill: it is cancelled, and the next fill asks afresh."""

    charge = a_hold()

    assert charge.heard(payment(PaymentStatus.CANCELLED), at=AT) is True
    assert charge.status is SeatChargeStatus.CANCELLED
    assert not charge.held_now


def test_a_taken_charge_is_never_heard_cancelled():
    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)

    assert charge.heard(payment(PaymentStatus.CANCELLED), at=AT) is False
    assert charge.status is SeatChargeStatus.TAKING


def test_the_club_pays_the_card_fee_the_provider_took_on_the_capture():
    """A card from outside the EEA costs the club more than a personal EU
    card's 1,45 zł on a 30 zł share: what the provider says it took is the fee
    (#548), and nothing stands in for it before then (#641)."""

    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)
    # Never an estimate (#641): not yet known until the provider says.
    assert charge.card_fee_grosze is None

    charge.heard(
        Payment(
            payment_id="pi_1",
            status=PaymentStatus.CAPTURED,
            amount_grosze=30_00,
            fee_grosze=1_98,
        ),
        at=AT,
    )

    assert charge.card_fee_grosze == 1_98
    assert charge.net_grosze == 28_02
    assert SeatCharge.from_history(charge.pull_events()).card_fee_grosze == 1_98


def test_a_share_given_back_whole_costs_the_club_its_card_fee():
    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)
    charge.captured(at=AT, fee_grosze=1_45)
    charge.refund(withhold_fee=False, at=AT)

    assert (charge.given_back_grosze, charge.net_grosze) == (30_00, -1_45)
    assert charge.settled is False  # until the provider gives it back


def test_a_hold_records_its_last_moment():
    """**Whether a hold reaches the club's cut-off** is decided off when it
    ends, which the provider reports when it holds the share (ADR-0190's
    2026-10-10 amendment)."""

    ends = AT + timedelta(days=4, hours=18)
    charge = SeatCharge.held(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        payment=Payment(
            payment_id="pi_1",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=30_00,
            last_moment=ends,
        ),
        sport=Sport.PADEL,
        starts_at=GAME,
        at=AT,
    )

    assert charge.last_moment == ends
    assert SeatCharge.from_history(charge.pull_events()).last_moment == ends


def test_a_payment_its_player_confirmed_records_the_last_moment_of_its_hold():
    ends = AT + timedelta(days=7)
    charge = a_refusal()

    charge.heard(
        Payment(
            payment_id="pi_1",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=30_00,
            last_moment=ends,
        ),
        at=AT,
    )

    assert charge.last_moment == ends
    assert SeatCharge.from_history(charge.pull_events()).last_moment == ends


def test_a_fee_not_yet_known_at_the_capture_is_recorded_when_a_reading_reports_it():
    charge = a_hold()
    charge.take(booking_id=uuid4(), at=AT)
    charge.heard(payment(PaymentStatus.CAPTURED), at=AT)
    assert charge.fee_taken_grosze is None

    reported = Payment(
        payment_id="pi_1",
        status=PaymentStatus.CAPTURED,
        amount_grosze=30_00,
        fee_grosze=1_45,
    )

    assert charge.heard(reported, at=AT) is True
    assert charge.heard(reported, at=AT) is False
    assert charge.fee_taken_grosze == 1_45


# --------------------------------------------------------------------------- #
# Held until the cut-off, then taken (#637; ADR-0189's 2026-10-10 amendment)
# --------------------------------------------------------------------------- #

CUT_OFF = GAME - timedelta(hours=24)


def test_a_hold_kept_for_the_booked_game_is_held_not_paid_and_not_settled():
    """**A held charge is not paid**: nothing is taken until the cut-off, so a
    receipt, *Collected* and a payout all wait for it."""

    charge = a_hold()
    booking = uuid4()

    charge.keep(booking_id=booking, until=CUT_OFF, at=AT)

    assert charge.status is SeatChargeStatus.HELD
    assert (charge.booking_id, charge.held_until) == (booking, CUT_OFF)
    assert not charge.held_now  # decided: no later fill may take it
    assert charge.status not in PAID
    assert not charge.settled
    assert charge.net_grosze == 0 and charge.card_fee_grosze == 0
    replayed = SeatCharge.from_history(charge.pull_events())
    assert (replayed.status, replayed.held_until) == (SeatChargeStatus.HELD, CUT_OFF)


def test_the_cut_off_takes_a_held_share():
    charge = a_hold()
    booking = uuid4()
    charge.keep(booking_id=booking, until=CUT_OFF, at=AT)

    charge.take(booking_id=booking, at=CUT_OFF)

    assert charge.status is SeatChargeStatus.TAKING
    assert charge.taken_at == CUT_OFF
    assert charge.status in PAID


def test_a_held_share_let_go_is_released_untaken_and_settled():
    charge = a_hold()
    charge.keep(booking_id=uuid4(), until=CUT_OFF, at=AT)

    assert charge.let_go(at=AT) is True
    assert charge.status is SeatChargeStatus.RELEASING
    assert charge.settled
    assert charge.cancelled(at=AT) is True
    assert charge.status is SeatChargeStatus.CANCELLED
    assert charge.net_grosze == 0


def test_only_a_held_share_is_let_go():
    taken = a_hold()
    taken.take(booking_id=uuid4(), at=AT)
    undecided = a_hold()

    assert taken.let_go(at=AT) is False
    assert undecided.let_go(at=AT) is False
    assert undecided.held_now


def test_a_held_share_is_never_released_as_an_undecided_one():
    """The fill's *release what this game was not paid with* lets go of
    undecided charges only: a share held for the booked game is the game's."""

    charge = a_hold()
    charge.keep(booking_id=uuid4(), until=CUT_OFF, at=AT)

    assert charge.release(at=AT) is False
    assert charge.status is SeatChargeStatus.HELD


def test_a_held_share_whose_hold_the_provider_dropped_is_cancelled():
    charge = a_hold()
    charge.keep(booking_id=uuid4(), until=CUT_OFF, at=AT)

    assert charge.heard(payment(PaymentStatus.CANCELLED), at=AT) is True
    assert charge.status is SeatChargeStatus.CANCELLED


def test_the_cut_off_takes_only_a_share_held_for_the_game():
    held, undecided = a_hold(), a_hold()
    held.keep(booking_id=uuid4(), until=CUT_OFF, at=AT)

    assert held.take_at_the_cut_off(at=CUT_OFF) is True
    assert held.status is SeatChargeStatus.TAKING
    assert held.take_at_the_cut_off(at=CUT_OFF) is False
    assert undecided.take_at_the_cut_off(at=CUT_OFF) is False
    assert undecided.held_now


# --------------------------------------------------------------------------- #
# No estimate: real or not yet known (#641; the mechanics §12.1, §16.11, Q113)
# --------------------------------------------------------------------------- #


def a_share_taken(*, fee_grosze: int | None, amount_grosze: int = 40_00) -> SeatCharge:
    charge = SeatCharge.held(
        charge_id=uuid4(),
        player_id=uuid4(),
        game_id=uuid4(),
        club_id=uuid4(),
        account_id="acct_1",
        payment=Payment(
            payment_id="pi_1",
            status=PaymentStatus.AUTHORISED,
            amount_grosze=amount_grosze,
        ),
        sport=Sport.PADEL,
        starts_at=GAME,
        at=AT,
    )
    charge.keep(booking_id=charge.game_id, until=CUT_OFF, at=AT)
    charge.take(booking_id=charge.game_id, at=CUT_OFF)
    charge.captured(at=CUT_OFF, fee_grosze=fee_grosze)
    return charge


def test_a_share_taken_before_its_fee_is_known_has_no_fee_net_or_settlement():
    """**No estimate stands in** (#641): the club's card fee and what is its
    own are *not yet known*, and the payout waits for the fee — a club on its
    own negotiated pricing is told it after the capture."""

    charge = a_share_taken(fee_grosze=None)

    assert (charge.card_fee_grosze, charge.net_grosze) == (None, None)
    assert not charge.settled

    charge.fee_reported(1_76, at=CUT_OFF)

    assert (charge.card_fee_grosze, charge.net_grosze) == (1_76, 38_24)
    assert charge.settled


def test_a_late_leaver_would_get_the_share_less_exactly_the_fee_kept_on_it():
    """*If someone takes your seat, you get 38,24 zł back (40 zł less the 1,76
    zł kept on your payment)* — a business card's fee, to the grosz (Q113)."""

    assert a_share_taken(fee_grosze=1_76).less_the_fee_kept_grosze == 38_24
    assert a_share_taken(fee_grosze=2_30).less_the_fee_kept_grosze == 37_70
    assert a_share_taken(fee_grosze=1_60).less_the_fee_kept_grosze == 38_40


def test_nothing_is_said_of_a_late_leave_s_refund_before_the_fee_is_known():
    assert a_share_taken(fee_grosze=None).less_the_fee_kept_grosze is None
    held = a_hold()
    held.keep(booking_id=uuid4(), until=CUT_OFF, at=AT)
    assert held.less_the_fee_kept_grosze is None  # nothing taken yet


def test_a_refund_waiting_on_a_fee_not_yet_known_gives_back_what_is_not_yet_known():
    charge = a_share_taken(fee_grosze=None)

    charge.refund(withhold_fee=True, at=CUT_OFF)

    assert charge.given_back_grosze is None
    assert charge.net_grosze is None
    charge.fee_reported(1_76, at=CUT_OFF)
    assert (charge.given_back_grosze, charge.net_grosze) == (38_24, 0)


def test_a_refund_records_why_it_was_decided():
    charge = a_share_taken(fee_grosze=1_76)

    charge.refund(withhold_fee=True, at=CUT_OFF, reason=RefundReason.SEAT_TAKEN)

    assert charge.refund_reason is RefundReason.SEAT_TAKEN
    replayed = SeatCharge.from_history(charge.pull_events())
    assert replayed.refund_reason is RefundReason.SEAT_TAKEN


def test_a_held_share_let_go_records_when_and_an_undecided_hold_released_does_not():
    """*40 zł held · released* is a receipt of its own (#641), dated when the
    hold was let go; a hold the fill released because the game did not book
    on it never held anything for a game."""

    held, undecided = a_hold(), a_hold()
    held.keep(booking_id=uuid4(), until=CUT_OFF, at=AT)
    let_go_at = AT + timedelta(hours=3)

    held.let_go(at=let_go_at, reason=RefundReason.LEFT)
    undecided.release(at=AT)

    assert held.released_at == let_go_at
    assert SeatCharge.from_history(held.pull_events()).released_at == let_go_at
    assert undecided.released_at is None
