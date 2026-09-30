"""What a caller asks the Club context for, in the primitives it asked in.

Plain values rather than value objects, for the reason ``RegisterUserCommand``
gives: a command is what a caller *asked for*, and the boundary must be able to
express the answer that gets refused, or the refusal has nowhere to happen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.kernel import Sport
from app.modules.clubs.domain.prices import BandDays
from app.modules.clubs.domain.raketa_terms import WayOfWorking


@dataclass(frozen=True)
class ClubDetailsInput:
    """The five details, as typed into the club website's form."""

    name: str
    district: str
    city: str
    sports: tuple[Sport, ...]
    latitude: float
    longitude: float


@dataclass(frozen=True)
class SignUpClubCommand:
    """A club signs up: its details, and the email and password its desk will
    sign in with — one request, one transaction (``docs/adr/0182`` §4)."""

    details: ClubDetailsInput
    email: str
    password: str


@dataclass(frozen=True)
class ChangeClubDetailsCommand:
    """The desk saves its club's details. ``club_id`` comes from the session,
    never from the body."""

    club_id: UUID
    details: ClubDetailsInput


@dataclass(frozen=True)
class SignInClubCommand:
    email: str
    password: str


# --------------------------------------------------------------------------- #
# Club courts (#535) — every ``club_id`` comes from the session, never the body
# --------------------------------------------------------------------------- #


@dataclass(frozen=True)
class AddCourtCommand:
    """The desk adds a court: its name, its one sport, indoor or outdoor."""

    club_id: UUID
    name: str
    sport: Sport
    indoor: bool


@dataclass(frozen=True)
class ChangeCourtCommand:
    """The desk saves a court's edit form: all four facts, as they now stand."""

    club_id: UUID
    court_id: UUID
    name: str
    sport: Sport
    indoor: bool
    offered: bool


@dataclass(frozen=True)
class RemoveCourtCommand:
    club_id: UUID
    court_id: UUID


@dataclass(frozen=True)
class SetRaketaHoursCommand:
    """The same week of ``(weekday, hour)`` cells on each of these courts."""

    club_id: UUID
    court_ids: tuple[UUID, ...]
    hours: tuple[tuple[int, int], ...]


@dataclass(frozen=True)
class AddExceptionCommand:
    """Hours to close: every court (``court_ids`` is ``None``) or these, from
    ``first_day`` to ``last_day`` inclusive, the whole day or between two hours."""

    club_id: UUID
    court_ids: tuple[UUID, ...] | None
    first_day: date
    last_day: date
    from_hour: int | None
    until_hour: int | None
    reason: str


@dataclass(frozen=True)
class RemoveExceptionCommand:
    club_id: UUID
    exception_id: UUID


@dataclass(frozen=True)
class PriceBandInput:
    days: BandDays
    from_hour: int
    until_hour: int
    price_grosze: int


@dataclass(frozen=True)
class SportPriceInput:
    sport: Sport
    price_grosze: int
    bands: tuple[PriceBandInput, ...]


@dataclass(frozen=True)
class SetPricesCommand:
    """The whole price table, as the desk saves it."""

    club_id: UUID
    prices: tuple[SportPriceInput, ...]


@dataclass(frozen=True)
class ChooseWayOfWorkingCommand:
    club_id: UUID
    way: WayOfWorking


@dataclass(frozen=True)
class SaveRaketaSettingsCommand:
    """The settings form, every field as the desk leaves it."""

    club_id: UUID
    release_lead_days: int
    cut_off_hours: int
    minimum_notice_hours: int
    time_to_confirm_minutes: int
    other_clubs_courts: bool
    other_clubs_within_km: int
    check_in: bool
    paused: bool


@dataclass(frozen=True)
class ConnectPaymentsCommand:
    """The desk asked to connect payments, or to continue: its club, and the
    email it signs in with — which the provider's pages open with."""

    club_id: UUID
    email: str
