"""The Club courts stream: what a club offers Raketa, and how it works with it.

**One stream per club, filed under the club's own id** (``docs/adr/0189`` §5),
so *this club's courts* is a stream read and a second stream for one club is not
a thing the store can hold. It is a stream of its own rather than more events on
the club's, because the club's is what the search projection every player reads
is built from, and a desk painting hours is not a fact about where a club is.

**Nothing is written when a club signs up.** A club that has done nothing here
has no stream and folds to no courts, no way of working and the defaults —
exactly what the setup checklist says of it — so the first act is the birth.

Every event carries ``club_id``, the stream's own key, as a Plan's events carry
their challenge's: a record read alone still says whose it is.

A tuple a stream holds is **forced to a tuple on the way in and out**, since the
codec hands a JSON array back as a list and an event read back must equal the
one appended; the ids inside one are forced back to ``UUID`` for the same
reason, the codec coercing only a field declared as one.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class CourtAdded:
    """The desk added a court: its name, its one sport, and indoor or outdoor.
    A court is born **offered**, and offering nothing until its hours are
    painted."""

    club_id: UUID
    court_id: UUID
    name: str
    sport: str
    indoor: bool
    occurred_at: datetime


@dataclass(frozen=True)
class CourtChanged:
    """The desk edited a court — **its name, sport and roof, as they now
    stand**, one event for any of the three because they are one form."""

    club_id: UUID
    court_id: UUID
    name: str
    sport: str
    indoor: bool
    occurred_at: datetime


@dataclass(frozen=True)
class CourtSwitchedOff:
    """The court is no longer offered to Raketa. It keeps its name and hours,
    and a game already booked on it is played as booked."""

    club_id: UUID
    court_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CourtSwitchedOn:
    """The court is offered to Raketa again, on the hours it kept."""

    club_id: UUID
    court_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CourtRemoved:
    """The desk deleted a court. Refused while a booking is ahead of it, so a
    court removed is one nothing will be played on."""

    club_id: UUID
    court_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class RaketaHoursSet:
    """The hours of an ordinary week this court is offered to Raketa, **as they
    now stand** — the player's grid, each cell as its durable code
    (``"2:19"``), in the week's own order. Empty is a court offering nothing."""

    club_id: UUID
    court_id: UUID
    hours: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "hours", tuple(self.hours))


@dataclass(frozen=True)
class ExceptionAdded:
    """The desk closed hours without touching the pattern.

    ``court_ids`` is ``None`` for **every** court; the days are local ISO dates
    (``"2026-10-04"``), inclusive; the hours are both ``None`` for the whole day
    or the hour closing starts and the hour it ends.
    """

    club_id: UUID
    exception_id: UUID
    court_ids: tuple[UUID, ...] | None
    first_day: str
    last_day: str
    from_hour: int | None
    until_hour: int | None
    reason: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if self.court_ids is not None:
            object.__setattr__(
                self,
                "court_ids",
                tuple(UUID(str(court_id)) for court_id in self.court_ids),
            )


@dataclass(frozen=True)
class ExceptionRemoved:
    """The desk removed an exception: its hours are open again, as the pattern
    has them."""

    club_id: UUID
    exception_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class PricesSet:
    """One sport's prices, **as they now stand**: the standard court-hour in
    grosze and its bands, each as its durable code (``"WEEKDAYS:17:22:14000"``)
    in the canonical order. ``price_grosze`` is ``None`` — and ``bands`` empty —
    when the sport is no longer priced."""

    club_id: UUID
    sport: str
    price_grosze: int | None
    bands: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(self, "bands", tuple(self.bands))


@dataclass(frozen=True)
class WayOfWorkingChosen:
    """The club chose how it works with Raketa — or changed it, which applies
    to hours not yet booked (the mechanics §16.3)."""

    club_id: UUID
    way: str
    occurred_at: datetime


@dataclass(frozen=True)
class RaketaSettingsChanged:
    """The club saved its Raketa settings, **all of them as they now stand**.
    The first one is also the club **confirming** them — defaults included —
    which is the setup checklist's last step."""

    club_id: UUID
    release_lead_days: int
    cut_off_hours: int
    minimum_notice_hours: int
    time_to_confirm_minutes: int
    other_clubs_courts: bool
    other_clubs_within_km: int
    check_in: bool
    occurred_at: datetime


@dataclass(frozen=True)
class RaketaPaused:
    """No new cards on this club's courts. Booked games are played as booked,
    and cards already dealt keep their court until their book-by (§16.15)."""

    club_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class RaketaResumed:
    """New cards on this club's courts again."""

    club_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class PaymentsAccountOpened:
    """Raketa opened the club's account at the payment provider, where the club
    is paid as the seller (#537). **Once, for ever**: every later link continues
    this account. It is born not started — the club has filled in nothing."""

    club_id: UUID
    account_id: str
    occurred_at: datetime


@dataclass(frozen=True)
class PaymentsStatusChanged:
    """The provider says the club's account now stands otherwise — **as read
    from the provider**, never off a notice, since notices arrive out of order.
    Ready is the setup checklist's first step done; ready no longer is the club
    off players' decks until the provider has what it wants."""

    club_id: UUID
    status: str
    occurred_at: datetime
