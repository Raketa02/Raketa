"""``RequestsCounted`` over ``friend_requests_counted`` (#773).

One statement: a count over a range on the primary key's prefix — the
requester, then every instant since their Warsaw midnight. **Same session as
the write**, so a request counted a moment ago in the transaction is counted.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Instant
from app.modules.friends.infrastructure.friendship_model import (
    FriendRequestCountedORM,
)


class SqlAlchemyRequestsCounted:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def counted_since(self, requester: UUID, since: Instant) -> int:
        counted = await self._session.scalar(
            select(func.count()).where(
                FriendRequestCountedORM.requester_id == requester,
                FriendRequestCountedORM.asked_at >= since,
            )
        )
        return int(counted or 0)


__all__ = ["SqlAlchemyRequestsCounted"]
