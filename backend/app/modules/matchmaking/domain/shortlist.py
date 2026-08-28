"""Stages 2 to 7 — the pipeline, from a partition to twenty ordered rows.

**Stages 1–6 are shared by every surface and only the terminal stage differs**,
which is the whole reason there is one engine rather than three. What is here is
those six plus the shortlist's own terminal stage; the line-up and the deck reuse
:func:`generate` and :func:`score_all` unchanged and end differently.

```
  1  GATE          ten hard exclusions. no relaxation reaches one
  2  GENERATE      sport ∧ box ∧ gates, over the partition
  3  FIT           eight terms, renormalised, evidence each   ── THE NUMBER
  4  MODIFY        three modifiers, ±10 stack, each prints
  5  QUALITY FLOOR below it, not shown at all. minimum evidence beside it
  6  LIVENESS      reorders. never enters Fit. never crosses as a number
  7  TERMINAL      ranked by rank_key, capped, unpaginated
```

**Determinism is a set-iteration problem** (``docs/adr/0105``), so nothing here
iterates a set or a dictionary to produce an order. The snapshot's rows arrive as
a tuple, every derived collection is a tuple, and the one sort in this file
breaks ties on ``(rank_key desc, fit desc, player_id asc)`` — three orders, the
last of which is unique. Two processes with different hash seeds produce the same
bytes, and a property test drives that across two subprocesses with the seed
**never pinned**.

**Reciprocal fit runs over the shortlist only, after the floor.** It is a second
``score()`` per row with the two sides swapped, over twenty to forty rows rather
than the whole pool — a stage that ran it earlier would be scoring exactly the
candidates the floor is about to discard.

**The near-miss band never leaves the building.** It is layer 3 of the telemetry
and no route returns it, to anyone: a player may ask why somebody was shown;
nobody may ask who was withheld.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Mapping, final
from uuid import UUID

from app.engines.matchfit.ranking import (
    Liveness,
    ModifiedFit,
    Reciprocal,
    rank_key,
)
from app.engines.matchfit.scorable import (
    LevelReading,
    LivenessFacts,
    ScorableCandidate,
    Searcher,
)
from app.engines.matchfit.core import Term
from app.engines.matchfit.scoring import Fit, MatchFit
from app.engines.matchfit.v1 import (
    Admission,
    Refusal,
    admits,
    modify,
    read_signals,
    reverse_mode,
)
from app.kernel import invariant, iso_weekday
from app.modules.matchmaking.domain.areas import area_code_of
from app.modules.matchmaking.domain.candidate_index import CandidateRow
from app.modules.matchmaking.domain.fence import (
    area_of,
    candidate_of,
    liveness_facts_of,
    modifier_facts_of,
    searcher_of,
    slots_of,
)
from app.modules.matchmaking.domain.gates import GATE_ROSTER, gate_of
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.domain.geography import (
    Point,
    bounding_box,
    whole_kilometres,
)
from app.modules.matchmaking.domain.geography import distance_km as measure_distance
from app.modules.matchmaking.domain.measurements import Overlap, overlap_of
from app.modules.matchmaking.domain.search_context import (
    SearchContext,
    is_new_at,
)
from app.modules.matchmaking.domain.searches import (
    InclusionReason,
    StagedCounts,
    WithheldReason,
)


@final
@dataclass(frozen=True, slots=True)
class Generated:
    """One candidate that survived the box and every gate.

    It carries the two measurements generation already made — the distance and
    the grid overlap — because both are read again downstream, and measuring
    either twice is how two answers to one question get into a system.
    """

    row: CandidateRow
    distance_km: float
    overlap: Overlap
    #: The candidate's id as the live reads key them. Parsed **once**, here,
    #: because the index spells an id as a string for the gate walk's sake and
    #: everything downstream of the gates asks the ports about it.
    player_uuid: UUID


@final
@dataclass(frozen=True, slots=True)
class Generation:
    """What stage 2 produced, and what it rejected on the way."""

    admitted: tuple[Generated, ...]
    #: Everyone inside the bounding box, before the gates. The client never sees
    #: this number; an analyst does.
    n_generated: int
    #: One key per gate code, counts only. **No candidate is named at this
    #: layer**, and the key set is the whole roster, so a gate that excluded
    #: nobody is a recorded zero rather than a missing key.
    excluded_by_gate: Mapping[str, int]


@final
@dataclass(frozen=True, slots=True)
class Scored:
    """One candidate with a Fit, the stack over it, and the floor's verdict.

    ``liveness`` and ``rank_key`` are ``None`` for a candidate the floor refused:
    stage 6 runs **after** the floor, so a refused candidate has no offset, and a
    field holding one would be a field somebody eventually sorts on.
    """

    generated: Generated
    fenced: ScorableCandidate
    fit: Fit
    modified: ModifiedFit
    admission: Admission
    liveness: Liveness | None = None
    #: The **raw inputs** stage 6 read, kept because the record stores those and
    #: never the offset: an offset is a function of the ruleset's bounds, so
    #: storing it would make a bounds change undiffable. ``None`` on a near-miss
    #: row, where stage 6 never ran at all.
    liveness_facts: LivenessFacts | None = None
    #: The reverse pairing, and the mode it ran under. The mode travels because
    #: it is not recoverable from the candidate's declaration: a
    #: ``NO_PREFERENCE`` candidate inherits the searcher's.
    reciprocal: Reciprocal | None = None
    rank_key: float | None = None
    inclusion_reason: InclusionReason | None = None

    @property
    def player_id(self) -> str:
        return self.generated.row.player_id

    @property
    def withheld_reason(self) -> WithheldReason | None:
        """How the near-miss band records this refusal."""

        if self.admission.refusal is None:
            return None
        if self.admission.refusal is Refusal.TOO_LITTLE_EVIDENCE:
            return WithheldReason.INSUFFICIENT_EVIDENCE
        return WithheldReason.BELOW_FLOOR

    @property
    def missing_terms(self) -> tuple[str, ...]:
        """Which live terms did not fire **for this specific person**.

        Recorded because *nobody was good enough* and *nobody was known enough*
        are different findings, and a floor investigation that cannot tell them
        apart is looking at the wrong number.
        """

        fired = set(self.admission.fired)
        return tuple(term.value for term in self.admission.live if term not in fired)

    @property
    def shown_distance_km(self) -> int | None:
        """Whole kilometres, as the wire carries them — or ``None``.

        ``None`` when the distance term stood down, which is **omitted** on the
        wire and is not a zero: a candidate whose distance could not be read is
        not next door, and the absence is what lets *Closest* sort them last
        instead of first.

        It is derived here, once, because three readers need the same answer and
        must not disagree: the response, the recorded row, and the sort that says
        whether *Closest* is honest. Two of those three are read back a month
        later against the third.
        """

        if Term.DISTANCE in self.fit.degraded_terms:
            return None
        return whole_kilometres(self.generated.distance_km)

    @property
    def reliability_penalty_applied(self) -> bool:
        return self.modified.modifiers.floor_breach is not None

    def reliability_penalty_decisive(self, quality_floor: int) -> bool:
        """Whether the dock is what put them below the floor — **docked** versus
        **docked out**.

        Re-derived from the two numbers rather than remembered, so it cannot
        disagree with the Fit beside it: the pairing was at or above the bar
        before the dock and is below it after.
        """

        breach = self.modified.modifiers.floor_breach
        if breach is None:
            return False
        without = self.modified.points - breach.points
        return self.modified.points < quality_floor <= without


@final
@dataclass(frozen=True, slots=True)
class Shortlist:
    """The answer, plus what the record needs and the response must never see."""

    returned: tuple[Scored, ...]
    #: Layer 3. **Engine-internal**, and no route returns it, to anyone.
    near_misses: tuple[Scored, ...]
    counts: StagedCounts
    #: The Fit of the best candidate that did not clear. ``None`` means nothing
    #: was withheld, which is not the same as ``0``.
    best_withheld_fit: float | None
    #: The post-gate pool the searcher is told about.
    players_in_range: int


def ids_in_box(
    snapshot: CandidateSnapshot,
    *,
    centre: Point,
    radius_km: int,
    excluding: UUID,
) -> tuple[UUID, ...]:
    """Who is inside the box, before anything live has been read.

    The live gate facts — the block set, the holds, the account states — are
    **set reads over a population**, and the population they are about is this
    one: everybody the box admits. So the box is walked once to name them, the
    three sets are resolved in one call each, and generation then walks it again
    with every gate in hand.

    Two walks rather than one, deliberately. A box test costs 18.5 ns and a
    candidate that survives it costs 1.00 µs, so the second walk is free at any
    population this platform will see; the alternatives are a query per row,
    which the ports refuse by shape, or resolving the sets over the whole
    partition, which asks three contexts about people who are not in the search.
    """

    box = bounding_box(centre, float(radius_km))
    me = str(excluding)
    return tuple(
        UUID(row.player_id)
        for row in snapshot.rows
        if row.player_id != me and box.contains(area_of(row))
    )


def generate(context: SearchContext) -> Generation:
    """``sport ∧ bounding box of the searcher's radius ∧ every gate``.

    **The shard conjunct is struck** (``docs/adr/0101``): an equality inside the
    generation conjunction *excludes*, so the partition is derived and there is
    no field for a future conjunct to attach to. The box is the only spatial
    truth, and it is a cheap over-approximation that the radius gate corrects —
    the box admits its own corners, and a search that stopped at it would quietly
    widen every radius by up to 41%.

    The searcher is dropped before the gates rather than by one of them. Being
    yourself is not an exclusion anybody is owed a count of, and a gate for it
    would put a permanent 1 in every histogram.
    """

    box = context.box
    centre = context.searcher.area
    searcher_slots = context.searcher.grid.slots
    today = iso_weekday(context.now.isoweekday())
    me = str(context.searcher.player_id)

    admitted: list[Generated] = []
    excluded = {code.value: 0 for code in GATE_ROSTER}
    n_generated = 0
    for row in context.snapshot.rows:
        if row.player_id == me:
            continue
        area = area_of(row)
        if not box.contains(area):
            continue
        n_generated += 1
        distance = measure_distance(centre, area)
        refused = gate_of(row, context, distance_km=distance)
        if refused is not None:
            excluded[refused.value] += 1
            continue
        admitted.append(
            Generated(
                row=row,
                distance_km=distance,
                overlap=overlap_of(searcher_slots, slots_of(row), today),
                player_uuid=UUID(row.player_id),
            )
        )
    return Generation(
        admitted=tuple(admitted),
        n_generated=n_generated,
        excluded_by_gate=excluded,
    )


def score_all(
    generation: Generation, context: SearchContext, engine: MatchFit
) -> tuple[Scored, ...]:
    """Stages 3 to 5 for every candidate that cleared the gates.

    The floor reads the **modified** Fit: the reliability dock exists to push
    somebody under it, and a bar reading the unmodified score would be
    decorative.
    """

    searcher = searcher_of(context)
    ruleset = context.ruleset
    scored: list[Scored] = []
    for candidate in generation.admitted:
        fenced = candidate_of(
            candidate.row,
            context,
            distance_km=candidate.distance_km,
            player_uuid=candidate.player_uuid,
        )
        fit = engine.score(searcher=searcher, candidate=fenced, ruleset=ruleset)
        modified = ModifiedFit(
            fit=fit,
            modifiers=modify(
                searcher,
                fenced,
                modifier_facts_of(candidate.row, context, candidate.player_uuid),
                ruleset,
            ),
        )
        scored.append(
            Scored(
                generated=candidate,
                fenced=fenced,
                fit=fit,
                modified=modified,
                admission=admits(
                    modified,
                    ruleset,
                    context.absent_terms,
                    newcomer=_is_new(candidate.row, context),
                ),
            )
        )
    return tuple(scored)


def run(context: SearchContext, engine: MatchFit) -> Shortlist:
    """The whole pipeline, from a bound snapshot to an ordered, capped answer."""

    generation = generate(context)
    scored = score_all(generation, context, engine)
    admitted = tuple(row for row in scored if row.admission.admitted)
    withheld = tuple(row for row in scored if not row.admission.admitted)
    returned = _rank(admitted, context, engine)[: context.ruleset.shape.shortlist_max]
    near_misses = _near_misses(withheld, context)
    return Shortlist(
        returned=returned,
        near_misses=near_misses,
        counts=StagedCounts(
            n_generated=generation.n_generated,
            excluded_by_gate=generation.excluded_by_gate,
            n_scored=len(scored),
            n_cleared_floor=len(admitted),
            n_returned=len(returned),
            n_near_miss_recorded=len(near_misses),
        ),
        best_withheld_fit=(
            max(row.modified.points for row in withheld) if withheld else None
        ),
        players_in_range=len(generation.admitted),
    )


def _rank(
    admitted: tuple[Scored, ...], context: SearchContext, engine: MatchFit
) -> tuple[Scored, ...]:
    """Stage 6 and the shortlist's terminal stage: the offset, then the order.

    ``rank_key = fit + liveness_offset``, and it is never shown and never crosses
    the wire in any shape. The sort's tie-breaks are total and end on the player
    id, so **a set is never the source of an order**.
    """

    searcher = searcher_of(context)
    moved = tuple(_with_liveness(row, context, engine, searcher) for row in admitted)
    return tuple(
        sorted(
            moved,
            key=lambda row: (-_key(row), -row.modified.points, row.player_id),
        )
    )


def _key(row: Scored) -> float:
    invariant(
        row.rank_key is not None,
        f"{row.player_id} reached the order with no rank key",
    )
    return row.rank_key if row.rank_key is not None else 0.0


def _with_liveness(
    row: Scored, context: SearchContext, engine: MatchFit, searcher: Searcher
) -> Scored:
    """One admitted candidate's offset, its reciprocal, and its rank key."""

    facts = liveness_facts_of(
        row.generated.row,
        context,
        row.generated.overlap,
        row.generated.player_uuid,
    )
    reciprocal = _reciprocal(row, context, engine, searcher)
    liveness = read_signals(facts, context.ruleset, reciprocal)
    return replace(
        row,
        liveness=liveness,
        liveness_facts=facts,
        reciprocal=reciprocal,
        rank_key=rank_key(row.modified, liveness),
        inclusion_reason=_inclusion_reason(row, context),
    )


def _reciprocal(
    row: Scored, context: SearchContext, engine: MatchFit, searcher: Searcher
) -> Reciprocal:
    """The candidate's own Fit for the searcher, under the mode they inherit.

    **The reverse pairing is assembled here and not in the engine**, and that is
    the fence rather than an omission: ``fit_ba`` needs facts about the
    *searcher* that do not cross into a ``ScorableCandidate`` — their id, their
    own declaration, their own area — and the module holds all of them because it
    holds the I/O.

    ``NO_PREFERENCE`` never selects a weight vector, it inherits one, so a
    candidate who declared it is judged under the *searcher's* mode: the game
    being proposed is the game they would be judging.
    """

    mode = reverse_mode(
        context.searcher.mode,
        row.generated.row.declared_intent,
        context.ruleset.intent,
    )
    them = Searcher(
        level=row.fenced.level,
        mode=mode,
        tags=row.fenced.tags,
        grid=row.fenced.grid,
        radius_km=row.fenced.radius_km,
        today=searcher.today,
        day_parts=searcher.day_parts,
    )
    reverse = engine.score(
        searcher=them,
        candidate=_searcher_as_candidate(row, context, searcher),
        ruleset=context.ruleset,
    )
    return Reciprocal(fit_ab=row.modified.points, fit_ba=reverse.points, mode=mode)


def _searcher_as_candidate(
    row: Scored, context: SearchContext, searcher: Searcher
) -> ScorableCandidate:
    """The searcher, fenced, so the candidate can be scored against them.

    It reuses the pair's own combined uncertainty and distance rather than
    recomputing either: both are symmetric facts about the pair, and computing
    them a second time from the other end is two chances to disagree about one
    number.

    The searcher's own reliability is ``None`` and would be even if
    ``player_score`` shipped: the reverse Fit exists to price how good a bet the
    *searcher* looks from the other side, and the module reads a Player Score for
    candidates rather than for the person searching.
    """

    facts = context.searcher
    return ScorableCandidate(
        player_id=str(facts.player_id),
        level=LevelReading(mu=facts.mu, sigma=facts.sigma),
        declared_intent=facts.declared_intent.value,
        tags=facts.tags,
        grid=searcher.grid,
        radius_km=float(facts.radius_km),
        area_code=area_code_of(facts.area),
        distance_km=row.generated.distance_km,
        combined=row.fenced.combined,
        reliability=None,
    )


def _near_misses(
    withheld: tuple[Scored, ...], context: SearchContext
) -> tuple[Scored, ...]:
    """Layer 3: the best ``NEAR_MISS_RECORDED`` that did not clear.

    Ordered on the modified Fit, because that is the number the floor read. Ties
    break on the player id for the reason the shortlist's do.
    """

    ranked = sorted(withheld, key=lambda row: (-row.modified.points, row.player_id))
    return tuple(ranked[: context.ruleset.telemetry.near_miss_recorded])


def _inclusion_reason(row: Scored, context: SearchContext) -> InclusionReason | None:
    """Why this candidate is in the answer, when there is a reason to record.

    **The store is open where the wire is closed.** Two of the three are
    reachable today and neither of them *admits* anybody — they reorder, which is
    exactly why only the third crosses the wire. The interest lift is the one
    that admits, and it arrives with the interest ledger.

    ``NEWCOMER_WINDOW`` is recorded ahead of ``ZERO_EXPOSURE`` because a newcomer
    who has also never been shown is being lifted for the more specific reason,
    and the column holds one value.
    """

    if _is_new(row.generated.row, context):
        return InclusionReason.NEWCOMER_WINDOW
    if context.terms.times_shown.get(row.generated.player_uuid, 0) == 0:
        return InclusionReason.ZERO_EXPOSURE
    return None


def _is_new(row: CandidateRow, context: SearchContext) -> bool:
    return is_new_at(row.profile_created_at, context.now)
