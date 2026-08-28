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
from app.modules.player_profile.domain.availability import Window
from app.modules.player_profile.domain.play_intent import PlayIntent


class SearchSurface(str, Enum):
    """Which terminal stage ran. Four values, and pooling their rates is how
    every number the engine is judged by becomes meaningless — ``FILL_SEATS`` is
    not even optimising for the searcher.

    Only ``SHORTLIST`` can be written today; the other three arrive with their
    routes. They are declared now because ``surface`` is a stored column and a
    vocabulary that grows one value per ticket is a vocabulary whose old rows
    cannot be read against the new ones.
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

    ``MOST_RELIABLE`` is in the vocabulary and is never offered today: the
    reliability term stands down for everybody, so the control **is not drawn**
    rather than drawn and inert.
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
@dataclass(frozen=True, slots=True)
class SearchCandidateRecord:
    """One recorded candidate, in either band.

    ``terms`` is **deliberately opaque**: it is stamped with ``ruleset_version``
    and its shape is allowed to change between rulesets, which is exactly what a
    relational schema would fight. ``degraded_terms`` is lifted out of it because
    it is the renormalisation basis — without it a Fit is uninterpretable a year
    later — and because a per-term ``NoEvidence`` rate has to be an array query
    rather than a blob scan.
    """

    band: CandidateBand
    position: int
    player_id: UUID
    fit: float
    terms: tuple[Mapping[str, Any], ...]
    degraded_terms: tuple[str, ...]
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

    def __post_init__(self) -> None:
        invariant(self.position >= 1, f"a position below one: {self.position}")
        invariant(
            (self.withheld_reason is None) == (self.band is CandidateBand.RETURNED),
            f"a {self.band.value} row with withheld reason {self.withheld_reason}",
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
    #: How many of the twenty-one grid cells the searcher had ticked. The
    #: availability term's **denominator**, per search rather than per candidate.
    searcher_slot_count: int
    #: Whether the widening ceiling clamped to the profile's own maximum.
    radius_clamp_bit: bool
    latency_ms_by_stage: Mapping[str, int]
    candidates: tuple[SearchCandidateRecord, ...]

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
        returned = sum(
            1 for row in self.candidates if row.band is CandidateBand.RETURNED
        )
        invariant(
            returned == self.counts.n_returned,
            f"n_returned says {self.counts.n_returned} and {returned} rows were "
            "written: the redaction detector must start out agreeing",
        )
