"""Home's statuses and money lines — the rules that need no I/O (#542; the
mechanics §14.1–§14.2, §15.1; the screens A4.1, A8).

**Home holds the player's games from the moment they fill** (``docs/adr/0189``
§6), and each card says one status. **The status is folded on every read** from
the booking, its ordinary Game's result and the clock — derived, never stored:
*Booked* until the game's hour, then the result states exactly as today's cards
say them, since after the fill everything that happens to a game today happens to
it unchanged (Q6).

**The statuses the later tickets produce are named here already** — *waiting for
the club* (#543), *seat open* (#544/#545), *called off* by the booking (#543,
#544, #547) — so a client can draw every one of them from the first build, as the
deck's *Seat open* card was named before rescues existed.

**One borrow, pure**: ``is_the_game_day`` from the Bookings domain, whose desk the
check-in code is for — *on the day* is the club's calendar day, one rule for the
phone that shows the code and the desk that scans it.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, exhaustive
from app.modules.bookings.domain.check_in import is_the_game_day
from app.modules.proposals.domain.deck import Sides


class HomeStatus(StrEnum):
    """What a game on Home is, right now (the mechanics §14.1)."""

    #: An On request club has not confirmed yet. Produced from #543.
    WAITING_FOR_THE_CLUB = "WAITING_FOR_THE_CLUB"
    #: Full and booked, its hour still ahead.
    BOOKED = "BOOKED"
    #: Somebody left and their seat is offered. Produced from #544/#545.
    SEAT_OPEN = "SEAT_OPEN"
    #: Its hour has come and nobody has said it happened.
    NEEDS_RESULT = "NEEDS_RESULT"
    #: A score is on the table, waiting for an answer.
    CONFIRM_THE_RESULT = "CONFIRM_THE_RESULT"
    #: A score is agreed.
    COUNTED = "COUNTED"
    #: They played, and no score is agreed.
    UNCOUNTED = "UNCOUNTED"
    #: Nobody said it happened before the entry window closed.
    NEVER_PLAYED = "NEVER_PLAYED"
    #: The game will not be played.
    CALLED_OFF = "CALLED_OFF"


class ResultStage(StrEnum):
    """Where a booked game's ordinary Game stands, in this context's words."""

    #: Nobody has said it happened yet.
    ENTRY_OPEN = "ENTRY_OPEN"
    #: They played, and a score is on the table inside its window.
    SCORE_TO_ANSWER = "SCORE_TO_ANSWER"
    CONFIRMED = "CONFIRMED"
    UNSCORED = "UNSCORED"
    NEVER_PLAYED = "NEVER_PLAYED"
    CALLED_OFF = "CALLED_OFF"


@final
@dataclass(frozen=True, slots=True)
class GameResult:
    """A booked game's result as one player reads it."""

    stage: ResultStage
    #: The other side's score waits on this player's agreement — the *result to
    #: confirm* that is theirs to clear (the mechanics §3). Only ever true with
    #: ``SCORE_TO_ANSWER``.
    awaits_your_agreement: bool


@final
@dataclass(frozen=True, slots=True)
class BookedGame:
    """A booked game, as Home and its details read it: the booking's record."""

    booking_id: UUID
    pool_id: UUID
    club_id: UUID
    court_name: str
    sport: Sport
    kind: SearchMode
    start: Instant
    share_grosze: int
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    #: When free leaving ends — the club's setting when the game filled.
    cut_off: Instant
    #: The ordinary Game the booking opened.
    game_id: UUID

    @property
    def players(self) -> tuple[UUID, ...]:
        return (*self.first_side, *self.second_side)

    def has_a_seat_for(self, player_id: UUID) -> bool:
        return player_id in self.players

    def seen_by(self, player_id: UUID) -> Sides:
        """The sides as this player reads them: theirs first, with them first
        on it — *You + Piotr vs Inés + Bartek*."""

        yours, theirs = (
            (self.second_side, self.first_side)
            if player_id in self.second_side
            else (self.first_side, self.second_side)
        )
        if player_id in yours:
            yours = (player_id, *(other for other in yours if other != player_id))
        return Sides(yours=yours, theirs=theirs)


@final
@dataclass(frozen=True, slots=True)
class CheckIn:
    """A player's check-in code for one booked game: to type, and to scan."""

    short_code: str
    qr_payload: str


@final
@dataclass(frozen=True, slots=True)
class BookedMoney:
    """The money line (the mechanics §14.1)."""

    share_grosze: int
    #: Every seat's share was taken — *Paid · 30 zł*.
    paid: bool
    #: The club's cut-off while it is still ahead — *free to leave until Sat
    #: 17:00* — and ``None`` from it on, and for a game that filled after it.
    free_to_leave_until: Instant | None


#: The two statuses at which the game awaits its entry with every seat filled —
#: the forecast's (the mechanics §14.2: *as today, hidden while a seat is open*).
_FORECAST_SHOWN: Final = frozenset({HomeStatus.BOOKED, HomeStatus.NEEDS_RESULT})

#: The statuses at which there is no game at the club's desk to check in to.
_NO_GAME_AT_THE_DESK: Final = frozenset(
    {HomeStatus.WAITING_FOR_THE_CLUB, HomeStatus.CALLED_OFF}
)


def status_of(
    game: BookedGame, result: GameResult | None, *, now: Instant
) -> HomeStatus:
    """The card's status. ``result`` is ``None`` for a Game that could not be
    read — folded on the clock alone, so the card stays drawn."""

    stage = ResultStage.ENTRY_OPEN if result is None else result.stage
    match stage:
        case ResultStage.ENTRY_OPEN:
            return HomeStatus.BOOKED if now < game.start else HomeStatus.NEEDS_RESULT
        case ResultStage.SCORE_TO_ANSWER:
            return HomeStatus.CONFIRM_THE_RESULT
        case ResultStage.CONFIRMED:
            return HomeStatus.COUNTED
        case ResultStage.UNSCORED:
            return HomeStatus.UNCOUNTED
        case ResultStage.NEVER_PLAYED:
            return HomeStatus.NEVER_PLAYED
        case ResultStage.CALLED_OFF:
            return HomeStatus.CALLED_OFF
        case _:
            exhaustive(stage)


def needs_you(status: HomeStatus, result: GameResult | None) -> bool:
    """Whether this game is one of the games that need the player — Home's
    badge (the mechanics §3): a result to enter, a score waiting on their
    agreement, a seat open in their game."""

    match status:
        case HomeStatus.NEEDS_RESULT | HomeStatus.SEAT_OPEN:
            return True
        case HomeStatus.CONFIRM_THE_RESULT:
            return result is not None and result.awaits_your_agreement
        case (
            HomeStatus.WAITING_FOR_THE_CLUB
            | HomeStatus.BOOKED
            | HomeStatus.COUNTED
            | HomeStatus.UNCOUNTED
            | HomeStatus.NEVER_PLAYED
            | HomeStatus.CALLED_OFF
        ):
            return False
        case _:
            exhaustive(status)


def money_of(game: BookedGame, *, now: Instant) -> BookedMoney:
    """A booked game's money line: every seat paid its share."""

    return BookedMoney(
        share_grosze=game.share_grosze,
        paid=True,
        free_to_leave_until=game.cut_off if now < game.cut_off else None,
    )


@final
@dataclass(frozen=True, slots=True)
class BookedState:
    """A booked game as it stands for one of its players at one instant: the
    card's status, whether it needs them, and its money line."""

    status: HomeStatus
    needs_you: bool
    money: BookedMoney


def state_of(
    game: BookedGame, result: GameResult | None, *, now: Instant
) -> BookedState:
    """Everything Home and the details fold off the booking, its Game's result
    and the clock — once, so a card and its details cannot disagree."""

    status = status_of(game, result, now=now)
    return BookedState(
        status=status,
        needs_you=needs_you(status, result),
        money=money_of(game, now=now),
    )


def shows_forecast(status: HomeStatus) -> bool:
    """Whether the details draw the balance forecast: while the game awaits its
    entry with every seat filled."""

    return status in _FORECAST_SHOWN


def check_in_shown(status: HomeStatus, *, start: Instant, now: Instant) -> bool:
    """Whether the details carry the check-in code: on the game's day, while
    there is a game at the desk to check in to (the mechanics §15.1)."""

    return status not in _NO_GAME_AT_THE_DESK and is_the_game_day(start, now=now)
