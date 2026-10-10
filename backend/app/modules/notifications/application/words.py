"""What a notice says — the words a phone shows when it is pushed, and the
recent list shows after (#549; the mechanics §17.2; the screens A9).

**The words live here, beside the use cases that send them**, as an email's do
(``docs/adr/0186`` §4): a push is drawn by the phone's system before the app
has run, so there is no client to choose a sentence from a code. The list draws
the same words, so the two never disagree.

**Drawn from facts, never stored**: a notice records the game, the club, the
hour, the money and the people it names, and they are put into words here,
when they are needed — a person's name as it stands, the club's as it is
called.

**The hour is the club's**, Europe/Warsaw — *Sat 10 Oct, 17:00* — and money is
said as the money emails say it (``zloty``): *30 zł*, *28,55 zł*. **A deadline
is said against the moment it was told**, as Home's *answers by* is against
now: *21:15* that day, *Fri 09:00* on another — so a notice read later in the
list says what it said when it was given.

**Every ending and fall-back of a full game has words of its own** (#623;
Q104, Q105, Q108): *filling again* never says whose week filled, who no longer
fits or whose card failed; the club's no and its silence read apart; and a
leaver is told in a leaver's words — *which you left* — and never promised a
new game.

**A time to pay names its time and never its payer** (#625, #626; Q109, Q110):
the payer reads *Confirm your payment by 14:40 to keep your seat*, the others
*It's a game! · waiting for one payment until 14:40* — at the club's yes, *Your
Fri 19:00 is waiting for one payment, until 21:20* — then *booked · you paid*,
never a second *It's a game!*, or *filling again*; the payer, out of time, *Your
time to pay ran out*.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

from app.kernel import Instant, Sport, invariant
from app.modules.bookings.domain.booking import CancelReason
from app.modules.clubs.domain.court_hours import CLUB_ZONE, local_day
from app.modules.notifications.domain.notices import NoticeKind, NoticeReason, Opens
from app.modules.payments.application.seat_charge_emails import zloty
from app.modules.payments.domain.seat_charge import FailureReason

_SPORT_WORDS: Final = {
    Sport.PADEL: "Padel",
    Sport.TENNIS: "Tennis",
    Sport.SQUASH: "Squash",
    Sport.BADMINTON: "Badminton",
}

#: Why a game was called off, as the notice says it — ``None`` is the club's
#: *other*, which names none.
_CALLED_OFF_BECAUSE: Final[dict[str, str | None]] = {
    CancelReason.WEATHER: "because of the weather",
    CancelReason.REPAIR: "because a court needs repair",
    CancelReason.DOUBLE_BOOKING: "because the court was booked twice",
    CancelReason.OTHER: None,
}


@dataclass(frozen=True, slots=True)
class Words:
    title: str
    body: str


@dataclass(frozen=True, slots=True)
class Said:
    """Everything a notice is put into words from."""

    kind: NoticeKind
    sport: Sport
    club: str
    starts_at: Instant
    opens: Opens
    amount_grosze: int | None = None
    #: The people it names, by Name, in the order the notice names them.
    names: tuple[str, ...] = ()
    reason: str | None = None
    #: How many more of its kind the day gathered into it.
    gathered: int = 0
    #: The deadline it names, if its kind names one.
    until: Instant | None = None
    #: When it was given — what its deadline is said against.
    given_at: Instant | None = None
    #: Told to a player who had left the game: in a leaver's words (Q108).
    you_left: bool = False
    #: What was kept on the payment a refund gave back less (#641).
    kept_grosze: int | None = None


def _when(at: Instant) -> str:
    """*Sat 10 Oct, 17:00*."""

    wall = at.astimezone(CLUB_ZONE)
    return f"{wall:%a} {wall.day} {wall:%b}, {wall:%H:%M}"


def _hour(at: Instant) -> str:
    """*Sat 17:00*."""

    wall = at.astimezone(CLUB_ZONE)
    return f"{wall:%a} {wall:%H:%M}"


def _by(deadline: Instant, *, given_at: Instant | None) -> str:
    """*21:15* on the day it was given, *Fri 09:00* on another."""

    if given_at is not None and local_day(deadline) == local_day(given_at):
        return f"{deadline.astimezone(CLUB_ZONE):%H:%M}"
    return _hour(deadline)


def _whose(at: Instant) -> str:
    """*Tuesday's 19:00*."""

    wall = at.astimezone(CLUB_ZONE)
    return f"{wall:%A}'s {wall:%H:%M}"


def _people(names: Sequence[str]) -> str:
    """*Kuba*, *Kuba and Ola*, *Kuba, Ola and Ewa*."""

    if len(names) <= 1:
        return "".join(names) or "Somebody"
    return f"{', '.join(names[:-1])} and {names[-1]}"


def words_for(said: Said) -> Words:
    sport = _SPORT_WORDS[said.sport]
    when = _when(said.starts_at)
    game = f"{sport} at {said.club} · {when}"
    money = zloty(said.amount_grosze or 0)
    kind = said.kind

    if kind is NoticeKind.GAME_BOOKED:
        # Held until the cut-off it keeps as ``until``, or taken at once after
        # it (#637, Q113).
        moved = f"{money} held" if said.until is not None else f"you paid {money}"
        if said.reason == NoticeReason.PAYMENT_CAME_IN:
            # *It's a game!* was told when it filled; never twice (Q110).
            return Words(
                title=f"Your {_hour(said.starts_at)} is booked · {moved}",
                body=f"{sport} at {said.club}.",
            )
        return Words(title=f"It's a game! · {moved}", body=f"{game}.")
    if kind is NoticeKind.WAITING_FOR_A_PAYMENT:
        pay_by = invariant(said.until, "a game waiting for a payment, by no time")
        by = _by(pay_by, given_at=said.given_at)
        if said.reason == NoticeReason.AT_THE_CLUBS_YES:
            # They had *It's a game!* when the club was asked (Q110).
            return Words(
                title=(
                    f"Your {_hour(said.starts_at)} is waiting for one payment, "
                    f"until {by}"
                ),
                body=f"{sport} at {said.club}. Nobody pays until it's in.",
            )
        return Words(
            title=f"It's a game! · waiting for one payment until {by}",
            body=(
                f"{sport} · {_hour(said.starts_at)} at {said.club}. Nobody pays "
                "until it's in."
            ),
        )
    if kind is NoticeKind.TIME_TO_PAY_RAN_OUT:
        return Words(
            title=f"Your time to pay ran out · {_hour(said.starts_at)}",
            body=(
                "Your seat is open to others now — confirm your payment to take "
                "it back while it's free."
            ),
        )
    if kind is NoticeKind.WAITING_FOR_THE_CLUB:
        answer_by = invariant(said.until, "a game waiting for its club, by no time")
        return Words(
            title=(
                f"It's a game! · {said.club} answers by "
                f"{_by(answer_by, given_at=said.given_at)}"
            ),
            body=f"{sport} · {_hour(said.starts_at)}. Nobody pays until it confirms.",
        )
    if kind is NoticeKind.CLUB_CONFIRMED:
        if said.until is not None:
            # Held until the cut-off, taken at it (#637, Q113).
            return Words(
                title=f"{said.club} confirmed your game · {money} held",
                body=f"{sport} · {when} — it's a game. {money} is held on your "
                f"card and taken at the club's cut-off, {_hour(said.until)}.",
            )
        return Words(
            title=f"{said.club} confirmed your game",
            body=f"{sport} · {when} — it's a game, and you paid {money}.",
        )
    if kind is NoticeKind.CLUB_COULD_NOT_TAKE_IT:
        # Its no and its silence read apart, as the email and Home say them
        # (Q105).
        return Words(
            title=f"{said.club} said no"
            if said.reason == NoticeReason.REFUSED
            else f"{said.club} didn't answer in time",
            body=f"{sport} · {_hour(said.starts_at)}. Nobody paid — you'll get a new "
            "card first.",
        )
    if kind is NoticeKind.NEW_GAME:
        return Words(
            title=f"Your new game · {_hour(said.starts_at)} at {said.club}",
            body=f"The same players · {money} a share — say yes to book it.",
        )
    if kind is NoticeKind.CONFIRM_PAYMENT:
        return _confirm_payment(said, game=game, money=money)
    if kind is NoticeKind.GAME_CALLED_OFF:
        return _game_called_off(said, sport=sport, when=when, game=game, money=money)
    if kind is NoticeKind.REFUNDED:
        if said.kept_grosze is None:
            # Told before what was kept was kept on the notice (#641).
            return Words(
                title=f"You've been refunded {money}",
                body=f"Somebody took your seat — {game}.",
            )
        share = zloty((said.amount_grosze or 0) + said.kept_grosze)
        return Words(
            title=f"You've been refunded {money} · your seat was taken",
            body=f"{share} less the {zloty(said.kept_grosze)} kept on your payment "
            f"— {game}.",
        )
    if kind is NoticeKind.SOMEONE_LEFT:
        if said.reason == NoticeReason.FELL_BACK:
            # Never whose week filled, who no longer fits or whose card failed
            # (Q104).
            return Words(
                title=f"Your {_hour(said.starts_at)} at {said.club} is filling again",
                body="A seat opened — nobody paid.",
            )
        if said.reason == NoticeReason.FILLING_AGAIN:
            after = "it's filling again"
        else:
            after = "the seat is open" if len(said.names) <= 1 else "the seats are open"
        return Words(
            title=f"{_people(said.names)} left your game", body=f"{game} — {after}."
        )
    if kind is NoticeKind.POST_DID_NOT_FILL:
        return Words(
            title=f"Your {_hour(said.starts_at)} didn't fill",
            body=f"{sport} at {said.club} — nobody paid. Post it again?",
        )
    if kind is NoticeKind.YOU_COMPLETE_IT:
        if said.gathered:
            return Words(
                title=f"{said.gathered + 1} games need only you",
                body=f"{game}, and {said.gathered} more — say yes and they're booked.",
            )
        return Words(
            title="A game needs only you", body=f"{game} — say yes and it's booked."
        )
    if kind is NoticeKind.CHALLENGE:
        lead = (
            f"{_people(said.names)} challenged you"
            if said.names
            else "A game was posted for you"
        )
        if said.gathered:
            return Words(
                title=f"{said.gathered + 1} challenges for you",
                body=f"{lead} — {game}, and {said.gathered} more.",
            )
        return Words(title=lead, body=f"{game}.")
    if kind is NoticeKind.FILL_IN_ALERT:
        return Words(
            title="A game you fit needs one more", body=f"{game} · {money} a seat."
        )
    raise ValueError(f"no words for {kind}")


def _confirm_payment(said: Said, *, game: str, money: str) -> Words:
    if said.until is not None and said.opens is not Opens.BOOKING:
        return _confirm_by(said, money=money)
    title = (
        "Confirm your payment to take the seat"
        if said.opens is Opens.BOOKING
        else "Confirm your payment to keep your seat"
    )
    if said.reason == FailureReason.TERMS_NEEDED:
        body = (
            "Accept the payment terms again — they changed, or your card's "
            f"brand did. {game}."
        )
    elif said.reason == FailureReason.NO_METHOD:
        body = (
            f"There's no payment method to charge — save one in You › Payments. {game}."
        )
    elif said.reason == FailureReason.DECLINED:
        body = f"Your bank declined {money} — confirm it with another card. {game}."
    else:
        body = f"Your bank wants you to confirm {money}. {game}."
    return Words(title=title, body=body)


def _confirm_by(said: Said, *, money: str) -> Words:
    """*Confirm your payment by 14:40 to keep your seat* — the payer's time to
    pay (#625, #626; Q109): the others are waiting."""

    assert said.until is not None
    sport = _SPORT_WORDS[said.sport]
    waiting = (
        f"{sport} · {_hour(said.starts_at)} at {said.club} — the others are waiting."
    )
    if said.reason == FailureReason.TERMS_NEEDED:
        body = (
            "Accept the payment terms again — they changed, or your card's "
            f"brand did. {waiting}"
        )
    elif said.reason == FailureReason.NO_METHOD:
        body = (
            "There's no payment method to charge — save one in You › Payments. "
            f"{waiting}"
        )
    else:
        body = waiting
    return Words(
        title=(
            f"Confirm your payment by {_by(said.until, given_at=said.given_at)} "
            "to keep your seat"
        ),
        body=body,
    )


#: Why a full game that went back to filling was called off before it was
#: full again — nobody paid (Q104, Q106).
_NOBODY_PAID: Final[dict[str, str]] = {
    NoticeReason.LEFT_AFTER_THE_BOOK_BY: "A seat opened after its last moment to book",
    NoticeReason.BOOK_BY_PASSED: "It didn't fill again before its last moment to book",
    NoticeReason.COURT_HOUR_LOST: "Its court went to another game before it filled "
    "again",
    NoticeReason.PAYMENT_NOT_IN_TIME: "A payment didn't go through in time",
    NoticeReason.COURT_LOST_WAITING_FOR_A_PAYMENT: "Its court went to another game "
    "before the payment came in",
}


def _game_called_off(
    said: Said, *, sport: str, when: str, game: str, money: str
) -> Words:
    why = _NOBODY_PAID.get(said.reason or "")
    if why is not None:
        if said.reason == NoticeReason.LEFT_AFTER_THE_BOOK_BY and said.names:
            why = f"{_people(said.names)} left after its last moment to book"
        return Words(
            title=f"Your {_hour(said.starts_at)} is called off · nobody paid",
            body=f"{why} — {sport} at {said.club}.",
        )
    if said.you_left:
        # A leaver's words: what became of the game they left, and their
        # money — never a new game (Q108).
        left = f"{_whose(said.starts_at)} at {said.club}, which you left"
        if said.reason == NoticeReason.SHORT_AT_THE_CUT_OFF:
            # Their hold was let go when they left (#637, Q113); a share taken
            # before they left was refunded then.
            stands = (
                "Nothing was taken from you."
                if said.amount_grosze is None
                else f"Your {money} refund stands."
            )
            return Words(
                title=f"{left}, was called off",
                body=f"Your seat stayed empty, so it counts on your record. {stands}",
            )
        because = _CALLED_OFF_BECAUSE.get(said.reason or CancelReason.OTHER)
        cancelled = f"{said.club} cancelled it" + (f" {because}" if because else "")
        return Words(
            title=f"{left}, was cancelled",
            body=f"{cancelled} — "
            + (
                "nothing was taken."
                if said.amount_grosze is None
                else f"you're refunded {money}."
            ),
        )
    if said.amount_grosze is None:
        # Every hold let go: at the cut-off, or the club's cancel before it
        # (#637, Q113).
        return Words(
            title="Game called off · nothing was taken",
            body=_called_off(said, sport=sport, when=when, game=game),
        )
    return Words(
        title=f"Game called off · you're refunded {money}",
        body=_called_off(said, sport=sport, when=when, game=game),
    )


def _called_off(said: Said, *, sport: str, when: str, game: str) -> str:
    if said.reason == NoticeReason.SHORT_AT_THE_CUT_OFF:
        return f"{game} was still short at the club's cut-off."
    because = _CALLED_OFF_BECAUSE.get(said.reason or CancelReason.OTHER)
    cancelled = f"{said.club} cancelled {sport.lower()} · {when}"
    return f"{cancelled} {because}." if because else f"{cancelled}."
