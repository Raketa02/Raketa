"""Seating the four — the enumeration, the mask, and the honest partial answer.

``group`` holds the objective; this holds the search for the combination that
maximises it. They are separate files because they answer separate questions —
*how good is this four* against *which four* — and only the second is cubic.

**Every gate binds all six pairs, and that is why the gate is here rather than at
generation** (``docs/adr/0116``). Eligibility for a *seat* is a property of a
**combination**, not of a candidate: `a` and `b` may each be perfectly eligible
against the searcher and blocked against each other. So the three absolute gates
arrive as one ``K × K``
:class:`~app.engines.matchfit.grouping.PairAdmissibility` mask, precomputed by
the module where the I/O is, and the enumeration asks it three times per
combination — ``O(K²)`` against a cubic walk, which cannot overtake it.

**The floor is applied per seat inside the enumeration, and only to the seats
this engine is filling.** ``docs/adr/0099``: a seat is never filled below
``QUALITY_FLOOR`` to complete a four, a newcomer least of all. The pool arrives
already past the floor for everybody except the one case that may sit below it —
a candidate admitted by an interest lift — and a lift is a reason to *show*
somebody, never a reason to seat them beside three others who did not ask. A
**locked** seat is not tested: the searcher chose that person by hand, and this
engine is not filling that seat.

**A four can be impossible where candidates are plentiful**, which is the
consequence ADR-0116 names. The answer is a partial line-up rather than an error,
and the fallback is deliberately not a second objective: with no admissible four
there is nothing for ``G`` to be compared against, so the remaining seats are
filled **in Fit order, subject to the same mask** — which is exactly what the
searcher would do by hand, and is the one rule that needs no new constant.

**Nothing here iterates a set** (``docs/adr/0105``). The pool arrives as an
ordered tuple, every combination is drawn from it by index, and the two orders
that decide anything — ``argmax G`` and the greedy fill — break their ties on the
player id, which is unique.
"""

from __future__ import annotations

from itertools import combinations
from typing import Sequence

from app.engines.matchfit.grouping import (
    Arrangement,
    GroupScore,
    LineupCounts,
    PairAdmissibility,
    Seated,
    Seating,
    SigmaCombiner,
)
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.scorable import Searcher
from app.engines.matchfit.v1.group import (
    arranged,
    arrangements,
    best,
    deciding_reason,
    evenest,
)
from app.kernel import invariant

#: How many people sit beside the searcher in a doubles line-up. Three, and it is
#: written once here because it is the arity of everything below — the
#: combination width, the arrangement count and the seat roster all read it.
GUESTS = 3


def seat(
    searcher: Searcher,
    pool: Sequence[Seated],
    ruleset: Ruleset,
    combine: SigmaCombiner,
    admissible: PairAdmissibility,
    *,
    locked: Sequence[Seated] = (),
) -> Seating:
    """Who sits down, which way round, and why this four beat the runner-up.

    ``pool`` is what this line-up may draw from, **ordered by Fit descending and
    already truncated to ``K``** — the truncation is the module's, because *how
    many* is a ruleset number and *which* is a ranking the module already
    computed for the shortlist. The order is load-bearing twice over: it is the
    fallback's fill order, and it is what makes two processes seat the same four.

    ``locked`` is the searcher's own hand-seating, and **it is the only
    difference between a line-up and filling seats**. Locked players are seated
    first, in the order they were sent, and every combination the enumeration
    tries contains all of them — which is what makes ⚡ after hand-seating
    somebody the same shape as ⚡ on an empty court. **They are held to the mask
    like anybody else**: hand-seating is not a way past a gate, and the one place
    that could have become one is the partial line-up, which starts from the
    locked seats and would otherwise never have tested them against each other.

    ``admissible`` is **positional and has no default**, deliberately. It is a
    fail-closed gate (``docs/adr/0116``), and a default that admitted everybody
    would be an accidental way to seat a four with the mask unread — the exact
    shape of failure the gate exists to prevent.

    The winner and the runner-up come back whole. ``G`` is on both, it stays on
    the record, and what a screen may draw is the arrangements, the two booleans
    and one closed reason code.
    """

    invariant(
        len(locked) <= GUESTS,
        f"a line-up with {len(locked)} seats locked: a four seats {GUESTS} "
        f"people beside the searcher",
    )
    invariant(
        _pairs_admit(locked, admissible),
        "a line-up whose hand-seated players may not share a court: a locked "
        "seat is held to the six pairs like every other",
    )
    taken = frozenset(one.player_id for one in locked)
    free = tuple(one for one in pool if one.player_id not in taken)
    fours, counts = _enumerate(
        searcher, free, locked, ruleset, combine, admissible=admissible
    )
    if fours:
        return _seated(fours, counts)
    return _fallback(searcher, free, locked, ruleset, combine, counts, admissible)


def _enumerate(
    searcher: Searcher,
    free: Sequence[Seated],
    locked: Sequence[Seated],
    ruleset: Ruleset,
    combine: SigmaCombiner,
    *,
    admissible: PairAdmissibility,
) -> tuple[tuple[tuple[GroupScore, ...], ...], LineupCounts]:
    """Every admissible four, each as its own three scored arrangements.

    All three are kept rather than only the winning one, because the builder is
    offered all three of whichever combination wins and recomputing them from the
    winner would be a second chance to produce a different forecast for the same
    four.

    The three counters are taken here rather than derived later, because *how
    many combinations the pairwise gate refused* is ``docs/adr/0116``'s own
    falsifier and there is nowhere else it exists.
    """

    open_seats = GUESTS - len(locked)
    walked = refused_by_gate = refused_by_floor = 0
    fours: list[tuple[GroupScore, ...]] = []
    for chosen in combinations(range(len(free)), open_seats):
        walked += 1
        four = (*locked, *(free[index] for index in chosen))
        if not _pairs_admit(four, admissible):
            refused_by_gate += 1
            continue
        if not _clears_the_floor(four, ruleset):
            refused_by_floor += 1
            continue
        fours.append(arrangements(searcher, four, ruleset, combine))
    counts = LineupCounts(
        combinations=walked,
        refused_by_gate=refused_by_gate,
        refused_by_floor=refused_by_floor,
    )
    return tuple(fours), counts


def _pairs_admit(four: Sequence[Seated], admissible: PairAdmissibility) -> bool:
    """Whether every candidate pair in this combination is admissible.

    Three lookups for a full four, and they are the three pairs no Fit ever saw:
    the searcher's own three passed every gate at generation, where the searcher
    is one half of every pair.
    """

    return all(
        admissible(one.player_id, other.player_id)
        for one, other in combinations(four, 2)
    )


def _clears_the_floor(four: Sequence[Seated], ruleset: Ruleset) -> bool:
    """Whether every seat **this engine is filling** is above the quality floor.

    A locked seat is exempt because the searcher put that person there: the rule
    is that a seat is never *filled* below the floor to complete a four, and
    hand-seating is not filling.
    """

    return all(one.locked or one.fit >= ruleset.floors.quality_floor for one in four)


def _seated(
    fours: Sequence[tuple[GroupScore, ...]], counts: LineupCounts
) -> Seating:
    """The winning combination, its three arrangements, and the deciding margin.

    A combination is compared at **its own best arrangement**, because that is
    the four the searcher would be offered — one judged at its worst way round
    would lose to a four nobody would ever seat.

    The runner-up is the **second-best combination**, never the second-best
    arrangement of the winner: the margin ``docs/adr/0117`` asks for is *why
    these four* and not *why this way round*, and the two questions have
    different answers whenever balance decides the arrangement.
    """

    ranked = sorted(
        ((best(ways), ways) for ways in fours),
        key=lambda entry: (-entry[0].objective, _members(entry[0])),
    )
    winner, ways = ranked[0]
    runner_up = ranked[1][0] if len(ranked) > 1 else None
    # **Projected once**, so that *which of these three is best* is answered by
    # identity downstream rather than by a renderer re-deriving it. ``arranged``
    # is a property and builds a fresh value on every read, so taking it twice
    # would hand a client three arrangements and a fourth object equal to one of
    # them — and *is this the best one* would then be a comparison nobody wrote.
    offered = {id(one): one.arranged for one in ways}
    return Seating(
        seated=winner.arrangement.seated,
        arrangements=tuple(offered[id(one)] for one in ways),
        best=offered[id(winner)],
        evenest=offered[id(evenest(ways))],
        # **``None`` when there was nothing to beat.** One admissible
        # combination is not a four that won an argument, and naming the term
        # with the largest margin over nobody would be the engine explaining an
        # arithmetic it never performed.
        reason=None if runner_up is None else deciding_reason(winner, runner_up),
        winner=winner,
        runner_up=runner_up,
        counts=counts,
    )


def _members(score: GroupScore) -> tuple[str, ...]:
    """A combination's members, **sorted**, as the total order ties break on.

    ``docs/adr/0105``: a set is never the source of an order. Two fours with the
    same ``G`` are told apart by who is in them and never by where the pool
    happened to put them — so a tie is broken by a fact about the people rather
    than by an ordering that came from upstream, and the same pool in a different
    order seats the same four.

    Sorted rather than seated-order, because *who is in this four* is a set and
    the three arrangements of one combination are the same combination.
    """

    return tuple(sorted(one.player_id for one in score.arrangement.seated))


def _fallback(
    searcher: Searcher,
    free: Sequence[Seated],
    locked: Sequence[Seated],
    ruleset: Ruleset,
    combine: SigmaCombiner,
    counts: LineupCounts,
    admissible: PairAdmissibility,
) -> Seating:
    """The honest partial line-up: **Fit order, subject to the same mask.**

    Reached only when no admissible four exists at all, which after ADR-0116 is
    an ordinary answer in a thin city rather than a failure. There is deliberately
    no second objective here — ``G`` compares two fours and there are none to
    compare — so what fills the remaining seats is the ranking the search already
    produced, admitted one at a time against everybody already sitting down.

    The floor still binds every seat this fills, and the locked seats still do
    not move: *three of four* is an answer, and *four of four with somebody who
    should not be there* is not.
    """

    seated: list[Seated] = list(locked)
    for candidate in free:
        if len(seated) == GUESTS:
            break
        if not _clears_the_floor((candidate,), ruleset):
            continue
        if not _pairs_admit((*seated, candidate), admissible):
            continue
        seated.append(candidate)
    return offer(searcher, tuple(seated), ruleset, combine, counts=counts)


def offer(
    searcher: Searcher,
    seated: Sequence[Seated],
    ruleset: Ruleset,
    combine: SigmaCombiner,
    *,
    counts: LineupCounts,
    seats_per_side: int = 2,
) -> Seating:
    """What the builder is offered when **no objective was computed at all.**

    Two callers reach it and they are the two cases where ``G`` does not exist: a
    doubles line-up with a seat still open, and a singles line-up, where the
    objective was struck by argument rather than by omission
    (``the-group-objective.md`` §2.4).

    ``best`` is ``None`` in both, and that is the honest answer rather than a
    fallback rule. There is nothing to be best **by** — no cross pairs, no seat
    delta, no mean over three Fits — and naming the min-gap arrangement *best*
    would quietly give ``is_best`` a second meaning on exactly the responses
    where the builder most needs the first one. *Even it out* still selects, and
    it is the only selection there is.
    """

    ways = tuple(
        arranged(searcher, one, ruleset, combine, seats_per_side=seats_per_side)
        for one in Arrangement.all_of(seated)
    )
    return Seating(
        seated=tuple(seated),
        arrangements=ways,
        best=None,
        evenest=(
            None
            if not ways
            else sorted(
                ways, key=lambda one: (one.side_gap, one.arrangement.partner_id)
            )[0]
        ),
        reason=None,
        winner=None,
        runner_up=None,
        counts=counts,
    )


__all__ = ["GUESTS", "offer", "seat"]
