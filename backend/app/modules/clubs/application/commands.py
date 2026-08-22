"""What a caller asks the Clubs context to do.

**No command carries an actor**, and that is the v1 decision rather than an
omission. ADR-0077 fixes that ``changedBy`` ships on every versioned row from the
first migration and reads the system sentinel until a club-staff identity exists;
there is no role concept on ``User`` and no club console, so a field a caller
could fill would be a field with nothing true to put in it. The column is there,
every row reads ``system``, and the day the console authors a change the command
gains the argument without a migration or a backfill.

Times are not on the commands either: *when* a version opens is the write's own
instant, taken from the ``Clock`` port, never from a caller. A caller-supplied
effective date is a way to open a row in the past, which would reorder a series
that the whole context exists to keep in order.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.kernel import Grosze, Sport

from app.modules.clubs.domain.policy import ClubPolicy
from app.modules.clubs.domain.value_objects import (
    CategoryName,
    ClubName,
    ClubPricing,
    CourtLabel,
    GeoPoint,
    PayoutDestination,
    StreetAddress,
)


@dataclass(frozen=True)
class RegisterClubCommand:
    name: ClubName
    address: StreetAddress
    point: GeoPoint
    #: An IANA name. Resolved to a ``Zone`` inside the use case, so a bad one is
    #: refused at the boundary of the context rather than at the first booking.
    timezone: str
    policy: ClubPolicy
    payout: PayoutDestination
    pricing: ClubPricing = ClubPricing()


@dataclass(frozen=True)
class ChangeClubPolicyCommand:
    club_id: UUID
    policy: ClubPolicy


@dataclass(frozen=True)
class ChangePayoutDestinationCommand:
    club_id: UUID
    destination: PayoutDestination


@dataclass(frozen=True)
class AddCourtCategoryCommand:
    club_id: UUID
    name: CategoryName
    sport: Sport
    #: What one booked block costs before the club's own multipliers, in grosze.
    rate: Grosze


@dataclass(frozen=True)
class RetireCourtCategoryCommand:
    club_id: UUID
    category_id: UUID


@dataclass(frozen=True)
class AddCourtCommand:
    club_id: UUID
    category_id: UUID
    label: CourtLabel


@dataclass(frozen=True)
class MoveCourtCommand:
    club_id: UUID
    court_id: UUID
    category_id: UUID
    label: CourtLabel | None = None


@dataclass(frozen=True)
class RetireCourtCommand:
    club_id: UUID
    court_id: UUID
