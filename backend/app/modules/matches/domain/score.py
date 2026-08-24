"""The score on the table: an ordered list of sets, two integers each.

**Never a display string.** ``Raketa02/Raketa#74`` fixes that a score crosses
*"per side as an ordered list of sets of two integers"*, and what crosses is what
is stored: a `"6-4 7-6"` in a column is a rendering decision frozen into
history, and the day a client wants `6:4` it is a migration.

**Two sides, not four players.** Side A is the first half of the match's seats
and side B the second, in the seats' fixed order — so the score means the same
thing however a card chooses to arrange the names. A viewer's own side going
first is the card's business (``Raketa02/Raketa#90``), and doing it here would
make the stored fact depend on who is looking.

**No tiebreak field in v1**, and none is smuggled in as a third integer: a real
7-6 is two integers and the tiebreak's own points are not modelled
(``Raketa02/Raketa#74``).

**The type's own validation is structural.** A set is two counts and there is at
least one of them. Whether *this* scoreline could have happened at *this* sport
is ``validate_score`` below, which the aggregate applies because it is the only
place that holds both the score and the sport — and it is deliberately not in
``__post_init__``, so a score replayed off a row that predates a limit still
reads back rather than blowing up a screen.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Mapping, final

from app.kernel import Sport, invariant

from app.modules.matches.domain.errors import ImpossibleScore


@final
@dataclass(frozen=True)
class SetScore:
    """One set, as games won by each side."""

    side_a: int
    side_b: int

    def __post_init__(self) -> None:
        if self.side_a < 0 or self.side_b < 0:
            raise ValueError(f"a set of {self.side_a}-{self.side_b}")

    def reversed(self) -> "SetScore":
        """The same set read from the other side of the net."""

        return SetScore(side_a=self.side_b, side_b=self.side_a)


@final
@dataclass(frozen=True)
class Score:
    """Every set, in the order they were played."""

    sets: tuple[SetScore, ...]

    def __post_init__(self) -> None:
        if not self.sets:
            raise ValueError("a score with no sets in it")

    def reversed(self) -> "Score":
        """The whole score from the other side of the net."""

        return Score(tuple(one.reversed() for one in self.sets))


#: How many sets or games one evening can hold. Five, for every sport: no racket
#: sport in the registry is played past a fifth, and a sixth row is the pad
#: having been leant on rather than a match nobody has heard of.
MAX_UNITS = 5

#: The ceiling on one side's count in a single set or game, per sport. **Not the
#: rulebook and not the pad** — ``deltas/result-confirmation.md`` §5 is explicit
#: that *"the app knows the shape and declines the obviously impossible; it does
#: not enforce the rulebook"*, because *"local variation is wide enough that a
#: strict validator eventually calls a real match illegal, which is a support
#: problem with no answer."*
#:
#: So each of these sits far above its format and below a slipped digit. Padel's
#: tiebreak closes a set at 7 and a super-tiebreak third at 10; squash is
#: win-by-two from 11 and badminton from 21 with a cap at 30; tennis is the one
#: with no ceiling at all — 70-68 has been played — so it gets the widest number
#: a two-digit pad can produce rather than a number somebody reasoned to.
MAX_UNIT_SCORE: Mapping[Sport, int] = MappingProxyType(
    {
        Sport.PADEL: 30,
        Sport.TENNIS: 99,
        Sport.SQUASH: 30,
        Sport.BADMINTON: 40,
    }
)

invariant(
    set(MAX_UNIT_SCORE) == set(Sport),
    "a sport can be played and its score cannot be checked",
)


def validate_score(score: Score, sport: Sport) -> None:
    """Refuse the obviously impossible, and nothing beyond it.

    Three refusals, and a real 7-6 is none of them: more sets or games than an
    evening holds, a count no format of this sport reaches, and a row nobody
    scored in — which is what an untouched pad produces and is the only *shape*
    error the instrument can make. Everything else stands, including scorelines
    that look wrong to somebody who knows the rules: two people who were both
    there are a better authority than a constant in this file, and a validator
    that is sure enough to argue with them is the support problem the delta
    names.
    """

    if len(score.sets) > MAX_UNITS:
        raise ImpossibleScore()
    ceiling = MAX_UNIT_SCORE[sport]
    for one in score.sets:
        if one.side_a > ceiling or one.side_b > ceiling:
            raise ImpossibleScore()
        if one.side_a == 0 and one.side_b == 0:
            raise ImpossibleScore()
