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

**Validation here is structural only.** A set is two counts and there is at
least one of them; whether *this* scoreline is a legal padel set is
``Raketa02/Raketa#79``'s permissive validator, and duplicating it here would be
two answers to one question — the failure this repository keeps refusing. What
this type guarantees is only that a stored score can be read back as the shape
it was written in.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final


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
