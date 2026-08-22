"""The two schedule queries, over the two schedule columns.

ADR-0076's *"one worker, three queries, one tick"*: the outbox's ``SELECT``, this
one, and — when there is a channel to schedule sends for (``Raketa02/Raketa#84``)
— a third beside it. No new interval, no second process, no Redis.

**``due`` is shaped like the outbox's fetch and for the same reason.**
``FOR UPDATE SKIP LOCKED`` is what lets N processes poll the same table with no
leader election and no distributed lock, which is the property ADR-0076 leans on
when it says the timekeeper can be scaled *"with no code change"*. SQLite has no
such clause and ignores it, which is correct rather than tolerated: the fast
suite is single-writer, so there is nothing to skip.

**Neither statement touches ``version``.** Reading the schedule is not reading
the match, and arming it is not changing one — the columns are derived, so
nothing about them is a fact anybody could ask to have explained. What ``re_arm``
does compare the version against is the row it was read at, so a real writer that
moved the match in between keeps its own, better answer.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, cast
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Boundary, Instant, WakeReason, instant

from app.modules.matches.domain.wake import MatchWake
from app.modules.matches.infrastructure.sqlalchemy_match_models import MatchORM


class SqlAlchemyMatchSchedule:
    """SQLAlchemy adapter for ``next_wake_at`` and ``wake_reason``."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def due(self, *, now: Instant, limit: int) -> list[MatchWake]:
        rows = (
            await self._session.execute(
                select(MatchORM.id, MatchORM.wake_reason, MatchORM.next_wake_at)
                .where(
                    MatchORM.next_wake_at.is_not(None),
                    MatchORM.next_wake_at <= now,
                )
                # Soonest first, broken by id. The tie-break is only about
                # determinism — two matches due in the same millisecond are two
                # independent looks — but an ambiguous ORDER BY under a LIMIT is
                # a row that can be starved out of every batch by a neighbour.
                .order_by(MatchORM.next_wake_at, MatchORM.id)
                .limit(limit)
                .with_for_update(skip_locked=True)
            )
        ).all()
        return [
            MatchWake(
                match_id=row.id,
                reason=WakeReason(row.wake_reason),
                scheduled_for=_as_instant(row.next_wake_at),
            )
            for row in rows
        ]

    async def re_arm(
        self, *, match_id: UUID, version: int, wake: Boundary | None
    ) -> bool:
        result = await self._session.execute(
            update(MatchORM)
            .where(MatchORM.id == match_id, MatchORM.version == version)
            .values(
                next_wake_at=None if wake is None else wake.at,
                wake_reason=None if wake is None else wake.reason.value,
            )
        )
        # `session.execute` is typed as returning `Result`, which has no
        # `rowcount`; a DML statement always yields a `CursorResult`, which does.
        return cast(CursorResult[Any], result).rowcount == 1


def _as_instant(value: datetime) -> Instant:
    """Re-attach UTC to what SQLite dropped, then normalise."""

    return instant(value if value.tzinfo else value.replace(tzinfo=timezone.utc))
