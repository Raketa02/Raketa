"""What a caller asks the Club context for, in the primitives it asked in.

Plain values rather than value objects, for the reason ``RegisterUserCommand``
gives: a command is what a caller *asked for*, and the boundary must be able to
express the answer that gets refused, or the refusal has nowhere to happen.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.kernel import Sport


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
