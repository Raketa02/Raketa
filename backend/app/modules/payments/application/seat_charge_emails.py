"""The money emails (the mechanics §17.2; the screens A9): the fill's two —
*It's a game! · you paid*, the booking confirmation, from the club as the
seller, and *Confirm your payment to keep your seat* — and a refund's two
(#544): *You left the game · your refund is on its way* and *Game called off ·
with the refund*.

**Every notice about money is also emailed**. The
words live here, beside the use case that queues them (``docs/adr/0186`` §4);
the wall clock is the club's, Europe/Warsaw, since that is where the court is.

**Money is said the way the screens say it**: whole złoty without grosze —
*30 zł* — and anything else with a decimal comma — *38,40 zł*.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Final

from app.application.mail.layout import ButtonEmail, render
from app.application.ports.mail import OutgoingMessage
from app.kernel import Instant, Sport
from app.modules.clubs.domain.court_hours import CLUB_ZONE
from app.modules.payments.domain.seat_charge import FailureReason

#: Every game is one hour, for every sport (the mechanics §2).
_A_GAME: Final = timedelta(hours=1)

#: The ``kind`` each is queued under — what outlives the purge.
GAME_BOOKED_KIND: Final = "payments.game_booked.player"
CONFIRM_PAYMENT_KIND: Final = "payments.confirm_payment.player"

_SPORT_WORDS: Final = {
    Sport.PADEL: "Padel",
    Sport.TENNIS: "Tennis",
    Sport.SQUASH: "Squash",
    Sport.BADMINTON: "Badminton",
}


def zloty(grosze: int) -> str:
    """*30 zł*, *38,40 zł*."""

    whole, part = divmod(grosze, 100)
    return f"{whole} zł" if part == 0 else f"{whole},{part:02d} zł"


def _wall(at: Instant) -> datetime:
    # Where every court is, and so the clock a game is told in.
    return at.astimezone(CLUB_ZONE)


def _day_and_time(at: Instant) -> str:
    """*Saturday 10 October, 17:00*."""

    wall = _wall(at)
    return f"{wall:%A} {wall.day} {wall:%B}, {wall:%H:%M}"


def _the_hour(at: Instant) -> str:
    """*Saturday 10 October, 17:00 until 18:00* — every game is one hour."""

    return f"{_day_and_time(at)} until {_wall(at + _A_GAME):%H:%M}"


def game_booked_email(
    *,
    to: str,
    name: str | None,
    club: str,
    court: str,
    sport: Sport,
    starts_at: Instant,
    paid_grosze: int,
    free_to_leave_until: Instant | None,
    app_link: str,
) -> OutgoingMessage:
    """*It's a game! · you paid* — the booking confirmation.
    ``free_to_leave_until`` is the club's cut-off, or ``None`` for a game that
    filled after it."""

    leaving = (
        f"You're free to leave until {_day_and_time(free_to_leave_until)} and "
        f"are refunded at once, minus the card fee."
        if free_to_leave_until is not None
        else "This game has no free cancellation: if you leave, you're refunded "
        "only when someone takes your seat."
    )
    return render(
        ButtonEmail(
            kind=GAME_BOOKED_KIND,
            to=to,
            subject=f"It's a game! · you paid {zloty(paid_grosze)}",
            heading="It's a game!" if name is None else f"It's a game, {name}!",
            lines=(
                f"{_SPORT_WORDS[sport]} at {club}, {court} — {_the_hour(starts_at)}.",
                f"You paid {zloty(paid_grosze)}, your share of the court. {club} "
                f"is the seller and charged your card.",
                leaving,
            ),
            button_label="Open the game",
            button_url=app_link,
        )
    )


_WHAT_TO_DO: Final = {
    FailureReason.AUTHENTICATION_REQUIRED: (
        "Your bank wants you to confirm the {amount} payment yourself."
    ),
    FailureReason.DECLINED: (
        "Your bank declined the {amount} payment. You can confirm it with another card."
    ),
    FailureReason.TERMS_NEEDED: (
        "Your card's brand changed, so the payment terms have to be accepted "
        "again before it can be charged. Accept them in You › Payments, then "
        "say yes again."
    ),
    FailureReason.NO_METHOD: (
        "There is no payment method to charge. Save one in You › Payments, "
        "then say yes again."
    ),
}


def confirm_payment_email(
    *,
    to: str,
    club: str,
    sport: Sport,
    starts_at: Instant,
    amount_grosze: int,
    reason: FailureReason,
    app_link: str,
) -> OutgoingMessage:
    """*Confirm your payment to keep your seat.* Nobody paid; the seat is open
    until somebody else takes it."""

    return render(
        ButtonEmail(
            kind=CONFIRM_PAYMENT_KIND,
            to=to,
            subject="Confirm your payment to keep your seat",
            heading="Confirm your payment to keep your seat",
            lines=(
                f"Everybody said yes to {_SPORT_WORDS[sport].lower()} at {club} on "
                f"{_day_and_time(starts_at)}, but your payment didn't go through.",
                _WHAT_TO_DO[reason].format(amount=zloty(amount_grosze)),
                "Nobody has paid, and your seat is open again. If you're back before "
                "somebody else takes it, the game books and everybody is charged.",
            ),
            button_label="Open Raketa",
            button_url=app_link,
        )
    )


#: The ``kind`` each refund email is queued under (#544).
LEFT_THE_GAME_KIND: Final = "payments.left_the_game.player"
GAME_CALLED_OFF_KIND: Final = "payments.game_called_off.player"


def left_the_game_email(
    *,
    to: str,
    name: str | None,
    club: str,
    sport: Sport,
    starts_at: Instant,
    share_grosze: int,
    fee_estimate_grosze: int,
    app_link: str,
) -> OutgoingMessage:
    """*You left the game · your refund is on its way* — left before the
    club's cut-off, so refunded at once, less the card fee the bank doesn't
    return. The amount here is the estimate the sheet quoted; what the provider
    kept back is on the receipt."""

    return render(
        ButtonEmail(
            kind=LEFT_THE_GAME_KIND,
            to=to,
            subject="You left the game · your refund is on its way",
            heading=(
                "You left the game" if name is None else f"You left the game, {name}"
            ),
            lines=(
                f"{_SPORT_WORDS[sport]} at {club} — {_the_hour(starts_at)}.",
                f"Your {zloty(share_grosze)} share is being refunded by {club}, less "
                f"the card fee that isn't returned (about "
                f"{zloty(fee_estimate_grosze)}). Your seat is offered to others.",
                "Refunds reach BLIK within hours and cards within up to two weeks.",
            ),
            button_label="Open Raketa",
            button_url=app_link,
        )
    )


def game_called_off_email(
    *,
    to: str,
    name: str | None,
    club: str,
    sport: Sport,
    starts_at: Instant,
    refunded_grosze: int,
    app_link: str,
) -> OutgoingMessage:
    """*Game called off · with the refund* — a seat was still empty at the
    club's cut-off, so the game is off and everybody still in gets all of their
    money back."""

    return render(
        ButtonEmail(
            kind=GAME_CALLED_OFF_KIND,
            to=to,
            subject=f"Game called off · you're refunded {zloty(refunded_grosze)}",
            heading="Game called off",
            lines=(
                f"{_SPORT_WORDS[sport]} at {club} — {_the_hour(starts_at)} — is off: "
                f"a seat was still empty at the club's cut-off.",
                f"Your {zloty(refunded_grosze)} is refunded in full by {club}.",
                "Refunds reach BLIK within hours and cards within up to two weeks.",
            ),
            button_label="Open Raketa",
            button_url=app_link,
        )
    )
