"""A score, and what it says about the person reading it.

**A score names a winner, and that invariant is the contract.** *Last 5* is *win
or loss*, and none of the four sports Raketa rates produces a draw — a set that
is level has not finished, and a match that is level has not been played to its
end. A score that named nobody would be a row on that card the client could not
draw.

**A set is whatever the sport calls its unit.** Tennis and padel play sets;
squash and badminton play games. One word is used here for all four, because the
platform's opinion about the shape of a score is *some number of parts, each won
by one side*, and a second noun would be a second thing to keep in step with
``SPORT_SPECS``.

**It crosses the wire as one string**, ``6-4,3-6,7-5``, for the reason every
value object in these events does: the codec coerces scalars, and a tuple of
dataclasses comes back as a list of dicts.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Iterable, final

from app.kernel import invariant
from app.modules.games.domain.errors import (
    AResultMustCarryAScore,
    AScoreIsNotThisShape,
    AScoreMustNameAWinner,
)
from app.modules.games.domain.lineup import GameSide

#: How many sets a score may hold. One is a real score — a single squash game
#: played to eleven — and five is the longest match any of the four sports has.
MIN_SETS = 1
MAX_SETS = 5

#: The most points either side may have taken in one set. Not a rule about any
#: sport: a bound that refuses a typo without the platform pretending to know
#: what a tiebreak is worth.
MAX_POINTS = 99

_SET_SEPARATOR = ","
_POINT_SEPARATOR = "-"


@final
class Outcome(str, Enum):
    """What a confirmed result says about one of the people who played.

    Two values. *Unscored* is not a third: a game with no agreed result produces
    **no outcome for anybody**, which is ADR-0049's *an evening, not evidence*
    stated as a type — the absence has one spelling, and it is not being in the
    answer.
    """

    WIN = "WIN"
    LOSS = "LOSS"


@final
@dataclass(frozen=True, slots=True)
class SetScore:
    """One set: what side ``A`` took, and what side ``B`` took.

    **Absolute, never relative.** A score stored from the reader's point of view
    would have to be flipped by whoever read it next, and the first reader to
    forget would publish a loss as a win.
    """

    a: int
    b: int

    def __post_init__(self) -> None:
        # **Refused, not asserted.** A score arrives from a person typing it, so
        # a bad one is a legitimate refusal with a code a client can act on —
        # never a broken precondition, which is what ``invariant`` is for and
        # what would answer somebody's typo with a 500.
        if not all(0 <= points <= MAX_POINTS for points in (self.a, self.b)):
            raise AScoreIsNotThisShape()
        if self.a == self.b:
            raise AScoreMustNameAWinner()

    @property
    def winner(self) -> GameSide:
        return GameSide.A if self.a > self.b else GameSide.B

    @property
    def code(self) -> str:
        return f"{self.a}{_POINT_SEPARATOR}{self.b}"

    @classmethod
    def from_code(cls, code: str) -> "SetScore":
        """One set back out of storage.

        ``invariant`` here and a refusal above, deliberately: a malformed code is
        a **broken precondition** — nothing but this class ever writes one — where
        a level set is somebody's typing.
        """

        parts = code.split(_POINT_SEPARATOR)
        invariant(len(parts) == 2, f"a set code with {len(parts)} halves: {code!r}")
        return cls(a=int(parts[0]), b=int(parts[1]))


@final
@dataclass(frozen=True, slots=True)
class Score:
    """The whole result: the sets, in the order they were played.

    **An empty score is refused here and not at the caller**, which is what makes
    *a counter must carry a score* an invariant rather than a convention. There
    is no bare rejection anywhere in this context, and the type is the reason: an
    objection with nothing in it cannot be constructed, so nothing downstream has
    to check for one.
    """

    sets: tuple[SetScore, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "sets", tuple(self.sets))
        # **A score with no sets in it is a result with no score**, and it is
        # refused under that name rather than under a shape one: a client
        # sending ``{"sets": []}`` and one sending nothing at all are making the
        # same bare rejection, and there is no bare rejection here.
        if not self.sets:
            raise AResultMustCarryAScore()
        if len(self.sets) > MAX_SETS:
            raise AScoreIsNotThisShape()
        if self.sets_won(GameSide.A) == self.sets_won(GameSide.B):
            raise AScoreMustNameAWinner()

    @classmethod
    def of(cls, sets: Iterable[SetScore]) -> "Score":
        return cls(sets=tuple(sets))

    def sets_won(self, side: GameSide) -> int:
        return sum(1 for one in self.sets if one.winner is side)

    @property
    def margin(self) -> int:
        """How many more games the winner took than the loser, **across every
        set** — what makes one of two scores naming the same winner the
        *closer* (#654; ``docs/adr/0195`` §5). Read off the games and never the
        sets: 6–4 3–6 6–4 is closer than 6–0 6–0, though it went to three."""

        return abs(sum(one.a for one in self.sets) - sum(one.b for one in self.sets))

    @property
    def winner(self) -> GameSide:
        """The side that won. **Always answerable**, by the invariant above."""

        if self.sets_won(GameSide.A) > self.sets_won(GameSide.B):
            return GameSide.A
        return GameSide.B

    def outcome_for(self, side: GameSide) -> Outcome:
        return Outcome.WIN if side is self.winner else Outcome.LOSS

    @property
    def code(self) -> str:
        """``6-4,3-6,7-5``. The durable spelling, and the only one."""

        return _SET_SEPARATOR.join(one.code for one in self.sets)

    @classmethod
    def from_code(cls, code: str) -> "Score":
        return cls(
            sets=tuple(
                SetScore.from_code(part) for part in code.split(_SET_SEPARATOR) if part
            )
        )
