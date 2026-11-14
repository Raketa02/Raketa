"""*Same competitive level players* — who a competitive game with would be
most even (``docs/adr/0204`` §4, §7; the home-rows mechanics §6, §9).

Pure: the levels and the Forecast are handed in.

- **The % even is the Forecast for one player a side** — the one forecast
  function, reached through a port (``HowEven``); nothing here computes it. It
  falls with the gap and with both players' doubt.
- **Each person is in the sport where the two are evenest**: every sport both
  hold a level in is compared, most even first — ties to the smaller gap, then
  the app's sport order (call 6 of #790). A See all page asked for one sport
  shows everybody in that sport instead, and every card keeps every shared
  sport for the comparison sheet.
- **Best first** is the % of the sport shown, then the smaller gap, then the
  player id (call 6).
- **The row of 10** (§9.1): fresh good matches first — 70% or more, neither a
  friend nor somebody the reader asked, not rested; somebody who asked the
  reader counts as fresh — best first; then the gaps, everybody else, best
  first. A new fresh match takes the weakest gap's place.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import Sport
from app.modules.discovery.domain.levels import (
    Band,
    CurrentLevel,
    Estimate,
    in_sport_order,
)
from app.modules.discovery.domain.relation import Relation

#: A good match: the % even at or above it (Q33; green on a game card).
GOOD_MATCH: Final = 70
#: Cards on Home's row.
ON_THE_ROW: Final = 10
#: Cards in a See all page (a call made while writing PRD #789).
A_PAGE: Final = 20

#: The Forecast for one player a side in a sport: a whole percent.
PercentEven = Callable[[Sport, Estimate, Estimate], int]


@final
@dataclass(frozen=True, slots=True)
class Comparison:
    """The reader and another player in one sport they both hold a level in."""

    sport: Sport
    your_level: float
    their_level: float
    #: The reader's own band — the comparison bar's bold name.
    your_band: Band
    percent_even: int

    @property
    def level_gap(self) -> float:
        """Their level less the reader's: *0,02 below you* is ``-0.02``."""

        return self.their_level - self.your_level

    @property
    def distance(self) -> float:
        """How far apart, however round — **to a millionth**, so two gaps alike
        in the store (2,83 and 2,59 from 2,71) are alike here, and the player
        id, not the subtraction's last bit, decides between them."""

        return round(abs(self.level_gap), 6)

    @property
    def order(self) -> tuple[int, float, int]:
        """Most even first, then the smaller gap, then the app's sport order."""

        return (-self.percent_even, self.distance, in_sport_order(self.sport))


def compared(
    mine: Mapping[Sport, CurrentLevel],
    theirs: Iterable[CurrentLevel],
    even: PercentEven,
) -> tuple[Comparison, ...]:
    """Every sport the reader and the other both hold a level in, most even
    first. Empty when they share none."""

    comparisons = [
        Comparison(
            sport=level.sport,
            your_level=mine[level.sport].mu,
            their_level=level.mu,
            your_band=mine[level.sport].band,
            percent_even=even(level.sport, mine[level.sport].estimate, level.estimate),
        )
        for level in theirs
        if level.sport in mine
    ]
    return tuple(sorted(comparisons, key=lambda one: one.order))


@final
@dataclass(frozen=True, slots=True)
class SameLevelKey:
    """Where a card stands in *best first*. **A See all cursor is one**: a page
    is everybody strictly behind the last card of the page before, as the list
    stands now."""

    percent_even: int
    distance: float
    player_id: UUID

    @property
    def order(self) -> tuple[int, float, int]:
        return (-self.percent_even, self.distance, self.player_id.int)

    def is_behind(self, other: "SameLevelKey") -> bool:
        """Whether this key comes **after** ``other`` in best-first order."""

        return self.order > other.order


@final
@dataclass(frozen=True, slots=True)
class SameLevelPlayer:
    """One card: the sport shown, and every shared sport for the sheet."""

    player_id: UUID
    shown: Comparison
    #: Every shared sport, most even first.
    comparisons: tuple[Comparison, ...]

    @property
    def key(self) -> SameLevelKey:
        return SameLevelKey(
            percent_even=self.shown.percent_even,
            distance=self.shown.distance,
            player_id=self.player_id,
        )


def same_level_player(
    player_id: UUID, comparisons: Sequence[Comparison], *, in_sport: Sport | None
) -> SameLevelPlayer | None:
    """The card: the evenest sport, or ``in_sport`` when See all asked for one.
    ``None`` when there is nothing to show — no shared sport, or not that one."""

    shown = next(
        (one for one in comparisons if in_sport is None or one.sport is in_sport),
        None,
    )
    if shown is None:
        return None
    return SameLevelPlayer(
        player_id=player_id, shown=shown, comparisons=tuple(comparisons)
    )


@final
@dataclass(frozen=True, slots=True)
class Reach:
    """What a level window settles. Beyond ``width`` of the reader's level in
    every sport compared, nobody reads more than ``ceiling`` — the Forecast for
    a player at exactly that gap, as sure as the surest in the sport — and
    anybody who reads
    it exactly is further than ``width`` away, so comes after a card as even
    and closer. **A card it settles stands where it stands**, whoever the next
    window finds."""

    ceiling: int
    width: float

    def settles(self, player: SameLevelPlayer) -> bool:
        pct = player.shown.percent_even
        return pct > self.ceiling or (
            pct == self.ceiling and player.shown.distance < self.width
        )


def is_fresh(player: SameLevelPlayer, relation: Relation, *, rested: bool) -> bool:
    """A good match the reader is not connected with, who hasn't rested."""

    return (
        player.shown.percent_even >= GOOD_MATCH
        and relation in (Relation.NONE, Relation.ASKED_YOU)
        and not rested
    )


@final
class RowOfTen:
    """The row, filled from the cards **best first**: fresh good matches, then
    the gaps at the right.

    **Full** once ten fresh are taken, or once a card below a good match has
    come — after it no card can be fresh — with ten taken in all. Until then a
    later fresh match would still take a gap's place."""

    def __init__(self) -> None:
        self._fresh: list[SameLevelPlayer] = []
        self._gaps: list[SameLevelPlayer] = []
        self._no_more_fresh = False

    def take(
        self, player: SameLevelPlayer, *, relation: Relation, rested: bool
    ) -> None:
        if player.shown.percent_even < GOOD_MATCH:
            self._no_more_fresh = True
        if is_fresh(player, relation, rested=rested):
            self._fresh.append(player)
        else:
            self._gaps.append(player)

    @property
    def full(self) -> bool:
        return len(self._fresh) >= ON_THE_ROW or (
            self._no_more_fresh and len(self._fresh) + len(self._gaps) >= ON_THE_ROW
        )

    def row(self) -> tuple[SameLevelPlayer, ...]:
        fresh = self._fresh[:ON_THE_ROW]
        return (*fresh, *self._gaps[: ON_THE_ROW - len(fresh)])
