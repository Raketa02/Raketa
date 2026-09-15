"""``DeckResetLedger`` over SQLAlchemy. **It adds rows and it never commits.**

The transaction boundary is the command's decision, exactly as it is for the
pass ledger and the interest ledger beside it.

**There is no delete and no update here.** A reset is a moment that happened,
and nothing but erasure will ever remove one, so a method for either would be a
method somebody reaches for.

**Nothing here can answer a question a route could ask.** One write, one read
answering a moment or ``None``: the port declares exactly those, and this
implements exactly those, so *no route ever returns a reset* is a property of
the shapes that exist rather than of the routes that happen to have been
written.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Instant, Sport, instant
from app.modules.matchmaking.domain.deck_reset import DeckReset
from app.modules.matchmaking.infrastructure.deck_reset_model import DeckResetORM
from app.shared.ids import new_uuid


class SqlAlchemyDeckResetLedger:
    """The durable record of every *Show them again*, over the caller's session."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def record(self, reset: DeckReset) -> None:
        """Append one reset. The caller commits.

        The id is minted here rather than carried on :class:`DeckReset`, because
        it is a storage identity and nothing in the domain, in a response or in
        a falsifier ever names it: what identifies a reset to anybody who asks is
        the player, the sport and the moment.
        """

        self._session.add(
            DeckResetORM(
                id=new_uuid(),
                player_id=reset.player_id,
                sport=reset.sport.value,
                reset_at=reset.at,
            )
        )
        await self._session.flush()

    async def latest_at(self, *, player_id: UUID, sport: Sport) -> Instant | None:
        """The most recent press for this player and sport, or ``None``.

        A ``max`` over the keyed range rather than the rows fetched and folded:
        the table is append-only, a player may hold several, and the latest is
        the only one the deal reads.
        """

        latest = await self._session.scalar(
            select(func.max(DeckResetORM.reset_at)).where(
                DeckResetORM.player_id == player_id,
                DeckResetORM.sport == sport.value,
            )
        )
        return None if latest is None else _utc(latest)


def _utc(value: datetime) -> Instant:
    """A stored moment, read back as the UTC it was written as.

    The same seam the pass ledger has, for the same reason: PostgreSQL's
    ``timestamptz`` carries the offset and SQLite does not, and the value was
    written as UTC — so reading it as anything else would move it, which here
    would move what a reset cleared by hours.
    """

    if value.tzinfo is None or value.utcoffset() is None:
        return instant(value.replace(tzinfo=timezone.utc))
    return instant(value)
