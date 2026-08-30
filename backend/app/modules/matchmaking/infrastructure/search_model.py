"""The two search tables. **Append-only, unexpiring, and never rewritten.**

``docs/adr/0104``: one row per engine invocation, written in the request's own
transaction and committed before the response returns. Nothing in this design
deletes a row except erasure, which does not exist yet — so there is no
``deleted_at``, no retention column and no update path, and their absence is what
makes ``n_returned`` a **redaction detector** rather than a redundant column:
compared against the number of ``RETURNED`` rows, a mismatch means erasure
removed a candidate from a search that survived.

**Every fact is search-time and cannot be reconstructed afterwards. There is no
backfill.** A column added later is a column that is null for every search before
it, forever, for every rate the engine is judged by.

**Two columns are recorded and read by nothing, deliberately.**
``their_slot_count`` and ``days_away`` had their consumers struck, and
``liveness_signals`` stores the raw inputs and never the offset. *A strike that
is not recorded becomes irreversible by accident.*

**The text arrays are arrays on PostgreSQL and JSON on SQLite.**
``degraded_terms`` is lifted out of the opaque ``terms`` blob precisely so that a
per-term ``NoEvidence`` rate is an array query with a GIN index rather than a
JSONB scan — a term quietly dying is invisible otherwise — and the variant keeps
the ASGI-over-in-memory-SQLite test seam working without weakening the column
where it runs. ``degraded_reasons`` rides beside it in the same shape rather than
inside it: pairs in one JSONB column would spend exactly the queryability that
lift bought.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base

#: The same ``BIGINT``-on-PostgreSQL / ``INTEGER``-on-SQLite variant the event
#: store's ``sequence_no`` uses. A watermark that could not hold every value the
#: column it watermarks can hold would be a watermark with a ceiling.
SNAPSHOT_SEQUENCE = BigInteger().with_variant(Integer(), "sqlite")

#: A list of machine codes. ``text[]`` where the queries that need it will run,
#: JSON where the test suite runs.
CODE_ARRAY = ARRAY(String()).with_variant(JSON(), "sqlite")

#: An opaque blob. **``JSONB`` where it will be queried**, the same variant the
#: event store's own payload column uses: these are read by an analyst asking
#: questions of a shape no relational schema could hold, and `JSON` on PostgreSQL
#: stores the text and indexes nothing.
BLOB = JSON().with_variant(JSONB(), "postgresql")

#: The same blob, for a column whose **absence is checked**. ``JSON`` renders a
#: Python ``None`` as the JSON literal ``null`` by default, which is a value and
#: not an absence — so a check constraint reading ``IS NOT NULL`` sees every row
#: as present and refuses them all. ``none_as_null`` is what makes *this column
#: does not apply here* the same thing in Python, in SQL and in the constraint.
NULLABLE_BLOB = JSON(none_as_null=True).with_variant(
    JSONB(none_as_null=True), "postgresql"
)


class SearchORM(Base):
    """One engine invocation, and everything counted about it."""

    __tablename__ = "search"
    __table_args__ = (
        # Time ordering comes from here, which is why a ``uuid4`` id is enough
        # and a time-ordered UUID buys nothing.
        Index("ix_search_searcher_at", "searcher_id", "at"),
        # **A check constraint, not a convention.** ``mode`` is ``NULL`` exactly
        # on the deck, which has no mode and scores against a declared Play
        # intent instead; ``intent_read`` is the mirror. The record type asserts
        # the same pair, and both are worth having: one refuses a row this build
        # could write, and the other refuses a row any writer could.
        CheckConstraint(
            "(mode IS NULL) = (surface = 'DECK')",
            name="ck_search_mode_null_exactly_on_the_deck",
        ),
        CheckConstraint(
            "(intent_read IS NOT NULL) = (surface = 'DECK')",
            name="ck_search_intent_read_set_exactly_on_the_deck",
        ),
        # The other pair that must never be half-written. A rung is taken *from
        # an offer*, so a row naming one without citing the search that made it
        # is a take-up figure with no denominator — and the join the falsifier
        # needs is exactly these two columns.
        CheckConstraint(
            "(rung_taken IS NULL) = (offered_by_search_id IS NULL)",
            name="ck_search_rung_taken_cites_its_offer",
        ),
        # The suppression count belongs to a deal and to nothing else, because a
        # pass reaches no other surface (``docs/adr/0128``). Same shape as the
        # two above: a column whose *presence* carries meaning is a column that
        # must not be half-written.
        CheckConstraint(
            "(n_excluded_by_suppression IS NOT NULL) = (surface = 'DECK')",
            name="ck_search_suppression_count_only_on_the_deck",
        ),
        # Layer 4 belongs to the two surfaces that seat people and to no other,
        # because its unit is the **combination** and only a line-up has one.
        # The fourth column in this file whose presence carries meaning, and the
        # fourth for which that is a constraint rather than a convention.
        CheckConstraint(
            "(lineup IS NOT NULL) = (surface IN ('LINEUP', 'FILL_SEATS'))",
            name="ck_search_lineup_only_where_seats_were_filled",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    searcher_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), nullable=False
    )
    #: **Fixes the seat count.** There is no ``format`` column and there never
    #: will be — game format is a term this context refuses.
    sport: Mapped[str] = mapped_column(String(50), nullable=False)
    #: ``NULL`` exactly when the surface is the deck, which has no mode.
    mode: Mapped[str | None] = mapped_column(String(20), nullable=True)
    #: The mirror of ``mode``'s rule: non-null exactly on the deck. It records
    #: the **declaration as it stood**, never the vector it mapped to.
    intent_read: Mapped[str | None] = mapped_column(String(20), nullable=True)
    surface: Mapped[str] = mapped_column(String(20), nullable=False)
    #: Orthogonal to the surface: an engine-pushed deck card is ``DECK`` +
    #: ``ENGINE``. Two columns, because pooling them makes both meaningless.
    initiation: Mapped[str] = mapped_column(String(20), nullable=False)
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    engine_version: Mapped[str] = mapped_column(String(50), nullable=False)
    ruleset_version: Mapped[str] = mapped_column(String(50), nullable=False)
    #: *Everything up to and including this is applied.* What makes an unexpiring
    #: search record reproducible.
    snapshot_version: Mapped[int] = mapped_column(SNAPSHOT_SEQUENCE, nullable=False)
    #: The request's ``X-Request-ID``. One column, and *"it showed me somebody
    #: strange"* reaches the exact log line.
    trace_id: Mapped[str] = mapped_column(String(64), nullable=False)
    index_stale: Mapped[bool] = mapped_column(Boolean, nullable=False)

    n_generated: Mapped[int] = mapped_column(Integer, nullable=False)
    #: A histogram over the ten gate codes. **Counts only; no candidate is named
    #: at this layer.**
    excluded_by_gate: Mapped[dict[str, Any]] = mapped_column(BLOB, nullable=False)
    n_scored: Mapped[int] = mapped_column(Integer, nullable=False)
    n_cleared_floor: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Also the redaction detector. **Never denormalised away.**
    n_returned: Mapped[int] = mapped_column(Integer, nullable=False)
    #: The same detector for the near-miss band, which ``best_withheld_fit``
    #: cannot provide because it is a value and not a count.
    n_near_miss_recorded: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Null means nothing was withheld, which is not the same as ``0``.
    best_withheld_fit: Mapped[float | None] = mapped_column(Float, nullable=True)
    #: Written on **every** search: a thin pool and a broken floor are
    #: indistinguishable without it.
    pool_description: Mapped[dict[str, Any]] = mapped_column(BLOB, nullable=False)
    #: The grid this search **ran on** — the profile's own, or the one a rung-A
    #: widening improvised for this search alone. It is stored so the window is
    #: **re-derived** from it rather than read back as a label: a stored label is
    #: how a stale window ships the day ``window_of`` changes, where this grid
    #: and this row's own ``at`` reproduce the answer that was given.
    searcher_grid: Mapped[list[str]] = mapped_column(CODE_ARRAY, nullable=False)
    #: The availability term's denominator, per search rather than per candidate.
    searcher_slot_count: Mapped[int] = mapped_column(Integer, nullable=False)
    radius_clamp_bit: Mapped[bool] = mapped_column(Boolean, nullable=False)
    #: Which rungs were offered and each one's real count. **``NULL`` means the
    #: offers were not computed at all** — the shortlist cleared ``MIN_SHORTLIST``
    #: — where an empty list means computed and none available. That difference
    #: is ``MIN_SHORTLIST``'s own falsifier, and it is read off these rows.
    rung_offers: Mapped[list[Any] | None] = mapped_column(BLOB, nullable=True)
    #: The search whose offer this one accepts. A self-reference rather than a
    #: flag, because take-up per rung is *the pair* — what was offered, and what
    #: the same person did next — and a boolean cannot join.
    offered_by_search_id: Mapped[UUID | None] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("search.id", ondelete="RESTRICT"),
        nullable=True,
    )
    #: Which rung this search took, on the **accepting** row.
    rung_taken: Mapped[str | None] = mapped_column(String(1), nullable=True)
    latency_ms_by_stage: Mapped[dict[str, Any]] = mapped_column(BLOB, nullable=False)
    #: How many candidates a **live** pass suppression removed from this deal.
    #: **Deck deals only**, null elsewhere — a check constraint, not a
    #: convention. It is the only thing that distinguishes *your own passes
    #: emptied your deck* from *the pool is empty*, and nobody can see it from
    #: any screen because no route returns a pass.
    n_excluded_by_suppression: Mapped[int | None] = mapped_column(
        Integer, nullable=True
    )
    #: **Layer 4, and no route returns any of it.** The winning combination and
    #: the runner-up, each with the whole ``G`` breakdown the deciding margin is
    #: computed from, plus the three enumeration counters and the deepest Fit
    #: rank the engine reached. Two rows, not 1 771 — a layer holding every
    #: combination that lost would be a group-shaped answer to *who was
    #: withheld*.
    #:
    #: Opaque for the reason ``search_candidate.terms`` is: it is stamped with
    #: ``ruleset_version`` and the group vector may gain or lose a term between
    #: rulesets, which is precisely what a relational schema would fight.
    #: **Line-up surfaces only**, null elsewhere, by check constraint.
    lineup: Mapped[dict[str, Any] | None] = mapped_column(
        NULLABLE_BLOB, nullable=True
    )


class SearchCandidateORM(Base):
    """One recorded candidate, in either band.

    **Layer 3 lives in this table and leaves it through no route.** A player may
    ask why somebody was shown; nobody may ask who was withheld — which is why
    the only read the store offers is keyed on the searcher *and* the band.
    """

    __tablename__ = "search_candidate"
    __table_args__ = (
        # For erasure, which is the only thing that will ever delete one of
        # these — in both roles, as searcher and as recorded candidate.
        Index("ix_search_candidate_player", "player_id"),
    )

    search_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), ForeignKey("search.id"), primary_key=True
    )
    band: Mapped[str] = mapped_column(String(20), primary_key=True)
    #: Rank within the band. ``1`` is the top of the shortlist, or the best
    #: withheld.
    position: Mapped[int] = mapped_column(Integer, primary_key=True)
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    fit: Mapped[float] = mapped_column(Float, nullable=False)
    #: **Deliberately opaque.** Stamped with the search's ``ruleset_version``,
    #: and its shape is allowed to change between rulesets — which is exactly
    #: what a relational schema would fight.
    terms: Mapped[list[Any]] = mapped_column(BLOB, nullable=False)
    #: Lifted out of the blob: the renormalisation basis, without which a Fit is
    #: uninterpretable a year later.
    degraded_terms: Mapped[list[str]] = mapped_column(CODE_ARRAY, nullable=False)
    #: Whose gap each of those was, **index-aligned** with the column above and
    #: not folded into it: pairs in one JSONB column would spend the queryability
    #: the lift out of the blob bought. A read-back never recomputes, so the code
    #: a card printed has to be the code the row kept.
    degraded_reasons: Mapped[list[str]] = mapped_column(CODE_ARRAY, nullable=False)
    modifiers: Mapped[list[Any]] = mapped_column(BLOB, nullable=False)
    liveness_reasons: Mapped[list[str]] = mapped_column(CODE_ARRAY, nullable=False)
    #: The **raw input** per signal, never the offset it produced: an offset is a
    #: function of the ruleset's bounds, so storing it would make a bounds change
    #: undiffable.
    liveness_signals: Mapped[dict[str, Any]] = mapped_column(BLOB, nullable=False)
    #: With ``search.searcher_slot_count`` this **is** the availability term, so
    #: the value in ``terms`` is checkable against its own inputs.
    shared_count: Mapped[int] = mapped_column(Integer, nullable=False)
    #: **Nothing reads it.** Recorded so a ruleset re-admitting the struck factor
    #: is re-derivable over the corpus reaching back to the first search.
    their_slot_count: Mapped[int] = mapped_column(Integer, nullable=False)
    #: Null means nothing is shared, which is not ``0``. Also unread.
    days_away: Mapped[int | None] = mapped_column(Integer, nullable=True)
    #: All three values live here; **only one crosses the wire.**
    inclusion_reason: Mapped[str | None] = mapped_column(String(30), nullable=True)
    #: ``NEAR_MISS`` rows only.
    withheld_reason: Mapped[str | None] = mapped_column(String(30), nullable=True)
    #: Which live terms did not fire for this specific person. Distinguishes
    #: *nobody was good enough* from *nobody was known enough*.
    missing_terms: Mapped[list[str]] = mapped_column(CODE_ARRAY, nullable=False)
    reliability_penalty_applied: Mapped[bool] = mapped_column(Boolean, nullable=False)
    #: **Docked** versus **docked out**.
    reliability_penalty_decisive: Mapped[bool] = mapped_column(
        Boolean, nullable=False
    )
    #: The terms the engine judged genuinely weak, over points forgone. An array
    #: for the same shape of query ``degraded_terms`` is one for, and stored
    #: rather than re-derived because the judgement belongs to the ruleset this
    #: row is stamped with.
    concerns: Mapped[list[str]] = mapped_column(CODE_ARRAY, nullable=False)
    #: Whole kilometres, as the wire carried it. Null when the distance term
    #: stood down, which is **omitted** on the wire and is not a zero.
    distance_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    #: The card **as it was shown**, so a read-back answers the search that ran
    #: rather than the one that would run now. It holds a ``photo_id`` and never
    #: the link: a presigned URL is dead within the hour and this row is kept
    #: for ever, so the link is signed over this id per response and never
    #: written here (``docs/adr/0107``).
    player_card: Mapped[dict[str, Any] | None] = mapped_column(BLOB, nullable=True)
    #: What a counted game would have been worth then. Null in for fun, where a
    #: counted result is meaningless rather than unavailable.
    at_stake: Mapped[dict[str, Any] | None] = mapped_column(BLOB, nullable=True)
    #: Whether this card is a **re-show** — the pairing had a pass whose 30-day
    #: suppression has since lapsed. Set on a dealt card and null everywhere
    #: else. It reads the **durable pass record**, never the cache, because a
    #: lapsed key leaves no trace the pair was ever passed — and without it only
    #: plain pass rate is computable, never *pass rate on re-shown profiles*.
    suppression_lapsed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
