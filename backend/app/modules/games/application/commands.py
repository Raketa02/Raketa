"""What a caller may ask this context to do. **Eight commands, and no flags.**

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
    line_up: Sequence[tuple[str, UUID]]
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
class ReportANoShowCommand:
    """*Kuba didn't come* (#547): ``player_id`` came, ``absent_id`` did not."""

    game_id: UUID
    player_id: UUID
    absent_id: UUID


@dataclass(frozen=True, slots=True)
class DisputeANoShowCommand:
    """*I was there* (#547): ``player_id`` was reported as not coming."""

    game_id: UUID
    player_id: UUID
