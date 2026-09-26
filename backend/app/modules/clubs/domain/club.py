"""The Club aggregate — event-sourced, and its details are its whole state.

A club's stream begins with ``ClubRegistered`` and every later edit is
``ClubDetailsChanged`` (``docs/adr/0182`` §1). Nothing else happens to a club in
this build: it is not verified, it holds no courts, and it cannot be deleted.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterable
from uuid import UUID

from app.kernel import Sport
from app.modules.clubs.domain.events import ClubDetailsChanged, ClubRegistered
from app.modules.clubs.domain.value_objects import (
    City,
    ClubDetails,
    ClubName,
    District,
    MapPoint,
    OfferedSports,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Club:
    """One club, as its stream leaves it."""

    id: UUID
    details: ClubDetails
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    @classmethod
    def from_history(cls, events: Iterable[DomainEvent]) -> "Club":
        club = cls._empty()
        for event in events:
            club._apply(event)
        return club

    @classmethod
    def _empty(cls) -> "Club":
        club = cls.__new__(cls)
        club.version = 0
        club._events = EventRecorder()
        return club

    @classmethod
    def register(
        cls, *, club_id: UUID, details: ClubDetails, occurred_at: datetime
    ) -> "Club":
        """A club signs up — **the only way one begins** (``docs/adr/0182`` §7)."""

        club = cls._empty()
        club._record_that(
            _details_event(
                ClubRegistered,
                club_id=club_id,
                details=details,
                occurred_at=occurred_at,
            )
        )
        return club

    def change_details(self, details: ClubDetails, *, occurred_at: datetime) -> None:
        """The desk saves its club's details (``docs/adr/0182`` §5).

        **Saving them unchanged records nothing**, as a second ``disable`` does
        on a User: the stream records acts, and this one changed nothing. The
        refusal of a sport an official group declares is not this aggregate's to
        know — it is a fact about groups, and the use case asks them
        (``domain/untick.py``).
        """

        if details == self.details:
            return
        self._record_that(
            _details_event(
                ClubDetailsChanged,
                club_id=self.id,
                details=details,
                occurred_at=occurred_at,
            )
        )

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, (ClubRegistered, ClubDetailsChanged)):
            self.id = event.club_id
            self.details = ClubDetails(
                name=ClubName(event.name),
                district=District(event.district),
                city=City(event.city),
                sports=OfferedSports.of(Sport(code) for code in event.sports),
                point=MapPoint(latitude=event.latitude, longitude=event.longitude),
            )
            self.version += 1
            return
        raise TypeError(f"Unsupported club event {event!r}")


def _details_event(
    kind: type[ClubRegistered] | type[ClubDetailsChanged],
    *,
    club_id: UUID,
    details: ClubDetails,
    occurred_at: datetime,
) -> ClubRegistered | ClubDetailsChanged:
    """Either event, carrying the five details as both spell them."""

    return kind(
        club_id=club_id,
        name=details.name.value,
        district=details.district.value,
        city=details.city.value,
        sports=tuple(sport.value for sport in details.sports.in_registry_order()),
        latitude=details.point.latitude,
        longitude=details.point.longitude,
        occurred_at=occurred_at,
    )
