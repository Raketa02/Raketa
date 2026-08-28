"""Pricing a rung: **a genuine re-run of generation and scoring, every time.**

``docs/adr/0099`` made relaxation an *offer*, and the offer is only worth
anything if the number on it is true. So a rung is priced by rebuilding the
search context with the searcher's own ask widened and running stages 2 to 5
again — the same :func:`generate` and :func:`score_all` the strict answer ran,
against the same bound snapshot and the same live facts.

**Nothing here touches a measurement, a term, a weight or the floor.** The only
thing that changes between the strict run and a rung's run is one field of
:class:`SearcherFacts`: the grid, or the radius. Everything downstream — the
gates, the eight terms, the modifier stack, ``QUALITY_FLOOR`` and minimum
evidence — is the ruleset's, unchanged, which is what makes *the quality floor is
never relaxed, at any rung* a property of the shape rather than a promise in a
comment.

**Rung A can evict.** Adding a slot to the searcher's grid moves every candidate
who does not share it from ``s/m`` to ``s/(m+1)``, so the times rung is the one
rung whose set is **not** a superset of the strict set. That is recorded here and
asserted in the suite rather than discovered in production; nothing is hidden,
because the count on the offer is this real re-run and not the strict count plus
something.

**What that costs, and what bounds it.** One rung is one pass over the partition
— roughly 3 ms at the scale this platform runs at — and rung A tests one addition
per *distinct slot somebody in range has ticked and the searcher has not*. A slot
nobody holds cannot admit anybody, so testing it would be a pass over the
partition to prove a tautology. The whole ladder is computed only when the strict
shortlist came back under ``MIN_SHORTLIST``, which is where the thin pools are,
which is where a pass is cheapest.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import final

from app.engines.matchfit.scoring import MatchFit
from app.modules.matchmaking.domain.relaxation import (
    RelaxationAsk,
    Rung,
    RungOffer,
    radius_ladder,
)
from app.modules.matchmaking.domain.search_context import SearchContext
from app.modules.matchmaking.domain.shortlist import generate, score_all
from app.modules.player_profile.domain.availability import (
    AvailabilityGrid,
    AvailabilitySlot,
    Window,
    window_of,
)


@final
@dataclass(frozen=True, slots=True)
class Widened:
    """One rung, run. **The ids and not just the count.**

    The set is carried because the two monotonicity properties are statements
    about *sets* — ``B ⊆ C``, and both ``⊇`` the strict set — and a count cannot
    express either. It is a sorted tuple rather than a ``frozenset`` for the
    reason nothing in this module iterates a set: an order that came from a hash
    seed is an order that changes between processes.
    """

    rung: Rung
    ask: RelaxationAsk
    #: Everybody who would clear the quality floor at this rung, ids ascending.
    above_floor: tuple[str, ...]
    window: Window
    radius_km: int | None = None
    slot: AvailabilitySlot | None = None

    @property
    def offer(self) -> RungOffer:
        """This rung as it crosses the wire and lands on the record."""

        return RungOffer(
            rung=self.rung,
            ask=self.ask,
            candidates_above_floor=len(self.above_floor),
            window=self.window,
            radius_km=self.radius_km,
            slot=None if self.slot is None else self.slot.code,
        )


@final
@dataclass(frozen=True, slots=True)
class Ladder:
    """Every rung available to this searcher, priced, plus the clamp bit.

    ``radius_clamped`` is true when the profile slider's ceiling bit at all —
    including when it bit so hard that there is no radius rung left, which is the
    searcher already at the maximum and is exactly the population the bit exists
    to count.
    """

    rungs: tuple[Widened, ...]
    radius_clamped: bool

    @property
    def offers(self) -> tuple[RungOffer, ...]:
        return tuple(rung.offer for rung in self.rungs)


def ladder_for(
    context: SearchContext, engine: MatchFit, *, strict_above_floor: int
) -> Ladder:
    """The whole ladder for one search, in the order the engine recommends.

    **The order is a recommendation, not a lock** (``docs/adr/0099`` §2): times
    first because a slot the player was already free in costs nothing, and the
    client leads with the cheapest — but a player who knows they will never be
    free on a Saturday may take a radius rung directly, so all of them travel.

    ``strict_above_floor`` is the strict run's own count, and it is what rung A
    is judged against: the times rung is offered only when a slot addition would
    genuinely leave **more** people above the floor than the search already
    found. It is the one rung with a choice to make — up to twenty additions and
    one offer — so *which slot* has to be decided by something, and *the one that
    helps most* is the only criterion that is about the player rather than about
    the grid's layout.
    """

    rungs: list[Widened] = []
    times = _times_rung(context, engine, strict_above_floor=strict_above_floor)
    if times is not None:
        rungs.append(times)
    ladder = radius_ladder(context.searcher.radius_km)
    for radius in ladder.rungs:
        rungs.append(_radius_rung(context, engine, radius.rung, radius.radius_km))
    return Ladder(rungs=tuple(rungs), radius_clamped=ladder.clamped)


def cleared_floor(context: SearchContext, engine: MatchFit) -> tuple[str, ...]:
    """Who clears the floor in this context, ids ascending.

    Stages 2 to 5, exactly as the strict answer runs them. It stops before stage
    6 deliberately: Liveness reorders and never admits, so the set is settled at
    the floor and running the offset per rung would be work whose result nothing
    reads.
    """

    scored = score_all(generate(context), context, engine)
    return tuple(sorted(row.player_id for row in scored if row.admission.admitted))


def _radius_rung(
    context: SearchContext, engine: MatchFit, rung: Rung, radius_km: int
) -> Widened:
    """One radius rung: the same search, from a wider ring.

    The whole widening is one field of :class:`SearcherFacts`. The bounding box,
    the radius gate and the distance term all read it — which is why they all
    widen together and none of them had to be told.

    The window is unchanged and travels anyway: every rung carries its own
    window, and *unchanged* is the answer for a rung that did not touch the grid
    rather than a reason to omit the field.
    """

    return Widened(
        rung=rung,
        ask=RelaxationAsk.RADIUS,
        above_floor=cleared_floor(_with_radius(context, radius_km), engine),
        window=window_of(context.searcher.grid, context.today),
        radius_km=radius_km,
    )


def _times_rung(
    context: SearchContext, engine: MatchFit, *, strict_above_floor: int
) -> Widened | None:
    """The single-slot addition that helps most, or nothing at all.

    ``None`` when no addition leaves more people above the floor than the strict
    search already found — which is an honest answer and not a failure. Offering
    a times rung that admits nobody would be inviting a player to widen a grid
    they may not truthfully be free in, for nothing, and ghost rate is worse than
    a decline (``docs/adr/0099``, *rung A can manufacture ghosts*).

    Ties break on the slot's own reading order, so two additions that admit the
    same number of people resolve to the earlier cell of the week rather than to
    whichever the dictionary happened to yield first.
    """

    best: Widened | None = None
    for slot in _additions_worth_testing(context):
        widened = _with_grid(context, _grid_plus(context.searcher.grid, slot))
        admitted = cleared_floor(widened, engine)
        if len(admitted) <= strict_above_floor:
            continue
        if best is not None and len(admitted) <= len(best.above_floor):
            continue
        best = Widened(
            rung=Rung.A,
            ask=RelaxationAsk.TIMES,
            above_floor=admitted,
            window=window_of(widened.searcher.grid, context.today),
            slot=slot,
        )
    return best


def _additions_worth_testing(
    context: SearchContext,
) -> tuple[AvailabilitySlot, ...]:
    """The cells a candidate holds and the searcher does not, in reading order.

    A cell nobody in range has ticked cannot admit anybody: the availability term
    reads ``|shared| / |mine|``, so adding it can only grow the denominator. This
    is a bound on the work rather than a rule about the answer — every slot it
    drops is one whose re-run is provably not an improvement.

    The population it reads is the **post-gate** one, because the gates do not
    read a grid: a blank grid was never a gate, so widening one cannot admit
    somebody a gate excluded.
    """

    mine = set(context.searcher.grid.slots)
    theirs = {
        slot
        for row in generate(context).admitted
        for slot in (AvailabilitySlot.from_code(code) for code in row.row.availability)
    }
    return tuple(sorted(theirs - mine, key=lambda slot: slot.in_reading_order))


def _grid_plus(grid: AvailabilityGrid, slot: AvailabilitySlot) -> AvailabilityGrid:
    """The searcher's own grid with one more cell ticked. **For one search.**

    Built through ``of`` so the addition lands in the grid's canonical order,
    which is what keeps two grids holding the same cells equal whatever order
    they were assembled in. Nothing here writes anything: an accepted widen is a
    new search citing the one that offered it, never a silent profile edit.
    """

    return AvailabilityGrid.of((*grid.slots, slot))


def _with_grid(context: SearchContext, grid: AvailabilityGrid) -> SearchContext:
    return replace(context, searcher=replace(context.searcher, grid=grid))


def _with_radius(context: SearchContext, radius_km: int) -> SearchContext:
    return replace(context, searcher=replace(context.searcher, radius_km=radius_km))
