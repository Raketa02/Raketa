"""*A booking is waiting for your answer*, as the desk reads it (the mechanics
§16.8, §16.12; the screens B9) — and *a game was called off at the cut-off*
(#544) and *a game didn't go ahead* (#626), the other emails a club is sent at
once — and *New bookings today*
(#548), the one it is sent once a day. **And the club's answer, as each player
reads it** (#623; Q105): *Kazimierz Padel said no* and *Kazimierz Padel didn't
answer in time*, told apart, though no money moves — while push is off, email
is the only way to reach a player outside the app.

**At once, because the window is short**: an On request club has its time to
confirm — thirty minutes by default — and nobody may be watching the website,
so the club is emailed the moment a full game is put to it, and again each time
the same game is put to it afresh. The words live here, beside the use case
that queues them (``docs/adr/0186`` §4); the wall clock is the club's,
Europe/Warsaw, since that is where the court is.

**What the desk needs and nothing more** (the mechanics §16.14): the hour, the
sport, the court reserved for it, the court's price and the countdown — no player's
name, which the website shows to a signed-in desk, never an inbox.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Final

from app.application.mail.layout import ButtonEmail, render
from app.application.ports.mail import OutgoingMessage
from app.kernel import SPORT_SPECS, Instant, Sport
from app.modules.clubs.domain.court_hours import CLUB_ZONE, day_closes_at

#: Every game is one hour, for every sport (the mechanics §2).
_A_GAME: Final = timedelta(hours=1)

#: The ``kind`` it is queued under — what outlives the purge.
REQUEST_WAITING_KIND: Final = "bookings.request_waiting.club"

_SPORT_WORDS: Final = {
    Sport.PADEL: "Padel",
    Sport.TENNIS: "Tennis",
    Sport.SQUASH: "Squash",
    Sport.BADMINTON: "Badminton",
}

_PLAYERS_IN_WORDS: Final = {2: "Two", 4: "Four"}


def _zloty(grosze: int) -> str:
    """*120 zł*, *118,40 zł* — as the screens say money."""

    whole, part = divmod(grosze, 100)
    return f"{whole} zł" if part == 0 else f"{whole},{part:02d} zł"


def _wall(at: Instant) -> datetime:
    return at.astimezone(CLUB_ZONE)


def _day_and_time(at: Instant) -> str:
    """*Saturday 10 October, 17:00*."""

    wall = _wall(at)
    return f"{wall:%A} {wall.day} {wall:%B}, {wall:%H:%M}"


def request_waiting_email(
    *,
    to: str,
    club: str,
    court: str,
    sport: Sport,
    starts_at: Instant,
    share_grosze: int,
    answer_by: Instant,
    link: str,
) -> OutgoingMessage:
    """*A booking is waiting for your answer* — with the countdown, and that
    the shares are held when the club accepts and taken at its cut-off (#637;
    the mechanics §16.8, Q113)."""

    players = SPORT_SPECS[sport].players
    return render(
        ButtonEmail(
            kind=REQUEST_WAITING_KIND,
            to=to,
            subject="A booking is waiting for your answer",
            heading="A booking is waiting for your answer",
            lines=(
                f"{_SPORT_WORDS[sport]} at {club}, {court} — "
                f"{_day_and_time(starts_at)} until "
                f"{_wall(starts_at + _A_GAME):%H:%M}.",
                f"{_PLAYERS_IN_WORDS.get(players, str(players))} players want it, "
                f"{_zloty(share_grosze * players)} for the court. Nobody has paid: "
                f"the shares are held when you accept and taken at the cut-off.",
                f"Answer by {_day_and_time(answer_by)}. If you don't, the request "
                f"expires, nobody pays and the hour is yours to sell again.",
            ),
            button_label="Answer the request",
            button_url=link,
        )
    )


#: The ``kind`` each of the club's two turn-downs is queued under (#623).
CLUB_SAID_NO_KIND: Final = "bookings.club_said_no.player"
CLUB_DID_NOT_ANSWER_KIND: Final = "bookings.club_did_not_answer.player"


def club_turned_it_down_email(
    *,
    to: str,
    club: str,
    sport: Sport,
    starts_at: Instant,
    refused: bool,
    link: str,
) -> OutgoingMessage:
    """*Kazimierz Padel said no*, or *… didn't answer in time* (#623; the
    mechanics Q105) — the notice's title as the subject: the game, nobody paid,
    and a new card first. Its no and its silence are told apart; the club's own
    note on a refusal is its, never the player's."""

    said = f"{club} said no" if refused else f"{club} didn't answer in time"
    # *The club said no*, for a club that can no longer be named.
    said = said[:1].upper() + said[1:]
    return render(
        ButtonEmail(
            kind=CLUB_SAID_NO_KIND if refused else CLUB_DID_NOT_ANSWER_KIND,
            to=to,
            subject=said,
            heading=said,
            lines=(
                f"{_SPORT_WORDS[sport]} at {club} — {_day_and_time(starts_at)} "
                f"until {_wall(starts_at + _A_GAME):%H:%M}.",
                "Nobody paid.",
                "You'll get a new card first: the same players, at another hour "
                "or club.",
            ),
            button_label="Open Raketa",
            button_url=link,
        )
    )


#: The ``kind`` the cut-off's email is queued under (#544).
CALLED_OFF_AT_THE_CUT_OFF_KIND: Final = "bookings.called_off_at_the_cut_off.club"


def called_off_at_the_cut_off_email(
    *,
    to: str,
    club: str,
    court: str,
    sport: Sport,
    starts_at: Instant,
    hour_still_ahead: bool,
    link: str,
) -> OutgoingMessage:
    """*A game was called off at the cut-off — the hour is free again* (#544;
    the mechanics §16.12, at once): a seat that opened before the club's own
    cut-off was still empty at it, so the game is off and its court the club's
    to sell again. Every share was only held, and every hold is let go: nobody
    pays anything and no card fee arises, the club's included (#637, Q113). A
    job that reaches the game only after its hour has begun has no hour to
    offer back, and says so."""

    return render(
        ButtonEmail(
            kind=CALLED_OFF_AT_THE_CUT_OFF_KIND,
            to=to,
            subject=(
                "A game was called off at the cut-off — the hour is free again"
                if hour_still_ahead
                else "A game was called off at the cut-off"
            ),
            heading="A game was called off at the cut-off",
            lines=(
                f"{_SPORT_WORDS[sport]} at {club}, {court} — "
                f"{_day_and_time(starts_at)} until "
                f"{_wall(starts_at + _A_GAME):%H:%M}.",
                "A player left and nobody took the seat before your free "
                "cancellation ended, so the game is off. Every share was only "
                "held, and every hold is let go: nobody pays, and no card fee "
                "is yours.",
                (
                    "The hour is free again: it is yours to sell."
                    if hour_still_ahead
                    else "Its hour has already begun."
                ),
            ),
            button_label="Open your bookings",
            button_url=link,
        )
    )


#: The ``kind`` a payment that did not come in time is queued under (#626).
PAYMENT_NOT_IN_TIME_KIND: Final = "bookings.payment_not_in_time.club"


def payment_not_in_time_email(
    *,
    to: str,
    club: str,
    court: str,
    sport: Sport,
    starts_at: Instant,
    for_good: bool,
    link: str,
) -> OutgoingMessage:
    """*A game didn't go ahead* (#626; the mechanics §16.12, Q112, at once): the
    desk said yes, and a player's payment did not come in time — or could not,
    the game's last moment to book having come — so the game is off and its
    court the club's to sell again, in the manner of the cut-off's email.
    **Never the player's name**: the desk is told what happened to its court.
    ``for_good`` when the game can no longer fill, so nobody will ask again."""

    return render(
        ButtonEmail(
            kind=PAYMENT_NOT_IN_TIME_KIND,
            to=to,
            subject="A game didn't go ahead",
            heading="A game didn't go ahead",
            lines=(
                f"{_SPORT_WORDS[sport]} at {club}, {court} — "
                f"{_day_and_time(starts_at)} until "
                f"{_wall(starts_at + _A_GAME):%H:%M}.",
                "A player's payment didn't come in time — the court is free "
                "again. Nobody paid.",
                "Its last moment to book has passed, so it won't come back."
                if for_good
                else "If the game is full again, you'll be asked again as for "
                "any new request.",
            ),
            button_label="Open your bookings",
            button_url=link,
        )
    )


#: The ``kind`` the day's summary is queued under (#548).
NEW_BOOKINGS_KIND: Final = "bookings.new_bookings.club"


@dataclass(frozen=True, slots=True)
class NewBooking:
    """One game booked at the club, as the summary lists it."""

    court: str
    sport: Sport
    starts_at: Instant
    price_grosze: int
    #: Called off since — refused, unanswered, short at the cut-off or
    #: cancelled — and listed all the same: it was booked that day.
    called_off: bool


def new_bookings_email(
    *,
    to: str,
    club: str,
    day: date,
    booked: tuple[NewBooking, ...],
    link: str,
) -> OutgoingMessage:
    """*New bookings today* (#548; the mechanics §16.12, a daily summary): every
    game booked at the club in the day up to the close of ``day`` — since the
    summary before — the soonest first: the hour, the court, the sport and the
    court's price. No player's name, which only a signed-in desk reads."""

    games = "1 game" if len(booked) == 1 else f"{len(booked)} games"
    called_off = any(one.called_off for one in booked)
    return render(
        ButtonEmail(
            kind=NEW_BOOKINGS_KIND,
            to=to,
            subject="New bookings today",
            heading="New bookings today",
            lines=(
                f"Raketa players booked {games} at {club} in the day to "
                f"{day:%A} {day.day} {day:%B}, {_wall(day_closes_at(day)):%H:%M}:",
                *(
                    f"{_day_and_time(one.starts_at)} · {one.court} · "
                    f"{_SPORT_WORDS[one.sport]} · {_zloty(one.price_grosze)}"
                    + (" — since called off" if one.called_off else "")
                    for one in booked
                ),
                (
                    "The players paid as each game was booked, and were given "
                    "it back on one called off since. Your money for a game goes "
                    "to your bank once it is played."
                    if called_off
                    else "The players paid as each game was booked. Your money "
                    "for a game goes to your bank once it is played."
                ),
            ),
            button_label="Open your bookings",
            button_url=link,
        )
    )
