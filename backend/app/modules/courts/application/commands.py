"""What a caller asks the Courts context to do.

**A caller asks for a category and a window, never for a court.** ADR-0035:
*"The match does not reach into court inventory. It asks for a court of this
category, for this window, and is given a reservation or refused. It never learns
how courts are organised."* So there is no `court_id` on ``ClaimCourtCommand``,
and that absence is the context's whole interface promise.

``ReassignCourtCommand`` is the one command that names a court, because
reassignment is the club's operation and the club is looking at its own courts.
It still cannot name a category: the category was bought.

Times are the caller's here, unlike Clubs' — a reservation is *for* a window, and
the window is the thing being asked about. The **instant of the write** still
comes from the ``Clock`` port; nothing on a command says when it was issued.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.modules.courts.domain.reservation import Holder
from app.modules.courts.domain.time_range import TimeRange


@dataclass(frozen=True)
class ClaimCourtCommand:
    """*A court of this category, for this window* — and who will hold it."""

    club_id: UUID
    category_id: UUID
    #: The interval the players get. What is claimed may be wider; what is shown
    #: never is.
    played: TimeRange
    holder: Holder


@dataclass(frozen=True)
class BookCourtCommand:
    """A player buying a court outright: a Booking, and the claim it holds."""

    club_id: UUID
    category_id: UUID
    played: TimeRange
    player_id: UUID


@dataclass(frozen=True)
class ReassignCourtCommand:
    """Swap which court a live reservation names, inside its own category."""

    reservation_id: UUID
    court_id: UUID


@dataclass(frozen=True)
class ReleaseReservationCommand:
    """Give the court back and keep the row."""

    reservation_id: UUID


@dataclass(frozen=True)
class CourtAvailabilityQuery:
    """*Is a court of this category free for this window*, asked of reservations."""

    club_id: UUID
    category_id: UUID
    window: TimeRange
