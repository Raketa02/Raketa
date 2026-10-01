"""*A booking is waiting for your answer*, as the desk reads it (the mechanics
§16.8, §16.12; the screens B9) — and *a game was called off at the cut-off*
(#544), the other email a club is sent at once.

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

from datetime import datetime, timedelta
from typing import Final

from app.application.mail.layout import ButtonEmail, render
from app.application.ports.mail import OutgoingMessage
from app.kernel import SPORT_SPECS, Instant, Sport
from app.modules.clubs.domain.court_hours import CLUB_ZONE

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
    """*A booking is waiting for your answer* — with the countdown."""

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
                f"everybody is charged the moment you accept.",
                f"Answer by {_day_and_time(answer_by)}. If you don't, the request "
                f"expires, nobody is charged and the hour is yours to sell again.",
            ),
            button_label="Answer the request",
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
    to sell again. Everybody still in is refunded in full, from the club's
    account, which bears the card fees — it is its own free-cancellation rule.
    A job that reaches the game only after its hour has begun has no hour to
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
                "cancellation ended, so the game is off. Everybody still in is "
                "refunded in full; the card fees on those payments are not "
                "returned.",
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
