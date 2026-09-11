"""The search record: what one engine invocation is, once it has happened.

``docs/adr/0104`` makes every invocation a durable, unexpiring row, written in the
request's own transaction and **committed before the response returns — if it
fails, the search fails.** The ``search_id`` *is* the answer's identity, which is
why nothing here is optional for convenience and why there is no path that
returns a shortlist without one.

**Every fact is search-time and cannot be reconstructed afterwards. There is no
backfill** (``search-telemetry.md``). A day without a column is a day of
permanently missing denominator, for every rate the engine is judged by, forever.

**Three layers, and the third never leaves the building.** Counters on the search
row, the returned rows in full, and the best ``NEAR_MISS_RECORDED`` that did not
clear. *A player may ask why somebody was shown; nobody may ask who was
withheld* — so layer 3 is engine-internal and no route returns it, to anyone.

**The empty-result rate is a guardrail metric and never a target, and it is
reported only paired with the return rate** (``docs/adr/0099`` §7 — Kohavi's and
Spotify's vocabulary, used deliberately so the position stops reading as
idiosyncratic). Both halves are computable from these rows and neither is
computed here: there is no metrics surface in this backend, and inventing one
would be inventing the reporting rule too. What the rule binds is whoever builds
that surface — ``n_returned == 0`` over searches run is **not** a number that may
be shown, alerted on or optimised alone, and any change to ``QUALITY_FLOOR``
lands as an ADR for which the empty-result rate is never sufficient grounds on
its own.

**Two columns are recorded and read by nothing, deliberately.**
``their_slot_count`` and ``days_away`` had their consumers struck by
``docs/adr/0120``, and ``liveness_signals`` stores the **raw inputs** and never
the offset for the same reason: *a strike that is not recorded becomes
irreversible by accident*, and an offset is a function of the ruleset's bounds,
so storing it would make a bounds change undiffable.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Mapping, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport, invariant
from app.modules.matchmaking.domain.ports import AtStake
from app.modules.matchmaking.domain.relaxation import Rung, RungOffer
from app.modules.player_profile.domain.availability import Window
from app.modules.player_profile.domain.photos import PhotoReviewDecision
from app.modules.player_profile.domain.play_intent import PlayIntent


class SearchSurface(str, Enum):
    """Which terminal stage ran. Four values, and pooling their rates is how
    every number the engine is judged by becomes meaningless — ``FILL_SEATS`` is
    not even optimising for the searcher.

    ``SHORTLIST`` and ``DECK`` can be written today; the two line-up surfaces
    arrive with their route. All four were declared before any of them could be
    written, because ``surface`` is a stored column and a vocabulary that grows
    one value per ticket is a vocabulary whose old rows cannot be read against
    the new ones.
    """

    SHORTLIST = "SHORTLIST"
    LINEUP = "LINEUP"
    DECK = "DECK"
    FILL_SEATS = "FILL_SEATS"


class SearchInitiation(str, Enum):
    """Who asked. **Orthogonal to the surface**, which is why it is a second
    column rather than a fifth value: an engine-pushed deck card is ``DECK`` +
    ``ENGINE``.

    It is also the only thing the proposals opt-in reads. That gate *gates the
    push, not the person*, so a player who opted out of proposals is a full
    candidate in a search a human ran.
    """

    HUMAN = "HUMAN"
    ENGINE = "ENGINE"


class CandidateBand(str, Enum):
    """Which layer a recorded candidate belongs to.

    ``RETURNED`` is what the response carried. ``NEAR_MISS`` is the best few that
    did not clear, and it is **engine-internal** — no route returns a row in this
    band, to anybody, ever.
    """

    RETURNED = "RETURNED"
    NEAR_MISS = "NEAR_MISS"


class WithheldReason(str, Enum):
    """Why a scored candidate was not shown. ``NEAR_MISS`` rows only.

    The two are kept apart because they are different facts about the product:
    *the bar is in the right place and this pairing is poor* against *we do not
    know enough about this person to say*. Collapsed, the floor's own falsifier
    would be a mixture of two populations.
    """

    BELOW_FLOOR = "BELOW_FLOOR"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class InclusionReason(str, Enum):
    """Why this candidate is in the answer at all. **The store is open where the
    wire is closed** (``the-two-contracts.md`` §4).

    All three are kept here; only ``INTEREST_LIFT`` crosses the wire, because it
    is the only one that **admits** anybody. ``NEWCOMER_WINDOW`` reorders and
    ships to the client as a Liveness reason instead; ``ZERO_EXPOSURE`` never
    crosses at all — *you are seeing this person because nobody has been shown
    them all week* is a third party's unpopularity, and the searcher is owed no
    version of it.
    """

    INTEREST_LIFT = "INTEREST_LIFT"
    NEWCOMER_WINDOW = "NEWCOMER_WINDOW"
    ZERO_EXPOSURE = "ZERO_EXPOSURE"


class SortOption(str, Enum):
    """The re-sorts a client may offer over rows it already holds.

    **Server-driven, and a sort that would reorder nothing is not drawn.** A
    client deriving offerability from ``degraded_terms`` would be encoding a
    sort-to-term mapping, which is the objection that promoted ``distance_km``
    out of the distance evidence in the first place.

    ``MOST_RELIABLE`` reads the **published** Player Score, and it is offered on
    a search whose candidates have one and withheld on a search whose candidates
    do not — a fact about *that* search, re-derived per search rather than
    hardcoded. Most people have no record yet, so most searches still do not draw
    it, and that is the derivation working rather than a gap. ``EVENEST`` reads
    ``would_be_forecast``, which no shortlist carries.
    """

    BEST_FIT = "BEST_FIT"
    CLOSEST = "CLOSEST"
    EVENEST = "EVENEST"
    MOST_RELIABLE = "MOST_RELIABLE"


@final
@dataclass(frozen=True, slots=True)
class PoolDescription:
    """What the searcher is being told about the pool this answer came from.

    Written on **every** search and not only on empty ones: a thin pool and a
    broken floor are indistinguishable without it.

    ``post_gate`` is fixed true and travels anyway, because the count is
    deliberately the one *after* the gates. ``docs/adr/0096``'s mutual gender
    gate makes a pre-gate count and a post-gate count differ **per searcher**,
    and the delta would be readable — which is precisely what a mutual gate must
    never be.
    """

    sport: Sport
    radius_km_used: int
    players_in_range: int
    window: Window
    post_gate: bool = True

    def __post_init__(self) -> None:
        invariant(self.post_gate, "a pool description that is not post-gate")
        invariant(
            self.players_in_range >= 0,
            f"a pool of {self.players_in_range} players",
        )


@final
@dataclass(frozen=True, slots=True)
class StagedCounts:
    """The pool, counted at every stage. **None of it crosses the wire.**

    ``n_generated``, ``excluded_by_gate``, ``n_scored`` and ``n_cleared_floor``
    live on the record, where an analyst reads them. The client gets the pool
    description and nothing else.

    ``excluded_by_gate`` is a histogram over the **ten** gate codes, counts only:
    no candidate is named at this layer.
    """

    n_generated: int
    excluded_by_gate: Mapping[str, int]
    n_scored: int
    n_cleared_floor: int
    n_returned: int
    n_near_miss_recorded: int

    def __post_init__(self) -> None:
        for name, count in (
            ("n_generated", self.n_generated),
            ("n_scored", self.n_scored),
            ("n_cleared_floor", self.n_cleared_floor),
            ("n_returned", self.n_returned),
            ("n_near_miss_recorded", self.n_near_miss_recorded),
        ):
            invariant(count >= 0, f"{name} counted {count}")


@final
class GameResult(str, Enum):
    """How one counted game went for one of the people who played it.

    **The matcher's own word for it**, as ``PairwiseOutcome`` is for the
    familiarity term's tallies, and mapped from ``games``' own ``Outcome`` at the
    adapter that reads it. Two values and never a third: a game with no agreed
    result produces no result for anybody, and absence is spelled by not being in
    the run at all (``docs/adr/0137``).

    It is here rather than beside the port that answers it because a run of form
    is **recorded**, and every other word a row is written in is declared in this
    file.
    """

    WIN = "WIN"
    LOSS = "LOSS"


#: How long the run of form on a card is — the matcher's own spelling of what
#: ``games``' ``RECENT_RESULTS`` answers. Two contexts, two spellings, because
#: ``games`` may not import the matcher; the adapter between them refuses to load
#: if they ever disagree, which is the only thing that keeps a second number from
#: being silent. It sits beside :class:`GameResult` because the run is a
#: **recorded** thing and this file declares every word a row is written in.
LAST_FIVE = 5


@final
@dataclass(frozen=True, slots=True)
class RecordedCard:
    """The player card **as it was shown**, kept on the row that showed it.

    The card is assembled outside the engine (``docs/adr/0107``) from two
    sources — the index row and ``users`` — and neither of them remembers what it
    said an hour ago. A read-back that re-read them would answer a *different*
    search: a nickname changed since, a Level that has moved, an area the player
    has left. So the card is recorded here, and the round trip reproduces the
    answer that was given rather than the one that would be given now.

    **A photo id, and never the URL beside it on the wire.** A presigned link is
    dead within the hour and this row is kept for ever, so what is stored is the
    id; ``player_card.photo_url`` is signed over it per response and written down
    nowhere — the one difference the round-trip assertion allows itself
    (``docs/adr/0107``, ``docs/adr/0109``).

    **And the record block, recorded for the reason the rest of the card is.** A
    Player Score moves, a run of form gains a game and a counted-game count only
    ever grows, so a read-back that went and asked would answer a *different*
    search — the shape ``docs/adr/0109`` refuses. What was shown is what is
    stored.

    **Its three fields are required like every other one here, and that is the
    point of them.** Two of the three are absent on almost every card, which is
    exactly why a default would be wrong: an absence nobody stated and an absence
    the assembler decided on would be one value, and this is the type whose whole
    job is that a card cannot be stored half-assembled.
    """

    nickname: str
    #: ``None`` when they had no photo, and the client drew the generated court
    #: poster. **Not a measured zero** — there is no photo to point at.
    photo_id: UUID | None
    #: What the on-court check had concluded about that photograph when this
    #: search ran, or ``None`` for *nobody looked* (``docs/adr/0138``).
    #:
    #: **Recorded rather than re-read**, for the reason every other fact on this
    #: card is: the verdict is user metadata on an object, so a read-back that
    #: went and asked would pay a store round trip per row to answer a *different*
    #: search — one where the re-review backfill has since been round. The
    #: shield the read-back draws is the shield that was drawn.
    review: PhotoReviewDecision | None
    area_code: str
    social_tags: tuple[str, ...]
    #: Their Level as RacketSkill published it *then*.
    level: float
    band: str
    #: The **likely range** that was shown beside the Level — μ ± σ, as
    #: ``rating`` published it and as the index row carried it. Two floats and
    #: never ``None``: a card that stated a Level always stated how sure of it
    #: the platform was, so an absence here would be a card this build cannot
    #: have shown.
    range_low: float
    range_high: float
    #: The **published** Player Score they were shown with, out of a hundred —
    #: the figure their own profile prints, read through ``PlayerScoreQuery``
    #: and never re-derived (``docs/adr/0140``).
    #:
    #: ``None`` where the player has no record at all, which is **omitted** on
    #: the wire and is not a nought: somebody nothing has ever been arranged for
    #: has not failed to turn up. It is also what lets *Most reliable* sort them
    #: last on a read-back rather than first — ``distance_km``'s rule, for
    #: ``distance_km``'s reason.
    player_score: int | None
    #: How many counted games they had played, friendlies excluded. ``None``
    #: where they had none — the same absence, and never a measured ``0``, which
    #: is the one place this card disagrees with what ``games`` answers its own
    #: callers.
    counted_games: int | None
    #: The last five counted results, **oldest to newest**. Empty where nothing
    #: of theirs had been counted and agreed, and **never padded** — fewer than
    #: five is a real answer and the card draws the gap.
    last_five: tuple[GameResult, ...]


@final
@dataclass(frozen=True, slots=True)
class SearchCandidateRecord:
    """One recorded candidate, in either band.

    ``terms`` is **deliberately opaque**: it is stamped with ``ruleset_version``
    and its shape is allowed to change between rulesets, which is exactly what a
    relational schema would fight. ``degraded_terms`` is lifted out of it because
    it is the renormalisation basis — without it a Fit is uninterpretable a year
    later — and because a per-term ``NoEvidence`` rate has to be an array query
    rather than a blob scan.

    ``degraded_reasons`` is **index-aligned with it and never folded into it**. A
    read-back never recomputes, so whose gap each stood-down term was has to be
    on the row; widening ``degraded_terms`` into pairs would spend exactly the
    queryability it was lifted out of the blob to buy.
    """

    band: CandidateBand
    position: int
    player_id: UUID
    fit: float
    terms: tuple[Mapping[str, Any], ...]
    degraded_terms: tuple[str, ...]
    #: Whose gap each of those was, **positionally**: one code per entry above,
    #: in the same order, which the invariant below refuses to let drift.
    #: ``missing_terms`` is the same fact from the evidence gate's side and the
    #: two may not disagree either —
    #: ``tests/unit/test_run_shortlist_search.py`` asserts it is exactly the
    #: non-``NOT_YET_ON_THIS_PLATFORM`` subset, because two columns answering
    #: *whose gap is this* are two columns that can drift.
    degraded_reasons: tuple[str, ...]
    modifiers: tuple[Mapping[str, Any], ...]
    liveness_reasons: tuple[str, ...]
    #: The **raw input** per signal, never the offset it produced.
    liveness_signals: Mapping[str, Any]
    #: Grid cells both players ticked. With ``search.searcher_slot_count`` this
    #: **is** the availability term, so the value in ``terms`` is checkable
    #: against its own inputs.
    shared_count: int
    #: The candidate's ticked cells. **Nothing reads it** — recorded so that a
    #: ruleset re-admitting the struck factor is re-derivable over the whole
    #: corpus.
    their_slot_count: int
    #: Days to the next shared slot. ``None`` means nothing is shared, which is
    #: not ``0``. Also unread, and recorded for the same reason.
    days_away: int | None
    inclusion_reason: InclusionReason | None
    withheld_reason: WithheldReason | None
    missing_terms: tuple[str, ...]
    reliability_penalty_applied: bool
    #: Whether the penalty is what put them below the floor — **docked** versus
    #: **docked out**.
    reliability_penalty_decisive: bool
    #: The terms the engine judged genuinely weak, over **points forgone**. Kept
    #: as codes rather than re-derived on a read-back: the judgement belongs to
    #: the ruleset this row is stamped with, and re-deriving it under a later one
    #: would answer a question about a search that never ran.
    concerns: tuple[str, ...]
    #: Whole kilometres, as the wire carried it. ``None`` when the distance term
    #: stood down — which is **omitted** on the wire and not a zero, and is what
    #: lets a stood-down row sort last instead of first.
    distance_km: int | None
    #: The card as it was shown. Present on a ``RETURNED`` row and absent on a
    #: near miss, which was never shown to anybody — a biconditional, so *a
    #: returned row with nobody on it* is unrepresentable rather than merely
    #: unwritten, and the renderer's ``None`` branch is unreachable.
    card: RecordedCard | None
    #: What a counted game would have been worth **then**. ``None`` in for fun,
    #: where a counted result is meaningless rather than unavailable.
    at_stake: AtStake | None
    #: Whether this pairing had a pass whose suppression had already **lapsed** —
    #: that is, whether this card is a **re-show**. Set on a dealt card and
    #: ``None`` everywhere else, which is a biconditional rather than a default:
    #: a shortlist row is not a card, and a near miss was dealt to nobody.
    #:
    #: It reads the **durable pass record**, never the suppression cache: a
    #: lapsed key leaves no trace the pair was ever passed, so at the exact
    #: moment the re-show happens the fact that makes it one has expired. Without
    #: this column only plain pass rate is computable, never *pass rate on
    #: re-shown profiles* — the only falsifier ``PASS_SUPPRESS`` has
    #: (``docs/adr/0128``).
    suppression_lapsed: bool | None = None

    def __post_init__(self) -> None:
        invariant(self.position >= 1, f"a position below one: {self.position}")
        invariant(
            (self.withheld_reason is None) == (self.band is CandidateBand.RETURNED),
            f"a {self.band.value} row with withheld reason {self.withheld_reason}",
        )
        invariant(
            (self.card is not None) == (self.band is CandidateBand.RETURNED),
            f"a {self.band.value} row with card {self.card}",
        )
        # The two halves of the renormalisation basis are one fact in two
        # columns, and a row where they had drifted is a basis nobody can read.
        # Refused here rather than at the wire, where it would surface as a
        # five-hundred on a read-back of a row that was already written wrong —
        # and rather than as a check constraint, which would have to be spelled
        # twice for two dialects that store these arrays differently.
        invariant(
            len(self.degraded_terms) == len(self.degraded_reasons),
            f"{len(self.degraded_terms)} degraded terms and "
            f"{len(self.degraded_reasons)} reasons beside them",
        )


@final
class CombinationBand(str, Enum):
    """Which of layer 4's **two rows** this is.

    Two, and never a band: the winning combination and the one it beat. A layer
    holding 1 771 near-miss fours would be a group-shaped answer to *who was
    withheld*, which is the question nobody may ask.
    """

    WINNER = "WINNER"
    RUNNER_UP = "RUNNER_UP"


@final
@dataclass(frozen=True, slots=True)
class RecordedCombination:
    """One four the objective compared, and the whole ``G`` breakdown behind it.

    **Exactly what the deciding margin is computed from**, and no more: the
    margin is over contributions, so the terms and the renormalisation basis both
    have to be here or the reason code is unreproducible a year later.

    ``terms`` is opaque for the reason ``SearchCandidateRecord.terms`` is — it is
    stamped with ``ruleset_version`` and its shape may change between rulesets,
    which is exactly what a relational schema would fight.
    """

    band: CombinationBand
    #: The three people seated beside the searcher, in the arrangement's own
    #: order: the partner first, then the two opponents.
    members: tuple[UUID, ...]
    #: Who partnered the searcher in the arrangement this combination was judged
    #: at. ``None`` is not a value here: a scored combination is a complete four.
    partner_id: UUID
    terms: tuple[Mapping[str, Any], ...]
    #: The group terms that stood down — the renormalisation basis, without which
    #: two objectives are not comparable.
    degraded_terms: tuple[str, ...]
    side_gap: float
    forecast_pct: int


@final
@dataclass(frozen=True, slots=True)
class LineupRecord:
    """Layer 4. **Two rows and four counters, and no route returns any of it.**

    ``the-group-objective.md`` §6: the first three layers are all **per
    candidate** and a line-up's unit is the **combination**, so ADR-0116's gate
    would be unfalsifiable and §5's reason code unreproducible without this. It
    inherits layer 3's rules unchanged — written before the answer is returned,
    never expires, and engine-internal — because a runner-up combination is a
    group-shaped near miss.

    ``max_fit_rank_seated`` is ``K``'s replacement falsifier. §24's own reads
    *whether the winning combination ever contains a candidate ranked past ``K``*
    and cannot fire, because the pool is truncated at ``K`` by construction; this
    one measures how deep into the ranking the engine actually reached.

    ``seated`` is **who sat down**, and it is here because the returned band no
    longer says (#407): that band is the pool the four were drawn from, and a
    complete four's seated are the winner's members — but a partial line-up and
    a singles court record no winner, and a search-time fact the record used to
    hold is not one it may lose. ``None`` is *not recorded* — a search written
    while the returned band was the seated in seat order, which searches being
    kept for ever makes a standing state rather than a migration's leftover.
    """

    combinations: int
    refused_by_gate: int
    refused_by_floor: int
    #: ``None`` when nobody was seated at all.
    max_fit_rank_seated: int | None
    #: The winner, then the runner-up. Empty when no combination was scored, and
    #: one row long when there was nothing to beat.
    rows: tuple[RecordedCombination, ...]
    #: Who took a seat, in the order they were seated — nought to three, and an
    #: empty tuple is *nobody tonight*. ``None`` is *not recorded*, never
    #: *nobody* — and it has no default, so *not recorded* is a state a writer
    #: has to spell rather than the one it gets by forgetting.
    seated: tuple[UUID, ...] | None

    def __post_init__(self) -> None:
        for name, count in (
            ("combinations", self.combinations),
            ("refused_by_gate", self.refused_by_gate),
            ("refused_by_floor", self.refused_by_floor),
        ):
            invariant(count >= 0, f"{name} counted {count}")
        invariant(
            len(self.rows) <= 2,
            f"layer 4 recording {len(self.rows)} combinations: two rows, not "
            f"two thousand",
        )
        invariant(
            [row.band for row in self.rows]
            == [CombinationBand.WINNER, CombinationBand.RUNNER_UP][: len(self.rows)],
            "layer 4's rows are the winner then the runner-up, in that order",
        )
        # The two facts about the seated are one fact in two columns: a rank
        # among nobody, or nobody with a rank, is a row where they have drifted.
        if self.seated is not None:
            invariant(
                (self.max_fit_rank_seated is None) == (not self.seated),
                f"layer 4 seats {len(self.seated)} and reads a deepest rank of "
                f"{self.max_fit_rank_seated}",
            )


@final
@dataclass(frozen=True, slots=True)
class SearchRecord:
    """One row per engine invocation, and the identity of the answer beside it.

    Kept forever. Erasure is the only path that ever deletes one, which is what
    makes ``n_returned`` a **redaction detector** — compared against the count of
    ``RETURNED`` rows, a mismatch means erasure removed a candidate from a search
    that survived — rather than a redundant column.
    """

    id: UUID
    searcher_id: UUID
    sport: Sport
    #: ``NULL`` exactly when the surface is the deck, which has no mode and
    #: scores against a declared Play intent instead.
    mode: SearchMode | None
    #: The mirror of ``mode``'s constraint: non-null exactly on the deck. It
    #: records the **declaration as it stood**, never the vector it mapped to, so
    #: a later change to the mapping does not rewrite history.
    intent_read: PlayIntent | None
    surface: SearchSurface
    initiation: SearchInitiation
    at: datetime
    engine_version: str
    ruleset_version: str
    #: The ``event_store.sequence_no`` the index had consumed when the search
    #: began. *Everything up to and including this is applied.*
    snapshot_version: int
    trace_id: str
    #: The internal staleness flag. The ladder that turns lag into a refusal is
    #: ``index_staleness``; this is the middle rung, where a search is served and
    #: the fact recorded.
    index_stale: bool
    counts: StagedCounts
    #: The Fit of the best candidate that did not clear. ``None`` means nothing
    #: was withheld, which is not the same as ``0``.
    best_withheld_fit: float | None
    pool_description: PoolDescription
    #: The grid this search actually **ran on**, as slot codes — the profile's
    #: grid, or the one a rung-A widening improvised for this one search. It is
    #: recorded because the window is *re-derived* from it rather than read back
    #: as a stored label (``the-two-contracts.md`` §3): a label read back is how
    #: a stale window ships the day ``window_of`` changes, and a derivation from
    #: this grid and this row's own ``at`` reproduces the answer that was given.
    searcher_grid: tuple[str, ...]
    #: How many of the twenty-one grid cells the searcher had ticked. The
    #: availability term's **denominator**, per search rather than per candidate.
    searcher_slot_count: int
    #: The searcher's **own** coarse area, as the code the wire spells areas in,
    #: and as this search ran on it.
    #:
    #: Recorded for ``searcher_grid``'s reason rather than read back off the
    #: profile: a read-back never recomputes, and the profile's *current* area is
    #: a different fact for a player who has moved since — a card saying *in your
    #: area* over an area they have left is the answer that would be given now
    #: rather than the one that was given.
    #:
    #: ``None`` is **not an area**. It is a search recorded before this column
    #: existed, which searches being kept for ever (``docs/adr/0104``) makes a
    #: standing state rather than a migration's leftover, and the wire spells it
    #: by **omitting** the field (``docs/adr/0106`` §4) — an empty code would
    #: compare unequal to every real one and would quietly mean *never in your
    #: area*, which is a claim rather than a gap.
    searcher_area_code: str | None
    #: Whether the widening ceiling clamped to the profile's own maximum. It is
    #: true for the searcher already **at** the maximum too, whose ladder has no
    #: radius rung on it at all — counting them is the whole job of the bit.
    radius_clamp_bit: bool
    #: Which rungs were offered, each with its real count. ``None`` is *the
    #: offers were not computed at all* — the shortlist cleared
    #: ``MIN_SHORTLIST`` — and an empty tuple is *computed, and none available*.
    #: The difference is `MIN_SHORTLIST`'s own falsifier, read off these rows.
    rung_offers: tuple[RungOffer, ...] | None
    #: The search whose offer this one accepts. **An accepted widen is a new
    #: search citing the one that offered it**, never a silent profile edit, so
    #: take-up per rung is a join over two rows rather than a flag on one.
    offered_by_search_id: UUID | None
    #: Which rung this search took. Set on the **accepting** search, beside the
    #: citation, and never on the search that made the offer.
    rung_taken: Rung | None
    latency_ms_by_stage: Mapping[str, int]
    candidates: tuple[SearchCandidateRecord, ...]
    #: Layer 4. **Non-null exactly on the two line-up surfaces**, and returned by
    #: no route to anybody.
    lineup: LineupRecord | None = None
    #: How many candidates a **live** pass suppression removed from this deal.
    #: **Deck deals only**, ``None`` elsewhere.
    #:
    #: It is the only thing that distinguishes *your own passes emptied your
    #: deck* from *the pool is empty* — the failure mode nobody can see from any
    #: screen, since no route returns a pass, to anyone, in any shape
    #: (``docs/adr/0128`` §4).
    n_excluded_by_suppression: int | None = None

    def __post_init__(self) -> None:
        on_the_deck = self.surface is SearchSurface.DECK
        invariant(
            (self.mode is None) == on_the_deck,
            f"a {self.surface.value} search with mode {self.mode}",
        )
        invariant(
            (self.intent_read is not None) == on_the_deck,
            f"a {self.surface.value} search with intent_read {self.intent_read}",
        )
        invariant(
            (self.lineup is not None) == self.seats_a_lineup,
            f"a {self.surface.value} search with layer 4 {self.lineup}: the "
            f"combination is a line-up's unit and no other surface has one",
        )
        invariant(
            (self.n_excluded_by_suppression is not None) == on_the_deck,
            f"a {self.surface.value} search counting "
            f"{self.n_excluded_by_suppression} suppressed: the count belongs to "
            "a deal and to nothing else, because a pass reaches no other surface",
        )
        for row in self.candidates:
            # **A re-show is a fact about a card**, so the flag is set exactly
            # where a card was dealt: on this surface, in this band. A near miss
            # was shown to nobody and a shortlist row is not a card, and both
            # would otherwise carry a ``false`` that reads as *not a re-show*
            # rather than as *not asked*.
            invariant(
                (row.suppression_lapsed is not None)
                == (on_the_deck and row.band is CandidateBand.RETURNED),
                f"a {self.surface.value} {row.band.value} row with "
                f"suppression_lapsed {row.suppression_lapsed}",
            )
        invariant(
            len(self.returned) == self.counts.n_returned,
            f"n_returned says {self.counts.n_returned} and {len(self.returned)} "
            "rows were written: the redaction detector must start out agreeing",
        )
        invariant(
            (self.rung_taken is None) == (self.offered_by_search_id is None),
            f"a search taking rung {self.rung_taken} cited "
            f"{self.offered_by_search_id}: a rung is taken from an offer, and "
            "the pair is what makes take-up a join",
        )
        invariant(
            self.searcher_slot_count == len(self.searcher_grid),
            f"a slot count of {self.searcher_slot_count} over a grid of "
            f"{len(self.searcher_grid)} cells",
        )
        invariant(
            self.searcher_area_code != "",
            "a search recorded with an empty area code: absence is None and "
            "means *not recorded*, where an empty string is a code nothing can "
            "produce and every real code compares unequal to",
        )

    @property
    def seats_a_lineup(self) -> bool:
        """Whether this search seated people rather than listing them.

        Two surfaces and one question, asked here rather than at each call site:
        **a line-up and filling seats differ only by locked seats**, so every
        rule that reads *is this a line-up* must read both or neither.
        """

        return self.surface in (SearchSurface.LINEUP, SearchSurface.FILL_SEATS)

    @property
    def returned(self) -> tuple[SearchCandidateRecord, ...]:
        """The rows the response carried, in position order.

        **The one way a candidate leaves this record.** Every renderer reads
        here rather than filtering ``candidates`` itself, because the filter
        that keeps layer 3 inside the building should exist once and be testable
        once — a near-miss row reaching a screen would be a band predicate
        somebody dropped in a renderer nobody thought of as a surface.
        """

        return tuple(
            row for row in self.candidates if row.band is CandidateBand.RETURNED
        )
