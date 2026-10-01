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
be In — withdraws the request: nobody paid, **nobody keeps a seat on it**, and
the game is filling again, where the people still In find it. **Full again,
the same game is asked again on the same stream**, with whoever is In then: one
id from the first card to the court.

**A player leaves a booked game** (#544; the mechanics §12.3, §13): their seat
opens — *seat open* — and the game is still the others'. **A game plays full or
not at all**: a seat that opened before the club's cut-off and is still open at
it calls the game off (``CalledOffAtCutOff``), the court the club's again; a
seat that opened after the cut-off leaves the game going ahead short. Whether a
game is **short at its cut-off** is read off the departures and the clock, so
every read says it from the cut-off on, whether or not the job has recorded it.

A rescue taking an open seat arrives with #545, *played* with #547, each as an
event on this stream.
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
    BookingConfirmed,
    BookingRefused,
    BookingRequested,
    BookingTimedOut,
    CalledOffAtCutOff,
    RequestWithdrawn,
    SeatLeft,
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


@dataclass(frozen=True, slots=True)
class Departure:
    """A player who left the booked game: from which side — where a rescue
    taking the seat sits (#545) — and when, which against the booking's
    cut-off says whether leaving was free."""

    player_id: UUID
    #: ``A`` — the first side — or ``B``.
    side: str
    at: Instant


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
    #: Why it will not be played, once called off.
    called_off: CalledOff | None = None
    #: The club's own note when it refused — for its records, never a player's.
    refusal_reason: str | None = None
    #: When it was booked — ``None`` while it waits, and if it never was.
    booked_at: Instant | None = None
    #: Everybody who left the booked game, in the order they did (#544).
    departures: tuple[Departure, ...] = ()
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
        at: Instant,
    ) -> "Booking":
        """A full game put to its On request club, the court reserved for it."""

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
        return self.state is BookingState.WAITING_FOR_THE_CLUB

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
    def is_booked(self) -> bool:
        """Booked and not called off — whole, or with a seat open."""

        return self.state in (BookingState.BOOKED, BookingState.SEAT_OPEN)

    @property
    def open_since(self) -> Instant | None:
        """When the first seat still open opened — ``None`` while every seat is
        held. Until rescues arrive (#545) every seat that opened is open."""

        if self.open_seats == 0:
            return None
        return min(left.at for left in self.departures)

    @property
    def left_before_the_cut_off(self) -> tuple[Departure, ...]:
        """The leavers who left while leaving was free — a game that filled
        after its cut-off never had any."""

        return tuple(left for left in self.departures if left.at < self.cut_off)

    @property
    def short_from(self) -> Instant | None:
        """**A game plays full or not at all**: the moment a booked game with a
        seat that opened before its cut-off, and is open still, is off — its
        cut-off — or ``None`` for a game whole, or short only by a seat that
        opened after the cut-off, which goes ahead short.

        Until rescues arrive (#545) a seat that opened stays open, so every
        departure before the cut-off is a seat still open at it."""

        if self.state is BookingState.SEAT_OPEN and self.left_before_the_cut_off:
            return self.cut_off
        return None

    def short_at_the_cut_off(self, *, now: Instant) -> bool:
        """Off at ``now`` because a seat was still open at the cut-off — read
        off the clock, so every read says so before the job records it."""

        return self.short_from is not None and now >= self.short_from

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
        """The club said yes, every seat was paid, and ``game_id`` is open."""

        self._refuse_unless_waiting()
        self._record_that(
            BookingAccepted(booking_id=self.booking_id, game_id=game_id, occurred_at=at)
        )

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

    def withdraw_request(self, player_ids: tuple[UUID, ...], *, at: Instant) -> bool:
        """These players' seats opened while the game waited: the request is
        off, and nobody keeps a seat on it. Answers whether anything was
        recorded — nothing on a booking not waiting for the club."""

        if not self.is_waiting:
            return False
        invariant(
            bool(player_ids) and set(player_ids) <= set(self.players),
            f"{player_ids} are not all on {self.booking_id}",
        )
        self._record_that(
            RequestWithdrawn(
                booking_id=self.booking_id, player_ids=player_ids, occurred_at=at
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
        at: Instant,
    ) -> None:
        """The game whose request was withdrawn is full again: put to the club
        again, with whoever is In now, on the first free court now."""

        invariant(
            self.called_off is CalledOff.SEAT_OPENED,
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
                at=at,
            )
        )

    # ------------------------------------------------------------------- fold

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
            self.first_side = ()
            self.second_side = ()
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
        elif isinstance(event, CalledOffAtCutOff):
            self.state = BookingState.CALLED_OFF
            self.called_off = CalledOff.SHORT_AT_THE_CUT_OFF
        elif isinstance(event, BookingRequested):
            self.court = BookedCourt(court_id=event.court_id, name=event.court_name)
            self.first_side = tuple(event.first_side)
            self.second_side = tuple(event.second_side)
            self.cut_off = instant(event.cut_off)
            self.answer_by = instant(event.answer_by)
            self.state = BookingState.WAITING_FOR_THE_CLUB
            self.called_off = None
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
    )
