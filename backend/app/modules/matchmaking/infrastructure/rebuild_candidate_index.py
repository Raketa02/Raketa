"""Drop the candidate index and fold the whole log back into it.

**A one-shot operation, reached by a ``make`` target and never by a route**
(``docs/adr/0110``). A button that drops and rebuilds the index is a button that
is eventually pressed in the wrong place; ``docs/adr/0092``'s register is for
loops, and this is not one. The engineer-facing promise is that **a corrupt
projection is a command, not an incident.**

**It replays through the same tail reader, and that is deliberate rather than
lazy.** A second folder would be a second answer, and the two would agree with
each other's tests while disagreeing with the index — the failure the
judged-pairings harness already refuses in its own domain. What differs between a
rebuild and a tail is only the *schedule*: a rebuild is one long run of large
batches over a log that is not moving, a tail is a tick a second over one that
is. ``rebuild == tail`` is therefore the assertion that **the fold does not
depend on how the log was cut into batches**, which is the same thing as saying
it is a pure function of the log — and it is exactly what would be false if the
projection had a bug.

**It lives in ``infrastructure/`` and not in ``application/``, and the rule
decides that rather than taste.** A use case depends on ports; this one empties
two tables and resets a watermark, which is SQL about this projection's own
schema. Putting it a layer in would have meant inventing a port whose single
implementation is the statement below, and a port with one caller and one
implementation is a layer, not a seam.

**The wall clock is a metric this logs, never a bound anything asserts.** A
five-minute bound on a shared CI runner is a flaky test that gets muted. Measured,
the projection is not the constraint anyway: 959 000 events/s on one core, 1.0 s
of CPU for a 50 000-player city — the read and the write batching set the wall
clock.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import final

from sqlalchemy import delete, update
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.kernel import Clock
from app.modules.matchmaking.infrastructure.candidate_index_model import (
    CANDIDATE_INDEX_CURSOR,
    CandidateIndexCursorORM,
    CandidatePlayerFactsORM,
    CandidateRowORM,
)
from app.modules.matchmaking.infrastructure.candidate_index_tail import (
    CandidateIndexTail,
)

logger = logging.getLogger(__name__)

#: The name this operation reports under. It is not a job — nothing schedules it.
REBUILD_NAME = "candidate-index-rebuild"


@final
@dataclass(frozen=True, slots=True)
class RebuildReport:
    """What the rebuild folded in, and how long it took to do it."""

    events_applied: int
    rows_moved: int
    snapshot_version: int
    ticks: int
    seconds: float
    #: The gap the rebuild could not cross, if it stopped at one.
    #:
    #: **A rebuild is not finished just because a tick applied nothing.** On
    #: PostgreSQL a tick also applies nothing while it is waiting on a hole whose
    #: horizon has not settled, and a run that exited quietly there would have
    #: rebuilt a *prefix* of the log while reporting success — which is
    #: ``rebuild == tail`` failing in the one place nobody would look. So the
    #: hole travels out with the report, the command prints it, and the exit
    #: status says so.
    waiting_on_hole: int | None

    @property
    def reached_the_end_of_the_log(self) -> bool:
        return self.waiting_on_hole is None


@final
class RebuildCandidateIndex:
    """Empty the two projected tables, reset the cursor, and tail from zero."""

    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
        tail: CandidateIndexTail,
        clock: Clock,
    ) -> None:
        self._session_factory = session_factory
        self._tail = tail
        self._clock = clock

    async def execute(self) -> RebuildReport:
        started = self._clock.now()
        async with self._session_factory() as session:
            await self._empty(session)

        events = 0
        rows = 0
        ticks = 0
        version = 0
        waiting_on_hole = None
        while True:
            async with self._session_factory() as session:
                report = await self._tail.tick(session)
            ticks += 1
            events += report.events_applied
            rows += report.rows_moved
            version = report.snapshot_version
            waiting_on_hole = report.waiting_on_hole
            # A tick that applied nothing has reached the end of the log — **or**
            # a hole it cannot cross, and the two are emphatically not the same
            # outcome. Looping would spin either way, so the run stops; what
            # distinguishes them is the hole, which travels out on the report.
            if report.events_applied == 0:
                break

        rebuilt = RebuildReport(
            events_applied=events,
            rows_moved=rows,
            snapshot_version=version,
            ticks=ticks,
            seconds=(self._clock.now() - started).total_seconds(),
            waiting_on_hole=waiting_on_hole,
        )
        logger.log(
            logging.INFO if rebuilt.reached_the_end_of_the_log else logging.ERROR,
            "candidate index rebuilt"
            if rebuilt.reached_the_end_of_the_log
            else "candidate index rebuild stopped short of the log",
            extra={
                "job": REBUILD_NAME,
                "events_applied": rebuilt.events_applied,
                "rows_moved": rebuilt.rows_moved,
                "snapshot_version": rebuilt.snapshot_version,
                "ticks": rebuilt.ticks,
                # The metric §7.4 keeps, and the number nothing asserts.
                "seconds": rebuilt.seconds,
                "waiting_on_hole": rebuilt.waiting_on_hole,
            },
        )
        return rebuilt

    async def _empty(self, session: AsyncSession) -> None:
        """Both projected tables emptied and the watermark reset, in one transaction.

        The cursor is **reset rather than deleted**: *the projection has never
        run* and *the projection is broken* are different observations, and a
        missing cursor row makes them look the same.
        """

        async with session.begin():
            await session.execute(delete(CandidateRowORM))
            await session.execute(delete(CandidatePlayerFactsORM))
            await session.execute(
                update(CandidateIndexCursorORM)
                .where(CandidateIndexCursorORM.projection == CANDIDATE_INDEX_CURSOR)
                .values(
                    applied_through_sequence_no=0,
                    hole_at_sequence_no=None,
                    hole_settles_at=None,
                )
            )


__all__ = ["REBUILD_NAME", "RebuildCandidateIndex", "RebuildReport"]
