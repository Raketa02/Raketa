"""``CommandLog`` over one table, and the prune that keeps it from growing.

Two operations and one sweep. Everything about the window is applied on the
**read** — a row past twenty-four hours is not a replay whether or not anything
has deleted it yet — so correctness never depends on the prune having run, and
the prune is free to be opportunistic.

**The prune runs on the write, not on a schedule.** ADR-0030 names *"a new thing
to prune"* as this decision's cost, and a scheduled job would be a second moving
part with its own deploy, its own failure mode and nothing watching it. One
indexed delete per destructive command, scoped to that command's own rows, keeps
the table bounded by *how many of these were sent in the last day* — which is
the only number it should ever be bounded by.

**Neither operation commits.** The log row joins the transaction its command is
written in; a log that could disagree with the write it describes is the one
state that makes a replay dangerous rather than merely useless.
"""

from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports import COMMAND_LOG_WINDOW_HOURS, LoggedCommand
from app.infrastructure.database.command_log_model import CommandLogORM
from app.kernel import Instant, hours, instant, shifted


class SqlAlchemyCommandLog:
    """What has already been done, under the key the client chose for it."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def recall(
        self, *, command: str, key: str, now: Instant
    ) -> LoggedCommand | None:
        """The first application under this key, if it is still inside 24 hours.

        The stored moment is **normalised before it is compared**, and that is
        not tidiness: SQLite hands a naive value back where PostgreSQL hands an
        aware one, so the comparison is a `TypeError` on the fast suite and
        correct in production — the worst available split, because the fast
        suite is the one that runs on every change.
        """

        row = await self._session.get(CommandLogORM, (command, key))
        if row is None:
            return None
        recorded = instant(_aware(row.recorded_at))
        if recorded < _window_opens(now):
            # Past its twenty-four hours. Answered as *never seen* rather than
            # deleted here: a read that writes is a read that cannot be taken
            # inside somebody else's transaction, and the next write of this
            # command sweeps it anyway.
            return None
        return LoggedCommand(
            command=row.command,
            key=row.key,
            player_id=row.player_id,
            result=row.result,
            recorded_at=recorded,
        )

    async def remember(self, entry: LoggedCommand) -> None:
        await self._session.execute(
            delete(CommandLogORM).where(
                CommandLogORM.command == entry.command,
                CommandLogORM.recorded_at < _window_opens(entry.recorded_at),
            )
        )
        self._session.add(
            CommandLogORM(
                command=entry.command,
                key=entry.key,
                player_id=entry.player_id,
                result=entry.result,
                recorded_at=entry.recorded_at,
            )
        )
        # Flushed rather than left pending, so a second command under the same
        # key inside one transaction collides here instead of at commit, where
        # the failure would name a statement nobody wrote.
        await self._session.flush()


def _aware(value: datetime) -> datetime:
    """A stored moment with its zone put back if the driver dropped it.

    SQLite has no timezone type, so ``DateTime(timezone=True)`` round-trips
    naive there and aware on PostgreSQL. Every moment in this table was written
    as UTC by ``Instant``, so restoring UTC is stating what the write meant
    rather than guessing.
    """

    return value if value.tzinfo is not None else value.replace(tzinfo=timezone.utc)


def _window_opens(now: Instant) -> Instant:
    """The oldest moment a row may carry and still answer for its command."""

    return shifted(now, hours(-COMMAND_LOG_WINDOW_HOURS))
