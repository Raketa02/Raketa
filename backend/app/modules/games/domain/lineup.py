"""Who played, on which side, and what kind of evening it was.

**The line-up is settled at the plan and never afterwards.** ``challenges``'
invariant is that *an acceptance is to the game, not to the side* — the
membership is fixed the moment the last seat accepts, and the arrangement is
still the organiser's to choose. This context takes the arrangement as it stood
at that instant and freezes it, because a result is about the two sides that
played and there is nothing here that can move anybody.

**One string per seating on the wire**, the precedent ``challenges`` set for its
seats: the event codec coerces scalars only, so a tuple of dataclasses comes back
out of storage as a list of dicts and the aggregate would rebuild the shape on
every replay.

``GameSide`` is a **third** spelling of A and B in this repository, after
``challenges.domain.seats.GameSide`` and ``matchmaking.domain.lineups.GameSide``. The
strings are equal on purpose so the mapping at each seam is identity rather than
a table; what differs is what the word is *about*. The matcher's is a side of a
line-up it is ranking, ``challenges``' is a position somebody was asked to sit
in, and this one is **the side that won or lost**.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, final
from uuid import UUID

from app.kernel import invariant

#: What separates the two fields of a seating code. A pipe rather than a colon
#: for the reason ``challenges`` chose one: nothing else in either field can
#: spell it, and a uuid is full of hyphens.
_FIELD = "|"


@final
class GameSide(str, Enum):
    """Which side of the net. **Two, and the game names one of them.**"""

    A = "A"
    B = "B"

    @property
    def other(self) -> "GameSide":
        """The side across the net. The only thing this context does with a side."""

        return GameSide.B if self is GameSide.A else GameSide.A


@final
class GameKind(str, Enum):
    """Whether this game is evidence about how well anybody plays.

    **Stamped at the plan and never derived at the end.** ADR-0049's fourth
    rejected option is the reason: *a friendly is a thing people choose*, and
    reclassifying a counted game because nobody typed a score hands a player the
    exact evening they said they did not want, and gives one word two meanings —
    what you chose, and what you failed to record.
    """

    COUNTED = "COUNTED"
    FRIENDLY = "FRIENDLY"


@final
@dataclass(frozen=True, slots=True)
class Seating:
    """One person, on one side. **Both fields required** — an empty seat cannot
    reach this context, because a line-up completes before a game is planned."""

    side: GameSide
    player_id: UUID

    @property
    def code(self) -> str:
        """``A|<uuid>``. The durable spelling, and the only one."""

        return f"{self.side.value}{_FIELD}{self.player_id}"

    @classmethod
    def from_code(cls, code: str) -> "Seating":
        parts = code.split(_FIELD)
        invariant(len(parts) == 2, f"a seating code with {len(parts)} fields: {code!r}")
        side, player_id = parts
        return cls(side=GameSide(side), player_id=UUID(player_id))


@final
@dataclass(frozen=True, slots=True)
class LineUp:
    """The court that played, in the order ``challenges`` handed it over.

    **Both sides are occupied and nobody sits twice**, checked here rather than
    trusted: this is the one place the arrangement crosses out of the context
    that built it, and a court with an empty side would make *the opposing side*
    a question with no answer.
    """

    seatings: tuple[Seating, ...]

    def __post_init__(self) -> None:
        players = [seating.player_id for seating in self.seatings]
        invariant(
            len(players) == len(set(players)),
            "a line-up seating somebody twice",
        )
        for side in GameSide:
            invariant(
                any(seating.side is side for seating in self.seatings),
                f"a line-up with nobody on side {side.value}",
            )

    @classmethod
    def of(cls, seatings: Iterable[Seating]) -> "LineUp":
        return cls(seatings=tuple(seatings))

    @classmethod
    def from_codes(cls, codes: Iterable[str]) -> "LineUp":
        return cls(seatings=tuple(Seating.from_code(code) for code in codes))

    @property
    def codes(self) -> tuple[str, ...]:
        return tuple(seating.code for seating in self.seatings)

    @property
    def players(self) -> frozenset[UUID]:
        """Everybody who played. **The people who may act**, and nobody else."""

        return frozenset(seating.player_id for seating in self.seatings)

    def side_of(self, player_id: UUID) -> GameSide | None:
        """Which side this person played on, or ``None`` if they did not play."""

        for seating in self.seatings:
            if seating.player_id == player_id:
                return seating.side
        return None

    def players_on(self, side: GameSide) -> frozenset[UUID]:
        return frozenset(
            seating.player_id for seating in self.seatings if seating.side is side
        )

    def counterparts_of(self, player_id: UUID) -> frozenset[UUID]:
        """Everybody else on this court — partner and opponents alike.

        **A pair is anybody you were on a court with.** ``challenges`` reaches the
        same answer for an open challenge (*sharing a line-up makes a pair*), and
        familiarity is a fact about two people having played, not about which way
        round the net they stood.
        """

        return self.players - {player_id}
