"""The closed Sport registry.

Four sports, each played by a fixed number of players and sold in a fixed set of
durations. This is a *closed* set: adding a sport is a code change and a release,
never a row in a table. A club's sport list *filters* this registry and never
extends or overrides it.

There is deliberately no ``Format`` dimension. One rating per sport, one question
bank per sport, worded for how that sport is actually played — padel and badminton
as doubles, tennis and squash as singles. Reintroducing formats is a new decision,
not a gap to be filled.

    Sport      PADEL              TENNIS        SQUASH           BADMINTON
    players    4                  2             2                4
    durations  60 / 90 / 120      60 / 90       45 / 60 / 90     60 / 90
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Mapping


class Sport(str, Enum):
    """The four sports Rakieta rates, as a closed enum."""

    PADEL = "PADEL"
    TENNIS = "TENNIS"
    SQUASH = "SQUASH"
    BADMINTON = "BADMINTON"


@dataclass(frozen=True)
class SportSpec:
    """The frozen facts about how one sport is played and sold."""

    sport: Sport
    players: int
    durations: tuple[int, ...]


SPORT_SPECS: Mapping[Sport, SportSpec] = MappingProxyType(
    {
        Sport.PADEL: SportSpec(Sport.PADEL, players=4, durations=(60, 90, 120)),
        Sport.TENNIS: SportSpec(Sport.TENNIS, players=2, durations=(60, 90)),
        Sport.SQUASH: SportSpec(Sport.SQUASH, players=2, durations=(45, 60, 90)),
        Sport.BADMINTON: SportSpec(Sport.BADMINTON, players=4, durations=(60, 90)),
    }
)
