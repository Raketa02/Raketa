"""The Booking aggregate — event-sourced, one stream per filled proposal
(``docs/adr/0189`` §5; the mechanics §11).

**A booking is the game a full card became**, and its id is the card's. It holds
what the fill decided and nothing a reader could derive: the court and its
number, who sits on which side, the cut-off as the club set it when the game
filled, and the Game it opened. Its money is the Seat charges' (``payments``),
its result the Game's (``games``) — after the fill, *everything that happens to a
game today happens to it unchanged* (Q6).

**Born booked** (#541). The states the mechanics name beside *booked* —
*waiting for the club*, *seat open*, *called off*, *played* — arrive with the
tickets that build them (#543, #544, #545, #547), each as an event on this
stream.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import SPORT_SPECS, Instant, Sport, instant, invariant
from app.modules.bookings.domain.events import BookingConfirmed
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass(frozen=True, slots=True)
class BookedCourt:
    """The court a game is booked on: its id, and what the club calls it."""

    court_id: UUID
    name: str


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
    game_id: UUID
    booked_at: Instant
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

        per_side = SPORT_SPECS[sport].players // 2
        invariant(
            len(first_side) == len(second_side) == per_side,
            f"sides {first_side} and {second_side} for {per_side} a side",
        )
        invariant(
            not set(first_side) & set(second_side),
            f"somebody on both sides: {first_side} {second_side}",
        )
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
        booking = cls._born(confirmed)
        booking._events.record(confirmed)
        return booking

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Booking":
        history = iter(events)
        opening = next(history)
        invariant(
            isinstance(opening, BookingConfirmed),
            f"a booking stream opens {opening!r}",
        )
        assert isinstance(opening, BookingConfirmed)
        booking = cls._born(opening)
        for event in history:
            raise TypeError(f"Unsupported booking event {event!r}")
        return booking

    @classmethod
    def _born(cls, confirmed: BookingConfirmed) -> "Booking":
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
            game_id=confirmed.game_id,
            booked_at=instant(confirmed.occurred_at),
            version=1,
        )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()
