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
from app.modules.payments.application.seat_charge_emails import game_booked_email

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int):
    return instant(datetime(2026, 10, day, hour, tzinfo=WARSAW))


def a_booking_email(*, held_until, booked_on_a_payment: bool = False):
    """Thursday's padel at Bonarka Arena, 40 zł a seat."""

    return game_booked_email(
        to="ivan@example.com",
        name="Ivan",
        club="Bonarka Arena",
        court="Court 2",
        sport=Sport.PADEL,
        starts_at=warsaw(8, 19),
        share_grosze=40_00,
        held_until=held_until,
        app_link="raketa://home",
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
