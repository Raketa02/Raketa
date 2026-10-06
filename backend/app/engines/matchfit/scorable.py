"""The two facts about a person the forecast and the overlap read.

**What crosses into the engine is a number and an hour, never a person.** A
Level arrives as μ and σ, already published by RacketSkill, and a week arrives as
the hours someone ticked. No id, no name, no gender, no photo and no location is
in either type, so nothing downstream of here can read a protected
characteristic: the value is not in the process.

The rest of what used to cross this fence — the scorable candidate, the
searcher, reliability observations, shared history, modifier and liveness facts
— was the ranking's, and went with it (#580, PRD #569).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.kernel import IsoWeekday, invariant


@final
@dataclass(frozen=True, slots=True)
class LevelReading:
    """A player's Level and Uncertainty, as RacketSkill published them.

    Copied rather than re-derived. The forecast reads μ and σ; it never asks how
    they were arrived at, and it never calls ``band_for`` — the shipped bands are
    deliberately uneven because *evidence* is unevenly available down the scale,
    not because a tenth of a point means less at the top.
    """

    mu: float
    sigma: float

    def __post_init__(self) -> None:
        invariant(self.sigma >= 0.0, f"a negative Uncertainty: {self.sigma}")


@final
@dataclass(frozen=True, slots=True)
class GridCell:
    """One hour of the ordinary week a player may have ticked.

    The day is the kernel's ``IsoWeekday`` because Monday-first is already what
    ISO means. The hour is the one the cell **starts at**, wall clock, and the
    engine only compares hours for equality and orders them — so it checks that
    this is an hour of a day and nothing narrower: which hours a player may tick
    is the Player profile's rule (``docs/adr/0189`` §5), not a fact the engine
    holds a second copy of.
    """

    day: IsoWeekday
    hour: int

    def __post_init__(self) -> None:
        invariant(1 <= int(self.day) <= 7, f"a grid cell outside the week: {self.day}")
        invariant(
            not isinstance(self.hour, bool) and 0 <= self.hour <= 23,
            f"a grid cell outside the day: {self.hour!r}",
        )


__all__ = ["GridCell", "LevelReading"]
