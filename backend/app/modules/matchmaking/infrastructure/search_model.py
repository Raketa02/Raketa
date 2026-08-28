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

**The three text arrays are arrays on PostgreSQL and JSON on SQLite.**
``degraded_terms`` is lifted out of the opaque ``terms`` blob precisely so that a
per-term ``NoEvidence`` rate is an array query with a GIN index rather than a
JSONB scan — a term quietly dying is invisible otherwise — and the variant keeps
the ASGI-over-in-memory-SQLite test seam working without weakening the column
where it runs.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
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


class SearchORM(Base):
    """One engine invocation, and everything counted about it."""

    __tablename__ = "search"
    __table_args__ = (
        # Time ordering comes from here, which is why a ``uuid4`` id is enough
        # and a time-ordered UUID buys nothing.
        Index("ix_search_searcher_at", "searcher_id", "at"),
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
    excluded_by_gate: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
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
    pool_description: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    #: The availability term's denominator, per search rather than per candidate.
    searcher_slot_count: Mapped[int] = mapped_column(Integer, nullable=False)
    radius_clamp_bit: Mapped[bool] = mapped_column(Boolean, nullable=False)
    latency_ms_by_stage: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)


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
    terms: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    #: Lifted out of the blob: the renormalisation basis, without which a Fit is
    #: uninterpretable a year later.
    degraded_terms: Mapped[list[str]] = mapped_column(CODE_ARRAY, nullable=False)
    modifiers: Mapped[list[Any]] = mapped_column(JSON, nullable=False)
    liveness_reasons: Mapped[list[str]] = mapped_column(CODE_ARRAY, nullable=False)
    #: The **raw input** per signal, never the offset it produced: an offset is a
    #: function of the ruleset's bounds, so storing it would make a bounds change
    #: undiffable.
    liveness_signals: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
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
