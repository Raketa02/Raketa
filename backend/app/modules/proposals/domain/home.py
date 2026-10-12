"""Home's statuses and money lines — the rules that need no I/O (#542; the
mechanics §14.1–§14.2; the screens A4.1, A8).

**Home holds the player's games from the moment they fill** (``docs/adr/0189``
§6), and each card says one status. **The status is folded on every read** from
the booking, its ordinary Game's result and the clock — derived, never stored:
*Booked* until the game's hour, then the result states exactly as today's cards
say them, since after the fill everything that happens to a game today happens to
it unchanged (Q6).

**Home holds a game its club has still to answer too** (#543): at an On request
club a full game is a booking *waiting for the club* — nobody has paid, there is
no Game yet and no court given — and the club's no, or its silence, calls it
off, with nobody paid and the reason said. **A seat opening while it waited takes
the request back, and the game stays on the Home of the people still In as
*Seat open*** (#624, Q106): nobody paid, it asks nothing of them, and it is
folded against its proposal on every read (``as_filling_again``) — who is In
now, and whether its book-by passed, or its court went, before it filled again,
which calls it off.
**A game may wait for one payment** (#625, #626; Q111): a share refused as the
game filled — or as its club said yes — gives its player time to pay, and the
game is *Waiting for one payment* on all four's Home until it comes, nobody
paid. At a club that books at once it has no booking until it books, so its
card is folded off its proposal (``without_a_booking``); and when the time runs
out, or somebody else's seat opens, it is *Seat open* as any full game gone back
to filling.
**Somebody may leave a booked game** (#544): it is *seat open* until its hour —
and **a game plays full or not at all**, so one with a seat open since before
its cut-off is *called off* from the cut-off on, read off the clock whether or
not the job has recorded it, and everybody still in is refunded in full. One
whose seat opened after the cut-off goes ahead short, and once its hour comes
it is *uncounted · a seat was empty*. What leaving would cost the reader is
said before they leave (``leave_terms``).

**Home sends what Home draws** (#613): every live game, an ended one until a
day after its hour's end — the phone's own shelf — and any game that needs the
reader, read only from the earliest hour a game can still ask anything of its
players (``on_home_since``). Everything older is a card nobody would see.

**One borrow, pure**: how long a booked game needs its players, from the Games
domain's own clocks, so the hour Home reads from moves when one of them does.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field, replace
from datetime import timedelta
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import SPORT_SPECS, Instant, Sport, exhaustive, instant, invariant
from app.modules.games.domain.windows import A_BOOKED_GAME_NEEDS_ITS_PLAYERS_FOR
from app.modules.proposals.domain.deck import GAME_LENGTH, Sides
from app.modules.proposals.domain.proposal import (
    Proposal,
    ReopenReason,
    Standing,
    TimeTo,
)


class HomeStatus(StrEnum):
    """What a game on Home is, right now (the mechanics §14.1)."""

    #: An On request club has not confirmed yet. Produced from #543.
    WAITING_FOR_THE_CLUB = "WAITING_FOR_THE_CLUB"
    #: Full, and one player's share was refused: their time to pay runs, and
    #: nobody pays until it is in (#625, #626; Q111).
    WAITING_FOR_A_PAYMENT = "WAITING_FOR_A_PAYMENT"
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
    #: Full at its hour, and nobody recorded it before the entry window closed:
    #: played for everybody on it, and no Level moves (#655; it took *Never
    #: played*'s place).
    PLAYED_NO_SCORE = "PLAYED_NO_SCORE"
    #: The game will not be played.
    CALLED_OFF = "CALLED_OFF"


class BookingStage(StrEnum):
    """Where the booking itself stands, in this context's words."""

    #: Its On request club has not answered yet: no Game, nobody paid.
    WAITING_FOR_THE_CLUB = "WAITING_FOR_THE_CLUB"
    #: A share was refused as it filled — or at its club's yes — and its
    #: player's time to pay runs: no Game, nobody paid (#625, #626).
    WAITING_FOR_A_PAYMENT = "WAITING_FOR_A_PAYMENT"
    BOOKED = "BOOKED"
    #: Booked, and somebody left: a seat is open (#544).
    SEAT_OPEN = "SEAT_OPEN"
    CALLED_OFF = "CALLED_OFF"
    #: Its request was taken back because a seat opened while the club decided:
    #: a full game gone back to filling, nobody paid, its people still In
    #: keeping their places (#624, Q106).
    FILLING_AGAIN = "FILLING_AGAIN"


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
    #: It went back to filling and its book-by came before it was full again —
    #: or a seat opened after its book-by while the club decided, so it could
    #: not fill again: nobody paid (#624, Q104, Q106).
    BOOK_BY_PASSED = "BOOK_BY_PASSED"
    #: It went back to filling and its court went to another game before it
    #: was full again — or before the payment it waited for came in: nobody
    #: paid, and its people are dealt a new card first (#624, #625).
    COURT_HOUR_LOST = "COURT_HOUR_LOST"
    #: A payment it waited for did not come in time and it could no longer
    #: fill — the book-by had come — or, to its club, a payment its yes waited
    #: on did not come in time (#625, #626; Q112): nobody paid.
    PAYMENT_NOT_IN_TIME = "PAYMENT_NOT_IN_TIME"


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
    #: Two scores named different winners and neither side gave way (#654):
    #: no Level moves.
    DISPUTED = "DISPUTED"
    #: A full court nobody recorded before its entry window closed (#655).
    PLAYED_NO_SCORE = "PLAYED_NO_SCORE"
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
class RefusedHolding:
    """A player whose holding was refused (#639; Q113): until when their time
    to fix the card runs, the payment they confirm, and why it was refused."""

    until: Instant
    seat_charge_id: UUID
    reason: ReopenReason


@final
@dataclass(frozen=True, slots=True)
class KeptSeat:
    """A seat kept for a rescuer whose share was refused (#640; Q113): until
    when, the payment they confirm, why it was refused — and what their time
    is for, to fix the card before the cut-off or to pay after it."""

    until: Instant
    seat_charge_id: UUID
    reason: ReopenReason
    time_to: TimeTo


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
    #: When its On request club's answer is due — on a booking ever put to it.
    answer_by: Instant | None = None
    #: The booking's stream version — what a rescue's attempts are counted by.
    version: int = 0
    #: Everybody whose refused share the game waits for, and until when —
    #: their time to pay (#625, #626) — and, on a booked game, everybody whose
    #: holding was refused, until their time to fix the card ends (#639).
    #: Empty while nobody's is awaited.
    paying: Mapping[UUID, Instant] = field(default_factory=dict)
    #: What their time is for — to fix the card, before the cut-off, or to pay,
    #: after it (#638); ``None`` while nobody's payment is awaited.
    time_to: TimeTo | None = None
    #: When it was booked — at the fill, or at its On request club's yes.
    #: ``None`` until it is.
    booked_at: Instant | None = None
    #: When its club cancelled it, once it did (#637).
    cancelled_at: Instant | None = None
    #: Everybody on the booked game whose holding was refused, their time to
    #: fix the card still to end — each with the payment to confirm (#639).
    cards_to_fix: Mapping[UUID, RefusedHolding] = field(default_factory=dict)
    #: Every rescuer whose share was refused and a seat kept for them (#640),
    #: as the booking records it — their time up too, until they take a seat
    #: or the game is off. ``kept_for`` reads it off the clock.
    kept: Mapping[UUID, KeptSeat] = field(default_factory=dict)
    #: Every rescuer whose kept seat ran out: none is kept for them again.
    keeps_ran_out: frozenset[UUID] = frozenset()

    @property
    def taken_at(self) -> Instant:
        """When the players' shares are taken (#637): the club's cut-off — or,
        for a game booked after it, when it was booked, which took them at
        once."""

        if self.booked_at is not None and self.booked_at > self.cut_off:
            return self.booked_at
        return self.cut_off

    @property
    def pay_by(self) -> Instant | None:
        """When the payment the game waits for is due — the earliest, if more
        than one is awaited."""

        return min(self.paying.values(), default=None)

    @property
    def players(self) -> tuple[UUID, ...]:
        return (*self.first_side, *self.second_side)

    @property
    def open_seats(self) -> int:
        """Seats a leaver left open on a booked game (#544) — and the seats
        nobody is In on, on a game gone back to filling while it fills (#624)."""

        if self.stage is BookingStage.FILLING_AGAIN and self.called_off is None:
            return SPORT_SPECS[self.sport].players - len(self.players)
        if self.stage is not BookingStage.SEAT_OPEN:
            return 0
        return SPORT_SPECS[self.sport].players - len(self.players)

    @property
    def filling_again(self) -> bool:
        """A full game that went back to filling before it was booked (Q106)."""

        return self.stage is BookingStage.FILLING_AGAIN

    @property
    def club_confirms(self) -> bool:
        """Its club confirms each game: it was put to the club once full — and,
        gone back to filling, is put to it again once full again (#624)."""

        return self.answer_by is not None

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

    def kept_for(self, player_id: UUID, *, now: Instant) -> KeptSeat | None:
        """The seat kept for this rescuer, while their time runs (#640)."""

        kept = self.kept.get(player_id)
        return kept if kept is not None and now < kept.until else None

    def keep_to_run_out(self, player_id: UUID, *, now: Instant) -> bool:
        """A seat kept for this rescuer whose time is up at ``now``, its
        running out not yet recorded (#640)."""

        return (
            player_id in self.kept
            and self.kept_for(player_id, now=now) is None
            and player_id not in self.keeps_ran_out
        )

    def seats_kept(self, *, now: Instant, but: UUID | None = None) -> int:
        """How many open seats are kept at ``now`` for rescuers whose time
        runs (#640) — ``but``'s own not counted."""

        return sum(
            1
            for player in self.kept
            if player != but and self.kept_for(player, now=now)
        )

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


class ShareState(StrEnum):
    """Where the players' shares of a booked game stand (#637; the mechanics
    §12.2, §14.1, Q113)."""

    #: Held on each card until the club's cut-off, which takes it — *30 zł ·
    #: free to leave until Fri 17:00*. Not paid.
    HELD = "HELD"
    #: The reader's card was only **checked** at the fill: their share is held
    #: from its Holding time — *40 zł held from Sat 19:00 · taken Wed 19:00*
    #: (#639). Not paid, and free to leave until the cut-off all the same.
    CHECKED = "CHECKED"
    #: Taken — at the cut-off, or at once for a game booked after it: *Paid ·
    #: 30 zł*.
    TAKEN = "TAKEN"


@final
@dataclass(frozen=True, slots=True)
class BookedMoney:
    """The money line (the mechanics §14.1)."""

    share_grosze: int
    #: Every seat's share was **taken** — *Paid · 30 zł*. Never while it is
    #: only held (#637).
    paid: bool
    #: The club's cut-off while it is still ahead — leaving before it takes
    #: nothing: the hold is let go — and ``None`` from it on, and for a game
    #: that filled after it.
    free_to_leave_until: Instant | None
    #: Whether the shares are held or taken (#637); ``None`` while nobody's
    #: money is on the game — waiting for its club or a payment, called off.
    share_state: ShareState | None = None
    #: When the shares are, or were, taken — the cut-off, or when a game booked
    #: after it was booked — whenever ``share_state`` is.
    taken_at: Instant | None = None
    #: When the reader's share is held — its Holding time — while it is only
    #: checked and that time is ahead (#639); ``None`` on every other line.
    held_from: Instant | None = None
    #: What everybody still in is given back — the whole share, on a game its
    #: club cancelled after its cut-off (#547); ``None`` where nothing is, and
    #: where nothing was taken (#637).
    refunded_grosze: int | None = None


class Leaving(StrEnum):
    """What *Leave the game* does, by when it is pressed (the mechanics §13) —
    said on the details before, and answered by the act after."""

    #: Before the club's cut-off: nothing is taken — the hold is let go (#637).
    BEFORE_THE_CUT_OFF = "BEFORE_THE_CUT_OFF"
    #: After it: refunded, less exactly the fee kept on the payment, only when
    #: somebody takes the seat.
    AFTER_THE_CUT_OFF = "AFTER_THE_CUT_OFF"
    #: While the club decides — or a payment is awaited (#625): nobody has
    #: paid, and leaving withdraws the yes.
    WHILE_WAITING_FOR_THE_CLUB = "WHILE_WAITING_FOR_THE_CLUB"


@final
@dataclass(frozen=True, slots=True)
class LateRefund:
    """What a player who leaves after the club's cut-off gets back if somebody
    takes their seat (Q113): their share less **exactly the fee kept on their
    payment** — *38,24 zł back (40 zł less the 1,76 zł kept on your
    payment)*."""

    refund_grosze: int
    fee_kept_grosze: int


@final
@dataclass(frozen=True, slots=True)
class LeaveTerms:
    """What leaving would cost the reader, said before they confirm — after the
    cut-off, *"If someone takes your seat, you get 38,24 zł back (40 zł less
    the 1,76 zł kept on your payment)"*, to the grosz (#641, Q113). **No quote
    before the cut-off** (#637): nothing is taken, so nothing comes back. **No
    figure while the fee kept is not yet known**: never an estimate."""

    kind: Leaving
    #: What comes back if somebody takes the seat — the share less exactly
    #: the fee kept on the payment; nought when nobody paid; ``None`` before
    #: the cut-off, and while that fee is not yet known.
    refund_grosze: int | None
    #: Exactly what was kept on the payment; ``None`` where ``refund_grosze``
    #: is.
    card_fee_grosze: int | None

#: The two statuses at which the game awaits its entry with every seat filled —
#: the forecast's (the mechanics §14.2: *as today, hidden while a seat is open*).
_FORECAST_SHOWN: Final = frozenset({HomeStatus.BOOKED, HomeStatus.NEEDS_RESULT})


def status_of(
    game: BookedGame, result: GameResult | None, *, now: Instant
) -> HomeStatus:
    """The card's status. ``result`` is ``None`` for a Game that could not be
    read — folded on the clock alone, so the card stays drawn — and for a
    booking that has no Game."""

    if game.stage is BookingStage.WAITING_FOR_THE_CLUB:
        return HomeStatus.WAITING_FOR_THE_CLUB
    if game.stage is BookingStage.WAITING_FOR_A_PAYMENT:
        return HomeStatus.WAITING_FOR_A_PAYMENT
    if game.called_off_reason(now) is not None:
        return HomeStatus.CALLED_OFF
    if game.stage is BookingStage.FILLING_AGAIN:
        # A full game gone back to filling: a seat open, nobody paid (Q106).
        return HomeStatus.SEAT_OPEN
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
        case ResultStage.UNSCORED | ResultStage.DISPUTED:
            return HomeStatus.UNCOUNTED
        case ResultStage.PLAYED_NO_SCORE:
            return HomeStatus.PLAYED_NO_SCORE
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
            # The payer's payment is the badge's already, as a payment to
            # confirm.
            | HomeStatus.WAITING_FOR_A_PAYMENT
            | HomeStatus.BOOKED
            | HomeStatus.COUNTED
            | HomeStatus.PLAYED_NO_SCORE
            | HomeStatus.CALLED_OFF
        ):
            return False
        case _:
            exhaustive(status)


def money_of(
    game: BookedGame, *, now: Instant, held_from: Instant | None = None
) -> BookedMoney:
    """The money line, **read off the clock** (#637; the mechanics §14.1,
    Q113): every seat of a booked game is held until the club's cut-off and
    taken at it — *30 zł · free to leave until Fri 17:00*, then *Paid · 30 zł*
    — nobody's money is on it while its club decides, once it turned it down or
    once it is called off, and everybody still in gets it all back only from a
    game its club cancelled after the cut-off had taken it (#547). A game short
    at its cut-off, or cancelled before it, took nothing. **The reader's card
    only checked at the fill** (#639) — ``held_from``, its Holding time — reads
    *held from Sat 19:00* until then, as the job holds it."""

    called_off = game.called_off_reason(now)
    on_it = (
        game.stage in (BookingStage.BOOKED, BookingStage.SEAT_OPEN)
        and called_off is None
    )
    taken = on_it and now >= game.cut_off
    checked = on_it and not taken and held_from is not None and now < held_from
    return BookedMoney(
        share_grosze=game.share_grosze,
        paid=taken,
        free_to_leave_until=game.cut_off if on_it and not taken else None,
        share_state=(
            None
            if not on_it
            else ShareState.TAKEN
            if taken
            else ShareState.CHECKED
            if checked
            else ShareState.HELD
        ),
        taken_at=game.taken_at if on_it else None,
        held_from=held_from if checked else None,
        refunded_grosze=(
            game.share_grosze
            if called_off is CalledOffReason.CANCELLED_BY_THE_CLUB
            and game.cancelled_at is not None
            and game.cancelled_at >= game.cut_off
            else None
        ),
    )


def answer_by_ahead(answer_by: Instant | None, *, now: Instant) -> Instant | None:
    """When an On request club must answer, while that is still ahead — *Bonarka
    answers by 20:45* (Q98). ``None`` from that moment on: the club can no
    longer say yes, and the line says only *nobody pays until Bonarka
    confirms* until the game is called off, as *free to leave until* leaves at
    the cut-off."""

    return answer_by if answer_by is not None and now < answer_by else None


def leaving_of(game: BookedGame, *, now: Instant) -> Leaving:
    """What leaving this game does at ``now`` — whether it may still be left
    at all is the caller's question."""

    if game.stage in (
        BookingStage.WAITING_FOR_THE_CLUB,
        BookingStage.WAITING_FOR_A_PAYMENT,
    ):
        return Leaving.WHILE_WAITING_FOR_THE_CLUB
    if now < game.cut_off:
        return Leaving.BEFORE_THE_CUT_OFF
    return Leaving.AFTER_THE_CUT_OFF


def leave_terms(
    game: BookedGame,
    status: HomeStatus,
    *,
    late_refund: LateRefund | None,
    now: Instant,
) -> LeaveTerms | None:
    """What *Leave the game* would cost now — ``None`` where there is no such
    button: once the hour has come, and on a game that is over. **Before the
    cut-off there is no quote** (#637): nothing is taken, and the hold is let
    go. **After it**, ``late_refund`` — the share less exactly the fee kept on
    the reader's payment — or no figure while that fee is not yet known
    (#641)."""

    if game.filling_again:
        # Its way out is a game still filling's: *Withdraw*, free (#624).
        return None
    leaving = leaving_of(game, now=now)
    if leaving is Leaving.WHILE_WAITING_FOR_THE_CLUB:
        return LeaveTerms(kind=leaving, refund_grosze=0, card_fee_grosze=0)
    if status not in (HomeStatus.BOOKED, HomeStatus.SEAT_OPEN) or now >= game.start:
        return None
    if leaving is Leaving.BEFORE_THE_CUT_OFF:
        return LeaveTerms(kind=leaving, refund_grosze=None, card_fee_grosze=None)
    return LeaveTerms(
        kind=leaving,
        refund_grosze=None if late_refund is None else late_refund.refund_grosze,
        card_fee_grosze=None if late_refund is None else late_refund.fee_kept_grosze,
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
    #: When its On request club must answer — the time its desk is given —
    #: while the game waits for it and the moment is ahead; ``None`` on every
    #: other status (Q98).
    answer_by: Instant | None = None
    #: When the payment the game waits for is due — *Waiting for one payment ·
    #: until 14:40* — while it waits for one; ``None`` on every other status
    #: (#625, Q111).
    pay_by: Instant | None = None


def state_of(
    game: BookedGame,
    result: GameResult | None,
    *,
    now: Instant,
    held_from: Instant | None = None,
) -> BookedState:
    """Everything Home and the details fold off the booking, its Game's result
    and the clock — once, so a card and its details cannot disagree.
    ``held_from`` is the reader's own share's Holding time, while it is only
    checked (#639)."""

    status = status_of(game, result, now=now)
    return BookedState(
        status=status,
        # A game gone back to filling asks nothing of those still In (Q106).
        needs_you=needs_you(status, result) and not game.filling_again,
        money=money_of(game, now=now, held_from=held_from),
        called_off=game.called_off_reason(now)
        if status is HomeStatus.CALLED_OFF
        else None,
        uncounted=uncounted_reason(game, status, result),
        cancel_reason=game.cancel_reason if status is HomeStatus.CALLED_OFF else None,
        # The booking keeps the moment once the club answered; the players
        # read it only while the answer is still to come.
        answer_by=(
            answer_by_ahead(game.answer_by, now=now)
            if status is HomeStatus.WAITING_FOR_THE_CLUB
            else None
        ),
        pay_by=game.pay_by if status is HomeStatus.WAITING_FOR_A_PAYMENT else None,
    )


#: How long an ended game keeps its card after its hour's end: **a day** — the
#: phone's own shelf (``onHome``), measured from the one instant every ending
#: has, since nothing dates the end of a booking.
ENDED_SHELF_LIFE: Final = timedelta(hours=24)

#: The four ends a card can say: a game that will not be played, or whose
#: result is settled — the phone's ``ended``. Every other status is live.
_ENDED: Final = frozenset(
    {
        HomeStatus.COUNTED,
        HomeStatus.UNCOUNTED,
        HomeStatus.PLAYED_NO_SCORE,
        HomeStatus.CALLED_OFF,
    }
)


def on_home(game: BookedGame, state: BookedState, *, now: Instant) -> bool:
    """Whether Home sends this card at ``now`` (#613): every live game, an
    ended one until a day after its hour's end — the phone's own rule — and
    **any game that needs the reader**, so the badge never counts a card that
    was not sent.

    That last clause is the phone's rule in all but one case: an *uncounted*
    game whose reader may still dispute a report of not coming outlives its
    day by up to another — sent, and on the badge, after the phone's Home has
    shelved it (story S-33 owns what the phone draws for it).
    """

    if state.status not in _ENDED or state.needs_you:
        return True
    return now < game.start + GAME_LENGTH + ENDED_SHELF_LIFE


def on_home_since(now: Instant) -> Instant:
    """The earliest hour a game Home sends at ``now`` can have started —
    **unless a score was put on its table again**, which the Games context's
    clocks say where to look for (``scores_still_waiting_since``).

    Read off how long a booked game needs its players, never written here as a
    number: a game that started earlier is past its result's day and its
    answer's, its report's dispute, and the phone's shelf, so it is a card
    nobody would see.
    """

    return instant(
        now - max(A_BOOKED_GAME_NEEDS_ITS_PLAYERS_FOR, GAME_LENGTH + ENDED_SHELF_LIFE)
    )


def shows_forecast(status: HomeStatus) -> bool:
    """Whether the details draw the balance forecast: while the game awaits its
    entry with every seat filled."""

    return status in _FORECAST_SHOWN


def as_filling_again(
    game: BookedGame,
    *,
    in_: Sequence[UUID],
    standing: Standing,
    paying: Mapping[UUID, Instant] | None = None,
    time_to: TimeTo | None = None,
) -> BookedGame:
    """**A full game that went back to filling, as its proposal has it now**
    (#624, Q106) — the booking keeps who was In when its request was taken
    back; the proposal, everything since. The people In now stand on the sides
    they were drawn on, anybody In since in the first place free; somebody who
    took their yes back since is off them. **Called off, nobody paid**, once
    the proposal is over before it was full again: its book-by passed — or a
    seat opened after it, while the club decided — or its court went to
    another game. A payer whose time to pay still runs (#625) is in
    ``paying``, as the proposal has it, and what it is for in ``time_to``
    (#638)."""

    invariant(
        game.stage is BookingStage.FILLING_AGAIN,
        f"{game.booking_id} is folded as filling again from {game.stage}",
    )
    per_side = SPORT_SPECS[game.sport].players // 2
    first = [player for player in game.first_side if player in in_]
    second = [player for player in game.second_side if player in in_]
    for player in in_:
        if player not in first and player not in second:
            (first if len(first) < per_side else second).append(player)
    return replace(
        game,
        first_side=tuple(first),
        second_side=tuple(second),
        called_off=_filling_again_ended(game, standing),
        paying=game.paying if paying is None else dict(paying),
        time_to=game.time_to if paying is None else time_to,
    )


def _filling_again_ended(
    game: BookedGame, standing: Standing
) -> CalledOffReason | None:
    """How a game gone back to filling ended before it was full again, as its
    card says it — ``None`` while it fills."""

    match standing:
        case Standing.FILLING | Standing.WITHDRAWN:
            # A post its poster withdrew with nobody else In: nobody is on it
            # to read it.
            return None
        case Standing.EXPIRED:
            return CalledOffReason.BOOK_BY_PASSED
        case Standing.COURT_HOUR_LOST:
            return CalledOffReason.COURT_HOUR_LOST
        case Standing.FILLED | Standing.TURNED_DOWN:
            # Full again, it is asked of its club again — a new request, and
            # a booking no longer taken back — before it is booked or turned
            # down.
            invariant(False, f"{game.booking_id} is taken back and {standing.value}")
            return None
        case _:
            exhaustive(standing)


def without_a_booking(proposal: Proposal, *, now: Instant) -> BookedGame:
    """**A game at a club that books at once that waited for a payment**
    (#625; Q111) — full when its share was refused, so its players were told
    *It's a game!* — has **no booking** until it books: no court is held, as for
    any game still filling. So its card is folded off its proposal: *Waiting
    for one payment* while the time to pay runs and every seat is In; *Seat
    open* — gone back to filling — once the time ran out or somebody else's
    seat opened; *called off*, nobody paid, once it ends before it is full
    again — its book-by (*a payment that didn't come in time* when the time ran
    out on it), or its court gone to another game. The people In stand in the
    order they said yes; nothing about the money is anybody's yet."""

    invariant(
        proposal.payment_awaited_at is not None,
        f"{proposal.proposal_id} never waited for a payment",
    )
    per_side = proposal.seats_per_side
    standing = proposal.standing_at(now)
    called_off: CalledOffReason | None = None
    if standing is Standing.EXPIRED:
        called_off = (
            CalledOffReason.PAYMENT_NOT_IN_TIME
            if proposal.ran_out_for_good or proposal.paying
            else CalledOffReason.BOOK_BY_PASSED
        )
    elif standing is Standing.COURT_HOUR_LOST:
        called_off = CalledOffReason.COURT_HOUR_LOST
    waiting = called_off is None and proposal.waiting_for_a_payment
    return BookedGame(
        booking_id=proposal.proposal_id,
        pool_id=proposal.pool.id,
        club_id=proposal.club_id,
        # No court is held for it, and none given.
        court_name="",
        sport=proposal.sport,
        kind=proposal.kind,
        start=proposal.start,
        share_grosze=proposal.share_grosze,
        first_side=proposal.yeses[:per_side],
        second_side=proposal.yeses[per_side:],
        # Nobody paid, so nothing reads when leaving stops being free.
        cut_off=proposal.start,
        game_id=None,
        stage=(
            BookingStage.WAITING_FOR_A_PAYMENT
            if waiting
            else BookingStage.FILLING_AGAIN
        ),
        called_off=called_off,
        paying=proposal.payments_due,
        time_to=proposal.time_to,
    )
