"""The per-worker index: load it once, refresh it by delta, hand out containers.

**One immutable container per partition per worker, published by rebinding a
single attribute** (``docs/adr/0112``). Rebinding is the ``atomic.Pointer`` §15.3
described in a language that has one: it is atomic under the GIL, a search takes
its container **once** at entry, and a refresh that lands mid-search rebinds while
the running search keeps its own container alive by reference. The outgoing
container is freed when the last search holding it finishes. That is the whole of
*the index cannot move underneath a running search*, and it costs nothing.

**The refresh is a delta and it shares row references.** ``applied_through_sequence_no``
says which rows moved since the outgoing containers were built; every other row is
carried across as a pointer. Rebuilding from scratch decodes 50 000 rows to change
the handful that moved — the 0.9 s figure that made a ×2 memory budget look
necessary. Because the steady state never holds two copies of a row, **trigger 4
loses its ×2** and becomes ``bytes_per_row × rows × workers`` > half the container
limit: roughly **25 000 players** at four workers on a 1 GB container, twice what
the ×2 allowed. (That sentence read *64 000* until #276 remeasured the row itself;
the doubling this paragraph argues for is untouched.)

**``_decode`` below copies every string the driver returned, and that is half a
row.** Neither asyncpg nor SQLAlchemy interns, so each row holds its own
``"PADEL"``, its own ``"ANY"`` and its own copy of every availability code it
ticks — **996 bytes a row**, of the measured 1 991, that routing the closed
vocabularies through themselves would give back. It is left alone deliberately:
#276 was a ticket about a figure nobody re-measured, and folding a projection
change into the commit that records the measurement would mean the recorded
number described code written in the same breath.

**It is rung 1 of ``scale-posture.md`` §5's memory ladder, and that is its home
rather than a backlog.** Nothing today wants the bytes — one worker holds a
launch city in 50 MB — so it is not work waiting to be done; it is the cheapest
thing to do *when trigger 4 fires*, which is exactly when somebody reads that
ladder. ``band`` is the one column to think about first: it is a published name
off the Level band table rather than a vocabulary this projection owns.

**``gc.freeze()`` after every load and refresh, and it is safe for a stated
reason.** One automatic gen-2 collection over a live index cost **57.9 ms
stop-the-world**, ~30× the search it interrupted; frozen, four collections
totalling 1.1 ms. Freezing moves the live index into a permanent generation
exempt from collection, which is only safe if the frozen objects cannot become
unreachable garbage — and a ``CandidateRow`` has **no reference cycles**, so
refcounting frees an outgoing row the moment the last container drops it and the
permanent generation does not accumulate. ``tests/unit/test_candidate_row_fence.py``
asserts that property rather than trusting it.

**There is no derived spatial structure to rebuild.** The bounding box rejects a
row in 18.5 ns against 1.00 µs per surviving candidate, which is what killed the
geo-cell bucket map — so a container is a list and a refresh is a pointer copy
plus a few decodes.

**Every worker holds its own copy and refreshes it independently**, so N workers
do N delta reads every 2 s and may briefly disagree about a row. That is the one
place ``docs/adr/0092``'s *N processes, N runs* is the behaviour wanted rather
than the cost paid, and the disagreement is bounded by the refresh interval —
exactly the kind ``docs/adr/0111`` says the index is allowed to have, and would
not be tolerable for anything the index is now forbidden to hold.
"""

from __future__ import annotations

import gc
import logging
from datetime import datetime, timezone
from dataclasses import dataclass
from typing import Mapping, Sequence, TypeVar, cast, final

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.kernel import Instant, instant, invariant
from app.modules.matchmaking.domain.candidate_index import (
    CandidateRow,
    IndexedArea,
    Partition,
    partition_of,
)
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSnapshot
from app.modules.matchmaking.infrastructure.candidate_index_model import (
    CANDIDATE_INDEX_CURSOR,
    CandidateIndexCursorORM,
    CandidatePlayerFactsORM,
    CandidateRowORM,
)

logger = logging.getLogger(__name__)

_T = TypeVar("_T")


@final
@dataclass(frozen=True, slots=True)
class RefreshReport:
    """What one refresh cost, and how much of it was the pointer copy.

    ``rows_decoded`` against ``rows_held`` is the instrument
    ``the-candidate-index.md`` §10 names as the 2 s interval's falsifier: a
    refresh whose cost stops being dominated by the pointer copy is the thing
    that would move the number.
    """

    snapshot_version: int
    partitions: int
    rows_held: int
    rows_decoded: int
    #: When the tail reader last **knew** it was caught up, as of this refresh.
    #: The staleness a search would read is measured from here, so the refresh
    #: loop can alert on §17's p99 without inventing a second clock.
    caught_up_at: Instant


class DatabaseCandidateSource:
    """This worker's whole index, and the one call a search makes into it."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        empty_at: Instant,
    ) -> None:
        self._session_factory = session_factory
        # The attribute the refresh rebinds. Read once per search and never
        # mutated: a container is replaced, never edited.
        self._snapshots: Mapping[Partition, CandidateSnapshot] = {}
        self._loaded_through = 0
        self._caught_up_at = empty_at

    def snapshot(self, partition: Partition) -> CandidateSnapshot:
        """This partition's container as it stands. **Bound once, at entry.**

        A partition nobody has rows for answers with an empty container rather
        than raising: *no padel players near you* is an answer, and a sport
        nobody has rated is not an error. The empty container still carries the
        index's version and freshness, so a search over an empty sport is
        recorded and refused on exactly the same terms as any other.
        """

        snapshots = self._snapshots
        existing = snapshots.get(partition)
        if existing is not None:
            return existing
        return CandidateSnapshot(
            partition=partition,
            rows=(),
            snapshot_version=self._loaded_through,
            caught_up_at=self._caught_up_at,
        )

    async def refresh(self) -> RefreshReport:
        """Rebuild the containers from what moved, then publish them.

        Reads the cursor **first**, so the version a container claims can only be
        one the reader had actually reached when the rows were read — a version
        read afterwards could name events this load did not see.
        """

        async with self._session_factory() as session:
            version, caught_up_at = await self._read_cursor(session)
            moved = (
                await self._load(session, after=self._loaded_through, through=version)
                if version != self._loaded_through
                else ()
            )

        rebuilt = self._rebind(moved, version=version, caught_up_at=caught_up_at)
        if rebuilt.rows_decoded:
            # **After every load and every refresh that decoded something.**
            #
            # `gc.freeze()` promotes *everything currently tracked* into the
            # permanent generation, not only the rows this just built — so a
            # refresh that decoded nothing would still permanently promote
            # whatever requests happened to be in flight, every two seconds,
            # for ever. That is a slow leak bought for nothing: a refresh with
            # no new rows has nothing to protect from the collection the freeze
            # exists to avoid. The cost this is paying for is real and measured
            # — one automatic gen-2 collection over a live index was 57.9 ms
            # stop-the-world — and it is paid where there is something to buy.
            gc.freeze()
        return rebuilt

    def _rebind(
        self,
        moved: Sequence[CandidateRow],
        *,
        version: int,
        caught_up_at: Instant,
    ) -> RefreshReport:
        by_key = {(row.player_id, row.sport): row for row in moved}
        rebuilt: dict[Partition, list[CandidateRow]] = {}
        appeared: dict[Partition, list[CandidateRow]] = {}

        for partition, outgoing in self._snapshots.items():
            # `pop`, so what is left in `by_key` afterwards is exactly the rows
            # that are new to this worker rather than replacements for rows it
            # already held.
            rebuilt[partition] = [
                by_key.pop((row.player_id, row.sport), row) for row in outgoing.rows
            ]
        for row in by_key.values():
            appeared.setdefault(partition_of(row), []).append(row)

        for partition, rows in appeared.items():
            rebuilt.setdefault(partition, [])
            # Sorted on the player id, ascending — the order ties break on
            # (`docs/adr/0105`), so two workers that saw the same rows arrive in
            # different orders still hold the same container.
            rebuilt[partition] = sorted(
                rebuilt[partition] + rows, key=lambda row: row.player_id
            )

        self._snapshots = {
            partition: CandidateSnapshot(
                partition=partition,
                rows=tuple(rows),
                snapshot_version=version,
                caught_up_at=caught_up_at,
            )
            for partition, rows in rebuilt.items()
        }
        self._loaded_through = version
        self._caught_up_at = caught_up_at
        return RefreshReport(
            snapshot_version=version,
            partitions=len(self._snapshots),
            rows_held=sum(len(rows) for rows in rebuilt.values()),
            rows_decoded=len(moved),
            caught_up_at=caught_up_at,
        )

    async def _read_cursor(self, session: AsyncSession) -> tuple[int, Instant]:
        cursor = (
            await session.execute(
                select(CandidateIndexCursorORM).where(
                    CandidateIndexCursorORM.projection == CANDIDATE_INDEX_CURSOR
                )
            )
        ).scalar_one_or_none()
        if cursor is None:
            return 0, self._caught_up_at
        return cursor.applied_through_sequence_no, _as_utc(cursor.caught_up_at)

    async def _load(
        self, session: AsyncSession, *, after: int, through: int
    ) -> Sequence[CandidateRow]:
        """Every row that moved in ``(after, through]``, joined to its player's facts.

        **Bounded at both ends, and the upper one is not a detail.** The cursor
        and the rows are two statements, and the tail reader may commit between
        them — so without ``through`` a container could hold a row reflecting
        events past the ``snapshot_version`` it claims. It would still be true
        that everything up to that version was applied, and it would no longer be
        true that the container *is* the index at that version, which is what
        makes a recorded search interpretable later (``docs/adr/0104``).

        **An inner join, and that is the whole of *which rows are candidates*.**
        A player rated before they finished onboarding has an index row and no
        grid and no area; one who finished onboarding and rated nothing has facts
        and no row. Neither can be generated for, and saying so with a join is
        what stops the alternative — columns full of nulls that a term eventually
        reads as a measured zero.
        """

        result = await session.execute(
            select(CandidateRowORM, CandidatePlayerFactsORM)
            .join(
                CandidatePlayerFactsORM,
                CandidatePlayerFactsORM.player_id == CandidateRowORM.player_id,
            )
            .where(
                CandidateRowORM.applied_through_sequence_no > after,
                CandidateRowORM.applied_through_sequence_no <= through,
                CandidateRowORM.mu.is_not(None),
                CandidatePlayerFactsORM.profile_created_at.is_not(None),
            )
            .order_by(CandidateRowORM.player_id, CandidateRowORM.sport)
        )
        return [_decode(row, facts) for row, facts in result.all()]


def _decode(row: CandidateRowORM, facts: CandidatePlayerFactsORM) -> CandidateRow:
    """Two table rows into the one object a search reads.

    Every column is **required** rather than defaulted, and that is the point.
    The join has already refused a row with no Level and a player with no
    profile, and every remaining column arrives with one of those two events —
    so a ``None`` here means the projection is broken, and defaulting it would
    hand a term an invented zero and call it measured.
    """

    return CandidateRow(
        player_id=str(row.player_id),
        sport=row.sport,
        mu=_required(row.mu, "a Level"),
        sigma=_required(row.sigma, "an Uncertainty"),
        confidence=_required(row.confidence, "a confidence"),
        range_low=_required(row.range_low, "a likely range floor"),
        range_high=_required(row.range_high, "a likely range ceiling"),
        band=_required(row.band, "a band"),
        band_lower=_required(row.band_lower, "a band floor"),
        band_upper=_required(row.band_upper, "a band ceiling"),
        rating_status=_required(row.rating_status, "a rating status"),
        calibration_priority=_required(
            row.calibration_priority, "a calibration priority"
        ),
        declared_intent=row.declared_intent,
        social_tags=tuple(_required(facts.social_tags, "a tag list")),
        tags_updated_at=_as_utc(_required(facts.tags_updated_at, "a tag moment")),
        # Optional for the ordinary reason and not the fold's: a player who
        # wrote no line has none, and the wire omits it.
        intro=facts.intro,
        availability=tuple(_required(facts.availability, "a grid")),
        grid_updated_at=_as_utc(_required(facts.grid_updated_at, "a grid moment")),
        areas=(
            IndexedArea(
                latitude=_required(facts.area_latitude, "an area"),
                longitude=_required(facts.area_longitude, "an area"),
            ),
        ),
        search_radius_km=_required(facts.search_radius_km, "a search radius"),
        proposals_opt_in=facts.proposals_opt_in,
        gender=facts.gender,
        gender_preference=_required(facts.gender_preference, "a gender preference"),
        profile_created_at=_as_utc(
            _required(facts.profile_created_at, "a profile commit moment")
        ),
        last_active_at=(
            None if facts.last_active_at is None else _as_utc(facts.last_active_at)
        ),
        applied_through_sequence_no=row.applied_through_sequence_no,
    )


def _as_utc(value: datetime) -> Instant:
    """A stored moment, read back as the UTC instant it was written as.

    **Every moment in this schema is written in UTC**, and the columns say
    ``timezone=True`` — but that is a promise the *database* keeps, and SQLite
    does not: it stores the text and hands back a naive ``datetime``. A search
    then subtracts it from ``now`` and raises, or silently reads a local hour.

    So the normalisation happens here, at the one seam where a stored column
    becomes a domain value, rather than being a fact every reader has to
    remember. It is a statement about the storage and not about the clock, which
    is why it attaches UTC rather than converting from local time: the value was
    written as UTC, so reading it as anything else would move it.

    It is the adapter's job and not the kernel's — ``instant()`` **refuses** a
    naive datetime on purpose, because in every other context one is a bug.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        return Instant(value.replace(tzinfo=timezone.utc))
    return instant(value)


def _required(value: _T | None, what: str) -> _T:
    """Refuse a half-projected row rather than defaulting the hole away.

    A broken precondition, so it raises through ``invariant()`` — this is not a
    legitimate domain state the caller could handle, it is the projection having
    written a row the join says cannot exist.
    """

    invariant(value is not None, f"a candidate row loaded without {what}")
    return cast("_T", value)


__all__ = ["DatabaseCandidateSource", "RefreshReport"]
