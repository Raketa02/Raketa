"""The candidate index's three tables, and why it is three rather than one.

**A search reads ``(player, sport)``; a player edits their profile once.** Tags,
a grid, an area, a radius, a gender and a session refresh are facts about *a
person*, and a profile edit cannot be asked which sports that person happens to
be rated in — the projection is a pure function of one event
(``candidate_projection``), and looking that up would be exactly the state read
that makes ``rebuild == tail`` stop being a property of the shape.

So the per-player facts have their own table and the per-sport row joins to it.
Nothing is denormalised across the two, and **the stamp is on both**: a profile
edit advances ``applied_through_sequence_no`` on the facts row *and* on every one
of that player's index rows, which is what lets the snapshot's delta refresh ask
one question — *which rows moved* — of one table (``docs/adr/0112``).

**A row enters a snapshot only when both halves exist.** A player rated before
they finished onboarding has an index row and no profile; a player who finished
onboarding and has rated nothing has profile facts and no row. Neither is
generable — one has no grid and no area, the other has no Level — and the
snapshot's load says so with a join rather than with a column full of nulls that
a term would eventually read as a measured zero.

**There is no partition column, and its absence is the point** (``docs/adr/0101``):
the partition is derived from the row, so there is no field for a future matching
conjunct to attach itself to. ``tests/unit/test_candidate_index_schema.py``
asserts it absent.

**The cursor is one row, and it is the whole of the concurrency control.** Taken
``FOR UPDATE`` for the tick, so a concurrent run blocks, then reads the advanced
cursor and finds nothing to do — which is how ``docs/adr/0092``'s *idempotent and
safe beside itself* stays literally true with no leader election and no lease to
leak.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import (
    JSON,
    BigInteger,
    Boolean,
    DateTime,
    Float,
    Integer,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base

#: The same ``BIGINT``-on-PostgreSQL / ``INTEGER``-on-SQLite variant the event
#: store's own ``sequence_no`` uses. A watermark that could not hold every value
#: the column it watermarks can hold would be a watermark with a ceiling.
APPLIED_SEQUENCE = BigInteger().with_variant(Integer(), "sqlite")

#: The cursor table holds exactly one row, and this identifies it. A string
#: rather than ``id = 1`` so the row says what it is when somebody reads the
#: table by hand, and so a second projection added later takes a second value
#: rather than an integer nobody can interpret.
CANDIDATE_INDEX_CURSOR = "candidate_index"


class CandidatePlayerFactsORM(Base):
    """What one player has said about themselves, whatever sports they play.

    Every column is nullable, and none of them is nullable for the reason a
    column usually is. This table is the *fold's own state*: a refresh-token
    event may create the row before the profile commit does, and a profile
    committed before the gender question existed genuinely has no answer. What
    makes that safe is that nothing reads a half-filled row — the snapshot's join
    requires ``profile_created_at``, which is set by exactly one event and is the
    moment the player became searchable.
    """

    __tablename__ = "candidate_player_facts"

    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    #: The moment onboarding ended. Doubles as *this player is searchable*: the
    #: newcomer window is clocked from it (`the-newcomer-path.md` §1), and the
    #: snapshot's join requires it.
    profile_created_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    social_tags: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    tags_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    availability: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    grid_updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    #: The **coarse** area's centroid, at the platform's own precision. The
    #: precise fix that produced it never reached an event, so there is no
    #: version of any stream from which one could be recovered.
    area_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    search_radius_km: Mapped[int | None] = mapped_column(Integer, nullable=True)
    proposals_opt_in: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(32), nullable=True)
    gender_preference: Mapped[str | None] = mapped_column(String(32), nullable=True)
    #: *Last session refresh*, and therefore days rather than hours
    #: (``docs/adr/0111``).
    last_active_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    applied_through_sequence_no: Mapped[int] = mapped_column(
        APPLIED_SEQUENCE, nullable=False
    )


class CandidateRowORM(Base):
    """One ``(player, sport)`` pair — the identity ``docs/adr/0101`` fixed.

    The Level columns are nullable because a Play intent may be declared for a
    sport before it is rated. Such a row is not a candidate and never reaches a
    snapshot; it is kept rather than deferred because the fold may not look
    anything up, and dropping the declaration would mean replaying the log in a
    different order produced a different table.
    """

    __tablename__ = "candidate_row"

    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    #: ``Sport.value``. The partition derives from it and there is deliberately
    #: no partition column beside it.
    sport: Mapped[str] = mapped_column(String(32), primary_key=True)

    mu: Mapped[float | None] = mapped_column(Float, nullable=True)
    sigma: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence: Mapped[int | None] = mapped_column(Integer, nullable=True)
    #: The likely range as ``rating`` published it, μ ± σ clamped to the scale.
    range_low: Mapped[float | None] = mapped_column(Float, nullable=True)
    range_high: Mapped[float | None] = mapped_column(Float, nullable=True)
    band: Mapped[str | None] = mapped_column(String(64), nullable=True)
    band_lower: Mapped[float | None] = mapped_column(Float, nullable=True)
    band_upper: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_status: Mapped[str | None] = mapped_column(String(32), nullable=True)
    calibration_priority: Mapped[str | None] = mapped_column(String(32), nullable=True)
    declared_intent: Mapped[str | None] = mapped_column(String(32), nullable=True)

    #: What a delta refresh reads to know this row moved. Indexed, because that
    #: read runs every two seconds in every worker and is the whole cost of a
    #: refresh once the pointer copy is free.
    applied_through_sequence_no: Mapped[int] = mapped_column(
        APPLIED_SEQUENCE, nullable=False, index=True
    )


class CandidateIndexCursorORM(Base):
    """The single row that says how far the log has been folded in.

    ``applied_through_sequence_no`` **is** ``snapshot_version`` and means
    *everything up to and including this is applied*. It is true by construction
    rather than by argument, because the reader only ever advances over a
    contiguous prefix (``docs/adr/0110``).

    ``hole_at_sequence_no`` and ``hole_settles_at`` are the wait: a gap, and the
    transaction id the wait ends at — the first id the store had not handed out
    when the hole was seen, so whoever holds the missing number is below it. Once
    the oldest running transaction reaches that value they have all finished, and
    the cursor steps over the hole. Both are null on SQLite for ever — there is no
    transaction horizon and no concurrent appender there, so the run asserts
    contiguity and the gap-stepping path is exercised against PostgreSQL or not
    at all.
    """

    __tablename__ = "candidate_index_cursor"

    #: Which projection this watermark belongs to. Spelled ``projection`` and
    #: not ``name`` for the reason the Level band on a row is spelled ``band``:
    #: no column in this index names a *name*, so the schema fence stays a flat
    #: rule with no exception in it — and an exception is what a fence is worth
    #: exactly nothing with.
    projection: Mapped[str] = mapped_column(String(64), primary_key=True)
    applied_through_sequence_no: Mapped[int] = mapped_column(
        APPLIED_SEQUENCE, nullable=False, server_default="0"
    )
    hole_at_sequence_no: Mapped[int | None] = mapped_column(
        APPLIED_SEQUENCE, nullable=True
    )
    hole_settles_at: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    #: When the reader last **knew** it was caught up — stamped every tick,
    #: whether or not anything moved. A healthy reader over a quiet log advances
    #: nothing, and a dead one looks identical if you only watch the cursor.
    caught_up_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )


__all__ = [
    "APPLIED_SEQUENCE",
    "CANDIDATE_INDEX_CURSOR",
    "CandidateIndexCursorORM",
    "CandidatePlayerFactsORM",
    "CandidateRowORM",
]
