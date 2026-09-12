"""What a caller may ask this context to do. **Four commands, and no flags.**

Each is one sentence a player could say. There is no *kind* on the result
command deciding between proposing, correcting and countering: which of the three
an act is follows from what already stands on the game, and a client that could
name it is a client that could name it wrongly.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence
from uuid import UUID

from app.kernel import Sport
from app.modules.games.domain.results import Score


@dataclass(frozen=True, slots=True)
class OpenPlannedGameCommand:
    """A line-up completed. ``challenges`` sends this and nothing else does."""

    challenge_id: UUID
    sport: Sport
    counted: bool
    window: str | None
    line_up: Sequence[tuple[str, UUID]]


@dataclass(frozen=True, slots=True)
class VacateSeatCommand:
    """Somebody left the game this challenge became. ``challenges`` sends this
    in the transaction of the departure, and nothing else does."""

    challenge_id: UUID
    player_id: UUID


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
