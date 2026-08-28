"""The three rungs, and the one line that makes them safe.

**A rung may only relax something the searcher themselves asked for. It may never
touch a measurement, a term, a weight, or the quality floor**
(``docs/adr/0099``). §9.8's rungs 1, 3 and 4 are struck: familiarity is a
modifier, availability overlap and level fit are terms, so all three raised
*scores* against a fixed floor rather than widening the catchment — which is
arithmetically indistinguishable from lowering the bar, and is the one move the
published record has an experiment against.

What is left is the searcher's own two asks, in this order:

```
  A  your times     one slot added to your own grid, for this one search
  B  your radius    × 1.5
  C  your radius    × 2.0
```

**Times before distance**, because a slot you were already free in costs nothing
while distance costs travel on every game forever. **There is no third radius
rung**: tripling still leaves 15% of searches under five candidates at launch
density, so past double it mostly spends the player's travel budget on failing.

**Every rung clamps to the profile slider's own ceiling.** A relaxation may never
offer a radius the player could not have set for themselves, which is the same
principle as *a rung may only relax what the searcher asked for*, applied to the
range the product allows them to ask within. Two consequences, both intended and
both tested: a searcher already at the maximum gets **no radius rung at all**,
and one whose two multipliers both clamp to it gets **one rung, not two**.

**Nothing here counts anybody.** The count on a rung is a real re-run of
generation and scoring and lives in ``widening.py``; this module holds the
vocabulary, the ladder's arithmetic and the shape that crosses the wire — so a
record, a response and a re-run cannot come to three opinions about what a rung
*is*.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final, final

from app.kernel import invariant
from app.modules.player_profile.domain.availability import Window
from app.modules.player_profile.domain.search_radius import SEARCH_RADIUS_BOUNDS


class Rung(StrEnum):
    """Which rung of the ladder an offer is.

    Three values and no more. They are letters rather than numbers because
    ``docs/adr/0099`` rebuilt the ladder from scratch and a rung ``1`` would
    invite a reader to line it up against §9.8's struck rung 1, which relaxed
    something else entirely.
    """

    A = "A"
    B = "B"
    C = "C"


class RelaxationAsk(StrEnum):
    """Which of the searcher's own asks a rung relaxes.

    The vocabulary is closed at two because there are exactly two asks a searcher
    makes: when they can play, and how far they will go. A third value would be
    the engine relaxing something the player never asked for, which is the line
    ``docs/adr/0099`` draws.
    """

    TIMES = "TIMES"
    RADIUS = "RADIUS"


#: What each radius rung multiplies the searcher's own radius by. **Two, and
#: there is no third** — the number is the widening ceiling and it is argued for
#: in ``the-five-numbers.md`` §3, not chosen here.
RADIUS_MULTIPLIERS: Final[tuple[tuple[Rung, float], ...]] = (
    (Rung.B, 1.5),
    (Rung.C, 2.0),
)


@final
@dataclass(frozen=True, slots=True)
class RadiusRung:
    """One radius rung's ask, after the ceiling has had its say."""

    rung: Rung
    radius_km: int


@final
@dataclass(frozen=True, slots=True)
class RadiusLadder:
    """Which radius rungs a searcher on this radius can be offered, and whether
    the ceiling bit.

    ``clamped`` is recorded even when it left no rung standing — that is exactly
    the searcher already at the maximum, and counting them is the whole point of
    the bit (``the-five-numbers.md`` §3).
    """

    rungs: tuple[RadiusRung, ...]
    clamped: bool


def radius_ladder(radius_km: int) -> RadiusLadder:
    """The radius rungs available to a searcher who asked for ``radius_km``.

    **Whole kilometres, rounded down.** The multiplier is a ceiling on what is
    offered rather than a target to land near, and the profile slider holds whole
    kilometres — so half a kilometre of widening is not a thing the player could
    have asked for themselves.

    Three rules, and each removes a rung that could not honestly be taken:

    - a rung past ``SEARCH_RADIUS_BOUNDS.maximum_km`` is **clamped** to it,
      because a relaxation may never offer a radius the player could not set;
    - a rung that lands on the radius the search already ran at is **dropped**,
      because it is not a widening;
    - a rung that duplicates an earlier rung's radius is **dropped**, so a
      searcher whose two multipliers both clamp gets one offer rather than the
      same offer twice.
    """

    invariant(radius_km > 0, f"a search radius of {radius_km} km")
    ceiling = SEARCH_RADIUS_BOUNDS.maximum_km
    rungs: list[RadiusRung] = []
    clamped = False
    for rung, multiplier in RADIUS_MULTIPLIERS:
        asked = int(radius_km * multiplier)
        if asked > ceiling:
            clamped = True
            asked = ceiling
        if asked <= radius_km:
            continue
        if any(offered.radius_km == asked for offered in rungs):
            continue
        rungs.append(RadiusRung(rung=rung, radius_km=asked))
    return RadiusLadder(rungs=tuple(rungs), clamped=clamped)


@final
@dataclass(frozen=True, slots=True)
class RungOffer:
    """One rung, priced. **The count is real and the player sees it first.**

    ``candidates_above_floor`` is the number of people who would clear the
    quality floor if this rung were taken, from a genuine re-run of generation
    and scoring — not an estimate, because a count on a screen that was estimated
    is the product lying in the one place it promises not to.

    ``window`` is this rung's **own** window code, not the search's: a challenge
    sliding from ``WEEKEND`` to ``THIS_WEEK`` is part of what widening costs, and
    ``docs/adr/0099``'s whole argument for offered-rather-than-applied is that
    the player sees the cost before paying it (``docs/adr/0100`` §3).

    The two payload fields are exclusive by ask and the invariant says so, so
    *a radius rung with a slot on it* is unrepresentable rather than merely
    unwritten.
    """

    rung: Rung
    ask: RelaxationAsk
    candidates_above_floor: int
    window: Window
    #: The widened radius, in whole kilometres. ``RADIUS`` rungs only.
    radius_km: int | None = None
    #: The one cell this rung would add to the searcher's own grid, as
    #: ``AvailabilitySlot.code`` spells it. ``TIMES`` rungs only, and **one**
    #: slot: the engine tests the additions and offers the one that helps most,
    #: because the player takes a rung and not a shopping list.
    slot: str | None = None

    def __post_init__(self) -> None:
        invariant(
            self.candidates_above_floor >= 0,
            f"a rung offering {self.candidates_above_floor} candidates",
        )
        invariant(
            (self.ask is RelaxationAsk.RADIUS) == (self.radius_km is not None),
            f"a {self.ask.value} rung with radius {self.radius_km}",
        )
        invariant(
            (self.ask is RelaxationAsk.TIMES) == (self.slot is not None),
            f"a {self.ask.value} rung with slot {self.slot}",
        )
        invariant(
            self.radius_km is None
            or self.radius_km <= SEARCH_RADIUS_BOUNDS.maximum_km,
            f"a rung offering {self.radius_km} km, past the slider's own "
            f"{SEARCH_RADIUS_BOUNDS.maximum_km} km ceiling",
        )
