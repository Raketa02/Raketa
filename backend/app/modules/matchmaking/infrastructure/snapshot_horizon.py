"""Whether a hole in the log can still be filled — and where that is knowable.

A gap in ``sequence_no`` is either a transaction still in flight or one that
aborted, and from a reader's side the two are indistinguishable. What tells them
apart is the store's **transaction horizon**, read as a pair: the oldest id still
running, and the first id not yet handed out. Whoever holds a missing sequence
number took it before the hole was seen, so their id is below that second number
— and once the oldest running id has *reached* it, they have all finished and the
cursor may step over the hole (``docs/adr/0110``). Why it takes two numbers and
not one is argued in ``candidate_tail``, beside the comparison itself.

**``xmin`` is PostgreSQL-specific, and the alternative was worse.** A safety lag
— consume only rows older than ``statement_timeout`` — needs no horizon and is
provably past any live transaction, and it spends the entire timeout out of a 2 s
freshness target for a race whose real duration is milliseconds. A second,
commit-ordered column on ``event_store`` is correct and is a second write on every
append to the platform's hottest table, for a property ``xmin`` already exposes.

**On SQLite the answer is ``None``, and that is honest rather than degraded.**
There is no snapshot horizon there and no concurrent appender, so a hole cannot
be proven permanent and is never stepped over: the run asserts contiguity, and
the gap-stepping path is exercised against PostgreSQL or not at all. That is a
place the suite is weaker than production and it is recorded — here, in
``docs/adr/0110`` and in the spec — rather than papered over with a fake number
that would make the wait end for the wrong reason.
"""

from __future__ import annotations

from typing import Mapping, Protocol, final, runtime_checkable

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.matchmaking.domain.candidate_tail import SnapshotBounds


@runtime_checkable
class SnapshotHorizon(Protocol):
    """Where the store's running transactions begin and end, right now."""

    async def current(self, session: AsyncSession) -> SnapshotBounds | None:
        """The bounds now, or ``None`` where the dialect has no such thing."""
        ...


@final
class PostgresSnapshotHorizon:
    """``pg_current_snapshot()``, as its two ends. One cheap read per tick."""

    async def current(self, session: AsyncSession) -> SnapshotBounds | None:
        # Through `text` because the values are `xid8`s, which have no ordering
        # operators against a bigint until they are cast — and the cast has to
        # happen in the database rather than in Python, where the wraparound the
        # 64-bit type exists to avoid would come back.
        row = (
            await session.execute(
                text(
                    "SELECT pg_snapshot_xmin(pg_current_snapshot())::text::bigint,"
                    "       pg_snapshot_xmax(pg_current_snapshot())::text::bigint"
                )
            )
        ).one()
        return SnapshotBounds(oldest_running=int(row[0]), next_unassigned=int(row[1]))


@final
class NoSnapshotHorizon:
    """There is no horizon here, and a hole is therefore waited on for ever.

    A **null object named for the fact it asserts**, in the idiom
    ``NoHoldsExist`` established: *null* would read as *not wired yet*, and this
    is wired. It says something true about SQLite, and it stops being the right
    answer on the day this projection runs anywhere else.
    """

    async def current(self, session: AsyncSession) -> SnapshotBounds | None:
        return None


@final
class DialectSnapshotHorizon:
    """Routes to whichever horizon the session's own database can answer with.

    **It routes and never chooses.** Both implementations are handed to it by
    ``app/bootstrap/composition.py``, because that is where a choice of adapter
    is made in this codebase and a dispatcher that constructed its own targets
    would be a second place that made one. What is decided *here* is not which
    adapter exists but which of them this session can be asked — and that is a
    fact about the connection, read per call rather than frozen at wiring time.

    **By dialect and never by environment.** Which holes a reader steps over is
    behaviour a test can observe, and ``docs/adr/0028`` reserves the environment
    for configuration.
    """

    def __init__(
        self,
        *,
        by_dialect: Mapping[str, SnapshotHorizon],
        otherwise: SnapshotHorizon,
    ) -> None:
        self._by_dialect = dict(by_dialect)
        self._otherwise = otherwise

    async def current(self, session: AsyncSession) -> SnapshotBounds | None:
        dialect = session.get_bind().dialect.name
        return await self._by_dialect.get(dialect, self._otherwise).current(session)


__all__ = [
    "DialectSnapshotHorizon",
    "NoSnapshotHorizon",
    "PostgresSnapshotHorizon",
    "SnapshotHorizon",
]
