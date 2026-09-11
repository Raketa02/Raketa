"""What a ruleset is, and what makes one malformed.

**Every number the engine uses, in one versioned, dated, frozen dataset.** A
ruleset is *named* (``2026.08.26-a``), *dated*, and **immutable once released**:
a new set is a new name, never an edit to an old one (``docs/adr/0093``).
Changing a weight is a ruleset release and a deploy — not a code change and never
an environment variable.

**It ships embedded with the code**, so a release is a deploy. The runtime store
is deferred deliberately until there is enough traffic for an experiment to mean
anything, and its arrival changes only where the file is read from, never what
the stamp guarantees.

**Validated on load, and a malformed ruleset refuses to load while the previous
one keeps serving.** It never falls back to defaults, because a matcher that
silently falls back is one that quietly A/B tests against itself. With an
embedded ruleset there is no hot reload to fall back through, so the mechanism is
``docs/adr/0119`` §6's: validation runs at import and at startup, a bad ruleset
fails the deploy, and the previous version keeps serving because the old pods are
still up. Same guarantee, different mechanism.

**Two of the validations are the map's own additions.** ``K`` may not exceed the
engine-side ceiling (``scale-posture.md`` §6), and every evidence kind the
ruleset can emit must be present in the wire union (``docs/adr/0106``). The
second cannot run here — an engine may not import a schema — so it runs in the
composition root, where the ruleset and the contract are both visible.

**What is deliberately absent**, because the input document's ruleset shape had
it and this map struck it: the ``newcomer`` mode (``docs/adr/0113`` replaced it
with a gate), the collapsed ``w_intent`` / ``w_tag`` group weights
(``docs/adr/0117`` replaced them with six terms that each read something no seat's
Fit read), ``max_rung`` and the ordered-rung list, ``score_min`` — a key nothing
in the design ever defines — and **diversity entire**, whose stage is struck
(``docs/adr/0126``).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, TypeVar

from app.engines.matchfit.core import (
    K_CEILING,
    ChallengeLoad,
    ClashSeverity,
    EvidenceKind,
    FamiliarityReading,
    GroupTerm,
    LivenessSignal,
    Modifier,
    RelaxationRung,
    ReliabilityStrand,
    SearchMode,
    Seat,
    TagColumn,
    TagRelationshipKind,
    Term,
)
from app.kernel import invariant

#: What a weight vector is keyed by — a term, a strand, or a group term. Named
#: rather than left as ``object`` so that a vector and the members it is checked
#: against cannot be two different vocabularies.
_Weighted = TypeVar("_Weighted")

#: Weights are expressed out of a hundred and sum to it **within a mode, before
#: renormalisation**. A term that produces no evidence is dropped from the sum and
#: the survivors renormalise per comparison, which is why the basis a Fit was
#: computed on has to be carried beside it or the number is uninterpretable.
WEIGHT_TOTAL = 100

#: The three modifiers that sit inside the budget. The reliability floor breach is
#: outside it and derived, so it is not one of these.
BUDGETED_MODIFIERS = (
    Modifier.CALIBRATION_VALUE,
    Modifier.FAMILIARITY,
    Modifier.WELCOMING_RECORD,
)


@dataclass(frozen=True)
class ModeRules:
    """One mode's weight vector, strand vector and level tolerance.

    **The inversion is the shape.** For fun, social vibe is the largest term in
    the match — larger than level — because that is what *for fun* means.

    ``free_band`` is ``None`` in competitive, where the concept does not apply:
    every tenth of a point of level gap is priced from zero. For fun it is the
    width at the bottom of the curve inside which a gap costs nothing, on the
    claim that *a friendly against someone a quarter-point above you is no worse
    than one against your exact twin* — a claim about the game, not about the
    weight.

    **``level_tolerance`` is also the level gate** (``docs/adr/0103``). One number
    per mode and not two, so the gate and the curve can never drift apart. It is
    absolute on μ and never reads a band: the shipped bands are deliberately
    uneven because *evidence* is unevenly available down the scale, not because a
    tenth of a point means less at the top.
    """

    weights: Mapping[Term, int]
    strand_weights: Mapping[ReliabilityStrand, int]
    level_tolerance: float
    free_band: float | None
    #: How much better a game the two tag terms together may be worth, expressed
    #: as a fraction of the level tolerance. It turns *"six well-chosen tags must
    #: not outrank a good level match"* from an intention into an inequality —
    #: and an intention does not survive a weight release. Both tag terms clamp
    #: to ``[0, 1]``, so their largest possible contribution is exactly
    #: ``w_style + w_vibe``, and the rule needs no knowledge of the curve or the
    #: matrix::
    #:
    #:     w_style + w_vibe  <  w_level × margin / level_tolerance
    #:
    #: **Competitive only, and ``None`` in for fun is the decision rather than a
    #: gap.** In a friendly the tags are *supposed* to outrank level — saying
    #: otherwise would delete the inversion the whole vector is built around —
    #: and what binds for fun is the six judged pairings, which is stricter and
    #: better argued.
    tag_stuffing_margin: float | None


@dataclass(frozen=True)
class TagRelationship:
    """One row of the relationship matrix: a claim about two tag ids.

    **Entries are symmetric — there is no direction field.** Fit is already
    asymmetric through familiarity, which reads the searcher's tags and never the
    candidate's, so asymmetry was available and is refused here: a directed row
    would score the same two people differently depending on who searched.

    **Firing.** Given searcher tags ``S`` and candidate tags ``C``, a row
    ``{a, b}`` fires iff ``(a∈S ∧ b∈C) ∨ (b∈S ∧ a∈C)`` — at most once per row per
    pair, whoever holds what. A shared tag may pay both a match and a complement:
    they are two different claims, *you both want this* against *your two things
    fit together*.

    **A pair may carry more than one row, and their ``modes × seats`` scopes must
    be disjoint** — which is how *far worse as partners than as opponents* is
    said without inventing a second severity field.

    **No ``sport`` field, ever.** A tag relationship is a claim about people;
    *levels never transfer between sports* is a claim about proof, not about
    temperament. The only sport-shaped variation the rows need is already carried
    by ``seats``, because a ``PARTNER`` row is unreachable in a two-player sport
    by arithmetic rather than by rule.
    """

    a: str
    b: str
    kind: TagRelationshipKind
    column: TagColumn
    modes: tuple[SearchMode, ...]
    seats: tuple[Seat, ...]
    #: ``COMPLEMENT`` only. A match is two people independently choosing the same
    #: string; a complement is product's editorial claim about two different ones,
    #: and the discount prices that. A row may override upward to a ceiling of
    #: 1.00 and **never below the default**, because parity is the most an
    #: editorial claim can be worth against two people's agreement.
    strength: float | None = None
    #: ``CLASH`` only, and graded rather than free, so that widening the clash arm
    #: is a visible edit to the severity table rather than a number nudged in a row.
    severity: ClashSeverity | None = None

    @property
    def pair(self) -> tuple[str, str]:
        """The unordered pair this row is about, in a stable order.

        Sorted rather than as written, so that two rows about the same two ids
        collide on one key however the author typed them — which is what makes
        the disjointness check see them at all.
        """

        return (self.a, self.b) if self.a <= self.b else (self.b, self.a)

    def scopes(self) -> frozenset[tuple[SearchMode, Seat]]:
        """Every ``(mode, seat)`` cell this row claims.

        Disjointness is checked over cells rather than over the two lists,
        because ``modes × seats`` is what a row actually occupies and two rows
        can overlap on one cell while differing in both lists.
        """

        return frozenset((mode, seat) for mode in self.modes for seat in self.seats)


@dataclass(frozen=True)
class TagRules:
    """The tag block: the curve, the two arms, the cap, the matrix and the map.

    ``dr(n) = 1 − phi ⁿ`` is the diminishing-returns curve both tag terms read.
    The second matched tag is worth less than the first, so tag-stuffing does not
    pay — and the platform caps selection at six precisely because it expects
    people to try.

    ``raw = dr(matches) + strength·dr(complements) − Σ severity``, normalised
    over ``[−clash_cap, 1]``. **The term's zero is a real clash and not an
    absence of relationship:** a pair with nothing firing scores 0.20, the
    *measured* zero — *different, not incompatible* — which is what makes the
    clash arm visible at all. Scored the other way, *"you two clash badly"* is
    numerically identical to *"you two share nothing"*, and two random four-tag
    draws from nineteen overlap 0.84 times on average, so the typical pair would
    sit at the bottom of a term carrying 24 of 100 in for fun.

    **Clash penalties are capped and smaller than match bonuses.** One real clash
    is worth less than one match, and the full cap costs 2.6 points of 100 in
    competitive — enough to notice, nowhere near enough to bury anybody. Being
    wrong about a match costs a duller evening; being wrong about a clash
    unfairly buries a person, and the magnitudes are asymmetric because the costs
    are.
    """

    phi: float
    complement_strength: float
    clash_severities: Mapping[ClashSeverity, float]
    clash_cap: float
    relationship_matrix: tuple[TagRelationship, ...]
    #: Product-owned, and a **second and separate map** from the matrix even
    #: where the two read the same ids. Exhaustive over the ``WHY_YOU_ARE_HERE``
    #: group; that exhaustiveness is checked in the composition root, because the
    #: tag vocabulary is a module's and an engine may not import one.
    familiarity_reading_map: Mapping[str, FamiliarityReading]

    def column_domain(self, column: TagColumn) -> frozenset[str]:
        """The tag ids this column scores, **derived from the matrix**.

        Never declared separately, so it re-derives itself the moment product
        edits a row. A tag may sit in both domains, and a tag with no row at all
        is in neither — which is what makes *this column stands down* mean
        *neither side said anything about the hour on court* rather than *we
        looked and found nothing*.
        """

        return frozenset(
            tag
            for row in self.relationship_matrix
            if row.column is column
            for tag in (row.a, row.b)
        )


@dataclass(frozen=True)
class BalanceRules:
    """The forecast: two coefficients and the clamp that is the term's range.

    ``pct = clamp(100 − Δμ·mu_coefficient − σ_pair·sigma_coefficient, min, max)``,
    normalised across the clamp. **The bounds are the term's zero and one, not
    cosmetics** — leaving them out wastes the bottom third of the range.

    ``σ_pair`` is the core's ``combine_sigma``, never re-derived here: *the
    single place any engine is allowed to combine two standard deviations*.

    **The most directly falsifiable numbers in the engine.** The coefficients are
    a forecast, and a forecast is checkable against confirmed results.
    """

    mu_coefficient: float
    sigma_coefficient: float
    pct_min: int
    pct_max: int
    #: How much of a doubles side's strength the **stronger** partner sets —
    #: ``the-group-objective.md`` §3.1's ``TEAM_STRENGTH_SHARE``. One number and
    #: not two, because the pair's shares are one fact: two fields could be
    #: released summing to something other than a whole side.
    #:
    #: Under a half, which is the claim: *the weaker partner sets more of a
    #: side*, because a doubles pair is attacked at its weaker half all evening.
    #: It reads only in a four — a pairwise forecast has no side to form — and it
    #: is why the three arrangements of one four differ at all.
    stronger_partner_share: float


@dataclass(frozen=True)
class ReliabilityRules:
    """The three bars a reliability reading has to clear.

    ``min_observations`` is a bar **per strand**, and the mapping is exhaustive:
    below its own bar that strand alone stands down and the survivors renormalise
    inside the term. **It was one number for every strand and is now one per
    strand** (``docs/adr/0156``), because *answers about results* needs a higher
    bar than the rest and raising the single number instead would take a newcomer
    who has played three games and turned up to all three from a full score to no
    score at all — a change to how the whole product treats newcomers, arrived at
    as a side effect of tuning one strand. A missing key is refused rather than
    defaulted: a strand nobody set a bar for would enter every reading on its
    first observation, which is the failure the bar exists to prevent.

    ``horizon_days`` binds the whole term — if the most recent observation across
    every strand is older, reliability stands down entirely.

    ``published_score_bar`` is read against the **published Player Score**, the
    number on the player's own profile, and not the matcher's per-mode blend of
    the same six strands. **This is the one deliberate place the matcher reads
    the blend instead of the strands**, recorded as an exception so it does not
    later read as an oversight: a penalty justified by a figure that exists
    nowhere a human can look is unexplainable, and a player who works their
    visible score back up must be able to see the penalty lift.
    """

    min_observations: Mapping[ReliabilityStrand, int]
    horizon_days: int
    published_score_bar: int


@dataclass(frozen=True)
class PointRange:
    """A signed points range a modifier or a liveness signal may take."""

    minimum: int
    maximum: int


@dataclass(frozen=True)
class FamiliarityRules:
    """How a shared history decays, and which way it points when nobody said.

    ``strength = 0.5 ^ (days_since_last / half_life_days) × (1 − depth_phi ⁿ)``.
    An eight-month-old single game sits at 15% of full — *effectively fresh
    again* without pretending it never happened.

    ``depth_phi`` carries the same value as the tag curve's ``phi`` and is a
    **separate constant with its own falsifier**: a coincidence of values must
    never become a shared constant.

    ``default_lean`` is the *mildly novelty-preferring* default a searcher falls
    to when none of their tags reads either way. **The arm is asymmetric on
    purpose** — being wrong about a positive costs a duller evening; being wrong
    about a negative buries a person.
    """

    half_life_days: int
    depth_phi: float
    default_lean: float


@dataclass(frozen=True)
class ModifierRules:
    """The budget, the three modifiers inside it, and the cap that refuses its integer.

    ``budget`` clamps the **summed stack** rather than each modifier, so a stack
    of small positives can never lift somebody over a recent no-show. On day one
    it is inert — calibration is the only modifier whose input exists — and that
    is correct for the same reason the evidence gate is: standing insurance, in
    place before it is needed.

    **The reliability floor penalty is derived, not picked.** The property that
    has to hold is that the stack cannot erase a no-show, so the smallest penalty
    that keeps the promise is ``budget + 1`` — and defining it that way means it
    moves by itself if the budget ever does.

    **``newcomer_absorption_cap`` keeps its rule and refuses its integer.** It
    bounds how often one player is volunteered into a *newcomer's* shortlist, and
    binds by dropping the **welcoming modifier** — the thumb that selects those
    players — never by withholding, and never the newcomer lift, which is the
    other side of the pairing's own subsidy (``docs/adr/0114``, amended). With no
    players there is no distribution to sit it in, and with the modifier it
    bounds unable to fire, any integer would be untestable. Its falsifier is
    written and its value is not, so it is ``None`` rather than a number nobody
    can defend.
    """

    budget: int
    ranges: Mapping[Modifier, PointRange]
    familiarity: FamiliarityRules
    newcomer_absorption_cap: int | None

    @property
    def floor_breach_penalty(self) -> int:
        """The reliability floor dock: outside the budget, derived from it."""

        return -(self.budget + 1)


@dataclass(frozen=True)
class ChallengeLoadRung:
    """One step of the full-inbox sink: a depth, what it costs, and its code.

    ``docs/adr/0125`` deleted the withholding at eight open challenges and
    **adopted §14.4's three thresholds whole**, changing only the third's effect.
    They are here rather than in the arithmetic because they are numbers, and
    every number the engine uses lives in one dated dataset — but the *shape* is
    a rung and not a curve, because that is what was adopted: three measured
    depths, not a slope somebody fitted through them.

    ``prints`` is the coarse code the rung crosses as, carried by the rung rather
    than derived from its position, so moving a threshold cannot silently
    re-point a code at a different depth. **The number itself never crosses** —
    their inbox depth is theirs.
    """

    at_least: int
    points: int
    prints: ChallengeLoad


@dataclass(frozen=True)
class SignalBound:
    """One liveness signal's range, and whether it owes the player a sentence.

    A **printable** signal can be named as the dominant reason a candidate moved.
    A **silent** one never can, so ``docs/adr/0123`` budgets the silent *stack*
    at the notice threshold: with the silent net inside it, any player moved more
    than the threshold necessarily has a printable contributor, and the printing
    promise falls out of the arithmetic rather than resting on a sentence.

    ``points`` is the range a **firing** signal may take. A signal that does not
    fire is absent from the list rather than present at zero — which is why the
    reachable silent net is computed against zero on each side.
    """

    points: PointRange
    printable: bool


@dataclass(frozen=True)
class LivenessRules:
    """The offset's bounds, the ten signals, the notice threshold, the tolerance.

    ``rank_key = fit + liveness_offset``, and **rank_key is never shown and never
    crosses the wire in any shape**. There is no field a Liveness offset could be
    written to: the printed Fit is the only number a player is asked to trust,
    and it stops meaning what it says the moment it silently contains *they open
    the app a lot*.

    ``move_notice`` does **two jobs, deliberately one constant and not two**: it
    is the movement above which a candidate's dominant printable reason is
    emitted, *and* it is the budget on the silent stack. Two constants could
    drift apart in a ruleset edit and break the printing guarantee silently.

    ``asymmetry_tolerance`` is the head start a reciprocal reading gets before it
    docks: a candidate whose own Fit for the searcher is far lower is a bad bet
    for the searcher, and that is priced proportionately rather than as a flat
    charge — the flat one was the same fact charged twice, once here and once
    inside the candidate's own distance term.
    """

    offset_minimum: int
    offset_maximum: int
    signals: Mapping[LivenessSignal, SignalBound]
    #: The full-inbox sink, deepest last. It is the one signal that reads a
    #: **count** rather than a normalised reading, because it is the one whose
    #: thresholds were measured and published before this map existed — the rest
    #: would need a curve invented here, and a number nobody measured is a number
    #: somebody picked.
    challenge_load_rungs: tuple[ChallengeLoadRung, ...]
    move_notice: int
    asymmetry_tolerance: int
    #: How steeply a reciprocal shortfall past the tolerance docks — ``dock =
    #: −min(bound, asym × slope)``. It is priced **proportionately** and not as a
    #: flat charge, which is what replaced the struck radius-asymmetry dock: that
    #: one charged a fact the candidate's own distance term had already priced.
    asymmetry_slope: float

    def silent_signals(self) -> tuple[LivenessSignal, ...]:
        """The signals that never print, in enum order.

        ``docs/adr/0123``'s roster: today it is exactly previous decline and the
        exposure adjustment, and a roster test pins it there. A third silent
        signal is a decision, not a row.
        """

        return tuple(
            signal
            for signal in LivenessSignal
            if signal in self.signals and not self.signals[signal].printable
        )

    def reachable_silent_net(self) -> PointRange:
        """The furthest the silent stack can move somebody **before** the clamp.

        Against zero on each side, because a signal that does not fire is absent
        rather than zero. Today this is ``[−12, +6]``, so the upper clamp is
        unreachable and the clamp only ever cuts a *bury* — which is true of the
        roster and not of the rule, and is exactly what the roster test is for.
        """

        firing = [self.signals[signal].points for signal in self.silent_signals()]
        return PointRange(
            minimum=sum(min(0, points.minimum) for points in firing),
            maximum=sum(max(0, points.maximum) for points in firing),
        )


@dataclass(frozen=True)
class GroupRules:
    """The doubles objective's weights per mode, and the candidate cap.

    **The inversion arrives without being asserted.** Competitive puts 36 of 100
    on the searcher's own seats against 14 on the three cross pairs; for fun it
    is 30 against 34 — and a for-fun cross reading is richer to begin with,
    because 51.7% of a for-fun Fit is person-to-person against 31.0% competitive.

    ``k`` is the candidate cap the enumeration truncates to, by Fit. It is
    ruleset data with an **engine-side ceiling that refuses to load a ruleset
    exceeding it**, because the enumeration is cubic in ``k`` and it is the one
    number that can destroy the line-up latency budget.
    """

    weights: Mapping[SearchMode, Mapping[GroupTerm, int]]
    k: int


@dataclass(frozen=True)
class Floors:
    """The three numbers that decide whether the product says anything at all.

    ``quality_floor`` is the Fit below which a candidate is not shown. It is
    **defined by the six judged pairings it must satisfy** and its integer is
    read off them on the day-one basis — not calibrated against a distribution,
    because there are no players. **One floor, both modes, every sport**: each
    extra dimension is another place the bar could be lowered quietly for
    whichever pool is thin. **Never relaxed, at any rung**, and the empty-result
    rate is never on its own sufficient grounds to move it.

    ``min_shortlist`` triggers nothing. It decides **whether the relaxation
    offers are computed at all** — the counts on those offers must be real, which
    means genuinely re-running generation and scoring per rung, and on most
    searches that is a lever nobody needs.

    ``minimum_evidence_fraction`` is the honesty rule beside the floor. The floor
    is a fixed bar over a score whose ingredients vary per comparison, so at the
    bar *giving nothing* would become a small advantage over giving something
    mediocre. Below a minimum of evidence **about that specific person** they are
    not shown — a gate, never a score adjustment — and it is a **fraction of the
    terms live for the platform** rather than a count, so it keeps meaning the
    same thing when a term turns on. **Today it excludes nobody, and that is the
    point.**
    """

    quality_floor: int
    min_shortlist: int
    minimum_evidence_fraction: float


@dataclass(frozen=True)
class ShapeRules:
    """Where each surface's answer stops.

    Here rather than under ``floors`` because a floor decides whether somebody is
    shown at all and these decide only where the list ends. The shortlist is
    bounded and **unpaginated** — past the last row there are rung offers or an
    honest empty state, never a page two — and a client never reads either number
    from anywhere: it renders the rows it is given.
    """

    shortlist_max: int
    deck_deal_max: int


@dataclass(frozen=True)
class RelaxationRules:
    """How far each radius rung reaches. **The ladder itself is not here.**

    ``max_rung`` and the ordered-rung list are struck rather than carried, and
    that is a decision and not an omission. *Times before distance* and *there is
    no third radius rung* are arguments — a slot you were already free in costs
    nothing where distance costs travel on every game forever, and tripling the
    radius still leaves 15% of searches short at launch density
    (``docs/adr/0099``). A ruleset that could add or reorder a rung would be a
    weight release changing what the product offers, which is exactly the line
    ``docs/adr/0106`` draws. **The ladder is ``RelaxationRung``'s own declaration
    order**; what a release may move is how far each radius rung reaches.

    Every radius rung clamps to the maximum the profile slider itself allows, so
    a rung can never offer a radius the player could not have set for themselves.
    A searcher already at the ceiling gets no radius rung at all, and one near it
    gets one rather than two, because a rung duplicating another rung's radius is
    not offered twice.
    """

    radius_multipliers: Mapping[RelaxationRung, float]


@dataclass(frozen=True)
class TelemetryRules:
    """How deep the engine's own record of a search reaches past the answer.

    The near-miss band is the best scored candidates that did **not** clear.
    It is engine-internal and no route ever returns it, to anybody: *a player may
    ask why somebody was shown, and nobody may ask who was withheld.* Its depth
    is a ruleset constant because it is a floor investigation's whole sample —
    the top row is the load-bearing one and the rest is the shape around it.
    """

    near_miss_recorded: int


@dataclass(frozen=True)
class InterestRules:
    """The three numbers behind *Let's play*, a pass, and how many yeses stand.

    ``ttl_days`` matters because **an interest lift is the only guaranteed
    inclusion left**: a human's own *Let's play* may admit a candidate below the
    quality floor, where nothing the engine computes may. It is **flat and then
    absent** rather than decaying, because the age already crosses as evidence
    and a decay would charge for the same fact a second time, invisibly.

    ``pass_suppress_days`` hides somebody **and nobody can see it happening** — a
    pass is write-only and no route returns one. It is deck-only and
    one-directional: a search is a question about the city and a swipe may not
    edit the answer. A second pass means nothing more; where repetition leads is
    a Block, which is symmetric, reversible, and requires somebody to mean it.

    ``outstanding_cap_per_sport`` decides whether a player may **act**. It hides
    nobody and its bite is visible the instant it lands, which is why it is an
    ordinary ruleset row rather than one of the product numbers beside it.
    """

    ttl_days: int
    outstanding_cap_per_sport: int
    pass_suppress_days: int


@dataclass(frozen=True)
class IntentRules:
    """The six cells: the searcher's Mode against the candidate's declaration.

    Two modes by three declarations, and the arities differ on purpose
    (``docs/adr/0094``). **A declaration crosses as the machine code it already
    is** — a ``PlayIntent`` is a module's closed vocabulary and an engine may not
    import one — so the columns are keyed by string here and checked against the
    served vocabulary in the composition root, exactly as the tag ids are.

    **Intent is a weight and not a gate.** A directly opposite declaration reads
    the table's zero and takes no further charge: the zero is the whole answer,
    and a second dock would be a gate wearing a modifier's clothes. Not declaring
    at all is not a cell — the term stands down and renormalises away, which is
    how declaring against the searcher already costs strictly more than silence.
    """

    #: One row per mode, one cell per declaration. The rows must agree on their
    #: columns, so *the six cells* is a rectangle rather than two lists that
    #: happen to be the same length today.
    alignment: Mapping[SearchMode, Mapping[str, float]]
    #: Which declaration each mode reads as **its own kind of evening** — what
    #: makes the evidence's ``aligned`` a fact about two declarations rather than
    #: a threshold quietly read off a weight. It is a map and not a comparison of
    #: two enums' spellings, because the two enums are deliberately different
    #: types and a shared spelling is a coincidence the arithmetic must not lean
    #: on.
    same_evening: Mapping[SearchMode, str]


@dataclass(frozen=True)
class DistanceRules:
    """Where the distance curve starts costing, and where it reaches zero.

    Both are fractions of **the searcher's own ring**, never kilometres: a ten
    kilometre searcher and a fifty kilometre one have each said what far means to
    them, and a constant in kilometres would overrule one of them.

    ``full_marks_within`` is where the curve leaves 1.00 and ``zero_at`` is where
    it reaches 0.00, so the slope needs no third constant — it is the gap between
    them, and there is no way to move one of the two and leave the curve
    inconsistent. **Zero sits past the ring**, so a candidate standing exactly on
    it still scores: the hard cut at the ring is a gate, and a curve that reached
    zero there would charge for the gate twice.
    """

    full_marks_within: float
    zero_at: float


@dataclass(frozen=True)
class ExplanationRules:
    """What makes a term weak enough to be worth warning about.

    ``concerns[]`` is **the engine's own statement** that a term is genuinely
    weak, and it carries the term and nothing else. A client thresholding a value
    would be that judgement in TypeScript, written differently in every client;
    the breakdown beside it does carry every term's weight and value, so what
    stops a client re-deciding weakness is not that the numbers are withheld but
    that the engine has already answered — and the answer is a list a card can
    render without arithmetic.

    The judgement is over **points forgone**, ``weight × (1 − value)``, and not
    over the raw value, because weakness is a property of the pairing and not of
    the term: a low social vibe costs 3.7 points of a competitive match and 19.3
    of a friendly, and only one of those is worth a line on a card. Reading the
    renormalised weight makes the same term concern-worthy in one mode and not in
    the other for free, which is what *for fun* means.

    **The cap is the client's**: a card shows one, *Why 78?* shows all of them.
    Capping here would throw away exactly the rows that explain a low Fit on the
    screen built to explain it.
    """

    #: The bar, in points of a hundred. Anchored rather than picked: the smallest
    #: weight any term carries on the day-one basis is social vibe's 4.6
    #: competitive, so a bar under five would let a term raise a warning about a
    #: shortfall it could not produce even by reading zero.
    concern_points: int


@dataclass(frozen=True)
class Ruleset:
    """A named, dated, frozen dataset of every number the engine uses.

    **Immutable once released.** A change is a new name and a new release, never
    an edit to this one, so that a search recorded a year ago can still say what
    the numbers were when it ran.

    **The version stamp is never selected by the environment.** ``local``,
    ``development``, ``staging`` and ``production`` run the same numbers unless
    somebody deliberately releases a different named ruleset. A weight is not a
    setting — it is the product's opinion about who a player should meet, which
    is behaviour a domain test can observe.
    """

    version: str
    released_on: str
    modes: Mapping[SearchMode, ModeRules]
    intent: IntentRules
    tags: TagRules
    balance: BalanceRules
    distance: DistanceRules
    reliability: ReliabilityRules
    modifiers: ModifierRules
    liveness: LivenessRules
    group: GroupRules
    floors: Floors
    shape: ShapeRules
    relaxation: RelaxationRules
    telemetry: TelemetryRules
    interest: InterestRules
    explanation: ExplanationRules

    def emittable_evidence_kinds(self) -> frozenset[EvidenceKind]:
        """Every evidence variant this ruleset can put on the wire.

        A term carrying no weight in either mode never scores and so never
        produces evidence; every other term can. This is the set the contract
        check reads: **a ruleset that can emit a kind the wire union does not
        publish fails to load**, because the client generates an exhaustive
        renderer per variant and a kind it has never seen renders as nothing at
        all — indistinguishable, on the card, from a term that stood down.

        Note that *stands down on day one* is not the same as *carries no
        weight*: reliability is weighted here and simply has no provider yet, so
        its variant is published and unfilled rather than absent.
        """

        return frozenset(
            term.evidence_kind
            for term in Term
            # Indexed rather than `.get`: `validate_ruleset` has already proved
            # every mode weights every term, so a default here would be a second
            # answer to a question the validator settled.
            if any(rules.weights[term] != 0 for rules in self.modes.values())
        )


def validate_ruleset(ruleset: Ruleset) -> Ruleset:
    """Refuse a ruleset that cannot be believed. Returns it when it can.

    Raises ``InvariantViolated``, which nothing catches — a malformed ruleset is
    a bug that shipped, and the only correct response is that the process does
    not start. **There is deliberately no fallback to defaults**: a matcher that
    silently falls back is one that quietly A/B tests against itself, and the
    previous ruleset keeps serving because the old pods are still up.

    Everything checkable **without a module** is checked here. The tag ids are
    strings to this layer, so *are these real tags* and *is the familiarity map
    exhaustive over ``WHY_YOU_ARE_HERE``* run in the composition root beside the
    evidence-kind check, where the platform's vocabularies are visible.
    """

    _validate_stamp(ruleset)
    for mode, rules in ruleset.modes.items():
        _validate_mode(mode, rules)
    invariant(
        set(ruleset.modes) == set(SearchMode),
        f"a ruleset must weight every search mode: "
        f"{sorted(m.value for m in ruleset.modes)}",
    )
    _validate_intent(ruleset.intent)
    _validate_tags(ruleset.tags)
    _validate_balance(ruleset.balance)
    _validate_distance(ruleset.distance)
    _validate_reliability(ruleset.reliability)
    _validate_modifiers(ruleset.modifiers)
    _validate_liveness(ruleset.liveness)
    _validate_group(ruleset.group)
    _validate_floors(ruleset.floors, ruleset.shape)
    _validate_relaxation(ruleset.relaxation)
    _validate_telemetry(ruleset.telemetry)
    _validate_interest(ruleset.interest)
    _validate_explanation(ruleset.explanation)
    return ruleset


def _validate_stamp(ruleset: Ruleset) -> None:
    """The name carries the date, and the date must agree with it.

    ``2026.08.26-a`` is a date and a letter, and the letter is what makes a
    second release on one day a different dataset rather than an edit to the
    first. Two spellings of one fact can disagree, so the pair is checked rather
    than trusted.
    """

    parts = ruleset.version.split("-")
    invariant(
        len(parts) == 2 and parts[1].isalpha() and parts[1].islower(),
        f"a ruleset version is a date and a lower-case letter: {ruleset.version!r}",
    )
    dotted = parts[0].split(".")
    invariant(
        len(dotted) == 3
        and len(dotted[0]) == 4
        and len(dotted[1]) == 2
        and len(dotted[2]) == 2
        and all(piece.isdigit() for piece in dotted),
        f"a ruleset version opens with YYYY.MM.DD: {ruleset.version!r}",
    )
    invariant(
        ruleset.released_on == "-".join(dotted),
        f"a ruleset's date disagrees with its name: "
        f"{ruleset.released_on!r} against {ruleset.version!r}",
    )


def _validate_mode(mode: SearchMode, rules: ModeRules) -> None:
    _validate_weights(
        rules.weights,
        tuple(Term),
        f"{mode.value} term weights",
    )
    _validate_weights(
        rules.strand_weights,
        tuple(ReliabilityStrand),
        f"{mode.value} reliability strand weights",
    )
    invariant(
        rules.level_tolerance > 0,
        f"{mode.value} level tolerance: {rules.level_tolerance}",
    )
    if rules.tag_stuffing_margin is not None:
        tags = rules.weights[Term.PLAYING_STYLE] + rules.weights[Term.SOCIAL_VIBE]
        ceiling = (
            rules.weights[Term.LEVEL_FIT]
            * rules.tag_stuffing_margin
            / rules.level_tolerance
        )
        invariant(
            tags < ceiling,
            f"{mode.value}: the tag terms together ({tags}) can outrank a "
            f"noticeably better level match ({ceiling:.2f})",
        )
    if rules.free_band is not None:
        # The free band is the flat bottom of the curve, so a band at or past the
        # tolerance would leave the curve no range to fall through and divide by
        # zero on the way.
        invariant(
            0 <= rules.free_band < rules.level_tolerance,
            f"{mode.value} free band {rules.free_band} is not inside its "
            f"tolerance {rules.level_tolerance}",
        )


def _validate_weights(
    weights: Mapping[_Weighted, int], expected: tuple[_Weighted, ...], subject: str
) -> None:
    """Every member weighted, none negative, summing to a hundred.

    Exhaustiveness first: a missing key would renormalise away silently and read
    as a term that stood down, which is the one thing this system is careful to
    keep distinguishable from a term that scored badly.
    """

    invariant(
        set(weights) == set(expected),
        f"{subject}: expected {sorted(str(e) for e in expected)}, "
        f"got {sorted(str(k) for k in weights)}",
    )
    invariant(
        all(weight >= 0 for weight in weights.values()),
        f"{subject}: a negative weight in {dict(weights)!r}",
    )
    total = sum(weights.values())
    invariant(
        total == WEIGHT_TOTAL,
        f"{subject}: sums to {total}, not {WEIGHT_TOTAL}",
    )


def _validate_tags(tags: TagRules) -> None:
    invariant(0 < tags.phi < 1, f"tag phi: {tags.phi}")
    invariant(
        0 < tags.complement_strength <= 1,
        f"tag complement strength: {tags.complement_strength}",
    )
    invariant(tags.clash_cap > 0, f"clash cap: {tags.clash_cap}")
    invariant(
        set(tags.clash_severities) == set(ClashSeverity),
        f"every clash grade needs a severity: "
        f"{sorted(g.value for g in tags.clash_severities)}",
    )
    invariant(
        all(
            0 < severity <= tags.clash_cap
            for severity in tags.clash_severities.values()
        ),
        f"a clash severity is outside (0, cap]: {dict(tags.clash_severities)!r}",
    )
    invariant(
        tags.clash_severities[ClashSeverity.MILD]
        < tags.clash_severities[ClashSeverity.REAL],
        f"a mild clash is not milder than a real one: {dict(tags.clash_severities)!r}",
    )

    matched: set[str] = set()
    scopes: dict[tuple[str, str], set[tuple[SearchMode, Seat]]] = {}
    for row in tags.relationship_matrix:
        _validate_relationship(row, tags.complement_strength)
        if row.kind is TagRelationshipKind.MATCH:
            invariant(
                row.a not in matched,
                f"a tag takes more than one match row: {row.a}",
            )
            matched.add(row.a)
        taken = scopes.setdefault(row.pair, set())
        overlap = taken & row.scopes()
        # Two rows about one pair are how "far worse as partners than as
        # opponents" is said without a second severity field. Overlapping scopes
        # would make them two answers to one question instead.
        invariant(
            not overlap,
            f"two matrix rows overlap on {row.pair}: "
            f"{sorted((m.value, s.value) for m, s in overlap)}",
        )
        taken |= row.scopes()


def _validate_relationship(row: TagRelationship, default_strength: float) -> None:
    invariant(bool(row.modes), f"a matrix row scopes no mode: {row.pair}")
    invariant(bool(row.seats), f"a matrix row scopes no seat: {row.pair}")
    invariant(
        len(set(row.modes)) == len(row.modes) and len(set(row.seats)) == len(row.seats),
        f"a matrix row repeats a mode or a seat: {row.pair}",
    )
    if row.kind is TagRelationshipKind.MATCH:
        # A match is a count, so it carries no strength; and it is one tag
        # against itself, because a match *is* two people choosing one string.
        invariant(
            row.a == row.b, f"a match row is not a tag against itself: {row.pair}"
        )
        invariant(row.strength is None, f"a match row carries a strength: {row.pair}")
        invariant(row.severity is None, f"a match row carries a severity: {row.pair}")
        return
    invariant(
        row.a != row.b, f"a {row.kind.value} row is a tag against itself: {row.a}"
    )
    if row.kind is TagRelationshipKind.COMPLEMENT:
        strength = invariant(
            row.strength, f"a complement row carries no strength: {row.pair}"
        )
        # Never below the default, because a complement product is not confident
        # about should not be a row; never above parity, because parity is the
        # most an editorial claim can be worth against two people's agreement.
        invariant(
            default_strength <= strength <= 1.0,
            f"complement strength {strength} is outside "
            f"[{default_strength}, 1.0]: {row.pair}",
        )
        invariant(
            row.severity is None,
            f"a complement row carries a severity: {row.pair}",
        )
        return
    invariant(row.severity is not None, f"a clash row carries no severity: {row.pair}")
    invariant(row.strength is None, f"a clash row carries a strength: {row.pair}")


def _validate_intent(intent: IntentRules) -> None:
    invariant(
        set(intent.alignment) == set(SearchMode),
        f"a ruleset must read intent in every mode: "
        f"{sorted(m.value for m in intent.alignment)}",
    )
    rows = list(intent.alignment.values())
    invariant(all(row for row in rows), "a mode reads intent against no declaration")
    # The table is *six cells* and not two lists that happen to be the same
    # length today: a declaration priced in one mode and absent from the other is
    # a candidate whose Fit depends on which tab the searcher is on for a reason
    # nobody wrote down.
    columns = {frozenset(row) for row in rows}
    invariant(
        len(columns) == 1,
        f"the two modes price different declarations: {[sorted(row) for row in rows]}",
    )
    invariant(
        all(0.0 <= cell <= 1.0 for row in rows for cell in row.values()),
        f"an intent cell outside [0, 1]: {[dict(row) for row in rows]!r}",
    )
    invariant(
        set(intent.same_evening) == set(SearchMode),
        f"every mode must name the declaration it reads as its own: "
        f"{sorted(m.value for m in intent.same_evening)}",
    )
    for mode, declaration in intent.same_evening.items():
        invariant(
            declaration in intent.alignment[mode],
            f"{mode.value} reads {declaration} as its own evening and does not "
            f"price it",
        )
    # Two modes reading the same declaration as their own would make one of them
    # unreachable as an alignment and the other's zero unwritable.
    invariant(
        len(set(intent.same_evening.values())) == len(SearchMode),
        f"two modes claim the same declaration: {dict(intent.same_evening)!r}",
    )


def _validate_distance(distance: DistanceRules) -> None:
    invariant(
        0 < distance.full_marks_within < distance.zero_at,
        f"the distance curve does not descend: full marks within "
        f"{distance.full_marks_within}, zero at {distance.zero_at}",
    )
    # The hard cut at the ring is a gate. A curve reaching zero at or inside it
    # would charge for that gate a second time, in a term.
    invariant(
        distance.zero_at > 1,
        f"the distance curve reaches zero inside the ring: {distance.zero_at}",
    )


def _validate_explanation(explanation: ExplanationRules) -> None:
    invariant(
        0 < explanation.concern_points <= WEIGHT_TOTAL,
        f"a concern bar outside (0, {WEIGHT_TOTAL}]: {explanation.concern_points}",
    )


def _validate_balance(balance: BalanceRules) -> None:
    invariant(
        balance.pct_min < balance.pct_max,
        f"balance clamp: {balance.pct_min}–{balance.pct_max}",
    )
    invariant(
        balance.mu_coefficient > 0 and balance.sigma_coefficient > 0,
        f"balance coefficients: {balance.mu_coefficient}, {balance.sigma_coefficient}",
    )
    invariant(
        0.0 < balance.stronger_partner_share < 0.5,
        "the stronger partner sets less than half a side, or the claim the "
        f"share exists to make is not being made: {balance.stronger_partner_share}",
    )


def _validate_reliability(reliability: ReliabilityRules) -> None:
    # Exhaustive over the vocabulary, checked here rather than trusted, because a
    # strand whose bar was never set would enter a reading on one observation and
    # nothing else in the pipeline would notice.
    invariant(
        set(reliability.min_observations) == set(ReliabilityStrand),
        "reliability minimum observations must name every strand: "
        f"{sorted(strand.value for strand in reliability.min_observations)}",
    )
    for strand, minimum in reliability.min_observations.items():
        invariant(
            minimum >= 1,
            f"reliability minimum observations for {strand.value}: {minimum}",
        )
    invariant(
        reliability.horizon_days >= 1,
        f"reliability horizon days: {reliability.horizon_days}",
    )
    invariant(
        0 <= reliability.published_score_bar <= 100,
        f"reliability published score bar: {reliability.published_score_bar}",
    )


def _validate_modifiers(modifiers: ModifierRules) -> None:
    invariant(modifiers.budget > 0, f"modifier budget: {modifiers.budget}")
    invariant(
        set(modifiers.ranges) == set(BUDGETED_MODIFIERS),
        f"the budgeted modifier roster is "
        f"{sorted(m.value for m in BUDGETED_MODIFIERS)}, got "
        f"{sorted(m.value for m in modifiers.ranges)}",
    )
    for modifier, points in modifiers.ranges.items():
        invariant(
            points.minimum <= points.maximum,
            f"{modifier.value} range: {points.minimum}…{points.maximum}",
        )
    familiarity = modifiers.familiarity
    invariant(
        familiarity.half_life_days >= 1,
        f"familiarity half-life days: {familiarity.half_life_days}",
    )
    invariant(
        0 < familiarity.depth_phi < 1,
        f"familiarity depth phi: {familiarity.depth_phi}",
    )
    invariant(
        0 <= familiarity.default_lean <= 1,
        f"familiarity default lean: {familiarity.default_lean}",
    )
    if modifiers.newcomer_absorption_cap is not None:
        invariant(
            modifiers.newcomer_absorption_cap >= 1,
            f"newcomer absorption cap: {modifiers.newcomer_absorption_cap}",
        )


def _validate_liveness(liveness: LivenessRules) -> None:
    invariant(
        liveness.offset_minimum < 0 < liveness.offset_maximum,
        f"liveness offset bounds: {liveness.offset_minimum}…{liveness.offset_maximum}",
    )
    invariant(
        set(liveness.signals) == set(LivenessSignal),
        f"every liveness signal needs a bound: "
        f"{sorted(s.value for s in liveness.signals)}",
    )
    for signal, bound in liveness.signals.items():
        invariant(
            bound.points.minimum <= bound.points.maximum,
            f"{signal.value} bound: {bound.points.minimum}…{bound.points.maximum}",
        )
        invariant(
            liveness.offset_minimum <= bound.points.minimum
            and bound.points.maximum <= liveness.offset_maximum,
            f"{signal.value} reaches past the offset's own bounds: "
            f"{bound.points.minimum}…{bound.points.maximum}",
        )
    invariant(liveness.move_notice > 0, f"move notice: {liveness.move_notice}")
    invariant(
        liveness.asymmetry_tolerance > 0,
        f"asymmetry tolerance: {liveness.asymmetry_tolerance}",
    )
    invariant(
        0 < liveness.asymmetry_slope <= 1,
        f"asymmetry slope: {liveness.asymmetry_slope}",
    )

    interest = liveness.signals[LivenessSignal.INTEREST_RECEIVED]
    # A human's own ask outranks the engine's opinion of that human's
    # popularity: a player who said *Let's play* to you still surfaces net
    # positive however full their inbox is.
    load = liveness.signals[LivenessSignal.CHALLENGE_LOAD]
    invariant(
        -load.points.minimum < interest.points.maximum,
        f"a full inbox ({load.points.minimum}) sinks a candidate past their own "
        f"*Let's play* ({interest.points.maximum})",
    )
    invariant(
        interest.printable,
        "the interest lift must print: a player is owed the reason they were "
        "shown somebody who asked for them",
    )
    invariant(
        liveness.signals[LivenessSignal.NEWCOMER_LIFT].printable,
        "the newcomer lift must print: *they're new* is a sentence the product "
        "wants said, where *nobody has been shown them* is not",
    )
    # Last, because the rungs are about how a bound is *reached* and everything
    # above is about the bound itself: a ruleset that widened the sink past the
    # interest lift owes that answer before it owes an answer about its ladder.
    _validate_challenge_load(liveness)


def _validate_challenge_load(liveness: LivenessRules) -> None:
    """The sink's three rungs: deeper costs more, and the deepest reaches the bound.

    ``docs/adr/0125`` adopted §14.4's thresholds **whole**, so what is checked
    here is that they are still a ladder and still the same ladder the signal's
    own bound describes. The last rung must reach the bound exactly: a sink that
    stopped short would leave a bound nothing can produce, which is the shape of
    a number somebody widened and then forgot to spend.
    """

    rungs = liveness.challenge_load_rungs
    bound = liveness.signals[LivenessSignal.CHALLENGE_LOAD].points
    invariant(bool(rungs), "a full-inbox sink with no rungs in it")
    invariant(
        len({rung.prints for rung in rungs}) == len(rungs),
        f"two rungs of the full-inbox sink print the same code: "
        f"{[rung.prints.value for rung in rungs]}",
    )
    previous: ChallengeLoadRung | None = None
    for rung in rungs:
        invariant(rung.at_least >= 1, f"a full-inbox rung at {rung.at_least} open")
        invariant(
            bound.minimum <= rung.points <= bound.maximum,
            f"a full-inbox rung at {rung.points} reaches past the signal's own "
            f"bound {bound.minimum}…{bound.maximum}",
        )
        if previous is not None:
            invariant(
                rung.at_least > previous.at_least,
                f"the full-inbox rungs are not deepest last: {previous.at_least} "
                f"then {rung.at_least}",
            )
            invariant(
                rung.points < previous.points,
                f"a deeper inbox costs no more than a shallower one: "
                f"{previous.points} then {rung.points}",
            )
        previous = rung
    invariant(
        rungs[-1].points == bound.minimum,
        f"the deepest rung sinks {rungs[-1].points} where the signal is bounded "
        f"at {bound.minimum}: a bound nothing can reach",
    )


def _validate_group(group: GroupRules) -> None:
    invariant(
        set(group.weights) == set(SearchMode),
        f"the group objective must weight every search mode: "
        f"{sorted(m.value for m in group.weights)}",
    )
    for mode, weights in group.weights.items():
        _validate_weights(weights, tuple(GroupTerm), f"{mode.value} group weights")
    invariant(group.k >= 1, f"group candidate cap: {group.k}")
    # The one number that can destroy the line-up latency budget, and the reason
    # it may not ship as "just configuration".
    invariant(
        group.k <= K_CEILING,
        f"group candidate cap {group.k} exceeds the engine-side ceiling {K_CEILING}",
    )


def _validate_floors(floors: Floors, shape: ShapeRules) -> None:
    invariant(
        0 < floors.quality_floor < 100,
        f"quality floor: {floors.quality_floor}",
    )
    invariant(floors.min_shortlist >= 1, f"minimum shortlist: {floors.min_shortlist}")
    invariant(
        0 < floors.minimum_evidence_fraction <= 1,
        f"minimum evidence fraction: {floors.minimum_evidence_fraction}",
    )
    invariant(shape.shortlist_max >= 1, f"shortlist maximum: {shape.shortlist_max}")
    invariant(shape.deck_deal_max >= 1, f"deck deal maximum: {shape.deck_deal_max}")
    # A shortlist that stopped below the length that decides whether the offers
    # are computed would offer a widen on every search that filled it.
    invariant(
        floors.min_shortlist <= shape.shortlist_max,
        f"the shortlist stops at {shape.shortlist_max}, below the "
        f"{floors.min_shortlist} that decides whether offers are computed",
    )


def _validate_relaxation(relaxation: RelaxationRules) -> None:
    invariant(
        RelaxationRung.TIMES not in relaxation.radius_multipliers,
        "the times rung is not a radius, and carries no multiplier",
    )
    # Read off the ladder rather than off the mapping, so a rung the enum gained
    # and the ruleset did not is a refusal rather than a rung that silently never
    # offers anything.
    radius_rungs = [rung for rung in RelaxationRung if rung is not RelaxationRung.TIMES]
    invariant(
        set(radius_rungs) == set(relaxation.radius_multipliers),
        f"every radius rung needs a multiplier: "
        f"{[r.value for r in radius_rungs]} against "
        f"{sorted(r.value for r in relaxation.radius_multipliers)}",
    )
    multipliers = [relaxation.radius_multipliers[rung] for rung in radius_rungs]
    invariant(
        all(multiplier > 1 for multiplier in multipliers),
        f"a radius rung that does not widen: {multipliers}",
    )
    # A rung that reaches no further than the one before it is a second offer of
    # the same search, which the ladder already refuses to print twice.
    invariant(
        all(a < b for a, b in zip(multipliers, multipliers[1:], strict=False)),
        f"the radius rungs do not widen in order: {multipliers}",
    )


def _validate_telemetry(telemetry: TelemetryRules) -> None:
    invariant(
        telemetry.near_miss_recorded >= 1,
        f"near-miss band depth: {telemetry.near_miss_recorded}",
    )


def _validate_interest(interest: InterestRules) -> None:
    invariant(interest.ttl_days >= 1, f"interest TTL days: {interest.ttl_days}")
    invariant(
        interest.pass_suppress_days >= 1,
        f"pass suppression days: {interest.pass_suppress_days}",
    )
    invariant(
        interest.outstanding_cap_per_sport >= 1,
        f"outstanding interest cap: {interest.outstanding_cap_per_sport}",
    )
