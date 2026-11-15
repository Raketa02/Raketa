"""Every player's **current level per sport**, as the people rows read it
(``docs/adr/0204`` §10; #794).

**A copy, never the record.** The rating is the one owner of a Level: each
entry is what the player's rating stream in that sport stands at now — the
questionnaire's opening or the last result's move — written when one of its
events is delivered and by the rebuild, asking the stream again each time. A
questionnaire level is one too: that is exactly what a newcomer has, and the
ranking's projection, made on a first result, could not serve it.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import Sport

_SPORT_ORDER: Final[Mapping[Sport, int]] = {sport: n for n, sport in enumerate(Sport)}


def in_sport_order(sport: Sport) -> int:
    """Where a sport stands in the app's own order — ``Sport``'s, so a fifth
    sport is ordered without anybody widening a list."""

    return _SPORT_ORDER[sport]


@final
@dataclass(frozen=True, slots=True)
class Band:
    """The band the rating published with the Level, its edges as it drew
    them — the comparison bar names the reader's, and never works one out."""

    name: str
    lower: float
    upper: float


@final
@dataclass(frozen=True, slots=True)
class Estimate:
    """A Level and its Uncertainty — what the Forecast reads."""

    mu: float
    sigma: float


@final
@dataclass(frozen=True, slots=True)
class CurrentLevel:
    """One player's level in one sport, as their rating stands now."""

    player_id: UUID
    sport: Sport
    #: The Level, as the rating committed it.
    mu: float
    #: Its Uncertainty: the questionnaire's alone is wide, and the % falls
    #: with it.
    sigma: float
    band: Band
    #: How many results have moved it — the projection keeps the fold with
    #: the most, so a fold read before a later move committed never takes the
    #: move back.
    results: int

    @property
    def estimate(self) -> Estimate:
        return Estimate(mu=self.mu, sigma=self.sigma)
