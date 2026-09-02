"""The line-up's own half of the pipeline: the pool, the mask, and the seats.

``shortlist.py`` ends in a ranked list of twenty; a line-up ends in a **seated
four**, and the six stages before the terminal one are shared unchanged — which
is the whole reason there is one engine rather than three. What is here is the
line-up's terminal stage and the one thing a shortlist never needed:
**a ``K × K`` admissibility mask over the candidates themselves.**

**A four contains six pairs and the searcher is in three of them**
(``docs/adr/0116``). The other three are gated against nobody unless somebody
builds this: `a` and `b` may each have passed all ten gates against the searcher
while `a` blocked `b` last month, or while `a` asked to play women only. A
pairwise gate over *candidates* cannot be spent at candidate generation, because
eligibility for a seat is a property of a **combination** — so the three absolute
gates are precomputed here, once, over the ``K`` ids the enumeration will draw
from, and handed to the engine as one question it asks three times per
combination.

**Two of the three are already in the process and the third is not.** Gender and
μ ride on the index row (``docs/adr/0111``); blocks deliberately do not, so the
line-up makes **one bulk block query over the ``K`` ids** and the mask **fails
closed** — a line-up that cannot evaluate it refuses rather than seating a four
on an unread gate.

**The pool is truncated by Fit and never by rank key.** Liveness reorders a list
somebody reads; it must not decide who is *eligible* for a court, and the
enumeration is cubic in ``K`` so the truncation is what keeps it inside the
budget. Ties break on the player id, because a set is never the source of an
order (``docs/adr/0105``).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random
from itertools import combinations
from typing import Mapping, Sequence, final
from uuid import UUID

from app.engines.matchfit.grouping import (
    Arrangement,
    LineupCounts,
    PairAdmissibility,
    Seated,
    Seating,
    SigmaCombiner,
)
from app.engines.matchfit.scorable import Searcher
from app.engines.matchfit.scoring import MatchFit
from app.engines.matchfit.ruleset import Ruleset
from app.engines.matchfit.v1 import GUESTS, group_availability, offer
from app.kernel import SPORT_SPECS, Sport, invariant
from app.modules.matchmaking.domain.candidate_index import CandidateRow
from app.modules.matchmaking.domain.gates import (
    gender_satisfied_between,
    level_close_enough,
)
from app.modules.matchmaking.domain.search_context import SearchContext
from app.modules.matchmaking.domain.searches import StagedCounts
from app.modules.matchmaking.domain.shortlist import (
    Scored,
    generate,
    near_misses_of,
    score_all,
    with_liveness,
)
from app.modules.matchmaking.domain.fence import searcher_of


@final
class UnfilledReason(str, Enum):
    """Why a seat is empty, and why the four-way week is.

    ``the-group-objective.md`` §5.1's closed vocabulary. **A partial line-up is
    always a `200`**: *three of four* is an honest answer, and *nobody* is the
    same shape with three seats carrying a reason rather than a separate empty
    state.

    ``NO_ADMISSIBLE_COMBINATION`` is the one ``docs/adr/0116`` added and it is
    load-bearing: without it a six-pair gate is indistinguishable from a thin
    pool, on the screen and in the telemetry — and after
    ``docs/adr/0113`` it is also how a screen says *nobody at their level yet*
    about a newcomer's first four rather than *nobody*.
    """

    #: The pool had people; none of them cleared ``QUALITY_FLOOR``.
    NO_CANDIDATE_ABOVE_FLOOR = "NO_CANDIDATE_ABOVE_FLOOR"
    #: Candidates cleared the floor; **no combination passed the six pairs.**
    NO_ADMISSIBLE_COMBINATION = "NO_ADMISSIBLE_COMBINATION"
    #: There was nobody — or nobody left, because everybody eligible is seated.
    POOL_EXHAUSTED = "POOL_EXHAUSTED"
    #: Seated, and the four-way intersection is empty. **A dock, never a
    #: refusal**: the availability term zeroes and the screen says *you would all
    #: have to bend*, and nobody is removed from the court for it.
    NO_SHARED_SLOTS = "NO_SHARED_SLOTS"


@final
class Relationship(str, Enum):
    """What one seat is to the searcher. **Stated, never inferred from a side.**

    ``the-two-contracts.md`` §5: the whole partner/opponent asymmetry hangs on
    it, and a client deriving it from which side somebody sits on would be a
    second implementation of a domain rule.
    """

    SELF = "SELF"
    PARTNER = "PARTNER"
    OPPONENT = "OPPONENT"


@final
class Side(str, Enum):
    """Which side of the net. The searcher is always on ``A``."""

    A = "A"
    B = "B"


@final
@dataclass(frozen=True, slots=True)
class LineupPool:
    """What the line-up may seat, and everything the record needs about it.

    ``rows`` is ordered by Fit descending and truncated to the ruleset's ``K``.
    ``fit_rank`` is over the **whole** admitted set rather than over the
    truncation, because ``max(fit_rank)`` among the seated is ``K``'s replacement
    falsifier and a rank that stopped at the cap could never exceed it.
    """

    rows: tuple[Scored, ...]
    admitted: tuple[Scored, ...]
    near_misses: tuple[Scored, ...]
    counts: StagedCounts
    players_in_range: int
    best_withheld_fit: float | None
    fit_rank: Mapping[str, int]
    #: The same rows, keyed. Built once with the tuple rather than searched per
    #: lookup, because the two callers ask about every seated player and every
    #: locked one — and a linear scan per seat is a quadratic walk written as a
    #: convenience.
    indexed: Mapping[str, Scored]

    def by_id(self, player_id: str) -> Scored | None:
        """The row for one player, or nothing at all."""

        return self.indexed.get(player_id)


def guests_for(sport: Sport) -> int:
    """How many people sit beside the searcher in this sport.

    Read off the closed sport registry rather than branched on: padel and
    badminton seat four and tennis and squash seat two, and a line-up that
    hard-coded three would be a doubles assumption in a file that serves all
    four.
    """

    return SPORT_SPECS[sport].players - 1


def seats_per_side(sport: Sport) -> int:
    """How many a **full side** holds. Two in doubles, one in singles.

    It is what decides whether a side of one is provisional or finished, and it
    is a seat count and never a mode: marking a singles forecast provisional
    would caveat a number nothing was assumed about.
    """

    return SPORT_SPECS[sport].players // 2


def pool_for(context: SearchContext, engine: MatchFit) -> LineupPool:
    """Stages 1 to 6, ending in the top ``K`` by Fit rather than in twenty rows.

    The six shared stages are ``shortlist.py``'s own functions, called here
    unchanged — a second surface that reimplemented stage 6 would be a second
    opinion about what moves somebody. What differs is only where the list stops
    and what it is ordered by.

    **Ordered by Fit and not by rank key.** Liveness reorders a list a person
    reads; deciding who is *eligible* to be seated beside three strangers is not
    a reordering, and the number the card prints is the number the seat is
    chosen on. Ties break on the player id, which is unique.
    """

    generation = generate(context)
    scored = score_all(generation, context, engine)
    admitted = tuple(row for row in scored if row.admission.admitted)
    withheld = tuple(row for row in scored if not row.admission.admitted)
    searcher = searcher_of(context)
    moved = tuple(
        with_liveness(row, context, engine, searcher) for row in admitted
    )
    ranked = tuple(
        sorted(moved, key=lambda row: (-row.modified.points, row.player_id))
    )
    rows = ranked[: context.ruleset.group.k]
    near_misses = near_misses_of(withheld, context)
    return LineupPool(
        rows=rows,
        admitted=ranked,
        near_misses=near_misses,
        counts=StagedCounts(
            n_generated=generation.n_generated,
            excluded_by_gate=generation.excluded_by_gate,
            n_scored=len(scored),
            n_cleared_floor=len(admitted),
            # Overwritten by the use case with the rows the response actually
            # carried, exactly as the shortlist's is: what makes this column a
            # redaction detector is that it starts out agreeing with the rows.
            n_returned=0,
            n_near_miss_recorded=len(near_misses),
        ),
        players_in_range=len(generation.admitted),
        best_withheld_fit=(
            max(row.modified.points for row in withheld) if withheld else None
        ),
        fit_rank={row.player_id: rank for rank, row in enumerate(ranked, start=1)},
        indexed={row.player_id: row for row in rows},
    )


def mask_over(
    rows: Sequence[Scored],
    context: SearchContext,
    blocked_pairs: frozenset[frozenset[UUID]],
) -> PairAdmissibility:
    """The ``K × K`` bit, precomputed once. **276 pairs at ``K = 24``.**

    Three gates bind pairwise (``docs/adr/0116``) and all three are evaluated
    here, over candidates only: the searcher's own three pairs already passed
    every gate at generation, where the searcher is one half of each.

    | Gate | Reading in a four |
    | --- | --- |
    | Block | no edge, either direction, between any two of the four |
    | Gender preference | mutually satisfied between every pair |
    | Level | ``Δμ < LEVEL_TOL_mode`` for every pair |

    **Newness tightens the pairs it is in, not the search** (``docs/adr/0113``):
    :func:`level_close_enough` takes two people rather than a searcher and a row,
    so every pair containing a newcomer takes the competitive tolerance whoever
    ran the search — which is precisely the hole ADR-0113 closed, reopened one
    enumeration later if this asked about the searcher instead.

    The admissible pairs are computed **once** and the returned callable is a set
    membership test, so the enumeration pays ``O(K²)`` against a cubic walk. It
    is a callable rather than the set itself because the engine may not be handed
    a structure it could take an order from.
    """

    admitted: set[frozenset[str]] = set()
    for one, other in combinations(rows, 2):
        if not _pair_admits(one, other, context, blocked_pairs):
            continue
        admitted.add(frozenset((one.player_id, other.player_id)))

    def admits(one: str, other: str) -> bool:
        return frozenset((one, other)) in admitted

    return admits


def _pair_admits(
    one: Scored,
    other: Scored,
    context: SearchContext,
    blocked_pairs: frozenset[frozenset[UUID]],
) -> bool:
    """The three gates over one candidate pair, in the roster's own order."""

    if frozenset((UUID(one.player_id), UUID(other.player_id))) in blocked_pairs:
        return False
    mine, theirs = one.generated.row, other.generated.row
    if not gender_satisfied_between(mine, theirs):
        return False
    return _levels_close(mine, theirs, context)


def _levels_close(
    one: CandidateRow, other: CandidateRow, context: SearchContext
) -> bool:
    return level_close_enough(
        mu_a=one.mu,
        mu_b=other.mu,
        a_created_at=one.profile_created_at,
        b_created_at=other.profile_created_at,
        mode=context.searcher.mode,
        ruleset=context.ruleset,
        now=context.now,
    )


def unfilled_reason(
    pool: LineupPool, seating: Seating, context: SearchContext, *, guests: int
) -> UnfilledReason | None:
    """Why the seats that are empty are empty. ``None`` when none is.

    Three answers over three questions, and the order below is the order of what
    each one explains. **There was nobody** is the pool before the floor;
    **nobody cleared the bar** is the pool after it; and *everybody who could sit
    down is sitting down* is exhaustion again rather than a gate — which is why
    ``NO_ADMISSIBLE_COMBINATION`` is reserved for the case ``docs/adr/0116``
    added it to name: candidates above the floor are left over and **not one of
    them may share a court** with the people already seated.

    A seat is never filled below the floor to complete a four
    (``docs/adr/0099``), a newcomer least of all, so *nobody good enough* is an
    answer this function has to be able to give rather than a case it should try
    to avoid reaching.
    """

    if len(seating.seated) >= guests:
        return None
    if not pool.players_in_range:
        return UnfilledReason.POOL_EXHAUSTED
    floor = context.ruleset.floors.quality_floor
    above = tuple(row for row in pool.rows if row.modified.points >= floor)
    if not above:
        return UnfilledReason.NO_CANDIDATE_ABOVE_FLOOR
    seated = frozenset(one.player_id for one in seating.seated)
    if all(row.player_id in seated for row in above):
        return UnfilledReason.POOL_EXHAUSTED
    return UnfilledReason.NO_ADMISSIBLE_COMBINATION


def no_shared_slots(searcher: Searcher, seating: Seating) -> bool:
    """Whether the four-way intersection of the week is empty. **A dock.**

    Three good pairwise overlaps do not imply a four-way one — a searcher free
    Monday and Tuesday, one candidate free Monday, one free Tuesday and one free
    Monday reads well on every Fit and gives a four with no common slot — and the
    group availability term is the only thing that can see it.

    It reads that term rather than a second intersection of its own, so the dock
    the screen prints and the sixteen points the objective lost are two readings
    of one number and cannot disagree.

    **It never removes anybody.** An empty intersection zeroes the term, sixteen
    points of a competitive objective and twenty of a friendly, and the screen
    says *you would all have to bend*; the pairwise term does not gate at zero
    either, and the times rung relaxes exactly these slots.

    A **blank** grid stands the term down rather than emptying the week, so it is
    not this: *we do not know* is a different claim from *you four never
    overlap*, and only the second is worth saying out loud.
    """

    if not seating.seated:
        return False
    reading = group_availability(
        (searcher.grid, *(one.grid for one in seating.seated))
    )
    return reading == 0.0


@final
@dataclass(frozen=True, slots=True)
class LineupSeat:
    """One place on the court, and what it is to the searcher.

    ``relationship`` is **stated and never inferred from ``side``**
    (``the-two-contracts.md`` §5). The whole partner/opponent asymmetry hangs on
    it — the matrix's own seat scope, and the seat delta the printed Fit declined
    to take — and a client deriving it from which half of the court somebody sits
    on would be a second implementation of a domain rule.

    ``player_id`` is ``None`` on an open seat, and on a **line-up** that seat
    always carries a reason: an empty seat with nothing to say would be the
    silent shortfall *three of four is an honest answer* exists to refuse. The
    implication runs one way and not both, because a **forecast** has open seats
    too and they are of a different kind — the searcher has simply not filled
    them yet, nobody looked for anybody, and the provisional forecast is already
    the whole of what there is to say. A *taken* seat never carries a reason
    either way, and that half is the invariant.
    """

    side: Side
    seat_index: int
    relationship: Relationship
    player_id: str | None
    unfilled_reason: UnfilledReason | None

    def __post_init__(self) -> None:
        invariant(
            self.player_id is None or self.unfilled_reason is None,
            f"seat {self.seat_index} holds {self.player_id} and reads "
            f"{self.unfilled_reason}: a taken seat has nothing to explain",
        )


def roster(
    arrangement: Arrangement | None,
    *,
    searcher_id: str,
    guests: int,
    reason: UnfilledReason | None,
) -> tuple[LineupSeat, ...]:
    """The court, seat by seat, for one way round. **Always the full court.**

    The searcher is seat 0 on side A, always: there is no arrangement in which
    they cross the net, because *which side am I on* is not a question a builder
    asks. The partner seat follows on A, and the opposition fills B.

    **A partial line-up is this shape with fewer people in it**, never a
    different one — which is what makes *nobody* and *three of four* one thing
    for a client to render, with one or three seats carrying a reason.
    """

    partner = None if arrangement is None else arrangement.partner
    opponents: tuple[Seated, ...] = (
        () if arrangement is None else arrangement.opponents
    )
    seats = [
        LineupSeat(
            side=Side.A,
            seat_index=0,
            relationship=Relationship.SELF,
            player_id=searcher_id,
            unfilled_reason=None,
        )
    ]
    if guests == GUESTS:
        seats.append(_seat(Side.A, 1, Relationship.PARTNER, partner, reason))
        seats.append(
            _seat(Side.B, 2, Relationship.OPPONENT, _at(opponents, 0), reason)
        )
        seats.append(
            _seat(Side.B, 3, Relationship.OPPONENT, _at(opponents, 1), reason)
        )
    else:
        seats.append(
            _seat(Side.B, 1, Relationship.OPPONENT, _at(opponents, 0), reason)
        )
    return tuple(seats)


def _seat(
    side: Side,
    index: int,
    relationship: Relationship,
    taken_by: Seated | None,
    reason: UnfilledReason | None,
) -> LineupSeat:
    """One seat, taken or open.

    The reason is the **line-up's own** and the same one on every open seat in
    one answer: *why could this not be filled* is a fact about the pool and the
    mask, never about a position on the court. A caller with no reason to give —
    a forecast, where the searcher simply has not filled the seat — passes none,
    and the seat says nothing rather than borrowing a line-up's explanation.
    """

    return LineupSeat(
        side=side,
        seat_index=index,
        relationship=relationship,
        player_id=None if taken_by is None else taken_by.player_id,
        unfilled_reason=None if taken_by is not None else reason,
    )


def _at(seated: Sequence[Seated], index: int) -> Seated | None:
    return seated[index] if index < len(seated) else None


def seated_from(rows: Sequence[Scored], *, locked: bool = False) -> tuple[Seated, ...]:
    """The pool as the objective reads it: **a fenced person and one number.**

    The number is the **post-modifier** Fit — the one the floor tested and the
    card prints — so a seated card shows exactly what the shortlist showed and
    nothing is re-scored behind the player's back (``docs/adr/0104``).
    """

    return tuple(
        Seated(candidate=row.fenced, fit=row.modified.points, locked=locked)
        for row in rows
    )


#: The chance any one eligible candidate is in the pool the engine seats from,
#: on any one automatic fill.
#:
#: **Why a court needs one at all.** The engine is an argmax: one pool, one
#: objective, one best four, and it returns that four every time it is asked.
#: That is right — a searcher asking twice with nothing changed should not be
#: told the second answer is better — but *the same request run again tomorrow*
#: is a different question, and the engine was answering it identically. With
#: twenty-odd people in range, three of them were being offered every game and
#: the other twenty were never offered at all, which is both a worse product for
#: the searcher and a dead platform for everybody else.
#:
#: **Turnout is the honest place to put it, and the ranking is not.** The
#: alternative is to make the engine deliberately pick a four it judged worse,
#: which breaks the one thing it promises and makes ``group_reason`` a sentence
#: about a comparison that did not decide anything. This changes *who was
#: there*, and the engine goes on returning the best four of whoever was — so
#: *"the engine looks for the combination that plays out evenest"* stays true as
#: written, and no seat is ever filled below ``QUALITY_FLOOR``.
#:
#: **Not the exposure floor's job.** §14.2 already spreads who gets shown across
#: a week, and it is doing it — but it is a ±6 point lift on one Fit, bounded on
#: purpose so that being under-shown never outranks being a good match. It
#: cannot reorder combinations a wider margin apart and should not be widened
#: until it can: that would be paying for variety in the one currency the
#: product promises not to spend.
#:
#: Three in five, so the three best are all present about one search in five and
#: the four on offer is usually *a* good four rather than *the* good four. Not
#: lower: a court is four people, and turnout thin enough to strand a seat turns
#: a real answer into ``POOL_EXHAUSTED``.
TURNOUT = 0.6

#: Below this many candidates, everybody turns up. A pool with barely enough
#: people to fill the court has no variety to offer and everything to lose: the
#: guard below already refuses a draw that strands a seat, and this stops the
#: engine spending draws on a pool where every draw would be refused.
TURNOUT_NEEDS = 8


def who_turned_up(
    rows: Sequence[Scored], *, key: str, guests: int
) -> tuple[Scored, ...]:
    """The pool for **one** automatic fill: a lobby, not a ranking.

    Each candidate is drawn independently and **keyed off who they are and which
    search this is**, never off their position: a pool in a different order has
    to produce the same turnout, or the answer would depend on how the index
    happened to sort (``docs/adr/0105``). The same search re-read gives the same
    people, which is what lets a recorded search be replayed and what keeps this
    out of the ruleset corpus's way — that harness seats from ``pool.rows``
    itself and never runs this.

    **Everybody, whenever a draw would cost more than it buys**: a pool too
    small to have alternatives, or a draw that came up short of a full court.
    The second is the important one — turnout may make the offered four less
    even, which is the trade, but it may never turn a court that could have been
    filled into an empty seat. That would be reported as ``POOL_EXHAUSTED``,
    which would be a lie about the pool.

    It never reorders and never re-scores: what comes back is a subsequence, so
    everything downstream still reads the same Fit in the same order.
    """

    if len(rows) < max(TURNOUT_NEEDS, guests):
        return tuple(rows)
    present = tuple(
        row
        for row in rows
        if random.Random(f"{key}|{row.player_id}").random() < TURNOUT
    )
    return present if len(present) >= guests else tuple(rows)


def single_seat(
    searcher: Searcher,
    pool: Sequence[Seated],
    ruleset: Ruleset,
    combine: SigmaCombiner,
    *,
    locked: Sequence[Seated] = (),
) -> Seating:
    """The singles line-up: **the top-ranked candidate by Fit, and nothing else.**

    ``the-group-objective.md`` §2.4 struck ``G`` for singles by argument rather
    than by omission: over two seats the mean and the min are the same number,
    there are no cross pairs and there is no arrangement, so the objective
    reduces to a monotone transform of Fit plus a re-charged balance term — and
    the transform is **not order-preserving**, so ``POST /lineups`` and
    ``POST /searches`` could name different best candidates for one search.

    So there is no enumeration here and no mask: one pair, already gated at
    generation, and one arrangement with no swap. It hands the seating to the
    engine's own :func:`~app.engines.matchfit.v1.lineup.offer`, which is where
    *a line-up nobody scored* is built — the same function a doubles four with an
    open seat goes through, because they are the same answer with a different
    reason for having no objective.

    The counters come back at zero because none were walked, which is a
    measurement rather than a gap.
    """

    chosen = tuple(locked) or tuple(
        one for one in pool if one.fit >= ruleset.floors.quality_floor
    )[:1]
    return offer(
        searcher,
        chosen,
        ruleset,
        combine,
        counts=LineupCounts(
            combinations=0, refused_by_gate=0, refused_by_floor=0
        ),
        seats_per_side=1,
    )


def max_fit_rank(pool: LineupPool, seating: Seating) -> int | None:
    """How deep into the Fit ranking the engine actually reached.

    ``K``'s replacement falsifier. §24's own reads *whether the winning
    combination ever contains a candidate ranked past ``K``*, and it cannot fire:
    the pool is truncated at ``K``, so the answer is *never*, by construction, at
    every value of ``K``. This one measures the thing that can move.

    ``None`` when nobody was seated, which is not a rank of zero.
    """

    ranks = [
        pool.fit_rank[one.player_id]
        for one in seating.seated
        if one.player_id in pool.fit_rank
    ]
    return max(ranks) if ranks else None
