"""What the Bookings context needs, in its own words.

**Two ports are its own store**: the Booking repository, whose ``save`` writes
the ``bookings`` and ``booking_seats`` projections in the caller's transaction,
and the directory that reads them back — which court hours bookings hold, which
games a player has booked, and how many were booked in each pool — and the
summaries of each club's day of new bookings, sent once (#548).

**And one is what it publishes**: the record of who kept their booked games
(#544), which the Player Score reads.

**Three are demands on contexts it does not write**: which courts a club still
has for Raketa at an hour, and its cut-off (``clubs``, over what it sells); the
ordinary Game a booking opens (``games``, over the use case a completed line-up
opens one with); and whom a club's email is addressed to and what the club is
called (``clubs``, over its own account and details). A club's cancel also
closes the court it took a game off for that hour (``clubs``, over its own
exceptions, #673).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.bookings.domain.booking import (
    BookedCourt,
    Booking,
    CancelReason,
    FreeCourt,
)
from app.modules.bookings.domain.keeping import KeepingRecord
from app.modules.bookings.domain.summary import NewBookingsSummary


@runtime_checkable
class BookingRepository(Protocol):
    async def load(self, booking_id: UUID) -> Booking | None: ...

    async def save(self, booking: Booking) -> None:
        """Append what the booking recorded and write its rows, in the caller's
        transaction."""
        ...


@final
@dataclass(frozen=True, slots=True)
class HeldCourtHour:
    """A court hour a booking holds."""

    court_id: UUID
    start: Instant
    booking_id: UUID


@runtime_checkable
class BookingDirectory(Protocol):
    """The projections, read. Written only by ``BookingRepository.save``."""

    async def held_at(
        self, club_id: UUID, *, start: Instant, end: Instant | None
    ) -> Sequence[HeldCourtHour]:
        """Every court hour of this club a booking holds, starting at or after
        ``start`` and before ``end`` — for ever when ``end`` is ``None``."""
        ...

    async def cards_to_fix_past(self, *, now: Instant) -> Sequence[UUID]:
        """Every booking with a player whose time to fix the card ran out at or
        before ``now`` (#639) — the time-to-pay job's candidates, the earliest
        first."""
        ...

    async def cards_to_fix_of(self, player_id: UUID) -> Sequence[UUID]:
        """Every booking on which this player's holding was refused and their
        card is still to fix (#639) — their *To confirm* rows."""
        ...

    async def keeps_past(self, *, now: Instant) -> Sequence[UUID]:
        """Every booked game with a seat kept for a rescuer whose time ran out
        by ``now`` — the earliest first (#640)."""
        ...

    async def kept_for(self, player_id: UUID) -> Sequence[UUID]:
        """Every booked game on which a seat was kept for this rescuer (#640),
        their time running or up — until they take one, or the game is off."""
        ...

    async def starts_for(
        self, player_id: UUID, *, start: Instant, end: Instant | None
    ) -> Sequence[Instant]:
        """When each of this player's **booked** games starts, from ``start``
        until ``end`` — for ever when ``end`` is ``None`` — soonest first. A game
        called off never will be, and one they left is not theirs (#544); one
        with a seat open is."""
        ...

    async def of_player(
        self, player_id: UUID, *, since: Instant | None
    ) -> Sequence[UUID]:
        """Every booking this player has a seat on whose game starts at or
        after ``since`` — whenever it is, when ``since`` is ``None`` — whatever
        it came to: **soonest game first**, and by id among games at one hour
        (#542). A seat they left is not theirs (#544). Home reads from an
        hour on, so how many it reads no longer grows with old games (#613)."""
        ...

    async def games_before(
        self, player_id: UUID, *, before: Instant
    ) -> Mapping[UUID, UUID]:
        """Each Game opened by a booking this player has a seat on whose game
        started before ``before``, to that booking — **ids alone, no stream
        read**: where Home looks for an older game whose score is still waiting
        (#613). A booking with no Game yet is not here, nor a seat they left."""
        ...

    async def counted_in(self, pool_ids: Collection[UUID]) -> Mapping[UUID, int]:
        """How many games were booked in each of these pools — one question
        about the set. A pool absent from the answer has booked none (#542).

        **Only a booked game counts** — whole, or with a seat open (#544): one
        called off is not a game anybody will play there."""
        ...

    async def ever_seated(
        self, player_ids: Collection[UUID]
    ) -> Sequence[tuple[UUID, UUID]]:
        """Each ``(player, booking)`` of these players on a game that was ever
        booked — **whether they left it or not**: the record's read (#544)."""
        ...

    async def rescues_in(
        self, pool_id: UUID, *, sport: Sport, now: Instant
    ) -> Sequence[UUID]:
        """Every booking in this pool and sport with a seat open whose hour is
        still ahead at ``now`` — **the soonest first**, and by id among games at
        one hour (#545). **Candidates**: the aggregate says whether a seat is
        there to take — not on a game short at its cut-off."""
        ...

    async def at_club(
        self, club_id: UUID, *, start: Instant, end: Instant
    ) -> Sequence[UUID]:
        """Every booking at this club whose game starts from ``start`` until
        ``end``, **whatever it came to** — booked, with a seat open, called
        off — soonest first, and by id among games at one hour: the
        club's Bookings page for a day (#547)."""
        ...

    async def booked_between(
        self, *, start: Instant, end: Instant
    ) -> Mapping[UUID, Sequence[UUID]]:
        """Each club's bookings **booked** from ``start`` until ``end`` —
        filled — whatever they came to since, the soonest game first (#548). A
        club that booked none is absent."""
        ...

    async def short_at_the_cut_off(self, *, now: Instant) -> Sequence[UUID]:
        """Every booking with a seat open since before its cut-off whose cut-off
        has come by ``now``, the earliest cut-off first — whether or not its
        hour has come too, since everybody still in is owed their money either
        way (#544). **Candidates**: the aggregate decides."""
        ...


@runtime_checkable
class BookingHistoryQuery(Protocol):
    """**What this context publishes about a player's record** (#544; the
    mechanics §15.4): who kept the booked games they held a seat on, and who
    broke them — the *keeps plans* strand's input, read by ``player_score``.

    **A player with no settled booked game is absent from the answer**, never a
    nought: nobody has failed to keep a game they never had. One question about
    the set, as every record read is."""

    async def keeping_for(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, KeepingRecord]:
        """Each of these players who has a settled booked game, at ``now``."""
        ...


@final
@dataclass(frozen=True, slots=True)
class CourtForTheGame:
    """The court a full game is booked on — **the first free court of its
    sport at its hour**, in the club's own order (the mechanics §11.2) — and
    how many hours before the game the club's free cancellation ends."""

    court: BookedCourt
    cut_off_hours: int


@runtime_checkable
class ClubCourtsAtTheHour(Protocol):
    """**A demand of the Club context**: the courts a club still has for Raketa
    at an hour."""

    async def first_free(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> CourtForTheGame | None:
        """The first court of ``sport`` the club still has for Raketa from
        ``start`` — **whatever deadline its settings now give the hour**, since
        a card keeps the book-by it was made with — and its cut-off. ``None``
        when every court of the sport then is booked, closed or no longer
        offered, or the club no longer sells."""
        ...

    async def free_courts(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> Sequence[FreeCourt]:
        """Every court of ``sport`` the club still has for Raketa from
        ``start``, read as ``first_free`` reads it — **in the club's own
        order** — where a booked game may be moved to (#547), each with the
        share one player pays for it at that hour, which a club's cancel asks
        of a court before it absorbs the game (#672). Empty when there is none,
        or the club no longer sells."""
        ...


@runtime_checkable
class CourtClosures(Protocol):
    """**A demand of the Club context**: the court a club's cancel took a game
    off, closed for the game's hour (#673, a ruling beside ``docs/adr/0196``
    §3) — it can't be played then, so it is never sold for that hour again."""

    async def close(
        self,
        club_id: UUID,
        court_id: UUID,
        *,
        start: Instant,
        because: CancelReason,
        at: Instant,
    ) -> None:
        """Close ``court_id`` for the hour from ``start``, in the caller's
        transaction, saying why in the club's own list — until the club
        opens it again."""
        ...


@runtime_checkable
class GameOpening(Protocol):
    """**A demand of the Games context**: the ordinary Game a booking opens,
    exactly as a completed line-up opens one (``docs/adr/0189`` §5, Q6)."""

    async def open(
        self,
        *,
        booking_id: UUID,
        sport: Sport,
        counted: bool,
        first_side: tuple[UUID, ...],
        second_side: tuple[UUID, ...],
        starts_at: Instant,
        at: Instant,
    ) -> UUID:
        """Open the game, in the caller's transaction, and answer its id."""
        ...


@runtime_checkable
class GameChanges(Protocol):
    """**A demand of the Games context**: what leaving, a rescue and the
    cut-off do to the ordinary Game a booking opened (#544, #545) — exactly
    what a departure, a re-seat and a call-off do to a completed line-up's
    game today."""

    async def vacate(self, booking_id: UUID, player_id: UUID, *, at: Instant) -> None:
        """This player left: their seat on the game is open — and they are out
        of its room, whose members are its line-up. In the caller's
        transaction."""
        ...

    async def seat(
        self, booking_id: UUID, player_id: UUID, *, side: str, at: Instant
    ) -> None:
        """This player took the open seat on ``side`` (``A`` or ``B``): they
        are on the game's court — and in its room. In the caller's
        transaction (#545)."""
        ...

    async def call_off(self, booking_id: UUID, *, at: Instant) -> None:
        """The game is off, called off by nobody — and its room with it. A game
        whose hour has already come with the seat still open ended by its own
        clock, and keeps that end. In the caller's transaction."""
        ...

    async def call_off_whole(self, booking_id: UUID, *, at: Instant) -> None:
        """The club cancelled the booking: the game is off, called off by nobody,
        **whole or with a seat open** — and its room with it. Before its hour,
        and in the caller's transaction (#547)."""
        ...


@runtime_checkable
class GameNoShows(Protocol):
    """**A demand of the Games context**: who Didn't come to the ordinary Game
    a booking opened (#547, #657; the mechanics §15.1, §15.4) — *the strongest
    mark* until the points ticket prices it once, which breaks the booked game
    on the record of whoever it names. Attendance is the Game's, so the record
    asks for it rather than keeping a copy."""

    async def did_not_come(self, booking_id: UUID, *, now: Instant) -> frozenset[UUID]:
        """Everybody who Didn't come at ``now``, for good — empty while a late
        claim's day still runs, and for a booking with no Game."""
        ...


@final
@dataclass(frozen=True, slots=True)
class ClubDesk:
    """Whom an email to a club is addressed to — its one sign-in — and what the
    club is called."""

    email: str
    club_name: str


@runtime_checkable
class ClubDesks(Protocol):
    """**A demand of the Club context**: the desk a club's email is sent to
    (the mechanics §16.12) — a game called off at the cut-off, at once, and the
    day's new bookings."""

    async def of(self, club_id: UUID) -> ClubDesk | None:
        """The club's desk, or ``None`` for a club that no longer exists."""
        ...


@runtime_checkable
class SummaryRepository(Protocol):
    """One stream per club per day, born once (#548)."""

    async def load(self, summary_id: UUID) -> NewBookingsSummary | None: ...

    async def save(self, summary: NewBookingsSummary) -> None:
        """Append it in the caller's transaction — a conflict if that club's
        day was summed up already."""
        ...
