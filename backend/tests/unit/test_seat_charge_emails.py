"""*It's a game! · you paid* — what the booking confirmation says about leaving
(Q99; the mechanics §14.1, §17.2).

Before the club's cut-off it says what leaving gives back — the share less the
card fee, the payments' own estimate — and never that leaving is free; a game
that filled after its cut-off keeps its own sentence. The mailbox tests read
the whole email as a player would (``tests/api/test_the_fill.py``); this one
pins the figures the product owner ruled on, on a 40 zł share.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from app.kernel import Sport, instant
from app.modules.payments.application.seat_charge_emails import game_booked_email
from app.modules.payments.domain.card_fee import estimated_card_fee

WARSAW = ZoneInfo("Europe/Warsaw")


def warsaw(day: int, hour: int):
    return instant(datetime(2026, 10, day, hour, tzinfo=WARSAW))


def a_booking_email(*, free_to_leave_until):
    """Thursday's padel at Bonarka Arena, 40 zł a seat."""

    return game_booked_email(
        to="ivan@example.com",
        name="Ivan",
        club="Bonarka Arena",
        court="Court 2",
        sport=Sport.PADEL,
        starts_at=warsaw(8, 19),
        paid_grosze=40_00,
        free_to_leave_until=free_to_leave_until,
        fee_estimate_grosze=estimated_card_fee(40_00),
        app_link="raketa://home",
    )


def test_before_the_cut_off_it_says_what_leaving_gives_back():
    email = a_booking_email(free_to_leave_until=warsaw(7, 19))

    assert email.subject == "It's a game! · you paid 40 zł"
    assert (
        "You can leave until Wednesday 7 October, 19:00 and get 38,40 zł back at "
        "once (the 1,60 zł card fee isn't returned)."
    ) in email.text
    assert "free to leave" not in email.text


def test_a_game_that_filled_after_its_cut_off_keeps_its_sentence():
    email = a_booking_email(free_to_leave_until=None)

    assert (
        "This game has no free cancellation: if you leave, you're refunded only "
        "when someone takes your seat."
    ) in email.text
    assert "You can leave until" not in email.text
