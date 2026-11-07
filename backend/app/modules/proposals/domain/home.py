"""Home's statuses and money lines — the rules that need no I/O (#542; the
mechanics §14.1–§14.2; the screens A4.1, A8).

**Home holds the player's games from the moment they fill** (``docs/adr/0189``
§6), and each card says one status. **The status is folded on every read** from
the booking, its ordinary Game's result and the clock — derived, never stored:
*Booked* until the game's hour, then the result states exactly as today's cards
say them, since after the fill everything that happens to a game today happens to
it unchanged (Q6).

**No game waits for its club** (``docs/adr/0196`` §1): the last yes books it at
every club (#669).
**A game may wait for one payment** (#625; Q111): a share refused as the game
filled gives its player time to pay, and the game is *Waiting for one payment*
on all four's Home until it comes, nobody paid. It has no booking until it
books, so its card is folded off its proposal (``without_a_booking``); and when
the time runs out, or somebody else's seat opens, it is *Seat open* — a full
game gone back to filling (Q106): nobody paid, and it asks nothing of the
people still In.
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

from collections.abc import Mapping
from dataclasses import dataclass, field
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

    #: Full, and one player's share was refused: their time to pay runs, and
    #: nobody pays until it is in (#625; Q111).
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

    #: A share was refused as it filled and its player's time to pay runs: no
    #: booking, no Game, nobody paid (#625).
    WAITING_FOR_A_PAYMENT = "WAITING_FOR_A_PAYMENT"
    BOOKED = "BOOKED"
    #: Booked, and somebody left: a seat is open (#544).
    SEAT_OPEN = "SEAT_OPEN"
    CALLED_OFF = "CALLED_OFF"
    #: A full game that waited for a payment went back to filling — the time
    #: ran out, or somebody else's seat opened: no booking, nobody paid, its
    #: people still In keeping their places (#625, Q106).
    FILLING_AGAIN = "FILLING_AGAIN"


class CalledOffReason(StrEnum):
    """Why a game will not be played (the mechanics §14.1)."""

    #: A seat that opened before the club's cut-off was still open at it:
    #: everybody still in is refunded in full (#544).
    SHORT_AT_THE_CUT_OFF = "SHORT_AT_THE_CUT_OFF"
    #: The club cancelled it, with its reason: everybody still in is refunded
    #: in full, and it is on nobody's record (#547).
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"
    #: It went back to filling and its book-by came before it was full again:
    #: nobody paid (#625, Q104, Q106).
    BOOK_BY_PASSED = "BOOK_BY_PASSED"
    #: It went back to filling and its court went to another game before it
    #: was full again — or before the payment it waited for came in: nobody
    #: paid, and its people are dealt a new card first (#625).
    COURT_HOUR_LOST = "COURT_HOUR_LOST"
    #: A payment it waited for did not come in time and it could no longer
    #: fill — the book-by had come (#625; Q112): nobody paid.
    PAYMENT_NOT_IN_TIME = "PAYMENT_NOT_IN_TIME"
    #: A friends game its sender called off before the cut-off (#751): every
    #: hold let go, nobody paid.
    BY_THE_SENDER = "BY_THE_SENDER"


class PayMode(StrEnum):
    """How a friends game's court is paid (``docs/adr/0202`` §6): each friend
    their own share on accepting, the sender covering what is unpaid at the
    cut-off — or the sender the whole court."""

    SPLIT_THE_COST = "SPLIT_THE_COST"
    WHOLE_COURT = "WHOLE_COURT"


class InvitationAnswer(StrEnum):
    """How an invited seat of a friends game was answered (#751)."""

    WAITING = "WAITING"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    RAN_OUT = "RAN_OUT"
    #: Somebody else took the seat first (#752).
    TAKEN = "TAKEN"


class SeatEmptied(StrEnum):
    """How a friends game's seat came to be empty (#752)."""

    DECLINED = "DECLINED"
    RAN_OUT = "RAN_OUT"
    LEFT = "LEFT"


class SeatState(StrEnum):
    """Where one seat of a friends game stands for everybody on it (#751; the
    words §29.8) — *In*, *waiting · 3 h left*, *can't make it*, *didn't
    answer*, *empty*."""

    IN = "IN"
    #: Held for its invited friend, their clock running.
    WAITING = "WAITING"
    #: Its friend said *Not this time*.
    CANT_MAKE_IT = "CANT_MAKE_IT"
    #: Its friend's clock ended without an answer — whether or not the job has
    #: recorded it.
    DIDNT_ANSWER = "DIDNT_ANSWER"
    #: Nobody's: its friend left it (#752).
    EMPTY = "EMPTY"
    #: Open to the group — a rescue anybody who fits may take (#752): opened by
    #: its sender, by the cut-off, or a leaver's seat on a game no longer
    #: covered.
    SEAT_OPEN = "SEAT_OPEN"


@final
@dataclass(frozen=True, slots=True)
class InvitedSeat:
    """A seat of a friends game held for one friend (#751): the side the card
    drew them on, until when they may answer, and how they did — or, invited
    later into an empty seat (#752), which seat and by whom."""

    player_id: UUID
    side: str
    until: Instant
    answer: InvitationAnswer = InvitationAnswer.WAITING
    #: The empty seat it is into, named by whose it was (#752) — ``None`` for
    #: the card's own seat for them.
    seat_of: UUID | None = None
    #: Who invited them: ``None`` for the card's — the sender's.
    invited_by: UUID | None = None

    @property
    def seat(self) -> UUID:
        """The seat it is for, by whose it is."""

        return self.player_id if self.seat_of is None else self.seat_of

    def waiting_at(self, now: Instant) -> bool:
        return self.answer is InvitationAnswer.WAITING and now < self.until


@final
@dataclass(frozen=True, slots=True)
class EmptySeat:
    """A friends game's seat nobody holds and nobody opened to the group
    (#752): the sender's to fill — invite a friend, or open it — until the
    cut-off, named by whose it was."""

    seat_of: UUID
    side: str
    since: Instant
    how: SeatEmptied


@final
@dataclass(frozen=True, slots=True)
class SeatInvitation:
    """A friend invited into an empty seat, still to answer (#752)."""

    player_id: UUID
    until: Instant
    #: Who invited them — anybody In.
    invited_by: UUID


@final
@dataclass(frozen=True, slots=True)
class FriendsSeat:
    """One seat of a friends game as everybody on it reads it (#751): whose
    face it draws, on which side, how it stands, and — while it waits — until
    when. **An empty seat** (#752) is named by whose it was — ``seat_of``, what
    an invitation or *Open to the group* names — with every invitation into it
    still waiting."""

    player_id: UUID
    side: str
    state: SeatState
    until: Instant | None = None
    #: The seat's name for an invitation into it or its opening (#752) — the
    #: friend it was for, or the leaver — ``None`` on a seat somebody holds,
    #: or still invited to its friend.
    seat_of: UUID | None = None
    invitations: tuple[SeatInvitation, ...] = ()


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
    #: Somebody tapped *isn't here yet* at the court and they never arrived
    #: (#657): **Didn't come** — the game takes no score and never counts,
    #: provisionally for a day while their *I was there* may be confirmed.
    DIDNT_COME = "DIDNT_COME"


class ResultStage(StrEnum):
    """Where a booked game's ordinary Game stands, in this context's words."""

    #: Nobody has said it happened yet.
    ENTRY_OPEN = "ENTRY_OPEN"
    #: They played, and a score is on the table inside its window.
    SCORE_TO_ANSWER = "SCORE_TO_ANSWER"
    CONFIRMED = "CONFIRMED"
    #: Two scores named different winners and neither side gave way (#654):
    #: no Level moves.
    DISPUTED = "DISPUTED"
    #: A full court nobody recorded before its entry window closed (#655).
    PLAYED_NO_SCORE = "PLAYED_NO_SCORE"
    CALLED_OFF = "CALLED_OFF"
    #: Its hour came with a seat open: no result can be told (#544).
    STARTED_SHORT = "STARTED_SHORT"
    #: Somebody was tapped *isn't here yet* and is still awaited, in the first
    #: thirty minutes (#657): the game is being played.
    NOT_HERE_YET = "NOT_HERE_YET"
    #: Somebody Didn't come (#657): the game takes no score and never counts.
    DIDNT_COME = "DIDNT_COME"


@final
@dataclass(frozen=True, slots=True)
class GameResult:
    """A booked game's result as one player reads it."""

    stage: ResultStage
    #: The other side's score waits on this player's agreement — the *result to
    #: confirm* that is theirs to clear (the mechanics §3). Only ever true with
    #: ``SCORE_TO_ANSWER``.
    awaits_your_agreement: bool
    #: Attendance waits on this player (#657): their own *I'm here* while they
    #: are awaited, their own *I was there* to say, or somebody else's to
    #: confirm. Only ever true with ``NOT_HERE_YET`` or ``DIDNT_COME``.
    attendance_waits_on_you: bool = False


@final
@dataclass(frozen=True, slots=True)
class OpenSeat:
    """A seat a leaver left open on a booked game (#544, #545): the side it
    is on, and who left it when — which against the cut-off says whether the
    leaver is refunded when somebody takes it. On a friends game (#752) it may
    be an empty seat opened to the group, named by whose it was, and
    **covered** by its sender's card: a taker after the cut-off refunds him."""

    #: ``A`` — the first side — or ``B``.
    side: str
    left_by: UUID
    left_at: Instant
    covered: bool = False


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
    #: The ordinary Game the booking opened — ``None`` on a game that waited
    #: for a payment and has no booking (#625).
    game_id: UUID | None
    #: The court's kind, indoor or outdoor, which follows a move (#671, Q122)
    #: — meaningful only where a court was given (``court_given``).
    indoor: bool = False
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
    #: The booking's stream version — what a rescue's attempts are counted by.
    version: int = 0
    #: Everybody whose refused share the game waits for, and until when —
    #: their time to pay (#625) — and, on a booked game, everybody whose
    #: holding was refused, until their time to fix the card ends (#639).
    #: Empty while nobody's is awaited.
    paying: Mapping[UUID, Instant] = field(default_factory=dict)
    #: What their time is for — to fix the card, before the cut-off, or to pay,
    #: after it (#638); ``None`` while nobody's payment is awaited.
    time_to: TimeTo | None = None
    #: When it was booked — at the fill. ``None`` until it is.
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
    #: A friends game's sender (#751) — ``None`` on a game a fill booked.
    sender: UUID | None = None
    #: How a friends game's court is paid — ``None`` on a fill's.
    pay_mode: PayMode | None = None
    #: A friends game's invited seats, in the card's order, each with its
    #: answer — then every invitation into an empty seat (#752).
    invited: tuple[InvitedSeat, ...] = ()
    #: A friends game's seats nobody holds and nobody opened (#752).
    empty: tuple[EmptySeat, ...] = ()
    #: A friends game its sender's card covers (#751, #752): never called off
    #: at its cut-off for an empty seat, which opens to the group then.
    covering: bool = False

    @property
    def is_friends_game(self) -> bool:
        """Booked by its sender at send (#751), not by a fill."""

        return self.sender is not None

    def invitation_of(self, player_id: UUID) -> InvitedSeat | None:
        return next(
            (seat for seat in self.invited if seat.player_id == player_id), None
        )

    def invited_now(self, player_id: UUID, *, now: Instant) -> InvitedSeat | None:
        """This player's invitation while it still waits on them at ``now`` —
        on a game still booked."""

        seat = self.invitation_of(player_id)
        if (
            seat is None
            or not seat.waiting_at(now)
            or self.stage not in (BookingStage.BOOKED, BookingStage.SEAT_OPEN)
            or self.called_off_reason(now) is not None
        ):
            return None
        return seat

    def seat_states(
        self, *, now: Instant, reader: UUID | None = None
    ) -> tuple[FriendsSeat, ...]:
        """Every seat of a friends game as it stands at ``now`` (the words
        §29.8; #752): each player In — the sender first — then each seat the
        card still holds for its friend, then each empty seat, then each seat
        open to the group (one still waiting for its friend among them, that
        friend among its invitations), every one of them once. An empty or open seat is
        drawn with the face of whose it was — or, for a ``reader`` invited into
        it, with theirs, still waiting. Empty on a game a fill booked."""

        if self.sender is None:
            return ()
        on = (*self.first_side, *self.second_side)
        holding = sorted(on, key=lambda player: player != self.sender)
        seats = [
            FriendsSeat(
                player_id=player,
                side="A" if player in self.first_side else "B",
                state=SeatState.IN,
            )
            for player in holding
        ]
        open_ = {left.left_by for left in self.open}
        for seat in self.invited:
            if (
                seat.seat_of is not None
                or seat.answer is not InvitationAnswer.WAITING
                # Opened while it waited for them (#752): drawn as open below.
                or seat.player_id in open_
            ):
                continue
            # The card's own seat for its friend, waiting — or, its time up,
            # *didn't answer* whether or not the job has recorded it.
            ended = now >= seat.until
            seats.append(
                FriendsSeat(
                    player_id=seat.player_id,
                    side=seat.side,
                    state=SeatState.DIDNT_ANSWER if ended else SeatState.WAITING,
                    until=None if ended else seat.until,
                    seat_of=seat.player_id if ended else None,
                )
            )
        vacancies = [
            (empty.seat_of, empty.side, _EMPTIED_READS[empty.how])
            for empty in self.empty
        ] + [(left.left_by, left.side, SeatState.SEAT_OPEN) for left in self.open]
        for seat_of, side, state in vacancies:
            waiting = tuple(
                SeatInvitation(
                    player_id=one.player_id,
                    until=one.until,
                    invited_by=one.invited_by or seat_of,
                )
                for one in self.invited
                if one.seat == seat_of and one.waiting_at(now)
            )
            yours = next((one for one in waiting if one.player_id == reader), None)
            seats.append(
                FriendsSeat(
                    player_id=seat_of if yours is None else yours.player_id,
                    side=side,
                    state=state if yours is None else SeatState.WAITING,
                    until=None if yours is None else yours.until,
                    seat_of=seat_of,
                    invitations=waiting,
                )
            )
        return tuple(seats)

    def vacancy(self, seat_of: UUID, *, now: Instant) -> FriendsSeat | None:
        """The seat named ``seat_of`` while nobody holds it at ``now`` (#752) —
        empty, open to the group, or a card seat whose friend's time is up."""

        return next(
            (
                seat
                for seat in self.seat_states(now=now)
                if seat.seat_of == seat_of and seat.state is not SeatState.WAITING
            ),
            None,
        )

    def may_invite(self, player_id: UUID, *, now: Instant) -> bool:
        """*Invite a friend* (#752; the friends mechanics §10.1, §10.3): anybody
        In, on a friends game still to be played, while a seat is empty —
        before the cut-off or after it."""

        return (
            self.is_friends_game
            and player_id in self.players
            and self.called_off_reason(now) is None
            and self.stage in (BookingStage.BOOKED, BookingStage.SEAT_OPEN)
            and now < self.start
        )

    def may_open(self, player_id: UUID, seat: FriendsSeat, *, now: Instant) -> bool:
        """*Open to the group* (#752): the sender's, while he is In and his card
        covers the game, before the cut-off, on a seat nobody holds and nobody
        opened yet."""

        return (
            self.covering
            and self.sender == player_id
            and player_id in self.players
            and seat.seat_of is not None
            and seat.state
            in (SeatState.CANT_MAKE_IT, SeatState.DIDNT_ANSWER, SeatState.EMPTY)
            and self.called_off_reason(now) is None
            and now < self.cut_off
            and now < self.start
        )

    @property
    def whole(self) -> bool:
        """Every seat held by somebody In."""

        return len(self.players) == SPORT_SPECS[self.sport].players

    def covers_due_at(self, now: Instant) -> bool:
        """A friends game whose covers are decided at ``now`` (#751): its
        cut-off has come, and no invitation still waits — one sent after the
        cut-off decides them when its invitations end."""

        return (
            self.is_friends_game
            and now >= self.cut_off
            # The card's own invitations: one into an empty seat waits on a
            # seat the cover already pays (#752).
            and not any(
                seat.waiting_at(now) for seat in self.invited if seat.seat_of is None
            )
        )

    def may_be_called_off_by(self, player_id: UUID, *, now: Instant) -> bool:
        """*Call it off* (#751): the sender's, while he is In, on a friends game
        still on, before the club's cut-off and the hour."""

        return (
            self.sender == player_id
            and player_id in self.players
            and self.stage in (BookingStage.BOOKED, BookingStage.SEAT_OPEN)
            and self.called_off_reason(now) is None
            and now < self.cut_off
            and now < self.start
        )

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
        nobody is In on, on a game gone back to filling while it fills (#625)."""

        if self.stage is BookingStage.FILLING_AGAIN and self.called_off is None:
            return SPORT_SPECS[self.sport].players - len(self.players)
        if self.stage is not BookingStage.SEAT_OPEN:
            return 0
        # A friends game's seat still empty, or still invited, is none (#752).
        return len(self.open)

    @property
    def filling_again(self) -> bool:
        """A full game that went back to filling before it was booked (Q106)."""

        return self.stage is BookingStage.FILLING_AGAIN

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
        """Whether the players have a court number: a booked game has one, and a
        game that waited for a payment has no booking, so none (#625)."""

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

    @property
    def planned_sides(self) -> tuple[tuple[UUID, ...], tuple[UUID, ...]]:
        """The sides as the game is drawn: everybody In — and, on a friends
        game, a face for every seat nobody holds, on its own side (#751,
        #752), so the court has its four faces."""

        return self.planned_sides_for(None, now=None)

    def planned_sides_for(
        self, reader: UUID | None, *, now: Instant | None
    ) -> tuple[tuple[UUID, ...], tuple[UUID, ...]]:
        """The sides drawn for ``reader``: every seat's face from
        ``seat_states`` — a seat they were invited into drawn with theirs."""

        if not self.is_friends_game:
            return self.first_side, self.second_side
        seats = self.seat_states(now=self.start if now is None else now, reader=reader)
        absent = [seat for seat in seats if seat.player_id not in self.players]
        return (
            (*self.first_side, *(s.player_id for s in absent if s.side == "A")),
            (*self.second_side, *(s.player_id for s in absent if s.side == "B")),
        )

    def seen_by(self, player_id: UUID, *, now: Instant | None = None) -> Sides:
        """The sides as this player reads them: theirs first, with them first
        on it — *You + Piotr vs Inés + Bartek*. A friends game draws a face for
        each seat nobody holds (``planned_sides_for``)."""

        first, second = self.planned_sides_for(player_id, now=now)
        yours, theirs = (second, first) if player_id in second else (first, second)
        if player_id in yours:
            yours = (player_id, *(other for other in yours if other != player_id))
        return Sides(yours=yours, theirs=theirs)


#: How an empty seat reads, by how it emptied (the words §29.8).
_EMPTIED_READS: Final = {
    SeatEmptied.DECLINED: SeatState.CANT_MAKE_IT,
    SeatEmptied.RAN_OUT: SeatState.DIDNT_ANSWER,
    SeatEmptied.LEFT: SeatState.EMPTY,
}


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
    #: While a payment is awaited (#625): nobody has paid, and leaving
    #: withdraws the yes.
    WHILE_WAITING_FOR_A_PAYMENT = "WHILE_WAITING_FOR_A_PAYMENT"


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
        case ResultStage.NOT_HERE_YET:
            # In its first half hour, waiting on somebody: still being played.
            return HomeStatus.NEEDS_RESULT
        case ResultStage.SCORE_TO_ANSWER:
            return HomeStatus.CONFIRM_THE_RESULT
        case ResultStage.CONFIRMED:
            return HomeStatus.COUNTED
        case ResultStage.DISPUTED:
            return HomeStatus.UNCOUNTED
        case ResultStage.PLAYED_NO_SCORE:
            return HomeStatus.PLAYED_NO_SCORE
        case ResultStage.CALLED_OFF:
            return HomeStatus.CALLED_OFF
        case ResultStage.STARTED_SHORT:
            return HomeStatus.UNCOUNTED
        case ResultStage.DIDNT_COME:
            # The game takes no score and never counts — unless a confirmed
            # *I was there* brings it back, when it is read again (#657).
            return HomeStatus.UNCOUNTED
        case _:
            exhaustive(stage)


def uncounted_reason(
    game: BookedGame, status: HomeStatus, result: GameResult | None
) -> UncountedReason | None:
    """Why an *uncounted* card says so, when nobody disagreed about a score:
    its hour came with a seat open, or somebody Didn't come (#657)."""

    if status is not HomeStatus.UNCOUNTED:
        return None
    if game.stage is BookingStage.SEAT_OPEN:
        return UncountedReason.SEAT_EMPTY
    if result is not None and result.stage is ResultStage.DIDNT_COME:
        return UncountedReason.DIDNT_COME
    return None


def needs_you(
    status: HomeStatus, result: GameResult | None, *, kind: SearchMode
) -> bool:
    """Whether this game is one of the games that need the player — Home's
    badge (the mechanics §3): a result to enter on a Competitive game, a score
    waiting on their agreement, a seat open in their game, an *I'm here* or a
    late claim theirs to make or to confirm (#657). ``kind`` is stated by the
    caller, never defaulted: **a For fun game asks nothing** (#654), so its
    hour passing with no score is a result anybody may add and nobody owes."""

    match status:
        case HomeStatus.NEEDS_RESULT:
            if result is not None and result.stage is ResultStage.NOT_HERE_YET:
                # No score is taken while somebody is awaited: only the player
                # awaited has something to do — *I'm here*.
                return result.attendance_waits_on_you
            return kind is not SearchMode.FOR_FUN
        case HomeStatus.SEAT_OPEN:
            return True
        case HomeStatus.CONFIRM_THE_RESULT:
            return result is not None and result.awaits_your_agreement
        case HomeStatus.UNCOUNTED:
            # *I was there* to say, or somebody else's to confirm, while the
            # late claim's day runs.
            return result is not None and result.attendance_waits_on_you
        case (
            # The payer's payment is the badge's already, as a payment to
            # confirm.
            HomeStatus.WAITING_FOR_A_PAYMENT
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
    — nobody's money is on it while it waits for a payment, or once it is
    called off, and everybody still in gets it all back only from a
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


def leaving_of(game: BookedGame, *, now: Instant) -> Leaving:
    """What leaving this game does at ``now`` — whether it may still be left
    at all is the caller's question."""

    if game.stage is BookingStage.WAITING_FOR_A_PAYMENT:
        return Leaving.WHILE_WAITING_FOR_A_PAYMENT
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
        # Its way out is a game still filling's: *Withdraw*, free (Q106).
        return None
    leaving = leaving_of(game, now=now)
    if leaving is Leaving.WHILE_WAITING_FOR_A_PAYMENT:
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
    #: Why it will not be played, once it will not (#544).
    called_off: CalledOffReason | None = None
    #: Why it is uncounted with nobody disagreeing (#544).
    uncounted: UncountedReason | None = None
    #: Why the club cancelled it, when it did (#547).
    cancel_reason: ClubCancelReason | None = None
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
        needs_you=needs_you(status, result, kind=game.kind) and not game.filling_again,
        money=money_of(game, now=now, held_from=held_from),
        called_off=game.called_off_reason(now)
        if status is HomeStatus.CALLED_OFF
        else None,
        uncounted=uncounted_reason(game, status, result),
        cancel_reason=game.cancel_reason if status is HomeStatus.CALLED_OFF else None,
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
    was not sent. A late *I was there* closes a day after the tap window
    (#657), before the shelf does, so the last clause sends nothing the
    phone's own rule would not.
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
    answer's, its late claim's (#657), and the phone's shelf, so it is a card
    nobody would see.
    """

    return instant(
        now - max(A_BOOKED_GAME_NEEDS_ITS_PLAYERS_FOR, GAME_LENGTH + ENDED_SHELF_LIFE)
    )


def shows_forecast(status: HomeStatus) -> bool:
    """Whether the details draw the balance forecast: while the game awaits its
    entry with every seat filled."""

    return status in _FORECAST_SHOWN


def without_a_booking(proposal: Proposal, *, now: Instant) -> BookedGame:
    """**A game that waited for a payment** (#625; Q111) — full when its share
    was refused, so its players were told *It's a game!* — has **no booking**
    until it books: no court is held, as for any game still filling. So its
    card is folded off its proposal: *Waiting for one payment* while the time
    to pay runs and every seat is In; *Seat open* — gone back to filling — once
    the time ran out or somebody else's seat opened; *called off*, nobody paid,
    once it ends before it is full again — its book-by (*a payment that didn't
    come in time* when the time ran out on it), or its court gone to another
    game. The people In stand in the order they said yes; nothing about the
    money is anybody's yet."""

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
        # No court is held for it, and none given — nor a kind.
        court_name="",
        indoor=False,
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
