"""The money emails (the mechanics §17.2; the screens A9): the fill's two —
*It's a game! · 30 zł held*, the booking confirmation, from the club as the
seller, saying when the share is taken (*you paid* when it was taken at once),
and *Confirm your payment to keep your seat* — and a share given back (#544):
*You left the game*, *Game called off* — and a rescue's (#545): *You've been
refunded 38,24 zł · your seat was taken*, and *Confirm your payment to take the
seat* — and the club's cancel (#547): *Game cancelled by the club*, saying why —
and, to a player who had left it, *The game you left was cancelled* (#623).

**After the cut-off every figure is exact** (#641; the mechanics §13, Q113): a
leaver whose seat is taken gets the share less exactly the fee kept on their
payment, and is told both — *40 zł less the 1,76 zł kept on your payment* —
and a leaver is told the same figure when they leave, or none while that fee is
not yet known. **No email names BLIK**, which isn't offered: a refund says it
can take up to two weeks to reach a card.

**A share only held is let go, never refunded** (#637; the mechanics Q113): a
leave before the cut-off, a game short at it and the club's cancel before it
take nothing, so their emails say *nothing was taken* — *the 30 zł hold on
your card is let go* — and never *refunded*.

**Every notice about money is also emailed**. The
words live here, beside the use case that queues them (``docs/adr/0186`` §4);
the wall clock is the club's, Europe/Warsaw, since that is where the court is.

**Money is said the way the screens say it**: whole złoty without grosze —
*30 zł* — and anything else with a decimal comma — *38,40 zł*.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from enum import StrEnum
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


def _short_hour(at: Instant) -> str:
    """*Tue 19:00* — as a notice says the game."""

    wall = _wall(at)
    return f"{wall:%a} {wall:%H:%M}"


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
    share_grosze: int,
    held_until: Instant | None,
    app_link: str,
    booked_on_a_payment: bool = False,
    held_from: Instant | None = None,
) -> OutgoingMessage:
    """*It's a game! · 30 zł held* — the booking confirmation, saying when the
    share is taken (#637; the mechanics §12.2, Q113): ``held_until`` is the
    club's cut-off, which takes it — *30 zł is held on your card and taken on
    Fri 17:00, the club's cut-off. Leave before then and nothing is taken.* —
    or ``None`` for a share taken at once, after the cut-off: *It's a game! ·
    you paid 30 zł*. **A card only checked** (#639) is told when the share is
    held, ``held_from``: *Your card was checked. 40 zł will be held from Sat
    19:00 and taken on Wed 19:00, the club's cut-off.* **A game booked on a
    payment it waited for** (#625, Q110) was *It's a game!* already when it
    filled: *Your Tue 19:00 is booked · 30 zł held*, never a second *It's a
    game!*."""

    share = zloty(share_grosze)
    said = f"{share} held" if held_until is not None else f"you paid {share}"
    if booked_on_a_payment:
        hour = _short_hour(starts_at)
        subject = f"Your {hour} is booked · {said}"
        heading = f"Your {hour} is booked"
    else:
        subject = f"It's a game! · {said}"
        heading = "It's a game!" if name is None else f"It's a game, {name}!"
    money: tuple[str, ...] = (
        (
            f"Your card was checked. {share} will be held from "
            f"{_short_hour(held_from)} and taken on {_short_hour(held_until)}, "
            "the club's cut-off. Leave before then and nothing is taken.",
            "A hold lasts only a few days, so we held your share for a moment "
            "and let it go, to check the money is there. You may see it come "
            "and go in your bank app.",
            f"{share} is your share of the court. {club} is the seller and holds "
            "it on your card.",
        )
        if held_until is not None and held_from is not None
        else (
            f"{share} is held on your card and taken on {_short_hour(held_until)}, "
            "the club's cut-off. Leave before then and nothing is taken.",
            f"{share} is your share of the court. {club} is the seller and holds "
            "it on your card.",
        )
        if held_until is not None
        else (
            f"You paid {share}, your share of the court. {club} is the seller "
            "and charged your card.",
            "This game has no free cancellation: if you leave, you're refunded "
            "only when someone takes your seat.",
        )
    )
    return render(
        ButtonEmail(
            kind=GAME_BOOKED_KIND,
            to=to,
            subject=subject,
            heading=heading,
            lines=(
                f"{_SPORT_WORDS[sport]} at {club}, {court} — {_the_hour(starts_at)}.",
                *money,
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
        "The payment terms have to be accepted again before your card can be "
        "held — they changed, or your card's brand did. Accept them in You › "
        "Payments, then say yes again."
    ),
    FailureReason.NO_METHOD: (
        "There is no payment method to charge. Save one in You › Payments, "
        "then say yes again."
    ),
}


#: What to do about a hold refused before the cut-off (#638): nothing is being
#: taken, so it is the card that is fixed, never a payment made.
_TO_FIX: Final = {
    FailureReason.AUTHENTICATION_REQUIRED: (
        "Your bank wants you to confirm the {amount} hold yourself."
    ),
    FailureReason.DECLINED: (
        "Your bank declined the {amount} hold. You can fix it with another card."
    ),
    FailureReason.TERMS_NEEDED: _WHAT_TO_DO[FailureReason.TERMS_NEEDED],
    FailureReason.NO_METHOD: (
        "There is no card to hold your share on. Save one in You › Payments, "
        "then say yes again."
    ),
}


#: What fixing a card refused at its Holding time asks (#639): the game is
#: booked, so there is no yes to say again — the share is held once it is fixed.
_TO_FIX_AT_THE_HOLDING: Final = {
    **_TO_FIX,
    FailureReason.TERMS_NEEDED: (
        "The payment terms have to be accepted again before your card can be "
        "held — they changed, or your card's brand did. Accept them in You › "
        "Payments, and your share is held on it."
    ),
    FailureReason.NO_METHOD: (
        "There is no card to hold your share on. Save one in You › Payments, "
        "and your share is held on it."
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
    rescue: bool = False,
    pay_by: Instant | None = None,
    cut_off: Instant | None = None,
    at_the_holding: bool = False,
) -> OutgoingMessage:
    """*Confirm your payment to keep your seat.* Nobody paid. **With time to
    pay** (#625, #626; Q109) the seat is held for them alone until ``pay_by``,
    and the email names the time — *Confirm your payment by 14:40 to keep your
    seat*: the others are waiting, and paying by then books the game at once.
    **Before the club's ``cut_off``** nothing is taken, only held, so it is
    their **time to fix the card** (#638; Q113): *Fix your card by 14:40 to
    keep your seat* — nothing is paid now, and fixing it only places the hold
    again, taken at the cut-off. **On a rescue** (#545) — an open seat on a
    booked game — *to take the seat*: nothing was charged, and the seat is
    theirs if they confirm before somebody else takes it. **At the Holding
    time** (#639) the game is booked already: the share could not be held
    again, and the seat is the player's until ``pay_by`` — then offered to
    others, and nothing owed."""

    if at_the_holding and pay_by is not None and cut_off is not None:
        by = f"{_wall(pay_by):%H:%M}"
        amount = zloty(amount_grosze)
        subject = f"Fix your card by {by} to keep your seat"
        lines: tuple[str, ...] = (
            f"Your {amount} for {_SPORT_WORDS[sport].lower()} at {club} on "
            f"{_day_and_time(starts_at)} couldn't be held on your card.",
            _TO_FIX_AT_THE_HOLDING[reason].format(amount=amount),
            f"Nothing is paid now: fixing your card only places the {amount} "
            f"hold on it, taken on {_short_hour(cut_off)}, the club's cut-off.",
            f"Your seat is kept for you until {by}. After that it's offered to "
            "others, and you owe nothing.",
        )
    elif rescue:
        subject = "Confirm your payment to take the seat"
        lines = (
            f"You went for the open seat in {_SPORT_WORDS[sport].lower()} at {club} "
            f"on {_day_and_time(starts_at)}, but your payment didn't go through.",
            _WHAT_TO_DO[reason].format(amount=zloty(amount_grosze)),
            "Nothing was charged. If you confirm it before somebody else takes "
            "the seat, it's yours.",
        )
    elif pay_by is not None and cut_off is not None:
        by = f"{_wall(pay_by):%H:%M}"
        amount = zloty(amount_grosze)
        subject = f"Fix your card by {by} to keep your seat"
        lines = (
            f"Everybody said yes to {_SPORT_WORDS[sport].lower()} at {club} on "
            f"{_day_and_time(starts_at)}, but your card didn't go through.",
            _TO_FIX[reason].format(amount=amount),
            f"Nothing is paid now: fixing your card only places the {amount} "
            f"hold on it again, taken on {_short_hour(cut_off)}, the club's "
            "cut-off.",
            f"Your seat is held for you until {by} — the others are waiting. "
            "Fix it by then and the game books at once; after that, your seat "
            "is open to others.",
        )
    elif pay_by is not None:
        by = f"{_wall(pay_by):%H:%M}"
        subject = f"Confirm your payment by {by} to keep your seat"
        lines = (
            f"Everybody said yes to {_SPORT_WORDS[sport].lower()} at {club} on "
            f"{_day_and_time(starts_at)}, but your payment didn't go through.",
            _WHAT_TO_DO[reason].format(amount=zloty(amount_grosze)),
            f"Nobody has paid yet, and your seat is held for you until {by} — "
            "the others are waiting. Confirm by then and the game books at "
            "once; after that, your seat is open to others.",
        )
    else:
        subject = "Confirm your payment to keep your seat"
        lines = (
            f"Everybody said yes to {_SPORT_WORDS[sport].lower()} at {club} on "
            f"{_day_and_time(starts_at)}, but your payment didn't go through.",
            _WHAT_TO_DO[reason].format(amount=zloty(amount_grosze)),
            "Nobody has paid, and your seat is open again. If you're back before "
            "somebody else takes it, the game books and everybody is charged.",
        )
    return render(
        ButtonEmail(
            kind=CONFIRM_PAYMENT_KIND,
            to=to,
            subject=subject,
            heading=subject,
            lines=lines,
            button_label="Open Raketa",
            button_url=app_link,
        )
    )


#: How long a refund takes to reach a card, said when it is issued (Q113) —
#: and nothing about BLIK, which isn't offered.
_REFUNDS_TAKE: Final = "Refunds can take up to two weeks to reach your card."

#: The ``kind`` each refund email is queued under (#544, #545).
LEFT_THE_GAME_KIND: Final = "payments.left_the_game.player"
GAME_CALLED_OFF_KIND: Final = "payments.game_called_off.player"
SEAT_TAKEN_KIND: Final = "payments.seat_taken.player"


def _let_go(amount_grosze: int, *, on_the_card: bool) -> str:
    """What letting a share go did to the card: its hold let go — or, a share
    only checked at the fill or refused at its holding (#639), nothing held on
    it to let go."""

    if on_the_card:
        return f"The {zloty(amount_grosze)} hold on your card is let go"
    return "Nothing is held on your card for it"


def left_the_game_email(
    *,
    to: str,
    name: str | None,
    club: str,
    sport: Sport,
    starts_at: Instant,
    share_grosze: int,
    app_link: str,
    held: bool = False,
    on_the_card: bool = True,
) -> OutgoingMessage:
    """*You left the game · nothing was taken* — left before the club's
    cut-off with the share only ``held``: the hold is let go (#637, Q113) — or,
    not ``on_the_card``, only checked, nothing was held to let go (#639). A
    share taken already — only #639's fallback takes one that early — is *your
    refund is on its way*: everything back, since leaving before the cut-off
    costs nothing."""

    heading = "You left the game" if name is None else f"You left the game, {name}"
    if held:
        return render(
            ButtonEmail(
                kind=LEFT_THE_GAME_KIND,
                to=to,
                subject="You left the game · nothing was taken",
                heading=heading,
                lines=(
                    f"{_SPORT_WORDS[sport]} at {club} — {_the_hour(starts_at)}.",
                    f"{_let_go(share_grosze, on_the_card=on_the_card)}. "
                    "Your seat is offered to others.",
                ),
                button_label="Open Raketa",
                button_url=app_link,
            )
        )
    return render(
        ButtonEmail(
            kind=LEFT_THE_GAME_KIND,
            to=to,
            subject="You left the game · your refund is on its way",
            heading=heading,
            lines=(
                f"{_SPORT_WORDS[sport]} at {club} — {_the_hour(starts_at)}.",
                f"Your {zloty(share_grosze)} share is being refunded in full by "
                f"{club}. Your seat is offered to others.",
                _REFUNDS_TAKE,
            ),
            button_label="Open Raketa",
            button_url=app_link,
        )
    )


def left_after_the_cut_off_email(
    *,
    to: str,
    name: str | None,
    club: str,
    sport: Sport,
    starts_at: Instant,
    share_grosze: int,
    refund_grosze: int | None,
    fee_kept_grosze: int | None,
    app_link: str,
) -> OutgoingMessage:
    """*You left the game* — after the club's cut-off (#641; the mechanics §13,
    Q113): the share stays paid and the seat is offered to others, and what
    comes back if somebody takes it is said **to the grosz**: the share less
    exactly the fee kept on the payment. While that fee is not yet known there
    is no figure and no clause — never an estimate."""

    heading = "You left the game" if name is None else f"You left the game, {name}"
    offered = "Your seat is offered to others."
    if refund_grosze is not None and fee_kept_grosze is not None:
        offered += (
            f" If someone takes it, you get {zloty(refund_grosze)} back "
            f"({zloty(share_grosze)} less the {zloty(fee_kept_grosze)} kept on "
            "your payment)."
        )
    return render(
        ButtonEmail(
            kind=LEFT_THE_GAME_KIND,
            to=to,
            subject="You left the game",
            heading=heading,
            lines=(
                f"{_SPORT_WORDS[sport]} at {club} — {_the_hour(starts_at)}.",
                offered,
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
    held: bool = False,
    on_the_card: bool = True,
) -> OutgoingMessage:
    """*Game called off · nothing was taken* — a seat was still empty at the
    club's cut-off, so the game is off and every share ``held`` is let go: nobody
    pays anything (#637, Q113). A share taken already is *with the refund*, in
    full."""

    off = (
        f"{_SPORT_WORDS[sport]} at {club} — {_the_hour(starts_at)} — is off: "
        f"a seat was still empty at the club's cut-off."
    )
    if held:
        subject = "Game called off · nothing was taken"
        lines: tuple[str, ...] = (
            off,
            f"{_let_go(refunded_grosze, on_the_card=on_the_card)}, so nothing "
            "was taken.",
        )
    else:
        subject = f"Game called off · you're refunded {zloty(refunded_grosze)}"
        lines = (
            off,
            f"Your {zloty(refunded_grosze)} is refunded in full by {club}.",
            _REFUNDS_TAKE,
        )
    return render(
        ButtonEmail(
            kind=GAME_CALLED_OFF_KIND,
            to=to,
            subject=subject,
            heading="Game called off",
            lines=lines,
            button_label="Open Raketa",
            button_url=app_link,
        )
    )


GAME_CANCELLED_KIND: Final = "payments.game_cancelled.player"


class CancelledBecause(StrEnum):
    """Why the club cancelled a booked game, as the refund's email says it
    (#547; the mechanics §16.9)."""

    WEATHER = "WEATHER"
    REPAIR = "REPAIR"
    DOUBLE_BOOKING = "DOUBLE_BOOKING"
    OTHER = "OTHER"


#: The email's words for each reason — ``None`` is the club's *other*, which
#: names none.
_CANCELLED_BECAUSE: Final[dict[CancelledBecause, str | None]] = {
    CancelledBecause.WEATHER: "because of the weather",
    CancelledBecause.REPAIR: "because a court needs repair",
    CancelledBecause.DOUBLE_BOOKING: "because the court was booked twice",
    CancelledBecause.OTHER: None,
}


def game_cancelled_email(
    *,
    to: str,
    name: str | None,
    club: str,
    sport: Sport,
    starts_at: Instant,
    refunded_grosze: int,
    because: CancelledBecause,
    app_link: str,
    held: bool = False,
    on_the_card: bool = True,
) -> OutgoingMessage:
    """*Game cancelled by the club* (#547): the club cancelled the booked game,
    nothing goes on anybody's record, and everybody in it is dealt a new game
    first. **Before the cut-off** every share was only ``held`` and is let go —
    *nothing was taken* (#637, Q113); after it everybody gets all of their
    money back — *you're refunded*."""

    reason = _CANCELLED_BECAUSE[because]
    cancelled = (
        f"{_SPORT_WORDS[sport]} at {club} — {_the_hour(starts_at)} — was "
        f"cancelled by the club" + ("." if reason is None else f" {reason}.")
    )
    if held:
        subject = f"Game cancelled by {club} · nothing was taken"
        lines: tuple[str, ...] = (
            cancelled,
            f"{_let_go(refunded_grosze, on_the_card=on_the_card)}: nothing was "
            "taken, and nothing about it goes on your record.",
            "We'll look for another game for you first.",
        )
    else:
        subject = f"Game cancelled by {club} · you're refunded {zloty(refunded_grosze)}"
        lines = (
            cancelled,
            f"Your {zloty(refunded_grosze)} is refunded in full by {club}, and "
            "nothing about it goes on your record.",
            "We'll look for another game for you first.",
            _REFUNDS_TAKE,
        )
    return render(
        ButtonEmail(
            kind=GAME_CANCELLED_KIND,
            to=to,
            subject=subject,
            heading="Game cancelled",
            lines=lines,
            button_label="Open Raketa",
            button_url=app_link,
        )
    )


GAME_YOU_LEFT_CANCELLED_KIND: Final = "payments.game_you_left_cancelled.player"


def game_you_left_cancelled_email(
    *,
    to: str,
    name: str | None,
    club: str,
    sport: Sport,
    starts_at: Instant,
    refunded_grosze: int,
    because: CancelledBecause,
    app_link: str,
    held: bool = False,
    on_the_card: bool = True,
) -> OutgoingMessage:
    """*The game you left was cancelled* (#623; the mechanics §13, Q108): the
    player left after the club's cut-off and their seat was still paid, and
    the club cancelled the game — so their share comes back in full, or, still
    only ``held`` because the cut-off had not taken it yet, is let go (#637).
    **In a leaver's words**: the club's reason and the money, and never a new
    game, which is owed only to the people still in."""

    reason = _CANCELLED_BECAUSE[because]
    if held:
        subject = "The game you left was cancelled · nothing was taken"
        money: tuple[str, ...] = (
            f"{_let_go(refunded_grosze, on_the_card=on_the_card)}: nothing was taken.",
        )
    else:
        subject = (
            f"The game you left was cancelled · you're refunded "
            f"{zloty(refunded_grosze)}"
        )
        money = (
            f"Your {zloty(refunded_grosze)} is refunded in full by {club}.",
            _REFUNDS_TAKE,
        )
    return render(
        ButtonEmail(
            kind=GAME_YOU_LEFT_CANCELLED_KIND,
            to=to,
            subject=subject,
            heading="The game you left was cancelled",
            lines=(
                f"{_SPORT_WORDS[sport]} at {club} — {_the_hour(starts_at)} — "
                f"which you left, was cancelled by the club"
                + ("." if reason is None else f" {reason}."),
                *money,
            ),
            button_label="Open Raketa",
            button_url=app_link,
        )
    )


def seat_taken_email(
    *,
    to: str,
    name: str | None,
    club: str,
    sport: Sport,
    starts_at: Instant,
    share_grosze: int,
    refunded_grosze: int,
    fee_kept_grosze: int,
    app_link: str,
) -> OutgoingMessage:
    """*You've been refunded 38,24 zł · your seat was taken* (#545, #641; the
    mechanics §12.3, §13, §17.2) — left after the club's cut-off, so refunded
    only now that somebody took the seat: the share less **exactly the fee kept
    on the payment**, both said — *(40 zł less the 1,76 zł kept on your
    payment)*. Sent once the refund is made, when the sum is known to the
    grosz."""

    return render(
        ButtonEmail(
            kind=SEAT_TAKEN_KIND,
            to=to,
            subject=(
                f"You've been refunded {zloty(refunded_grosze)} · your seat was taken"
            ),
            heading=(
                "Your seat was taken"
                if name is None
                else f"Your seat was taken, {name}"
            ),
            lines=(
                f"Somebody took your seat in {_SPORT_WORDS[sport].lower()} at {club} "
                f"— {_the_hour(starts_at)}.",
                f"{club} refunded you {zloty(refunded_grosze)} "
                f"({zloty(share_grosze)} less the {zloty(fee_kept_grosze)} kept on "
                "your payment).",
                _REFUNDS_TAKE,
            ),
            button_label="Open Raketa",
            button_url=app_link,
        )
    )


def seat_taken_nothing_taken_email(
    *,
    to: str,
    name: str | None,
    club: str,
    sport: Sport,
    starts_at: Instant,
    share_grosze: int,
    app_link: str,
) -> OutgoingMessage:
    """*Your seat was taken · nothing was taken* (#637) — left after the
    club's cut-off, but the cut-off had not taken the share yet when somebody
    took the seat: it was only held, and is let go."""

    return render(
        ButtonEmail(
            kind=SEAT_TAKEN_KIND,
            to=to,
            subject="Your seat was taken · nothing was taken",
            heading=(
                "Your seat was taken"
                if name is None
                else f"Your seat was taken, {name}"
            ),
            lines=(
                f"Somebody took your seat in {_SPORT_WORDS[sport].lower()} at "
                f"{club} — {_the_hour(starts_at)}.",
                f"The {zloty(share_grosze)} hold on your card is let go: "
                "nothing was taken.",
            ),
            button_label="Open Raketa",
            button_url=app_link,
        )
    )
