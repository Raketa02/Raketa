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
is said against the moment it was told**: *21:15* that day, *Fri 09:00* on
another — so a notice read later in the list says what it said when it was
given.

**Every ending and fall-back of a full game has words of its own** (#623;
Q104, Q108): *filling again* never says whose week filled, who no longer fits
or whose card failed; and a leaver is told in a leaver's words — *which you
left* — and never promised a new game. **The club's cancel promises the owed
card** to the players still in (#673; Q123): *We'll look for another game for
you first*, as their email says — and *Your new game* names the kind of court
when it is at the club and hour the cancel took.

**Each new step at the court reaches the person it waits on** (#663): *isn't
here yet* to the player awaited, *they're at the club* to whoever tapped it,
*How did it go?* to all four when the hour ends, *Is that right?* across the
net when a score goes up — saying when silence settles it, and that silence
costs nothing — and *were they there?* to the courtmates of a player who says
*I was there*.

**One notice is about no game** (#727; Q126): *Get your level so your groups
can deal you games.* — no club, no hour, no sport, drawn from its kind alone
(``words_about_no_game``).

**A time to pay names its time and never its payer** (#625; Q109, Q110): the
payer reads *Confirm your payment by 14:40 to keep your seat*, the others *It's
a game! · waiting for one payment until 14:40* — then *booked · you paid*,
never a second *It's a game!*, or *filling again*; the payer, out of time,
*Your time to pay ran out*. **Before the cut-off it is the payer's time to fix
the card** (#638; Q113) — nothing is taken then, so they are never asked to
pay: *Fix your card by 14:40 to keep your seat*, and out of time *Your time to
fix your card ran out*. The others' words are the same either way.
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

#: A court's kind, as a player reads it (Q122).
_KIND_WORDS: Final = {True: "indoor", False: "outdoor"}

#: Why the court a club's cancel moved the game from can't be played, as *Game
#: moved* says it after the court's name (#672; the mechanics §17.2, Q122).
_CANNOT_BE_PLAYED: Final[dict[str, str]] = {
    CancelReason.WEATHER: "can't be played in this weather",
    CancelReason.REPAIR: "can't be played",
    CancelReason.DOUBLE_BOOKING: "was booked twice",
    CancelReason.OTHER: "isn't available",
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
    #: The people it names, by nickname, in the order the notice names them.
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
    #: About a seat the player went for and does not hold — a rescue (#640).
    rescue: bool = False
    #: The court a move put the game on, and its kind (#671).
    court_name: str | None = None
    indoor: bool | None = None
    #: The court a club's cancel moved the game from (#672).
    moved_from: str | None = None


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


#: What a notice about no game says, by its kind (#727). *Get your level*
#: names no group and no sport (``docs/adr/0200`` §7); its second line is the
#: group door's own words, where the questions are.
_ABOUT_NO_GAME: Final[dict[NoticeKind, Words]] = {
    NoticeKind.GET_YOUR_LEVEL: Words(
        title="Get your level so your groups can deal you games.",
        body="Pick the sports you play — a few questions each.",
    ),
}


def words_about_no_game(kind: NoticeKind) -> Words:
    """The words of a notice that carries no game's facts — *Get your level*."""

    return invariant(_ABOUT_NO_GAME.get(kind), f"{kind} is about a game")


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
        return Words(
            title=f"It's a game! · waiting for one payment until {by}",
            body=(
                f"{sport} · {_hour(said.starts_at)} at {said.club}. Nobody pays "
                "until it's in."
            ),
        )
    if kind is NoticeKind.TIME_TO_PAY_RAN_OUT and said.rescue:
        # A rescuer's kept seat (#640): offered again, still theirs to take.
        return Words(
            title=f"Your time to pay ran out · {_hour(said.starts_at)}",
            body=(
                "The seat is offered to others again — confirm your payment to "
                "take it while it's free."
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
    if kind is NoticeKind.TIME_TO_FIX_RAN_OUT:
        if said.rescue:
            # A rescuer's kept seat (#640): offered again, still theirs to
            # take, and nothing owed.
            return Words(
                title=f"Your time to fix your card ran out · {_hour(said.starts_at)}",
                body=(
                    "The seat is offered to others again, and you owe nothing — "
                    "you can still take it while it's free."
                ),
            )
        if said.reason == NoticeReason.SEAT_OPEN:
            # At its holding, on a booked game (#639): the seat is offered to
            # others as a leaver's, never theirs to take back.
            return Words(
                title=f"Your time to fix your card ran out · {_hour(said.starts_at)}",
                body="Your seat is open to others now, and you owe nothing.",
            )
        return Words(
            title=f"Your time to fix your card ran out · {_hour(said.starts_at)}",
            body=(
                "Your seat is open to others now, and you owe nothing — you can "
                "still take it back while it's free."
            ),
        )
    if kind is NoticeKind.NEW_GAME:
        # At the club and hour the cancel took, the kind is what changed —
        # kept on the notice only then (#673, Q123).
        kind_of_court = "" if said.indoor is None else f" · {_KIND_WORDS[said.indoor]}"
        return Words(
            title=f"Your new game · {_hour(said.starts_at)} at {said.club}",
            body=(
                f"The same players{kind_of_court} · {money} a share "
                "— say yes to book it."
            ),
        )
    if kind is NoticeKind.GAME_MOVED:
        # The club's own Move (#671, Q122): the new court and its kind, and
        # that nothing else — the hour, the price, the players — changes. A
        # move by cancel (#672) first says why the court it left can't be
        # played, in the words of the club's reason.
        court = said.court_name or "another court"
        kind_of_court = "" if said.indoor is None else f" · {_KIND_WORDS[said.indoor]}"
        body = f"{sport}{kind_of_court} · nothing else changes"
        if said.reason is not None:
            left = said.moved_from or "Your court"
            body = f"{left} {_CANNOT_BE_PLAYED[said.reason]} · {body}"
        return Words(
            title=f"{said.club} moved your game to {court} · {_hour(said.starts_at)}",
            body=body,
        )
    if kind is NoticeKind.CONFIRM_PAYMENT:
        return _confirm_payment(said, game=game, money=money)
    if kind is NoticeKind.FIX_YOUR_CARD:
        if said.rescue:
            return _take_the_seat_by(said, money=money, fix=True)
        return _fix_by(said)
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
    if kind in _ON_THE_COURT:
        return _on_the_court(said, sport=sport, game=game)
    raise ValueError(f"no words for {kind}")


#: The court's own notices (#663) — each opening the game's result screen.
_ON_THE_COURT: Final = frozenset(
    {
        NoticeKind.NOT_HERE_YET,
        NoticeKind.AT_THE_CLUB,
        NoticeKind.HOW_DID_IT_GO,
        NoticeKind.IS_THAT_RIGHT,
        NoticeKind.WERE_THEY_THERE,
    }
)


def _on_the_court(said: Said, *, sport: str, game: str) -> Words:
    """**Each new step at the court, said to the person it waits on** (#663;
    ``docs/adr/0195`` §3, §5): who is not here yet and who arrived, *How did
    it go?* when the hour ends, *Is that right?* when a score goes up — when
    silence settles it, and that silence costs nothing — and *were they
    there?* when somebody who Didn't come says they were."""

    who = _people(said.names)
    hour = f"{sport} · {_hour(said.starts_at)}"
    kind = said.kind
    if kind is NoticeKind.NOT_HERE_YET:
        return Words(
            title=f"{who} is at {said.club} and you're not there yet",
            body=f"Tap I'm here when you arrive — {hour}.",
        )
    if kind is NoticeKind.AT_THE_CLUB:
        arrived = invariant(said.given_at, "an arrival told at no moment")
        return Words(
            title=f"{who} is at {said.club}",
            body=f"{hour} — arrived at {arrived.astimezone(CLUB_ZONE):%H:%M}.",
        )
    if kind is NoticeKind.HOW_DID_IT_GO:
        return Words(title="How did it go?", body=f"{game} — put the score up.")
    if kind is NoticeKind.IS_THAT_RIGHT:
        by = _by(
            invariant(said.until, "a score that settles at no time"),
            given_at=said.given_at,
        )
        where = f"{hour} at {said.club}."
        if said.reason == NoticeReason.COUNTERED:
            return Words(
                title=f"Is that right? · {who} put a different score up",
                body=f"{where} The two scores don't match — unless one side agrees "
                f"with the other's by {by}, it settles then. Saying nothing costs "
                "nothing.",
            )
        put = (
            "changed the score"
            if said.reason == NoticeReason.CORRECTED
            else "put a score up"
        )
        return Words(
            title=f"Is that right? · {who} {put}",
            body=f"{where} If nobody answers by {by}, it becomes the result — "
            "saying nothing costs nothing.",
        )
    if kind is NoticeKind.WERE_THEY_THERE:
        by = _by(
            invariant(said.until, "a claim confirmed by no time"),
            given_at=said.given_at,
        )
        return Words(
            title=f"Was {who} at {said.club}?",
            body=f"{who} tapped I was there for {hour} — confirm it by {by} if so.",
        )
    raise ValueError(f"no words for {kind}")


def _confirm_payment(said: Said, *, game: str, money: str) -> Words:
    if said.until is not None and said.rescue:
        return _take_the_seat_by(said, money=money, fix=False)
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


def _fix_by(said: Said) -> Words:
    """*Fix your card by 14:40 to keep your seat* — the payer's time to fix the
    card, before the cut-off (#638; Q113): nothing is taken then, so nothing is
    paid now, and the others are waiting."""

    fix_by = invariant(said.until, "a card to fix by no time")
    sport = _SPORT_WORDS[said.sport]
    waiting = (
        f"Nothing is paid now. {sport} · {_hour(said.starts_at)} at {said.club} — "
        "the others are waiting."
    )
    if said.reason == FailureReason.TERMS_NEEDED:
        body = (
            "Accept the payment terms again — they changed, or your card's "
            f"brand did. {waiting}"
        )
    elif said.reason == FailureReason.NO_METHOD:
        body = (
            "There's no card to hold your share on — save one in You › "
            f"Payments. {waiting}"
        )
    else:
        body = waiting
    return Words(
        title=(
            f"Fix your card by {_by(fix_by, given_at=said.given_at)} to keep your seat"
        ),
        body=body,
    )


def _take_the_seat_by(said: Said, *, money: str, fix: bool) -> Words:
    """*Fix your card by 14:40 to take the seat* — a rescuer's share refused
    before the cut-off (#640), nothing paid now — or after it *Confirm your
    payment by 14:40 to take the seat*: the seat is kept for them alone until
    then."""

    by = _by(invariant(said.until, "a seat kept until no time"), given_at=said.given_at)
    sport = _SPORT_WORDS[said.sport]
    kept = (
        f"{sport} · {_hour(said.starts_at)} at {said.club} — the seat is kept for "
        "you until then."
    )
    if fix:
        kept = f"Nothing is paid now. {kept}"
    if said.reason == FailureReason.TERMS_NEEDED:
        body = (
            "Accept the payment terms again — they changed, or your card's "
            f"brand did. {kept}"
        )
    elif said.reason == FailureReason.NO_METHOD:
        body = (
            "There's no card to hold your share on — save one in You › "
            f"Payments. {kept}"
        )
    elif said.reason == FailureReason.DECLINED:
        what = f"the {money} hold — fix it" if fix else f"{money} — confirm it"
        body = f"Your bank declined {what} with another card. {kept}"
    else:
        what = f"the {money} hold" if fix else money
        body = f"Your bank wants you to confirm {what}. {kept}"
    act = "Fix your card" if fix else "Confirm your payment"
    return Words(title=f"{act} by {by} to take the seat", body=body)


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
    why = f"{cancelled} {because}." if because else f"{cancelled}."
    # The players still in are owed the card first, as their email says
    # (#673, Q123) — a leaver is told in a leaver's words, promised nothing.
    return f"{why} We'll look for another game for you first."
