"""Home's statuses and money lines — the rules that need no I/O (#542; the
mechanics §14.1–§14.2, §15.1; the screens A4.1, A8).

**Home holds the player's games from the moment they fill** (``docs/adr/0189``
§6), and each card says one status. **The status is folded on every read** from
the booking, its ordinary Game's result and the clock — derived, never stored:
*Booked* until the game's hour, then the result states exactly as today's cards
say them, since after the fill everything that happens to a game today happens to
it unchanged (Q6).

**Home holds a game its club has still to answer too** (#543): at an On request
club a full game is a booking *waiting for the club* — nobody has paid, there is
no Game yet and no court given — and the club's no, or its silence, calls it
off, with nobody paid and the reason said. A seat opening while it waited takes
the request back: it leaves Home, and the people still In find the game filling
again in You're In.
**Somebody may leave a booked game** (#544): it is *seat open* until its hour —
and **a game plays full or not at all**, so one with a seat open since before
its cut-off is *called off* from the cut-off on, read off the clock whether or
not the job has recorded it, and everybody still in is refunded in full. One
whose seat opened after the cut-off goes ahead short, and once its hour comes
it is *uncounted · a seat was empty*. What leaving would cost the reader is
said before they leave (``leave_terms``).

**One borrow, pure**: ``is_the_game_day`` from the Bookings domain, whose desk the
check-in code is for — *on the day* is the club's calendar day, one rule for the
phone that shows the code and the desk that scans it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import SPORT_SPECS, Instant, Sport, exhaustive
from app.modules.bookings.domain.check_in import is_the_game_day
from app.modules.proposals.domain.deck import Sides


class HomeStatus(StrEnum):
    """What a game on Home is, right now (the mechanics §14.1)."""

    #: An On request club has not confirmed yet. Produced from #543.
    WAITING_FOR_THE_CLUB = "WAITING_FOR_THE_CLUB"
    #: Full and booked, its hour still ahead.
    BOOKED = "BOOKED"
    #: Somebody left and their seat is offered (#544).
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


class BookingStage(StrEnum):
    """Where the booking itself stands, in this context's words."""

    #: Its On request club has not answered yet: no Game, nobody paid.
    WAITING_FOR_THE_CLUB = "WAITING_FOR_THE_CLUB"
    BOOKED = "BOOKED"
    #: Booked and paid, and somebody left: a seat is open (#544).
    SEAT_OPEN = "SEAT_OPEN"
    CALLED_OFF = "CALLED_OFF"


class CalledOffReason(StrEnum):
    """Why a game will not be played (the mechanics §14.1)."""

    #: Its On request club refused it.
    REFUSED = "REFUSED"
    #: Its On request club did not answer in time.
    NO_ANSWER = "NO_ANSWER"
    #: A seat that opened before the club's cut-off was still open at it:
    #: everybody still in is refunded in full (#544).
    SHORT_AT_THE_CUT_OFF = "SHORT_AT_THE_CUT_OFF"
    #: The club cancelled it, with its reason: everybody still in is refunded
    #: in full, and it is on nobody's record (#547).
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"


class ClubCancelReason(StrEnum):
    """Why the club cancelled a booked game (the mechanics §16.9) — the players
    are told it with their refund."""

    WEATHER = "WEATHER"
    REPAIR = "REPAIR"
    DOUBLE_BOOKING = "DOUBLE_BOOKING"
    OTHER = "OTHER"


class UncountedReason(StrEnum):
    """Why a game ended uncounted without anybody disagreeing about a score."""

    #: Its hour came with a seat open: somebody left after the cut-off and
    #: nobody took the seat (#544). Nothing goes on the record of those who
    #: stayed.
    SEAT_EMPTY = "SEAT_EMPTY"
    #: Somebody who came reported a player who did not (#547): the game does
    #: not count, whether the report stands its day or is disputed.
    NO_SHOW = "NO_SHOW"


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
    #: Its hour came with a seat open: no result can be told (#544).
    STARTED_SHORT = "STARTED_SHORT"
    #: A player was reported as not coming, and their day to dispute it runs
    #: (#547).
    NO_SHOW_REPORTED = "NO_SHOW_REPORTED"
    #: A report of not coming stood its day (#547): the game does not count.
    NO_SHOW = "NO_SHOW"


@final
@dataclass(frozen=True, slots=True)
class GameResult:
    """A booked game's result as one player reads it."""

    stage: ResultStage
    #: The other side's score waits on this player's agreement — the *result to
    #: confirm* that is theirs to clear (the mechanics §3). Only ever true with
    #: ``SCORE_TO_ANSWER``.
    awaits_your_agreement: bool
    #: This player was reported as not coming and may still dispute it — a
    #: task that is theirs (#547). Only ever true with ``NO_SHOW_REPORTED``.
    you_may_dispute: bool = False


@final
@dataclass(frozen=True, slots=True)
class OpenSeat:
    """A seat a leaver left open on a booked game (#544, #545): the side it
    is on, and who left it when — which against the cut-off says whether the
    leaver is refunded when somebody takes it."""

    #: ``A`` — the first side — or ``B``.
    side: str
    left_by: UUID
    left_at: Instant


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
    #: The ordinary Game the booking opened — ``None`` until its On request
    #: club said yes, and for good if it never did.
    game_id: UUID | None
    stage: BookingStage = BookingStage.BOOKED
    #: Why it will not be played, once called off.
    called_off: CalledOffReason | None = None
    #: When a seat open since before the club's cut-off calls it off — its
    #: cut-off — or ``None`` while nothing will (#544; ``Booking.short_from``).
    short_from: Instant | None = None
    #: The seats still open, **the first to open first** — the one a rescue
    #: takes (#545).
    open: tuple[OpenSeat, ...] = ()
    #: Everybody who ever left it: a seat they left is never offered back.
    leavers: frozenset[UUID] = frozenset()
    #: Everybody who said no to its *Seat open* card.
    said_no: frozenset[UUID] = frozenset()
    #: Why the club cancelled it, once it did (#547).
    cancel_reason: ClubCancelReason | None = None
    #: Everybody the club's desk checked in, and when (#547) — never reported
    #: as not coming.
    checked_in: Mapping[UUID, Instant] = field(default_factory=dict)
    #: When its On request club's answer is due — on a booking ever put to it.
    answer_by: Instant | None = None
    #: The booking's stream version — what a rescue's attempts are counted by.
    version: int = 0

    @property
    def players(self) -> tuple[UUID, ...]:
        return (*self.first_side, *self.second_side)

    @property
    def open_seats(self) -> int:
        """Seats a leaver left open on a booked game (#544)."""

        if self.stage is not BookingStage.SEAT_OPEN:
            return 0
        return SPORT_SPECS[self.sport].players - len(self.players)

    def called_off_reason(self, now: Instant) -> CalledOffReason | None:
        """Why it will not be played at ``now`` — a seat open since before the
        cut-off calls it off from the cut-off on, whether or not that is
        recorded yet."""

        if self.called_off is not None:
            return self.called_off
        if self.short_from is not None and now >= self.short_from:
            return CalledOffReason.SHORT_AT_THE_CUT_OFF
        return None

    @property
    def court_given(self) -> bool:
        """Whether the players have a court number: an On request club gives it
        with its yes (the screens A4.2), and a request it never answered with
        one gave none."""

        return self.game_id is not None

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
    #: What everybody still in is given back — the whole share, on a game
    #: called off at its cut-off (#544); ``None`` where nothing is.
    refunded_grosze: int | None = None


class Leaving(StrEnum):
    """What *Leave the game* does, by when it is pressed (the mechanics §13) —
    said on the details before, and answered by the act after."""

    #: Before the club's cut-off: refunded at once, less the card fee.
    BEFORE_THE_CUT_OFF = "BEFORE_THE_CUT_OFF"
    #: After it: refunded, less the card fee, only when somebody takes the
    #: seat.
    AFTER_THE_CUT_OFF = "AFTER_THE_CUT_OFF"
    #: While the club decides: nobody has paid, and leaving withdraws the yes.
    WHILE_WAITING_FOR_THE_CLUB = "WHILE_WAITING_FOR_THE_CLUB"


@final
@dataclass(frozen=True, slots=True)
class LeaveTerms:
    """What leaving would cost the reader, said before they confirm —
    *"You'll be refunded 38,40 zł now (the 1,60 zł card fee isn't
    returned)"*."""

    kind: Leaving
    #: What comes back — the share less the card fee; nought when nobody paid.
    refund_grosze: int
    #: The card fee kept back — an estimate; what the provider keeps is on the
    #: receipt.
    card_fee_grosze: int


#: Why a game everybody still in is given all their money back from was called
#: off: the club's own rules — its cut-off, and its cancel (#547).
_REFUNDED_IN_FULL: Final = frozenset(
    {CalledOffReason.SHORT_AT_THE_CUT_OFF, CalledOffReason.CANCELLED_BY_THE_CLUB}
)

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
    read — folded on the clock alone, so the card stays drawn — and for a
    booking that has no Game."""

    if game.stage is BookingStage.WAITING_FOR_THE_CLUB:
        return HomeStatus.WAITING_FOR_THE_CLUB
    if game.called_off_reason(now) is not None:
        return HomeStatus.CALLED_OFF
    stage = ResultStage.ENTRY_OPEN if result is None else result.stage
    if stage is ResultStage.ENTRY_OPEN and game.stage is BookingStage.SEAT_OPEN:
        # A Game folded before its hour reads it ahead; one that could not be
        # read is folded on the clock, and the hour ends a seat left open.
        return HomeStatus.SEAT_OPEN if now < game.start else HomeStatus.UNCOUNTED
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
        case ResultStage.STARTED_SHORT:
            return HomeStatus.UNCOUNTED
        case ResultStage.NO_SHOW_REPORTED | ResultStage.NO_SHOW:
            # Whatever the report comes to, the game does not count (#547).
            return HomeStatus.UNCOUNTED
        case _:
            exhaustive(stage)


def uncounted_reason(
    game: BookedGame, status: HomeStatus, result: GameResult | None
) -> UncountedReason | None:
    """Why an *uncounted* card says so, when nobody disagreed about a score:
    its hour came with a seat open, or somebody reported a player who did not
    come and the report waits out its day or stood it (#547). A report every
    reported player disputed is an ordinary *uncounted*: nobody arbitrated."""

    if status is not HomeStatus.UNCOUNTED:
        return None
    if game.stage is BookingStage.SEAT_OPEN:
        return UncountedReason.SEAT_EMPTY
    if result is not None and result.stage in (
        ResultStage.NO_SHOW_REPORTED,
        ResultStage.NO_SHOW,
    ):
        return UncountedReason.NO_SHOW
    return None


def needs_you(status: HomeStatus, result: GameResult | None) -> bool:
    """Whether this game is one of the games that need the player — Home's
    badge (the mechanics §3): a result to enter, a score waiting on their
    agreement, a seat open in their game, a report of their not coming to
    dispute (#547)."""

    match status:
        case HomeStatus.NEEDS_RESULT | HomeStatus.SEAT_OPEN:
            return True
        case HomeStatus.CONFIRM_THE_RESULT:
            return result is not None and result.awaits_your_agreement
        case HomeStatus.UNCOUNTED:
            # A report of not coming, theirs to dispute while its day runs.
            return result is not None and result.you_may_dispute
        case (
            HomeStatus.WAITING_FOR_THE_CLUB
            | HomeStatus.BOOKED
            | HomeStatus.COUNTED
            | HomeStatus.NEVER_PLAYED
            | HomeStatus.CALLED_OFF
        ):
            return False
        case _:
            exhaustive(status)


def money_of(game: BookedGame, *, now: Instant) -> BookedMoney:
    """The money line: every seat held paid its share of a booked game —
    nobody anything while its club decides, or once it turned it down — and
    everybody still in gets it all back from a game called off at its
    cut-off, or cancelled by its club (#547)."""

    called_off = game.called_off_reason(now)
    paid = (
        game.stage in (BookingStage.BOOKED, BookingStage.SEAT_OPEN)
        and called_off is None
    )
    return BookedMoney(
        share_grosze=game.share_grosze,
        paid=paid,
        free_to_leave_until=game.cut_off if paid and now < game.cut_off else None,
        refunded_grosze=(
            game.share_grosze if called_off in _REFUNDED_IN_FULL else None
        ),
    )


def leaving_of(game: BookedGame, *, now: Instant) -> Leaving:
    """What leaving this game does at ``now`` — whether it may still be left
    at all is the caller's question."""

    if game.stage is BookingStage.WAITING_FOR_THE_CLUB:
        return Leaving.WHILE_WAITING_FOR_THE_CLUB
    if now < game.cut_off:
        return Leaving.BEFORE_THE_CUT_OFF
    return Leaving.AFTER_THE_CUT_OFF


def leave_terms(
    game: BookedGame, status: HomeStatus, *, card_fee_grosze: int, now: Instant
) -> LeaveTerms | None:
    """What *Leave the game* would cost now — ``None`` where there is no such
    button: once the hour has come, and on a game that is over."""

    leaving = leaving_of(game, now=now)
    if leaving is Leaving.WHILE_WAITING_FOR_THE_CLUB:
        return LeaveTerms(kind=leaving, refund_grosze=0, card_fee_grosze=0)
    if status not in (HomeStatus.BOOKED, HomeStatus.SEAT_OPEN) or now >= game.start:
        return None
    return LeaveTerms(
        kind=leaving,
        refund_grosze=game.share_grosze - card_fee_grosze,
        card_fee_grosze=card_fee_grosze,
    )


@final
@dataclass(frozen=True, slots=True)
class BookedState:
    """A booked game as it stands for one of its players at one instant: the
    card's status, whether it needs them, and its money line."""

    status: HomeStatus
    needs_you: bool
    money: BookedMoney
    #: Why it will not be played, once it will not (#543, #544).
    called_off: CalledOffReason | None = None
    #: Why it is uncounted with nobody disagreeing (#544).
    uncounted: UncountedReason | None = None
    #: Why the club cancelled it, when it did (#547).
    cancel_reason: ClubCancelReason | None = None


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
        called_off=game.called_off_reason(now)
        if status is HomeStatus.CALLED_OFF
        else None,
        uncounted=uncounted_reason(game, status, result),
        cancel_reason=game.cancel_reason if status is HomeStatus.CALLED_OFF else None,
    )


def shows_forecast(status: HomeStatus) -> bool:
    """Whether the details draw the balance forecast: while the game awaits its
    entry with every seat filled."""

    return status in _FORECAST_SHOWN


def check_in_shown(status: HomeStatus, *, start: Instant, now: Instant) -> bool:
    """Whether the details carry the check-in code: on the game's day, while
    there is a game at the desk to check in to (the mechanics §15.1)."""

    return status not in _NO_GAME_AT_THE_DESK and is_the_game_day(start, now=now)
