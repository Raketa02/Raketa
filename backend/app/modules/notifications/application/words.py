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
        return Words(title=f"It's a game! · you paid {money}", body=f"{game}.")
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
        return Words(
            title=f"{said.club} confirmed your game",
            body=f"{sport} · {when} — it's a game, and you paid {money}.",
        )
    if kind is NoticeKind.CLUB_COULD_NOT_TAKE_IT:
        return Words(
            title=f"{said.club} couldn't take your game",
            body=f"{sport} · {when}. Nobody paid — you'll get a new card first.",
        )
    if kind is NoticeKind.NEW_GAME:
        return Words(
            title=f"Your new game · {_hour(said.starts_at)} at {said.club}",
            body=f"The same players · {money} a share — say yes to book it.",
        )
    if kind is NoticeKind.CONFIRM_PAYMENT:
        return _confirm_payment(said, game=game, money=money)
    if kind is NoticeKind.GAME_CALLED_OFF:
        return Words(
            title=f"Game called off · you're refunded {money}",
            body=_called_off(said, sport=sport, when=when, game=game),
        )
    if kind is NoticeKind.REFUNDED:
        return Words(
            title=f"You've been refunded {money}",
            body=f"Somebody took your seat — {game}.",
        )
    if kind is NoticeKind.SOMEONE_LEFT:
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
    title = (
        "Confirm your payment to take the seat"
        if said.opens is Opens.BOOKING
        else "Confirm your payment to keep your seat"
    )
    if said.reason == FailureReason.TERMS_NEEDED:
        body = f"Your card's brand changed — accept the payment terms again. {game}."
    elif said.reason == FailureReason.NO_METHOD:
        body = (
            f"There's no payment method to charge — save one in You › Payments. {game}."
        )
    elif said.reason == FailureReason.DECLINED:
        body = f"Your bank declined {money} — confirm it with another card. {game}."
    else:
        body = f"Your bank wants you to confirm {money}. {game}."
    return Words(title=title, body=body)


def _called_off(said: Said, *, sport: str, when: str, game: str) -> str:
    if said.reason == NoticeReason.SHORT_AT_THE_CUT_OFF:
        return f"{game} was still short at the club's cut-off."
    because = _CALLED_OFF_BECAUSE.get(said.reason or CancelReason.OTHER)
    cancelled = f"{said.club} cancelled {sport.lower()} · {when}"
    return f"{cancelled} {because}." if because else f"{cancelled}."
