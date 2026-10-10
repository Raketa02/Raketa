"""The Booking aggregate — event-sourced, one stream per filled proposal
(``docs/adr/0189`` §5; the mechanics §11).

**A booking is the game a full card became**, and its id is the card's. It holds
what the fill decided and nothing a reader could derive: the court and its
number, who sits on which side, the cut-off as the club set it when the game
filled, and the Game it opened. Its money is the Seat charges' (``payments``),
its result the Game's (``games``) — after the fill, *everything that happens to a
game today happens to it unchanged* (Q6).

**Born booked** (#541), or **born waiting for the club** (#543): at an On
request club a full game is put to the club, which has its time to confirm to
say yes (the mechanics §16.3, §16.8). While it waits the court is **reserved**
for it — nobody else is offered that court — and nobody has paid. The club's
yes books it and opens the Game; its no, or no answer by the deadline, calls it
off; and **a seat opening while it waits** — somebody left, or could no longer
be In — withdraws the request: nobody paid, the game is filling again, and
**the people still In keep their places**, a seat open where each opener sat,
so it stays on their Home as *Seat open* (Q106). **Full again, the same game is
asked again on the same stream**, with whoever is In then: one id from the
first card to the court.

**A share refused at the club's yes waits for its player** (#626; Q109, Q112):
the booking stays accepted and its court held — *waiting for a payment* —
while that player has until ``pay_by`` to pay. The payment in time books it
and opens the Game, the club not asked again; out of time, it is called off
(*a player's payment didn't come in time*), the court the club's again, and
the people still In keep their places as after a withdrawn request — unless
the book-by had come, when it is called off for good.

**A player leaves a booked game** (#544; the mechanics §12.3, §13): their seat
opens — *seat open* — and the game is still the others'. **A game plays full or
not at all**: a seat that opened before the club's cut-off and is still open at
it calls the game off (``CalledOffAtCutOff``), the court the club's again; a
seat that opened after the cut-off leaves the game going ahead short. Whether a
game is **short at its cut-off** is read off the departures and the clock, so
every read says it from the cut-off on, whether or not the job has recorded it.

**An open seat is a rescue** (#545; the mechanics §10.1): somebody else takes
it, paid at once, and sits where the leaver sat. **The seat that opened first is
taken first** — the leavers are refunded in the order they left — and a seat
stays open until the cut-off whatever their number, then until the start. A
game whose seats are all taken is whole again, and *short at its cut-off* is read
off the seats still open.

**The club runs it** (#547; the mechanics §16.7–§16.10): it may **move** the
game to another court of its sport at the same hour, or **cancel** it with its
reason — everybody still in refunded in full, on nobody's record — until the
game starts; and its desk **checks players in** on the day. *Played* is read
off the clock — a booked game whose hour has passed — and never recorded: there
is nothing to decide about it, and a recorded copy would be wrong for the whole
gap until something wrote it.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Iterable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import SPORT_SPECS, Instant, Sport, instant, invariant
from app.modules.bookings.domain.events import (
    BookingAccepted,
    BookingAwaitingAPayment,
    BookingConfirmed,
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    CalledOffAtCutOff,
    CancelledByClub,
    CourtMoved,
    PaymentNotInTime,
    PlayerCheckedIn,
    RequestWithdrawn,
    NoSaidToTheSeat,
    SeatLeft,
    SeatRescued,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass(frozen=True, slots=True)
class BookedCourt:
    """The court a game is booked on: its id, and what the club calls it."""

    court_id: UUID
    name: str


class BookingState(StrEnum):
    """Where a booking stands (the mechanics §14.1, §16.7)."""

    #: An On request club has the full game and has not answered yet. The
    #: court is reserved for it; nobody has paid.
    WAITING_FOR_THE_CLUB = "WAITING_FOR_THE_CLUB"
    #: The club said yes, and one player's share could not be held: the yes
    #: and the court are kept while they have time to pay (#626). Nobody has
    #: paid.
    WAITING_FOR_A_PAYMENT = "WAITING_FOR_A_PAYMENT"
    #: Full and paid, the court the players'.
    BOOKED = "BOOKED"
    #: Booked and paid, and somebody left: a seat is open (#544).
    SEAT_OPEN = "SEAT_OPEN"
    #: It will not be played — and why is ``CalledOff``.
    CALLED_OFF = "CALLED_OFF"


class CalledOff(StrEnum):
    """Why a booking will not be played."""

    #: The club refused the request.
    REFUSED = "REFUSED"
    #: The club did not answer it in time.
    NO_ANSWER = "NO_ANSWER"
    #: A seat opened while it waited for the club; the game is filling again,
    #: and nobody has a seat on the request.
    SEAT_OPENED = "SEAT_OPENED"
    #: A seat that opened before the club's cut-off was still open at it (#544).
    SHORT_AT_THE_CUT_OFF = "SHORT_AT_THE_CUT_OFF"
    #: The club cancelled it, with its reason (#547).
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"
    #: The club said yes and a player's payment did not come in time (#626):
    #: nobody paid. The game is filling again for the people still In, unless
    #: it can no longer fill (``called_off_for_good``).
    PAYMENT_NOT_IN_TIME = "PAYMENT_NOT_IN_TIME"


class CancelReason(StrEnum):
    """Why the club cancelled a booked game (the mechanics §16.9) — told to
    the players with their refund."""

    WEATHER = "WEATHER"
    REPAIR = "REPAIR"
    #: The desk sold the hour too — an Instant club's double sale (§16.16).
    DOUBLE_BOOKING = "DOUBLE_BOOKING"
    OTHER = "OTHER"


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
    #: The ordinary Game it opened — ``None`` until the club said yes.
    game_id: UUID | None = None
    #: When the club's answer is due, while it waits — ``None`` on a booking
    #: born booked, and kept once answered.
    answer_by: Instant | None = None
    #: When its request was taken back because a seat opened, or the payment
    #: the club's yes waited on did not come — ``None`` while it waits, once
    #: asked again, and on a booking that never was.
    taken_back_at: Instant | None = None
    #: When the payment the club's yes waits on is due — ``None`` unless it
    #: waits for one (#626).
    pay_by: Instant | None = None
    #: Whose payment the club's yes waits on.
    payers: tuple[UUID, ...] = ()
    #: Called off as it could no longer fill — a payment refused at the club's
    #: yes with no time left before the book-by, or one whose time ran out on
    #: it (#626).
    called_off_for_good: bool = False
    #: Why it will not be played, once called off.
    called_off: CalledOff | None = None
    #: The club's own note when it refused — for its records, never a player's.
    refusal_reason: str | None = None
    #: When it was booked — ``None`` while it waits, and if it never was.
    booked_at: Instant | None = None
    #: When its club cancelled it, once it did (#637).
    cancelled_at: Instant | None = None
    #: Everybody who left the booked game, in the order they did (#544) — each
    #: with who took their seat, once somebody did (#545).
    departures: tuple[Departure, ...] = ()
    #: Everybody who said no to the open seat dealt to them as a card (#545).
    said_no: frozenset[UUID] = frozenset()
    #: Why the club cancelled it, once it did (#547).
    cancel_reason: CancelReason | None = None
    #: Everybody the club's desk checked in, and when (#547).
    checked_in: dict[UUID, Instant] = field(default_factory=dict)
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
    def requested(
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
        answer_by: Instant,
        filled_by: UUID | None,
        at: Instant,
    ) -> "Booking":
        """A full game put to its On request club, the court reserved for it —
        by ``filled_by``'s own act, if a player's."""

        requested = _a_request(
            booking_id=booking_id,
            pool_id=pool_id,
            club_id=club_id,
            court=court,
            sport=sport,
            kind=kind,
            start=start,
            share_grosze=share_grosze,
            first_side=first_side,
            second_side=second_side,
            cut_off=cut_off,
            answer_by=answer_by,
            filled_by=filled_by,
            at=at,
        )
        booking = cls._waiting(requested)
        booking._events.record(requested)
        return booking

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Booking":
        history = iter(events)
        opening = next(history)
        if isinstance(opening, BookingConfirmed):
            booking = cls._booked(opening)
        elif isinstance(opening, BookingRequested):
            booking = cls._waiting(opening)
        else:
            raise TypeError(f"A booking stream opens {opening!r}")
        for event in history:
            booking._apply(event)
        return booking

    @classmethod
    def _booked(cls, confirmed: BookingConfirmed) -> "Booking":
        return cls(
            booking_id=confirmed.booking_id,
            pool_id=confirmed.pool_id,
            club_id=confirmed.club_id,
            court=BookedCourt(court_id=confirmed.court_id, name=confirmed.court_name),
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

    @classmethod
    def _waiting(cls, requested: BookingRequested) -> "Booking":
        return cls(
            booking_id=requested.booking_id,
            pool_id=requested.pool_id,
            club_id=requested.club_id,
            court=BookedCourt(court_id=requested.court_id, name=requested.court_name),
            sport=Sport(requested.sport),
            kind=SearchMode(requested.kind),
            start=instant(requested.start),
            share_grosze=requested.share_grosze,
            first_side=tuple(requested.first_side),
            second_side=tuple(requested.second_side),
            cut_off=instant(requested.cut_off),
            state=BookingState.WAITING_FOR_THE_CLUB,
            answer_by=instant(requested.answer_by),
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
    def is_waiting(self) -> bool:
        """The club has still to answer."""

        return self.state is BookingState.WAITING_FOR_THE_CLUB

    @property
    def awaits_a_payment(self) -> bool:
        """The club said yes, and a payment it waits on is still to come
        (#626)."""

        return self.state is BookingState.WAITING_FOR_A_PAYMENT

    @property
    def seats(self) -> int:
        """Four for padel and badminton, two for tennis and squash."""

        return SPORT_SPECS[self.sport].players

    @property
    def open_seats(self) -> int:
        """Seats nobody holds on a booked game — the leavers' (#544). Nought on
        a request, which nobody has paid for, and on a game called off."""

        if self.state is not BookingState.SEAT_OPEN:
            return 0
        return self.seats - len(self.players)

    @property
    def taken_back(self) -> bool:
        """Its request was taken back because a seat opened — or the payment
        the club's yes waited on did not come, the game still able to fill
        (#626): the game is filling again, its people still In keeping their
        places (Q106)."""

        return self.called_off is CalledOff.SEAT_OPENED or (
            self.called_off is CalledOff.PAYMENT_NOT_IN_TIME
            and not self.called_off_for_good
        )

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

    def rescuable_at(self, now: Instant) -> bool:
        """Whether a seat is open to be taken at ``now`` (the mechanics §10.1):
        **until the cut-off whatever their number**, since the leavers' refunds
        and the game itself depend on them being taken — **then until the
        start**, on a game that goes ahead short. Never on a game called off,
        whether or not that is recorded yet."""

        return (
            self.open_seats > 0
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

    def rescue(self, player_id: UUID, *, at: Instant) -> Departure:
        """*I'm in* on an open seat: this player takes **the seat that opened
        first**, on its side, and has paid their share (#545). Answers whose
        seat it was. Whether they may — in the pool, a fit, free — is the
        caller's question, asked before this; that a seat is open to take, and
        that they are neither on the game nor a leaver of it, is this one's."""

        invariant(
            self.rescuable_at(at),
            f"{self.booking_id} has no seat to take at {at}: {self.state}, "
            f"{self.open_seats} open, cut-off {self.cut_off}, start {self.start}",
        )
        invariant(
            player_id not in self.players and player_id not in self.leavers,
            f"{player_id} takes a seat on {self.booking_id}, which they are on or left",
        )
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

    def move_to(self, court: BookedCourt, *, at: Instant) -> None:
        """The club puts the game on ``court`` — another court of its sport,
        free at the hour (#547). Whether it is free, and of the sport, is the
        caller's question, asked of what the club sells; that the game is still
        to be played, and the court another, is this one's."""

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
                occurred_at=at,
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

    def check_in(self, player_id: UUID, *, at: Instant) -> bool:
        """The desk checked this player in (#547; the mechanics §15.1). Answers
        whether anything was recorded — nothing for a player already checked
        in, whose first scan stands. Whether it is the game's day at the
        game's club is the caller's question; that the player has a seat on a
        booked game is this one's."""

        invariant(
            self.is_booked, f"{player_id} checked in to {self.booking_id} {self.state}"
        )
        invariant(
            player_id in self.players,
            f"{player_id} checked in with no seat on {self.booking_id}",
        )
        if player_id in self.checked_in:
            return False
        self._record_that(
            PlayerCheckedIn(
                booking_id=self.booking_id, player_id=player_id, occurred_at=at
            )
        )
        return True

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

    def accept(self, *, game_id: UUID, at: Instant) -> None:
        """The club said yes, every seat was paid, and ``game_id`` is open — at
        its yes, or when the payment its yes waited on came in (#626)."""

        invariant(
            self.is_waiting or self.awaits_a_payment,
            f"{self.booking_id} is accepted while {self.state}",
        )
        self._record_that(
            BookingAccepted(booking_id=self.booking_id, game_id=game_id, occurred_at=at)
        )

    def await_a_payment(
        self, player_ids: tuple[UUID, ...], *, until: Instant, at: Instant
    ) -> None:
        """The club said yes and these players' shares could not be held: the
        yes and the court are kept until ``until`` (#626; Q109)."""

        self._refuse_unless_waiting()
        invariant(
            bool(player_ids) and set(player_ids) <= set(self.players),
            f"{player_ids} are not all on {self.booking_id}",
        )
        invariant(at < until, f"{self.booking_id} awaits a payment until {until}")
        self._record_that(
            BookingAwaitingAPayment(
                booking_id=self.booking_id,
                player_ids=player_ids,
                until=until,
                occurred_at=at,
            )
        )

    def payment_not_in_time(
        self, player_ids: tuple[UUID, ...], *, for_good: bool, at: Instant
    ) -> bool:
        """The payment the club's yes waited on did not come in time — or no
        time was left at its yes (``at_once``: the booking was still waiting
        for the club): called off, nobody paid, the court free. ``for_good``
        when the game can no longer fill. Answers whether anything was
        recorded — nothing on a booking the club has no longer, or one whose
        request a seat opening took back first."""

        if not (self.awaits_a_payment or self.is_waiting):
            return False
        at_once = self.is_waiting
        invariant(not at_once or for_good, f"{self.booking_id} called off at once")
        invariant(
            bool(player_ids) and set(player_ids) <= set(self.players),
            f"{player_ids} are not all on {self.booking_id}",
        )
        self._record_that(
            PaymentNotInTime(
                booking_id=self.booking_id,
                player_ids=player_ids,
                occurred_at=at,
                for_good=for_good,
                at_once=at_once,
            )
        )
        return True

    def refuse(self, *, reason: str | None, at: Instant) -> None:
        """The club said no."""

        self._refuse_unless_waiting()
        self._record_that(
            BookingRefused(booking_id=self.booking_id, reason=reason, occurred_at=at)
        )

    def time_out(self, *, at: Instant) -> None:
        """The club's answer was due and never came."""

        self._refuse_unless_waiting()
        invariant(
            self.answer_by is not None and at >= self.answer_by,
            f"{self.booking_id} timed out at {at}, its answer due {self.answer_by}",
        )
        self._record_that(BookingTimedOut(booking_id=self.booking_id, occurred_at=at))

    def withdraw_request(
        self,
        player_ids: tuple[UUID, ...],
        *,
        left: tuple[UUID, ...] = (),
        at: Instant,
    ) -> bool:
        """These players' seats opened while the game waited: the request is
        off, and the others keep their places (Q106). ``left`` is those of them
        who took their own yes back. Answers whether anything was recorded —
        nothing on a booking not waiting for the club."""

        if not (self.is_waiting or self.awaits_a_payment):
            return False
        invariant(
            bool(player_ids) and set(player_ids) <= set(self.players),
            f"{player_ids} are not all on {self.booking_id}",
        )
        invariant(
            set(left) <= set(player_ids),
            f"{left} left {self.booking_id}, whose seats {player_ids} opened",
        )
        self._record_that(
            RequestWithdrawn(
                booking_id=self.booking_id,
                player_ids=player_ids,
                occurred_at=at,
                left=left,
            )
        )
        return True

    def request_again(
        self,
        *,
        court: BookedCourt,
        first_side: tuple[UUID, ...],
        second_side: tuple[UUID, ...],
        cut_off: Instant,
        answer_by: Instant,
        filled_by: UUID | None,
        at: Instant,
    ) -> None:
        """The game whose request was withdrawn is full again: put to the club
        again, with whoever is In now, on the first free court now — by
        ``filled_by``'s own act, if a player's."""

        invariant(
            self.taken_back,
            f"{self.booking_id} is asked again from {self.state}, {self.called_off}",
        )
        self._record_that(
            _a_request(
                booking_id=self.booking_id,
                pool_id=self.pool_id,
                club_id=self.club_id,
                court=court,
                sport=self.sport,
                kind=self.kind,
                start=self.start,
                share_grosze=self.share_grosze,
                first_side=first_side,
                second_side=second_side,
                cut_off=cut_off,
                answer_by=answer_by,
                filled_by=filled_by,
                at=at,
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

    def _refuse_unless_waiting(self) -> None:
        invariant(
            self.is_waiting,
            f"{self.booking_id} is answered while {self.state}",
        )

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, BookingAccepted):
            self.state = BookingState.BOOKED
            self.game_id = event.game_id
            self.booked_at = instant(event.occurred_at)
            self.pay_by = None
            self.payers = ()
        elif isinstance(event, BookingAwaitingAPayment):
            self.state = BookingState.WAITING_FOR_A_PAYMENT
            self.pay_by = instant(event.until)
            self.payers = tuple(event.player_ids)
        elif isinstance(event, PaymentNotInTime):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.PAYMENT_NOT_IN_TIME
            self.called_off_for_good = event.for_good
            self.pay_by = None
            self.payers = ()
            if not event.for_good:
                # The game is filling again: its players read it folded
                # against the proposal, and the club still sees all four, so
                # nobody is named by being left off (Q112).
                self.taken_back_at = instant(event.occurred_at)
        elif isinstance(event, BookingRefused):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.REFUSED
            self.refusal_reason = event.reason
        elif isinstance(event, BookingTimedOut):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.NO_ANSWER
        elif isinstance(event, RequestWithdrawn):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.SEAT_OPENED
            self.taken_back_at = instant(event.occurred_at)
            self.pay_by = None
            self.payers = ()
            opened = set(event.player_ids)
            self.first_side = tuple(p for p in self.first_side if p not in opened)
            self.second_side = tuple(p for p in self.second_side if p not in opened)
        elif isinstance(event, SeatLeft):
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
        elif isinstance(event, CalledOffAtCutOff):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.SHORT_AT_THE_CUT_OFF
        elif isinstance(event, CourtMoved):
            self.court = BookedCourt(court_id=event.court_id, name=event.court_name)
        elif isinstance(event, CancelledByClub):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.CANCELLED_BY_THE_CLUB
            self.cancel_reason = CancelReason(event.reason)
            self.cancelled_at = instant(event.occurred_at)
        elif isinstance(event, PlayerCheckedIn):
            self.checked_in = {
                **self.checked_in,
                event.player_id: instant(event.occurred_at),
            }
        elif isinstance(event, BookingRequested):
            self.court = BookedCourt(court_id=event.court_id, name=event.court_name)
            self.first_side = tuple(event.first_side)
            self.second_side = tuple(event.second_side)
            self.cut_off = instant(event.cut_off)
            self.answer_by = instant(event.answer_by)
            self.state = BookingState.WAITING_FOR_THE_CLUB
            self.called_off = None
            self.called_off_for_good = False
            self.taken_back_at = None
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


def _a_request(
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
    answer_by: Instant,
    filled_by: UUID | None,
    at: Instant,
) -> BookingRequested:
    _sides_of_a_game(sport, first_side, second_side)
    invariant(cut_off <= start, f"a cut-off {cut_off} after the game {start}")
    # The club's longest time to confirm is the shortest notice it may give,
    # so an answer is always due before the game could start.
    invariant(
        at < answer_by <= start,
        f"asked at {at}, answer due {answer_by}, the game at {start}",
    )
    return BookingRequested(
        booking_id=booking_id,
        pool_id=pool_id,
        club_id=club_id,
        court_id=court.court_id,
        court_name=court.name,
        sport=sport.value,
        kind=kind.value,
        start=start,
        share_grosze=share_grosze,
        first_side=first_side,
        second_side=second_side,
        cut_off=cut_off,
        answer_by=answer_by,
        occurred_at=at,
        filled_by=filled_by,
    )
