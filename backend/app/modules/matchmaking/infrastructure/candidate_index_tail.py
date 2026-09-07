"""The tail reader: one tick of the candidate index's only writer.

**It subscribes to the log, not to the outbox, and the two are different
subscriptions with different guarantees** (``docs/adr/0110``). The outbox keeps
delivering side effects — once per platform, leased, deliberately *not* in append
order, under a row id unrelated to the event's. A projection is a function of a
log that anybody may recompute, and it needs a number it can name: the outbox
cannot supply one, so this reads ``event_store`` ordered by ``sequence_no``. The
same domain event drives both. Neither is a fallback for the other, and a reader
of ``app/`` has to hold both in their head — which is why it is said here as well
as in the ADR.

One tick, in order:

1. Take the single cursor row **``FOR UPDATE``**. A concurrent run does not race:
   it **blocks, then reads the advanced cursor and finds nothing to do**. The
   lock is the transaction, so there is nothing to leak behind a dead process and
   nothing to expire mid-run — which is the exact property that let
   ``docs/adr/0092`` refuse leader election, kept literally true rather than by
   exemption.
2. Read ``event_store`` past the cursor in ``sequence_no`` order, bounded batch.
3. Apply the **contiguous prefix only**, stepping over a hole only once the
   snapshot horizon proves it permanent (``candidate_tail.plan_tail``).
4. Apply the batch and advance the cursor **in one transaction**. The cursor *is*
   the idempotency; there is no at-least-once delivery here to defend against, and
   §7.3's four-field row stamp — designed against HTTP delivery this design does
   not have — collapses to ``applied_through_sequence_no``.
5. Stamp every moved row with the sequence it was applied through, and stamp the
   cursor's ``caught_up_at`` **whether or not anything moved**: a healthy reader
   over a quiet log advances nothing, and a dead one looks identical if you only
   watch the cursor.

**A profile edit moves every one of that player's index rows.** The facts are
per-player and the rows are per ``(player, sport)``, so the stamp is written to
both — which is what lets a delta refresh ask its one question of one table.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Sequence, final
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.catalog import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EventCodec
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Clock
from app.modules.matchmaking.domain.candidate_projection import (
    PROJECTED_CONTRACTS,
    CandidateRowMoved,
    PlayerFactsMoved,
    project,
)
from app.modules.matchmaking.domain.candidate_tail import (
    ObservedHole,
    TailPlan,
    plan_tail,
)
from app.modules.matchmaking.infrastructure.candidate_index_model import (
    CANDIDATE_INDEX_CURSOR,
    CandidateIndexCursorORM,
    CandidatePlayerFactsORM,
    CandidateRowORM,
)
from app.modules.matchmaking.infrastructure.snapshot_horizon import SnapshotHorizon
from app.shared.domain import DomainEvent

logger = logging.getLogger(__name__)


@final
@dataclass(frozen=True, slots=True)
class TickReport:
    """What one tick did. Logged even when it did nothing.

    *The reader ran and found nothing* and *the reader did not run* are the two
    states this has to be able to tell apart from outside, and they are the two a
    silent job cannot.
    """

    events_applied: int
    rows_moved: int
    snapshot_version: int
    waiting_on_hole: int | None


class CandidateIndexTail:
    """Folds the log into the candidate index. **The index's only writer.**"""

    def __init__(
        self,
        *,
        codec: EventCodec,
        catalog: EventCatalog,
        horizon: SnapshotHorizon,
        clock: Clock,
        #: How many log rows one tick may look at. **Required, with no default
        #: here**: the number lives once, in ``CANDIDATE_INDEX_BATCH_SIZE``, and
        #: a default beside it would be a second copy that agreed with the
        #: settings until somebody changed one of them. It is a bound rather
        #: than *everything since the cursor*, so a projection restarted against
        #: a long log does bounded work per tick — and batches consistently
        #: hitting it are the instrument that would say the 1 s interval is too
        #: slow (`the-candidate-index.md` §10).
        batch_size: int,
    ) -> None:
        self._codec = codec
        self._horizon = horizon
        self._clock = clock
        self._batch_size = batch_size
        self._projected = frozenset(
            catalog.contract_for(event_cls).name for event_cls in PROJECTED_CONTRACTS
        )

    async def tick(self, session: AsyncSession) -> TickReport:
        """One pass. The whole of it is one transaction."""

        async with session.begin():
            cursor = await self._take_cursor(session)
            horizon = await self._horizon.current(session)
            log = await self._read_log(
                session, after=cursor.applied_through_sequence_no
            )
            plan = plan_tail(
                cursor=cursor.applied_through_sequence_no,
                sequence_nos=[row.sequence_no for row in log],
                observed_hole=_recorded_hole(cursor),
                horizon=horizon,
            )
            rows_moved = await self._apply(session, log=log, plan=plan)
            self._advance(cursor, plan)

        return TickReport(
            events_applied=len(plan.applicable),
            rows_moved=rows_moved,
            snapshot_version=plan.cursor_after,
            waiting_on_hole=plan.hole.sequence_no if plan.hole else None,
        )

    async def _take_cursor(self, session: AsyncSession) -> CandidateIndexCursorORM:
        """The single cursor row, held for the tick.

        ``FOR UPDATE`` renders on PostgreSQL and is dropped by the SQLite
        dialect, which is correct rather than a gap: the suite has one connection
        and no concurrent appender, so there is no second reader for it to serialise
        against.

        The row is created here if the migration's seed never ran — a projection
        with no cursor is at zero, and refusing to start would turn a fresh
        database into an incident.
        """

        cursor = (
            await session.execute(
                select(CandidateIndexCursorORM)
                .where(CandidateIndexCursorORM.projection == CANDIDATE_INDEX_CURSOR)
                .with_for_update()
            )
        ).scalar_one_or_none()
        if cursor is None:
            cursor = CandidateIndexCursorORM(
                projection=CANDIDATE_INDEX_CURSOR,
                applied_through_sequence_no=0,
                caught_up_at=self._clock.now(),
            )
            session.add(cursor)
        return cursor

    async def _read_log(
        self, session: AsyncSession, *, after: int
    ) -> Sequence[EventStoreORM]:
        """The next bounded batch, in append order.

        **Every row, not only the interesting ones.** Filtering in SQL would make
        a hole and an event this projection does not read indistinguishable, and
        the contiguous prefix is computed over the log's own numbering or it is
        computed over nothing.
        """

        return (
            (
                await session.execute(
                    select(EventStoreORM)
                    .where(EventStoreORM.sequence_no > after)
                    .order_by(EventStoreORM.sequence_no)
                    .limit(self._batch_size)
                )
            )
            .scalars()
            .all()
        )

    async def _apply(
        self,
        session: AsyncSession,
        *,
        log: Sequence[EventStoreORM],
        plan: TailPlan,
    ) -> int:
        """Fold the applicable events in, **one at a time and in append order.**

        Each moved row is stamped with **the sequence number of the event that
        moved it**, never with the batch's own end. That is what makes the stamp
        independent of how the log happened to be cut into batches — and
        therefore what makes ``rebuild == tail`` an equality over whole tables
        rather than over the columns somebody remembered to exclude. It costs the
        delta refresh nothing: a row moved by an event past a container's version
        still stamps past that version, which is the only question the refresh
        asks.

        **The two caches are correctness, not speed.** A row created by one event
        in this batch and moved again by the next must be the same object, and
        ``session.get`` would only find it after a flush — so this would work
        under an autoflushing session and quietly insert a duplicate under the
        one the lifespan actually builds (``autoflush=False``). Holding the
        objects makes the tick independent of that setting rather than dependent
        on it in a way nothing would notice.
        """

        applicable = set(plan.applicable)
        facts: dict[UUID, CandidatePlayerFactsORM] = {}
        rows: dict[tuple[UUID, str], CandidateRowORM] = {}
        touched: set[tuple[UUID, str | None]] = set()

        for stored in log:
            if stored.sequence_no not in applicable:
                continue
            if stored.event_type not in self._projected:
                continue
            for movement in project(self._decode(stored)):
                match movement:
                    case PlayerFactsMoved():
                        player_facts = await _facts_for(
                            session, facts, movement.player_id
                        )
                        for column, value in movement.changes.items():
                            setattr(player_facts, column, _jsonable(value))
                        player_facts.applied_through_sequence_no = stored.sequence_no
                        # A profile edit moves every one of that player's index
                        # rows, because the facts it changed are copied into each
                        # of them at read time. Restamping them here is what makes
                        # the delta refresh's single question — *which rows moved*
                        # — the right question to ask after an edit that touched
                        # no Level.
                        await _restamp_rows_of(
                            session,
                            held=rows,
                            player_id=movement.player_id,
                            through=stored.sequence_no,
                        )
                        touched.add((movement.player_id, None))
                    case CandidateRowMoved():
                        row = await _row_for(
                            session, rows, movement.player_id, movement.sport
                        )
                        for column, value in movement.changes.items():
                            setattr(row, column, value)
                        row.applied_through_sequence_no = stored.sequence_no
                        touched.add((movement.player_id, movement.sport))

        return len(touched)

    def _decode(self, stored: EventStoreORM) -> DomainEvent:
        return self._codec.decode(
            SerializedEventEnvelope(
                id=stored.id,
                event_type=stored.event_type,
                schema_version=stored.schema_version,
                payload=dict(stored.payload),
                occurred_at=stored.occurred_at,
                created_at=stored.created_at,
            )
        )

    def _advance(self, cursor: CandidateIndexCursorORM, plan: TailPlan) -> None:
        cursor.applied_through_sequence_no = plan.cursor_after
        cursor.hole_at_sequence_no = plan.hole.sequence_no if plan.hole else None
        cursor.hole_settles_at = plan.hole.settles_at if plan.hole else None
        # Stamped every tick, advance or not: this is *when the reader last knew
        # it was caught up*, which is the number staleness is measured from.
        cursor.caught_up_at = self._clock.now()


def _recorded_hole(cursor: CandidateIndexCursorORM) -> ObservedHole | None:
    if cursor.hole_at_sequence_no is None or cursor.hole_settles_at is None:
        return None
    return ObservedHole(
        sequence_no=cursor.hole_at_sequence_no, settles_at=cursor.hole_settles_at
    )


async def _facts_for(
    session: AsyncSession,
    held: dict[UUID, CandidatePlayerFactsORM],
    player_id: UUID,
) -> CandidatePlayerFactsORM:
    """This player's facts row — loaded, created, and held for the tick."""

    facts = held.get(player_id)
    if facts is None:
        facts = await session.get(CandidatePlayerFactsORM, player_id)
    if facts is None:
        facts = CandidatePlayerFactsORM(player_id=player_id)
        session.add(facts)
    held[player_id] = facts
    return facts


async def _row_for(
    session: AsyncSession,
    held: dict[tuple[UUID, str], CandidateRowORM],
    player_id: UUID,
    sport: str,
) -> CandidateRowORM:
    """This ``(player, sport)`` row — loaded, created, and held for the tick."""

    key = (player_id, sport)
    row = held.get(key)
    if row is None:
        row = await session.get(CandidateRowORM, key)
    if row is None:
        row = CandidateRowORM(player_id=player_id, sport=sport)
        session.add(row)
    held[key] = row
    return row


async def _restamp_rows_of(
    session: AsyncSession,
    *,
    held: dict[tuple[UUID, str], CandidateRowORM],
    player_id: UUID,
    through: int,
) -> None:
    """Mark every index row of this player as moved by ``through``.

    **Both halves, because the rows live in two places during a tick.** Rows this
    batch already touched are objects that may not have reached the database yet,
    so they are stamped in Python; everything else is stamped by one statement.
    A row in both is stamped twice with the same value, which is the harmless
    half of the overlap.

    ``synchronize_session=False`` because nothing in this transaction reads a
    stamp back through a query: the rows this tick cares about are the held ones,
    and they are already correct.
    """

    for (owner, _sport), row in held.items():
        if owner == player_id and row.applied_through_sequence_no < through:
            row.applied_through_sequence_no = through
    await session.execute(
        update(CandidateRowORM)
        .where(
            CandidateRowORM.player_id == player_id,
            CandidateRowORM.applied_through_sequence_no < through,
        )
        .values(applied_through_sequence_no=through)
        .execution_options(synchronize_session=False)
    )


def _jsonable(value: object) -> object:
    """A tuple becomes a list on the way into a JSON column; everything else passes.

    The projection speaks in tuples because the events do, and the column reads
    back a list either way — converting here rather than in the fold keeps the
    fold's output comparable to the events it came from.

    **Only the facts row needs it**, which is why the index row's own writes call
    ``setattr`` directly. Every column on ``candidate_row`` is a scalar — a
    Level, a band, a machine code — and the two collection-valued facts a player
    holds, their tags and their grid, are both on the facts row. A collection
    arriving on the index row would be a new kind of column and would need this
    on the way past.
    """

    if isinstance(value, tuple):
        return list(value)
    return value


__all__ = ["CandidateIndexTail", "TickReport"]
