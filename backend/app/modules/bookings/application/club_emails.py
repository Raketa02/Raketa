"""The emails a club's desk is sent (the mechanics §16.12; the screens B9): *a
game was called off at the cut-off* (#544), at once, and *New bookings today*
(#548), once a day. No club confirms a game (``docs/adr/0196`` §1), so no
request is ever waiting for the desk's answer, and nothing is sent about one
(#669).

The words live here, beside the use cases that queue them (``docs/adr/0186``
§4); the wall clock is the club's, Europe/Warsaw, since that is where the court
is. **What the desk needs and nothing more** (the mechanics §16.14): the hour,
the sport, the court and the court's price — no player's name, which the
website shows to a signed-in desk, never an inbox.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Final

from app.application.mail.layout import ButtonEmail, render
from app.application.ports.mail import OutgoingMessage
from app.kernel import Instant, Sport
from app.modules.clubs.domain.court_hours import CLUB_ZONE, day_closes_at

#: Every game is one hour, for every sport (the mechanics §2).
_A_GAME: Final = timedelta(hours=1)

_SPORT_WORDS: Final = {
    Sport.PADEL: "Padel",
    Sport.TENNIS: "Tennis",
    Sport.SQUASH: "Squash",
    Sport.BADMINTON: "Badminton",
}


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


#: The ``kind`` the day's summary is queued under (#548).
NEW_BOOKINGS_KIND: Final = "bookings.new_bookings.club"


@dataclass(frozen=True, slots=True)
class NewBooking:
    """One game booked at the club, as the summary lists it."""

    court: str
    sport: Sport
    starts_at: Instant
    price_grosze: int
    #: Called off since — short at the cut-off or cancelled — and listed all
    #: the same: it was booked that day.
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
                f"Rakieta players booked {games} at {club} in the day to "
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
