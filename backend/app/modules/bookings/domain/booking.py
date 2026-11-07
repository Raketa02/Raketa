"""The Booking aggregate — event-sourced, one stream per filled proposal
(``docs/adr/0189`` §5; the mechanics §11).

**A booking is the game a full card became**, and its id is the card's. It holds
what the fill decided and nothing a reader could derive: the court and its
number, who sits on which side, the cut-off as the club set it when the game
filled, and the Game it opened. Its money is the Seat charges' (``payments``),
its result the Game's (``games``) — after the fill, *everything that happens to a
game today happens to it unchanged* (Q6).

**Born booked** (#541), at every club: the last yes books the game the moment
it lands, and no club confirms it (``docs/adr/0196`` §1). On request, which
put a full game to the club's desk and waited for its answer, is removed — its
events left with it, the local store reset (#669).

**A player leaves a booked game** (#544; the mechanics §12.3, §13): their seat
opens — *seat open* — and the game is still the others'. **A game plays full or
not at all**: a seat that opened before the club's cut-off and is still open at
it calls the game off (``CalledOffAtCutOff``), the court the club's again; a
seat that opened after the cut-off leaves the game going ahead short. Whether a
game is **short at its cut-off** is read off the departures and the clock, so
every read says it from the cut-off on, whether or not the job has recorded it.

**A player whose holding was refused has their time to fix the card** (#639;
Q113): the game stays booked, their seat theirs alone until then. Fixed in
time, it is simply theirs again; run out, it opens as a leaver's does — before
the cut-off, which is how the record counts it.

**An open seat is a rescue** (#545; the mechanics §10.1): somebody else takes
it, their share held or taken like the others', and sits where the leaver sat.
**The seat that opened first is taken first** — the leavers are refunded in the
order they left — and a seat stays open until the cut-off whatever their
number, then until the start. A game whose seats are all taken is whole again,
and *short at its cut-off* is read off the seats still open. **A rescuer whose
share was refused keeps a seat** for themselves alone (#640): offered to nobody
else until their time to fix the card — or, after the cut-off, to pay — runs
out, never past the start. It is a seat, not a particular one: the seats are
still taken in the order they opened.

**A friends game is born booked the moment it is sent** (#751;
``docs/adr/0202`` §5–§6): its own id, no proposal before it, the sender **In**
and every other seat an **invited seat** — held for its friend for 24 hours,
never past the cut-off (or, sent after it, the start), and answered *accepted*,
*declined* or *run out*. An invited seat is neither held nor open: **it is no
rescue**, so the game is ``BOOKED`` with fewer players than seats, and never
called off at its cut-off for it — the sender's **cover** pays a seat its own
player hasn't (the money's, ``payments``). The sender may call it off before the
cut-off (``CalledOff.BY_THE_SENDER``). What becomes of an empty seat — another
invitation, a rescue — is #752's.

**The club runs it** (#547; the mechanics §16.7–§16.10): it may **move** the
game to another court of its sport at the same hour, or **cancel** it with its
reason — everybody still in refunded in full, on nobody's record — until the
game starts. Its desk no longer checks players in (#651). *Played* is read
off the clock — a booked game whose hour has passed — and never recorded: there
is nothing to decide about it, and a recorded copy would be wrong for the whole
gap until something wrote it.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta
from enum import StrEnum
from typing import Final, Iterable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import SPORT_SPECS, Instant, Sport, instant, invariant
from app.modules.bookings.domain.events import (
    BookedByAFriend,
    BookingConfirmed,
    CalledOffAtCutOff,
    CalledOffBySender,
    CancelledByClub,
    CardFixed,
    CardToFix,
    CourtMoved,
    InvitedSeatAccepted,
    InvitedSeatDeclined,
    InvitedSeatRanOut,
    PlayerCheckedIn,
    KeptSeatRanOut,
    NoSaidToTheSeat,
    SeatKept,
    SeatLeft,
    SeatRescued,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder

#: How long an invited friend has to answer (the friends mechanics §9, Q30):
#: a day, never past the cut-off — or the start, for an invitation made after
#: it. Domain, never configuration.
TIME_TO_ANSWER: Final = timedelta(hours=24)


def invited_until(at: Instant, *, cut_off: Instant, start: Instant) -> Instant:
    """When an invitation made at ``at`` ends: 24 hours on, **never past the
    cut-off** when it is made before it, and never past the start when made
    after it (call 9)."""

    last = cut_off if at < cut_off else start
    return instant(min(at + TIME_TO_ANSWER, last))


@dataclass(frozen=True, slots=True)
class BookedCourt:
    """The court a game is booked on: its id, what the club calls it, and its
    **kind** — indoor or outdoor — which the players always see on a booked
    game (#671; the mechanics §5.2, Q122)."""

    court_id: UUID
    name: str
    indoor: bool

    def may_move_to(self, court: "BookedCourt") -> bool:
        """Whether a game on this court may move to ``court`` for its kind
        (the mechanics §16.4, Q122, *a call*): the same kind, or indoor for an
        outdoor game — never outdoors from indoors, which would be a different
        game to the players."""

        return court.indoor or not self.indoor


@dataclass(frozen=True, slots=True)
class FreeCourt:
    """A court of the game's sport its club still sells at the game's hour,
    and the share one player pays for it there — what a club's cancel asks of
    it before the court may absorb the game (#672)."""

    court: BookedCourt
    share_grosze: int


class BookingState(StrEnum):
    """Where a booking stands (the mechanics §14.1, §16.7)."""

    #: Full and paid, the court the players'.
    BOOKED = "BOOKED"
    #: Booked and paid, and somebody left: a seat is open (#544).
    SEAT_OPEN = "SEAT_OPEN"
    #: It will not be played — and why is ``CalledOff``.
    CALLED_OFF = "CALLED_OFF"


class CalledOff(StrEnum):
    """Why a booking will not be played."""

    #: A seat that opened before the club's cut-off was still open at it (#544).
    SHORT_AT_THE_CUT_OFF = "SHORT_AT_THE_CUT_OFF"
    #: The club cancelled it, with its reason (#547).
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"
    #: A friends game its sender called off before the cut-off (#751): nobody
    #: paid.
    BY_THE_SENDER = "BY_THE_SENDER"


class PayMode(StrEnum):
    """How a friends game's court is paid (``docs/adr/0202`` §6) — the glossary's
    **Pay mode**; *Split* here is never a forecast's."""

    #: Each friend pays their own share on accepting; the sender's cover pays
    #: a seat still without its own payment at the cut-off.
    SPLIT_THE_COST = "SPLIT_THE_COST"
    #: The sender pays every seat; friends accept without paying.
    WHOLE_COURT = "WHOLE_COURT"


class Answer(StrEnum):
    """Where an invited seat stands (#751; the friends mechanics §9)."""

    #: Held for its friend, their clock running.
    WAITING = "WAITING"
    ACCEPTED = "ACCEPTED"
    #: *Not this time* — the friend can't make it.
    DECLINED = "DECLINED"
    #: Silence until the clock ended: the friend didn't answer.
    RAN_OUT = "RAN_OUT"


@dataclass(frozen=True, slots=True)
class InvitedSeat:
    """A seat of a friends game held for one friend (#751): on which side the
    card drew them, until when they may answer, and how they did."""

    player_id: UUID
    #: ``A`` — the first side — or ``B``.
    side: str
    until: Instant
    answer: Answer = Answer.WAITING
    answered_at: Instant | None = None

    def waiting_at(self, now: Instant) -> bool:
        """Still theirs to answer at ``now`` — read off the clock, so a seat
        whose time is up is not, whether or not its running out is recorded."""

        return self.answer is Answer.WAITING and now < self.until


class CancelReason(StrEnum):
    """Why the club cancelled a booked game (the mechanics §16.9) — told to
    the players with their refund."""

    WEATHER = "WEATHER"
    REPAIR = "REPAIR"
    #: The desk sold a handed-over hour too, by mistake (§16.3, §16.16). It
    #: stays with Only Raketa the one way (#670; ``docs/adr/0196`` §1).
    DOUBLE_BOOKING = "DOUBLE_BOOKING"
    OTHER = "OTHER"


@dataclass(frozen=True, slots=True)
class RefusedHolding:
    """A player's holding refused (#639): until when their time to fix the
    card runs, the payment to confirm, and why it was refused — the refusal's
    code, which is the money's to name."""

    until: Instant
    seat_charge_id: UUID
    reason: str


@dataclass(frozen=True, slots=True)
class KeptSeat:
    """A seat kept for a rescuer whose share was refused (#640): until when,
    the payment to confirm, why it was refused — the refusal's code, which is
    the money's to name — and whether their time is to fix the card, before
    the cut-off, or to pay."""

    until: Instant
    seat_charge_id: UUID
    reason: str
    to_fix_the_card: bool


@dataclass(frozen=True, slots=True)
class Departure:
    """A player who left the booked game: from which side — where a rescue
    taking the seat sits (#545) — and when, which against the booking's
    cut-off says whether leaving was free."""

    player_id: UUID
    #: ``A`` — the first side — or ``B``.
    side: str
    at: Instant
    #: Who took the seat, once somebody did (#545) — ``None`` while it is open.
    rescued_by: UUID | None = None

    @property
    def is_open(self) -> bool:
        return self.rescued_by is None


@dataclass
class Booking:
    booking_id: UUID
    pool_id: UUID
    club_id: UUID
    court: BookedCourt
    sport: Sport
    kind: SearchMode
    start: Instant
    share_grosze: int
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    cut_off: Instant
    state: BookingState
    #: The ordinary Game it opened.
    game_id: UUID
    #: When it was booked — the fill.
    booked_at: Instant
    #: Why it will not be played, once called off.
    called_off: CalledOff | None = None
    #: When its club cancelled it, once it did (#637).
    cancelled_at: Instant | None = None
    #: Everybody who left the booked game, in the order they did (#544) — each
    #: with who took their seat, once somebody did (#545).
    departures: tuple[Departure, ...] = ()
    #: Everybody who said no to the open seat dealt to them as a card (#545).
    said_no: frozenset[UUID] = frozenset()
    #: Why the club cancelled it, once it did (#547).
    cancel_reason: CancelReason | None = None
    #: Everybody whose holding was refused and whose time to fix the card runs
    #: (#639) — the game booked meanwhile.
    cards_to_fix: dict[UUID, RefusedHolding] = field(default_factory=dict)
    #: Every rescuer whose share was refused, and the seat kept for them (#640)
    #: — until they take one or the game is off. Read against the clock: one
    #: whose time is up keeps nothing, whether or not its running out is
    #: recorded, and stays here so their refused payment is still known.
    kept: dict[UUID, KeptSeat] = field(default_factory=dict)
    #: Every rescuer whose kept seat ran out: none is kept for them again here.
    keeps_ran_out: frozenset[UUID] = frozenset()
    #: A friends game's sender (#751) — ``None`` on a game a fill booked.
    sender: UUID | None = None
    #: How a friends game's court is paid — ``None`` on a fill's.
    pay_mode: PayMode | None = None
    #: A friends game's invited seats, in the order the card drew them, each
    #: with its answer — those accepted are In, on ``first_side`` or
    #: ``second_side`` too.
    invited: tuple[InvitedSeat, ...] = ()
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def confirmed(
        cls,
        *,
        booking_id: UUID,
        pool_id: UUID,
        club_id: UUID,
        court: BookedCourt,
        sport: Sport,
        kind: SearchMode,
        start: Instant,
        share_grosze: int,
        first_side: tuple[UUID, ...],
        second_side: tuple[UUID, ...],
        cut_off: Instant,
        game_id: UUID,
        at: Instant,
    ) -> "Booking":
        """A full game, booked: every seat on a side, every side full."""

        _sides_of_a_game(sport, first_side, second_side)
        invariant(cut_off <= start, f"a cut-off {cut_off} after the game {start}")
        confirmed = BookingConfirmed(
            booking_id=booking_id,
            pool_id=pool_id,
            club_id=club_id,
            court_id=court.court_id,
            court_name=court.name,
            indoor=court.indoor,
            sport=sport.value,
            kind=kind.value,
            start=start,
            share_grosze=share_grosze,
            first_side=first_side,
            second_side=second_side,
            cut_off=cut_off,
            game_id=game_id,
            occurred_at=at,
        )
        booking = cls._booked(confirmed)
        booking._events.record(confirmed)
        return booking

    @classmethod
    def booked_by_a_friend(
        cls,
        *,
        booking_id: UUID,
        pool_id: UUID,
        club_id: UUID,
        court: BookedCourt,
        sport: Sport,
        kind: SearchMode,
        start: Instant,
        share_grosze: int,
        sender: UUID,
        first_side: tuple[UUID, ...],
        second_side: tuple[UUID, ...],
        pay_mode: PayMode,
        cut_off: Instant,
        game_id: UUID,
        at: Instant,
    ) -> "Booking":
        """**A friends game, sent** (#751): the court booked at once, the
        sender In, and every other player on the card's sides an invited seat
        until ``invited_until`` — every seat on a side, the sender on one."""

        _sides_of_a_game(sport, first_side, second_side)
        invariant(
            sender in (*first_side, *second_side),
            f"the sender {sender} is on neither side of {booking_id}",
        )
        invariant(cut_off <= start, f"a cut-off {cut_off} after the game {start}")
        invariant(at < start, f"{booking_id} sent at {at}, after it began at {start}")
        booked = BookedByAFriend(
            booking_id=booking_id,
            pool_id=pool_id,
            club_id=club_id,
            court_id=court.court_id,
            court_name=court.name,
            indoor=court.indoor,
            sport=sport.value,
            kind=kind.value,
            start=start,
            share_grosze=share_grosze,
            sender_id=sender,
            first_side=first_side,
            second_side=second_side,
            pay_mode=pay_mode.value,
            invited_until=invited_until(at, cut_off=cut_off, start=start),
            cut_off=cut_off,
            game_id=game_id,
            occurred_at=at,
        )
        booking = cls._sent(booked)
        booking._events.record(booked)
        return booking

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Booking":
        history = iter(events)
        opening = next(history)
        if isinstance(opening, BookingConfirmed):
            booking = cls._booked(opening)
        elif isinstance(opening, BookedByAFriend):
            booking = cls._sent(opening)
        else:
            raise TypeError(f"A booking stream opens {opening!r}")
        for event in history:
            booking._apply(event)
        return booking

    @classmethod
    def _sent(cls, booked: BookedByAFriend) -> "Booking":
        sender = booked.sender_id
        until = instant(booked.invited_until)
        return cls(
            booking_id=booked.booking_id,
            pool_id=booked.pool_id,
            club_id=booked.club_id,
            court=BookedCourt(
                court_id=booked.court_id,
                name=booked.court_name,
                indoor=booked.indoor,
            ),
            sport=Sport(booked.sport),
            kind=SearchMode(booked.kind),
            start=instant(booked.start),
            share_grosze=booked.share_grosze,
            # Only the sender is In: every other seat is invited.
            first_side=tuple(p for p in booked.first_side if p == sender),
            second_side=tuple(p for p in booked.second_side if p == sender),
            cut_off=instant(booked.cut_off),
            state=BookingState.BOOKED,
            game_id=booked.game_id,
            booked_at=instant(booked.occurred_at),
            sender=sender,
            pay_mode=PayMode(booked.pay_mode),
            invited=tuple(
                InvitedSeat(player_id=player, side=side, until=until)
                for side, players in (
                    ("A", booked.first_side),
                    ("B", booked.second_side),
                )
                for player in players
                if player != sender
            ),
            version=1,
        )

    @classmethod
    def _booked(cls, confirmed: BookingConfirmed) -> "Booking":
        return cls(
            booking_id=confirmed.booking_id,
            pool_id=confirmed.pool_id,
            club_id=confirmed.club_id,
            court=BookedCourt(
                court_id=confirmed.court_id,
                name=confirmed.court_name,
                indoor=confirmed.indoor,
            ),
            sport=Sport(confirmed.sport),
            kind=SearchMode(confirmed.kind),
            start=instant(confirmed.start),
            share_grosze=confirmed.share_grosze,
            first_side=tuple(confirmed.first_side),
            second_side=tuple(confirmed.second_side),
            cut_off=instant(confirmed.cut_off),
            state=BookingState.BOOKED,
            game_id=confirmed.game_id,
            booked_at=instant(confirmed.occurred_at),
            version=1,
        )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    # ------------------------------------------------------------------ reads

    @property
    def players(self) -> tuple[UUID, ...]:
        """Everybody with a seat on it, the first side first."""

        return (*self.first_side, *self.second_side)

    @property
    def is_friends_game(self) -> bool:
        """Booked by a friend at send (#751), not by a fill."""

        return self.sender is not None

    @property
    def is_whole(self) -> bool:
        """Every seat held by somebody In."""

        return len(self.players) == self.seats

    def invitation_of(self, player_id: UUID) -> InvitedSeat | None:
        """This player's invited seat on a friends game, however it was
        answered — ``None`` for somebody never invited."""

        return next(
            (seat for seat in self.invited if seat.player_id == player_id), None
        )

    def waiting_at(self, now: Instant) -> tuple[InvitedSeat, ...]:
        """The invited seats still theirs to answer at ``now`` — none on a game
        called off."""

        if not self.is_booked:
            return ()
        return tuple(seat for seat in self.invited if seat.waiting_at(now))

    def to_run_out(self, now: Instant) -> tuple[InvitedSeat, ...]:
        """The invited seats whose time is up at ``now``, their running out not
        yet recorded — on a game still booked."""

        if not self.is_booked:
            return ()
        return tuple(
            seat
            for seat in self.invited
            if seat.answer is Answer.WAITING and now >= seat.until
        )

    @property
    def fixing_until(self) -> dict[UUID, Instant]:
        """Everybody whose holding was refused, and until when their time to
        fix the card runs (#639)."""

        return {player: refused.until for player, refused in self.cards_to_fix.items()}

    @property
    def kept_until(self) -> dict[UUID, Instant]:
        """Every rescuer a seat was kept for, and until when (#640) — a time
        already up included."""

        return {player: kept.until for player, kept in self.kept.items()}

    @property
    def seats(self) -> int:
        """Four for padel and badminton, two for tennis and squash."""

        return SPORT_SPECS[self.sport].players

    @property
    def open_seats(self) -> int:
        """Seats nobody holds on a booked game — the leavers' (#544). Nought on
        a game called off."""

        if self.state is not BookingState.SEAT_OPEN:
            return 0
        return self.seats - len(self.players)

    @property
    def is_booked(self) -> bool:
        """Booked and not called off — whole, or with a seat open."""

        return self.state in (BookingState.BOOKED, BookingState.SEAT_OPEN)

    @property
    def open_departures(self) -> tuple[Departure, ...]:
        """The seats still open, as the leavers who opened them — **the first
        to open first**, which is the one a rescue takes (#545)."""

        if self.state is not BookingState.SEAT_OPEN:
            return ()
        return tuple(left for left in self.departures if left.is_open)

    @property
    def leavers(self) -> frozenset[UUID]:
        """Everybody who ever left the booked game, whether or not their seat
        was taken."""

        return frozenset(left.player_id for left in self.departures)

    @property
    def open_since(self) -> Instant | None:
        """When the first seat still open opened — ``None`` while every seat is
        held."""

        still_open = self.open_departures
        return still_open[0].at if still_open else None

    @property
    def open_before_the_cut_off(self) -> tuple[Departure, ...]:
        """The seats still open that opened while leaving was free — a game that
        filled after its cut-off never had any, and a seat a rescue took is no
        longer one."""

        return tuple(left for left in self.open_departures if left.at < self.cut_off)

    @property
    def short_from(self) -> Instant | None:
        """**A game plays full or not at all**: the moment a booked game with a
        seat that opened before its cut-off, and is open still, is off — its
        cut-off — or ``None`` for a game whole, or short only by a seat that
        opened after the cut-off, which goes ahead short. A seat taken before
        the cut-off is one the game is not short of (#545)."""

        if self.open_before_the_cut_off:
            return self.cut_off
        return None

    def short_at_the_cut_off(self, *, now: Instant) -> bool:
        """Off at ``now`` because a seat was still open at the cut-off — read
        off the clock, so every read says so before the job records it."""

        return self.short_from is not None and now >= self.short_from

    def seats_kept(self, *, at: Instant, but: UUID | None = None) -> int:
        """How many open seats are kept at ``at`` for rescuers whose time runs
        (#640) — ``but``'s own not counted."""

        return sum(
            1 for player, kept in self.kept.items() if player != but and at < kept.until
        )

    def rescuable_at(self, now: Instant, *, by: UUID | None = None) -> bool:
        """Whether a seat is open to be taken at ``now`` (the mechanics §10.1):
        **until the cut-off whatever their number**, since the leavers' refunds
        and the game itself depend on them being taken — **then until the
        start**, on a game that goes ahead short. Never on a game called off,
        whether or not that is recorded yet. **By** a player, a seat kept for
        another rescuer whose time runs is not one (#640)."""

        kept = 0 if by is None else self.seats_kept(at=now, but=by)
        return (
            self.open_seats > kept
            and not self.short_at_the_cut_off(now=now)
            and now < self.start
        )

    # ------------------------------------------------------------------- acts

    def leave(self, player_id: UUID, *, at: Instant) -> None:
        """*Leave the game*: this player's seat on the booked game opens. Whose
        seat it is, and whether the game may still be left — booked, and not
        yet started — is the caller's question, asked before this."""

        invariant(self.is_booked, f"leaving {self.booking_id} while {self.state}")
        invariant(
            player_id in self.players,
            f"{player_id} has no seat on {self.booking_id}",
        )
        invariant(at < self.start, f"leaving {self.booking_id} at {at}, after it began")
        self._record_that(
            SeatLeft(booking_id=self.booking_id, player_id=player_id, occurred_at=at)
        )

    def accept(self, player_id: UUID, *, at: Instant) -> None:
        """*Accept* on an invitation (#751): this friend is In, on the side the
        card drew them on. Whether they may — their week, their hour, their
        money — is the caller's question, asked before this; that the seat is
        theirs and still waiting, and the game still to be played, is this
        one's."""

        seat = self.invitation_of(player_id)
        invariant(
            seat is not None and seat in self.waiting_at(at),
            f"{player_id} has no invitation waiting on {self.booking_id} at {at}",
        )
        assert seat is not None
        invariant(at < self.start, f"accepting {self.booking_id} after it began")
        self._record_that(
            InvitedSeatAccepted(
                booking_id=self.booking_id,
                player_id=player_id,
                side=seat.side,
                occurred_at=at,
                last_seat=len(self.players) + 1 == self.seats,
            )
        )

    def decline(self, player_id: UUID, *, at: Instant) -> bool:
        """*Not this time* on an invitation (#751). Answers whether anything
        was recorded — nothing for a seat no longer waiting: answered, run
        out, or on a game called off."""

        seat = self.invitation_of(player_id)
        if seat is None or seat not in self.waiting_at(at):
            return False
        self._record_that(
            InvitedSeatDeclined(
                booking_id=self.booking_id, player_id=player_id, occurred_at=at
            )
        )
        return True

    def invited_seat_ran_out(self, player_id: UUID, *, at: Instant) -> bool:
        """This friend's time to answer ended (#751): silence is *Not this
        time*. Answers whether anything was recorded — nothing while it still
        runs, for a seat answered, or once its running out is recorded."""

        seat = self.invitation_of(player_id)
        if seat is None or seat not in self.to_run_out(at):
            return False
        self._record_that(
            InvitedSeatRanOut(
                booking_id=self.booking_id, player_id=player_id, occurred_at=at
            )
        )
        return True

    def call_off_by_the_sender(self, *, at: Instant) -> None:
        """*Call it off* (#751; ``docs/adr/0202`` §6): the sender calls the
        friends game off before the cut-off — everybody In and every invitee
        still waiting named, to be told, every hold let go."""

        invariant(
            self.is_friends_game,
            f"{self.booking_id} is no friends game to be called off by its sender",
        )
        self._refuse_unless_still_to_be_played(at)
        invariant(
            at < self.cut_off,
            f"{self.booking_id} called off by its sender at {at}, "
            f"after its cut-off {self.cut_off}",
        )
        self._record_that(
            CalledOffBySender(
                booking_id=self.booking_id,
                player_ids=self.players,
                invited=tuple(seat.player_id for seat in self.waiting_at(at)),
                occurred_at=at,
            )
        )

    def card_to_fix(
        self,
        player_id: UUID,
        *,
        until: Instant,
        seat_charge_id: UUID,
        reason: str,
        at: Instant,
    ) -> None:
        """This player's holding was refused (#639): the game stays booked,
        their seat theirs alone until ``until`` — their time to fix the card,
        never past the cut-off. Whose share it is, and that it was refused, is
        the caller's to know; that they are on the booked game, and that the
        time is ahead and inside the cut-off, is this one's."""

        invariant(
            self.is_booked and player_id in self.players,
            f"{player_id} has no seat on {self.booking_id} to fix a card for",
        )
        invariant(
            at < until <= self.cut_off,
            f"a card on {self.booking_id} to fix by {until} at {at}, "
            f"cut-off {self.cut_off}",
        )
        self._record_that(
            CardToFix(
                booking_id=self.booking_id,
                player_id=player_id,
                until=until,
                seat_charge_id=seat_charge_id,
                reason=reason,
                occurred_at=at,
            )
        )

    def card_fixed(self, player_id: UUID, *, at: Instant) -> bool:
        """This player fixed their card in time (#639). Answers whether
        anything was recorded — nothing for a card not to fix."""

        if player_id not in self.cards_to_fix:
            return False
        self._record_that(
            CardFixed(booking_id=self.booking_id, player_id=player_id, occurred_at=at)
        )
        return True

    def card_not_fixed(self, player_id: UUID, *, at: Instant) -> bool:
        """This player's time to fix the card ran out (#639): their seat opens
        as a leaver's does — a Rescue on Fill in — and on the record it is a
        leave before the cut-off. Answers whether anything was recorded —
        nothing for a card not to fix, or one whose time still runs."""

        to_fix = self.cards_to_fix.get(player_id)
        if to_fix is None or at < to_fix.until or not self.is_booked:
            return False
        self._record_that(
            SeatLeft(
                booking_id=self.booking_id,
                player_id=player_id,
                occurred_at=at,
                card_not_fixed=True,
            )
        )
        return True

    def rescue(self, player_id: UUID, *, at: Instant) -> Departure:
        """*I'm in* on an open seat: this player takes **the seat that opened
        first**, on its side, and has paid their share (#545). Answers whose
        seat it was. Whether they may — in the pool, a fit, free — is the
        caller's question, asked before this; that a seat is open to take, and
        that they are neither on the game nor a leaver of it, is this one's."""

        invariant(
            self.rescuable_at(at, by=player_id),
            f"{self.booking_id} has no seat for {player_id} at {at}: {self.state}, "
            f"{self.open_seats} open, {self.seats_kept(at=at, but=player_id)} kept, "
            f"cut-off {self.cut_off}, start {self.start}",
        )
        invariant(
            player_id not in self.players and player_id not in self.leavers,
            f"{player_id} takes a seat on {self.booking_id}, which they are on or left",
        )
        # The seats are taken in the order they opened, a kept one too: a keep
        # holds a seat, not a particular one.
        taken = self.open_departures[0]
        self._record_that(
            SeatRescued(
                booking_id=self.booking_id,
                player_id=player_id,
                side=taken.side,
                replacing=taken.player_id,
                occurred_at=at,
            )
        )
        return taken

    def keep_the_seat(
        self,
        player_id: UUID,
        *,
        until: Instant,
        seat_charge_id: UUID,
        reason: str,
        to_fix_the_card: bool,
        at: Instant,
    ) -> None:
        """This rescuer's share was refused (#640): a seat is kept for them
        alone until ``until`` — to fix the card, before the cut-off, or to pay
        — never past the start, nor, to fix, the cut-off. Refused again within
        it, they keep the time they had. Whether they may take a seat at all —
        in the pool, a fit, free — is the caller's question, asked before this;
        that one is open to them, and that they are neither on the game, a
        leaver of it, nor one whose kept seat ran out, is this one's."""

        invariant(
            self.rescuable_at(at, by=player_id),
            f"{self.booking_id} has no seat to keep for {player_id} at {at}",
        )
        invariant(
            player_id not in self.players
            and player_id not in self.leavers
            and player_id not in self.keeps_ran_out,
            f"a seat on {self.booking_id} kept for {player_id}, who is on it, "
            "left it or ran out already",
        )
        last = self.cut_off if to_fix_the_card else self.start
        invariant(
            at < until <= last,
            f"a seat on {self.booking_id} kept until {until} at {at}, "
            f"cut-off {self.cut_off}, start {self.start}",
        )
        kept = self.kept.get(player_id)
        invariant(
            kept is None or at >= kept.until or until == kept.until,
            f"{player_id}'s seat on {self.booking_id} kept until {until}, "
            f"not the time they had",
        )
        self._record_that(
            SeatKept(
                booking_id=self.booking_id,
                player_id=player_id,
                until=until,
                seat_charge_id=seat_charge_id,
                reason=reason,
                to_fix_the_card=to_fix_the_card,
                occurred_at=at,
            )
        )

    def kept_seat_ran_out(self, player_id: UUID, *, at: Instant) -> bool:
        """This rescuer's time ran out (#640): the seat kept for them is
        offered again. Answers whether anything was recorded — nothing for a
        seat not kept for them, one whose time still runs, or one whose
        running out is recorded already."""

        kept = self.kept.get(player_id)
        if kept is None or at < kept.until or player_id in self.keeps_ran_out:
            return False
        self._record_that(
            KeptSeatRanOut(
                booking_id=self.booking_id,
                player_id=player_id,
                occurred_at=at,
                to_fix_the_card=kept.to_fix_the_card,
            )
        )
        return True

    def say_no(self, player_id: UUID, *, at: Instant) -> bool:
        """*Not this time* on a Seat open card (#545): the card does not come
        back to this player. Answers whether anything was recorded — nothing for
        a second no."""

        if player_id in self.said_no:
            return False
        self._record_that(
            NoSaidToTheSeat(
                booking_id=self.booking_id, player_id=player_id, occurred_at=at
            )
        )
        return True

    def absorbing_court(
        self, free: Iterable[FreeCourt], *, because: CancelReason
    ) -> BookedCourt | None:
        """The court that takes the game when its club cancels it ``because``
        — a **move by cancel** (#672; the mechanics §16.9, Q122) — or ``None``
        when none does, and the cancel calls the game off.

        ``free`` is every court of the game's sport its club still sells at
        the game's hour, in the club's order. One absorbs the cancel when
        nothing about the game would change: **the same share**, **the same
        kind, or indoor for an outdoor game** — and, for *weather*, **indoor
        only**, since an outdoor court at the same hour is rained on too. Of
        two, the same kind comes first, then indoor; within that, the club's
        own order."""

        absorbing = [
            one.court
            for one in free
            if one.court.court_id != self.court.court_id
            and one.share_grosze == self.share_grosze
            and self.court.may_move_to(one.court)
            and (because is not CancelReason.WEATHER or one.court.indoor)
        ]
        # A stable sort: the club's order holds within each kind.
        absorbing.sort(key=lambda court: court.indoor is not self.court.indoor)
        return absorbing[0] if absorbing else None

    def move_to(
        self, court: BookedCourt, *, at: Instant, because: CancelReason | None = None
    ) -> None:
        """The club puts the game on ``court`` — another court of its sport,
        free at the hour (#547). Whether it is free, of the sport, and of a kind
        the players would accept — the same kind, or indoor for an outdoor game
        (#671, Q122) — is the caller's question, asked of what the club sells;
        that the game is still to be played, and the court another, is this
        one's. The record carries the new court's kind, so the players read
        *Court 3 · indoor* from here on, and the court it left.

        ``because`` is the club's cancel the move takes the place of — a move
        by cancel (#672), its court found by ``absorbing_court`` — and ``None``
        for the club's own Move. Either way nothing else about the game
        changes: its players, its seats and their money stay as they are."""

        self._refuse_unless_still_to_be_played(at)
        invariant(
            court.court_id != self.court.court_id,
            f"{self.booking_id} is moved onto its own court {court.court_id}",
        )
        self._record_that(
            CourtMoved(
                booking_id=self.booking_id,
                court_id=court.court_id,
                court_name=court.name,
                indoor=court.indoor,
                occurred_at=at,
                reason=None if because is None else because.value,
                moved_from=self.court.name,
            )
        )

    def cancel(self, reason: CancelReason, *, at: Instant) -> None:
        """The club cancels the game, with its reason: everybody still in is
        named, to be refunded in full (#547; the mechanics §16.9)."""

        self._refuse_unless_still_to_be_played(at)
        self._record_that(
            CancelledByClub(
                booking_id=self.booking_id,
                reason=reason.value,
                player_ids=self.players,
                occurred_at=at,
            )
        )

    def call_off_at_the_cut_off(self, *, at: Instant) -> None:
        """Short at its cut-off: the game is off, and everybody still in is
        named, to be refunded in full."""

        invariant(
            self.short_at_the_cut_off(now=at),
            f"{self.booking_id} is called off at {at}, not short at its cut-off "
            f"{self.cut_off}",
        )
        self._record_that(
            CalledOffAtCutOff(
                booking_id=self.booking_id, player_ids=self.players, occurred_at=at
            )
        )

    # ------------------------------------------------------------------- fold

    def _refuse_unless_still_to_be_played(self, at: Instant) -> None:
        """Booked — whole or with a seat open — not short at its cut-off, and
        its hour still ahead: what the club may still move or cancel."""

        invariant(
            self.is_booked
            and not self.short_at_the_cut_off(now=at)
            and at < self.start,
            f"{self.booking_id} is no longer to be played at {at}: {self.state}, "
            f"cut-off {self.cut_off}, start {self.start}",
        )

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _answered(self, player_id: UUID, answer: Answer, at: datetime) -> None:
        self.invited = tuple(
            replace(seat, answer=answer, answered_at=instant(at))
            if seat.player_id == player_id
            else seat
            for seat in self.invited
        )

    def _no_card_to_fix(self, player_id: UUID) -> None:
        self.cards_to_fix = {
            player: refused
            for player, refused in self.cards_to_fix.items()
            if player != player_id
        }

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, CardToFix):
            self.cards_to_fix = {
                **self.cards_to_fix,
                event.player_id: RefusedHolding(
                    until=instant(event.until),
                    seat_charge_id=event.seat_charge_id,
                    reason=event.reason,
                ),
            }
        elif isinstance(event, CardFixed):
            self._no_card_to_fix(event.player_id)
        elif isinstance(event, SeatLeft):
            self._no_card_to_fix(event.player_id)
            side = "A" if event.player_id in self.first_side else "B"
            self.first_side = tuple(p for p in self.first_side if p != event.player_id)
            self.second_side = tuple(
                p for p in self.second_side if p != event.player_id
            )
            self.departures = (
                *self.departures,
                Departure(
                    player_id=event.player_id, side=side, at=instant(event.occurred_at)
                ),
            )
            self.state = BookingState.SEAT_OPEN
        elif isinstance(event, SeatRescued):
            self.kept = {
                player: kept
                for player, kept in self.kept.items()
                if player != event.player_id
            }
            if event.side == "A":
                self.first_side = (*self.first_side, event.player_id)
            else:
                self.second_side = (*self.second_side, event.player_id)
            self.departures = tuple(
                Departure(
                    player_id=left.player_id,
                    side=left.side,
                    at=left.at,
                    rescued_by=event.player_id,
                )
                if left.player_id == event.replacing and left.is_open
                else left
                for left in self.departures
            )
            self.state = (
                BookingState.BOOKED
                if len(self.players) == self.seats
                else BookingState.SEAT_OPEN
            )
        elif isinstance(event, NoSaidToTheSeat):
            self.said_no = self.said_no | {event.player_id}
        elif isinstance(event, SeatKept):
            self.kept = {
                **self.kept,
                event.player_id: KeptSeat(
                    until=instant(event.until),
                    seat_charge_id=event.seat_charge_id,
                    reason=event.reason,
                    to_fix_the_card=event.to_fix_the_card,
                ),
            }
        elif isinstance(event, KeptSeatRanOut):
            # Its time is up, so it keeps nothing; what was refused stays known.
            self.keeps_ran_out = self.keeps_ran_out | {event.player_id}
        elif isinstance(event, CalledOffAtCutOff):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.SHORT_AT_THE_CUT_OFF
            # A game off has no card to fix: its holds are all let go (#639) —
            # and no seat to keep (#640).
            self.cards_to_fix = {}
            self.kept = {}
        elif isinstance(event, CourtMoved):
            self.court = BookedCourt(
                court_id=event.court_id, name=event.court_name, indoor=event.indoor
            )
        elif isinstance(event, CancelledByClub):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.CANCELLED_BY_THE_CLUB
            self.cancel_reason = CancelReason(event.reason)
            self.cancelled_at = instant(event.occurred_at)
            self.cards_to_fix = {}
            self.kept = {}
        elif isinstance(event, InvitedSeatAccepted):
            if event.side == "A":
                self.first_side = (*self.first_side, event.player_id)
            else:
                self.second_side = (*self.second_side, event.player_id)
            self._answered(event.player_id, Answer.ACCEPTED, event.occurred_at)
        elif isinstance(event, InvitedSeatDeclined):
            self._answered(event.player_id, Answer.DECLINED, event.occurred_at)
        elif isinstance(event, InvitedSeatRanOut):
            self._answered(event.player_id, Answer.RAN_OUT, event.occurred_at)
        elif isinstance(event, CalledOffBySender):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.BY_THE_SENDER
            self.cards_to_fix = {}
            self.kept = {}
        elif isinstance(event, PlayerCheckedIn):
            # Retired (#651): a stored scan is read and changes nothing —
            # nothing asks who the desk saw any more.
            pass
        else:
            raise TypeError(f"Unsupported booking event {event!r}")
        self.version += 1


def _sides_of_a_game(
    sport: Sport, first_side: tuple[UUID, ...], second_side: tuple[UUID, ...]
) -> None:
    per_side = SPORT_SPECS[sport].players // 2
    invariant(
        len(first_side) == len(second_side) == per_side,
        f"sides {first_side} and {second_side} for {per_side} a side",
    )
    invariant(
        not set(first_side) & set(second_side),
        f"somebody on both sides: {first_side} {second_side}",
    )

