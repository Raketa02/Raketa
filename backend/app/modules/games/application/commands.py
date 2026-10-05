"""What a caller may ask this context to do. **Six commands, and no flags.**

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
    """A line-up completed. ``challenges`` sends this and nothing else does."""

    challenge_id: UUID
    sport: Sport
    counted: bool
    window: str | None
    line_up: Sequence[tuple[str, UUID]]
    #: The hour a booking opens it for (#541) — then ``challenge_id`` is the
    #: booking's id. ``None`` from a completed line-up.
    starts_at: Instant | None = None


@dataclass(frozen=True, slots=True)
class VacateSeatCommand:
    """Somebody left the game this challenge became. ``challenges`` sends this
    in the transaction of the departure — and ``bookings`` in a booked game's,
    its booking's id where a challenge's is (#544)."""

    challenge_id: UUID
    player_id: UUID


@dataclass(frozen=True, slots=True)
class TakeASeatCommand:
    """A booking's rescue took an open seat on the game it opened (#545):
    ``bookings`` sends this in the transaction of the rescue, its booking's id
    where a challenge's is, and the side the leaver sat on."""

    challenge_id: UUID
    player_id: UUID
    #: ``A`` or ``B`` — the open seat's side.
    side: str


@dataclass(frozen=True, slots=True)
class CallOffGameCommand:
    """The court was ended with a seat open, so the game it became is called
    off. ``challenges`` sends this in the transaction of the departure that
    left at most one player on the court (``docs/adr/0165`` §3), or of the
    hour that found the court still short of a player (``docs/adr/0175``
    §3) — and ``bookings`` when a booked game is short at its cut-off, its
    booking's id where a challenge's is (#544). ``called_by`` is the leaver, or
    ``None`` for the hour and the cut-off."""

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
class DismissGameCommand:
    """*Remove this card.* The reader's own, on a called-off game
    (``docs/adr/0172`` §5)."""

    game_id: UUID
    player_id: UUID


@dataclass(frozen=True, slots=True)
class DismissGameOfCourtCommand:
    """*Remove this row.* The reader's own, on the called-off game this
    challenge became — sent by ``challenges`` for anybody it had asked, seated
    on the game or not (``docs/adr/0175`` §5)."""

    challenge_id: UUID
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
