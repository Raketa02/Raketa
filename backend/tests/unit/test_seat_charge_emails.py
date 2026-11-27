"""*It's a game! · 40 zł held* — what the booking confirmation says about the
money (#637; the mechanics §12.2, §17.2, Q113).

Before the club's cut-off the share is held and taken at it, and leaving
before then takes nothing — the email says when, and never quotes a fee. A game
that filled after its cut-off was taken at once, *you paid*, and keeps its own
sentence. The mailbox tests read the whole email as a player would
(``tests/api/test_holding_until_the_cut_off.py``); this one pins the words the
product owner ruled on, on a 40 zł share.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.kernel import Sport, instant
from app.modules.payments.application.seat_charge_emails import (
    CancelledBecause,
    game_booked_email,
    game_called_off_email,
    game_cancelled_email,
    game_you_left_cancelled_email,
    left_after_the_cut_off_email,
    left_the_game_email,
    seat_taken_email,
)

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int):
    return instant(datetime(2026, 10, day, hour, tzinfo=WARSAW))


def a_booking_email(*, held_until, booked_on_a_payment: bool = False):
    """Thursday's padel at Bonarka Arena, 40 zł a seat."""

    return game_booked_email(
        to="ivan@example.com",
        nickname="ivan.k",
        club="Bonarka Arena",
        court="Court 2",
        sport=Sport.PADEL,
        starts_at=warsaw(8, 19),
        share_grosze=40_00,
        held_until=held_until,
        app_link="rakieta://home",
        booked_on_a_payment=booked_on_a_payment,
    )


def test_before_the_cut_off_it_says_the_share_is_held_and_when_it_is_taken():
    email = a_booking_email(held_until=warsaw(7, 19))

    assert email.subject == "It's a game! · 40 zł held"
    assert (
        "40 zł is held on your card and taken on Wed 19:00, the club's cut-off. "
        "Leave before then and nothing is taken."
    ) in email.text
    assert "card fee" not in email.text
    assert "you paid" not in email.text.lower()


def test_the_booking_greets_the_player_by_their_nickname():
    """*It's a game, ivan.k!* — the whole handle, never an @ and never a name
    (``docs/adr/0199`` §1)."""

    email = a_booking_email(held_until=warsaw(7, 19))

    assert email.text.startswith("It's a game, ivan.k!")
    assert "@ivan.k" not in email.text


def test_a_game_that_filled_after_its_cut_off_was_paid_and_keeps_its_sentence():
    email = a_booking_email(held_until=None)

    assert email.subject == "It's a game! · you paid 40 zł"
    assert (
        "This game has no free cancellation: if you leave, you're refunded only "
        "when someone takes your seat."
    ) in email.text
    assert "held on your card" not in email.text


def test_a_game_booked_on_the_payment_it_waited_for_is_booked_and_held():
    email = a_booking_email(held_until=warsaw(7, 19), booked_on_a_payment=True)

    assert email.subject == "Your Thu 19:00 is booked · 40 zł held"


# --------------------------------------------------------------------------- #
# After the cut-off: the exact sum, never an estimate (#641; the mechanics §13)
# --------------------------------------------------------------------------- #


def a_seat_taken_email(*, refunded_grosze: int, fee_kept_grosze: int):
    """Ivan's seat on Thursday's padel, taken after he left late."""

    return seat_taken_email(
        to="ivan@example.com",
        nickname="ivan.k",
        club="Bonarka Arena",
        sport=Sport.PADEL,
        starts_at=warsaw(8, 19),
        share_grosze=40_00,
        refunded_grosze=refunded_grosze,
        fee_kept_grosze=fee_kept_grosze,
        app_link="rakieta://home",
    )


def test_a_seat_taken_refund_states_the_exact_sum_and_what_was_kept():
    """Ivan paid by his business Visa, on which 1,76 zł was kept."""

    email = a_seat_taken_email(refunded_grosze=38_24, fee_kept_grosze=1_76)

    assert email.subject == "You've been refunded 38,24 zł · your seat was taken"
    assert "(40 zł less the 1,76 zł kept on your payment)" in email.text
    assert "about" not in email.text


def a_late_leave_email(*, refund_grosze: int | None, fee_kept_grosze: int | None):
    return left_after_the_cut_off_email(
        to="ivan@example.com",
        nickname="ivan.k",
        club="Bonarka Arena",
        sport=Sport.PADEL,
        starts_at=warsaw(8, 19),
        share_grosze=40_00,
        refund_grosze=refund_grosze,
        fee_kept_grosze=fee_kept_grosze,
        app_link="rakieta://home",
    )


def test_leaving_after_the_cut_off_says_what_comes_back_if_the_seat_is_taken():
    email = a_late_leave_email(refund_grosze=38_24, fee_kept_grosze=1_76)

    assert email.subject == "You left the game"
    assert (
        "Your seat is offered to others. If someone takes it, you get 38,24 zł "
        "back (40 zł less the 1,76 zł kept on your payment)."
    ) in email.text


def test_leaving_after_the_cut_off_gives_no_figure_while_the_fee_is_not_known():
    email = a_late_leave_email(refund_grosze=None, fee_kept_grosze=None)

    assert email.subject == "You left the game"
    assert "Your seat is offered to others." in email.text
    assert "If someone takes it" not in email.text
    assert "zł back" not in email.text


def test_no_money_email_mentions_blik():
    """BLIK isn't offered, so no email promises when a refund reaches it
    (Q113); how long one takes to reach a card is said when it is issued."""

    refunds = [
        a_seat_taken_email(refunded_grosze=38_24, fee_kept_grosze=1_76),
        game_called_off_email(
            to="ivan@example.com",
            nickname="ivan.k",
            club="Bonarka Arena",
            sport=Sport.PADEL,
            starts_at=warsaw(8, 19),
            refunded_grosze=40_00,
            app_link="rakieta://home",
        ),
        game_cancelled_email(
            to="ivan@example.com",
            nickname="ivan.k",
            club="Bonarka Arena",
            sport=Sport.PADEL,
            starts_at=warsaw(8, 19),
            refunded_grosze=40_00,
            because=CancelledBecause.WEATHER,
            app_link="rakieta://home",
        ),
        game_you_left_cancelled_email(
            to="ivan@example.com",
            nickname="ivan.k",
            club="Bonarka Arena",
            sport=Sport.PADEL,
            starts_at=warsaw(8, 19),
            refunded_grosze=40_00,
            because=CancelledBecause.WEATHER,
            app_link="rakieta://home",
        ),
        left_the_game_email(
            to="ivan@example.com",
            nickname="ivan.k",
            club="Bonarka Arena",
            sport=Sport.PADEL,
            starts_at=warsaw(8, 19),
            share_grosze=40_00,
            app_link="rakieta://home",
        ),
    ]

    for email in refunds:
        assert "BLIK" not in email.text, email.subject
        assert "Refunds can take up to two weeks to reach your card." in email.text
