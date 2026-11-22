"""How a table is scored for a seat — **two rules, one per Mode**
(``docs/adr/0207`` §1, #831).

**A Mode picks a scoring rule as well as the level window's tolerance**, so the
separation is in the code rather than in a number somebody has to remember:

- **Competitive** keeps the score the engine always had: the **best forecast**,
  then the **smallest level spread**;
- **For fun** ranks by the **Social vibe** — compared exactly, before it is
  rounded for a card — then the **new faces**, then the forecast, then the
  level spread.

**Skill is a guard on a For-fun table, never a weight**: the level window keeps
the game fair, the evenest arrangement still gives the sides, and the forecast
and the spread only break a tie. So the deck's order always agrees with the
number printed on the card.

**A new face** is a pair who have never played a game together and are not
friends. A table's count is how many of its pairs are new faces to each other,
and it never moves the number.

**Where a rule applies is wherever the engine names somebody for a seat**: the
proposer's picks, a seat's next best fits, a post's open seats, the owed and
lost cards' new ones (``domain/proposer.py``), and a rescue's best fits
(``domain/rescues.py``). Whatever is the gate — who may play, who fits whom,
which hours, which courts — is not here, and is the same for both kinds.

**Pure**: what a rule reads is handed in. A score is a tuple, the larger the
better, compared field by field.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable
from fractions import Fraction
from itertools import combinations
from typing import Final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import exhaustive

#: A score: the larger the better, compared field by field.
Score = tuple[Fraction | float, ...]

#: Where nobody at a table carries a tag that counts there is no Social vibe —
#: nothing to measure rather than nothing shared — and such a table ranks under
#: every table that has one, a 0% included, as the deck orders it last.
_NO_VIBE: Final = Fraction(-1)


def competitive_score(*, forecast: int, spread: float) -> Score:
    """**Competitive**: the forecast of the evenest way the people could stand,
    then how close their Levels are — a narrower spread is a larger score."""

    return (forecast, -spread)


def for_fun_score(
    *, vibe: Fraction | None, new_faces: int, forecast: int, spread: float
) -> Score:
    """**For fun**: the table's Social vibe, exact; then how many of its pairs
    are new faces to each other; then the competitive score, as a tie-break."""

    return (
        _NO_VIBE if vibe is None else vibe,
        new_faces,
        *competitive_score(forecast=forecast, spread=spread),
    )


def score_of(
    kind: SearchMode,
    *,
    forecast: int,
    spread: float,
    vibe: Fraction | None = None,
    new_faces: int = 0,
) -> Score:
    """The rule ``kind`` scores a table by. Competitive reads neither the vibe
    nor the new faces."""

    match kind:
        case SearchMode.COMPETITIVE:
            return competitive_score(forecast=forecast, spread=spread)
        case SearchMode.FOR_FUN:
            return for_fun_score(
                vibe=vibe, new_faces=new_faces, forecast=forecast, spread=spread
            )
        case _:
            exhaustive(kind)


def descending(score: Score) -> Score:
    """A score as a sort key that puts the best first."""

    return tuple(-field for field in score)


def new_faces_among(table: Iterable[UUID], known: Collection[frozenset[UUID]]) -> int:
    """How many pairs at this table are **new faces** to each other: every pair
    but the ones ``known`` names — who have played a game together, or are
    friends."""

    return sum(
        1
        for one, other in combinations(table, 2)
        if frozenset((one, other)) not in known
    )


def spread_of(levels: Iterable[float]) -> float:
    """How far apart a table's Levels are — nought with fewer than two."""

    mus = list(levels)
    return max(mus) - min(mus) if mus else 0.0


__all__ = [
    "Score",
    "competitive_score",
    "descending",
    "for_fun_score",
    "new_faces_among",
    "score_of",
    "spread_of",
]
