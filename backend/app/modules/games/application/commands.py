"""What a caller may ask this context to do. **Ten commands, and no flags.**

Each is one sentence a player could say. There is no *kind* on the result
command deciding between proposing, correcting and countering: which of the three
an act is follows from what already stands on the game, and a client that could
name it is a client that could name it wrongly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.games.domain.attendance import LocationFix
from app.modules.games.domain.results import Score


@dataclass(frozen=True, slots=True)
class OpenPlannedGameCommand:
    """A line-up was booked. ``bookings`` sends this and nothing else does
    (#541): ``challenge_id`` is the booking's id, under the name the field was
    born with, and ``starts_at`` the booked hour."""

    challenge_id: UUID
    sport: Sport
    counted: bool
    window: str | None
    #: Each seat's side and player — ``None`` for a seat still to be taken, a
    #: friends game's invited seat (#751), which a re-seat fills on accepting.
    line_up: Sequence[tuple[str, UUID | None]]
    starts_at: Instant | None = None


@dataclass(frozen=True, slots=True)
class VacateSeatCommand:
    """Somebody left the game their booking opened. ``bookings`` sends this in
    the transaction of the departure (#544)."""

    challenge_id: UUID
    player_id: UUID


@dataclass(frozen=True, slots=True)
class TakeASeatCommand:
    """A booking's rescue took an open seat on the game it opened (#545):
    ``bookings`` sends this in the transaction of the rescue, with the side the
    leaver sat on."""

    challenge_id: UUID
    player_id: UUID
    #: ``A`` or ``B`` — the open seat's side.
    side: str


@dataclass(frozen=True, slots=True)
class CallOffGameCommand:
    """A booked game is short at its club's cut-off, so it is called off.
    ``bookings`` sends this in the transaction of the cut-off (#544);
    ``called_by`` is ``None``, because the cut-off is nobody's act."""

    challenge_id: UUID
    called_by: UUID | None


@dataclass(frozen=True, slots=True)
class StateResultCommand:
    """*This is the score.* Entering, correcting and countering are all this."""

    game_id: UUID
    player_id: UUID
    score: Score | None


@dataclass(frozen=True, slots=True)
class AcceptResultCommand:
    """*That is what happened.* From the other side, and one is enough."""

    game_id: UUID
    player_id: UUID


@dataclass(frozen=True, slots=True)
class NoteAbsentCommand:
    """*Oscar isn't here yet* (#657): ``player_id`` is at the club, with the fix
    their phone read at the tap, and ``absent_id`` is not here yet."""

    game_id: UUID
    player_id: UUID
    absent_id: UUID
    fix: LocationFix


@dataclass(frozen=True, slots=True)
class NoteArrivalCommand:
    """*I'm here* when ``arrived_id`` is ``player_id``, *they're here* otherwise
    (#657) — from the club, with the fix read at the tap."""

    game_id: UUID
    player_id: UUID
    arrived_id: UUID
    fix: LocationFix


@dataclass(frozen=True, slots=True)
class ClaimPresenceCommand:
    """*I was there* (#657): ``player_id`` Didn't come, and says they did."""

    game_id: UUID
    player_id: UUID


@dataclass(frozen=True, slots=True)
class ConfirmPresenceCommand:
    """*Yes, they were here* (#657): ``player_id`` agrees with
    ``claimant_id``'s *I was there*."""

    game_id: UUID
    player_id: UUID
    claimant_id: UUID
