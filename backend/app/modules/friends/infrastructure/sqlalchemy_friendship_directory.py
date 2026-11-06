"""``FriendshipDirectory`` over ``friend_relations`` — the reader's side alone.

One statement per question, keyed on the reader (the primary key's prefix), and
``among`` an ``IN`` list for a face's set. **Same session as the write**, so an
act a moment ago is read by the read that follows it.
"""

from __future__ import annotations

from collections.abc import Collection
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import stored_instant
from app.kernel import Sport
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.ports import RelationRow
from app.modules.friends.domain.relation import FriendRelation, RequestOrigin
from app.modules.friends.infrastructure.friendship_model import FriendRelationORM


class SqlAlchemyFriendshipDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def rows_of(
        self, reader: UUID, *, among: Collection[UUID] | None = None
    ) -> tuple[RelationRow, ...]:
        statement = select(FriendRelationORM).where(
            FriendRelationORM.player_id == reader
        )
        if among is not None:
            wanted = sorted(set(among), key=str)
            if not wanted:
                return ()
            statement = statement.where(FriendRelationORM.other_id.in_(wanted))
        rows = (await self._session.scalars(statement)).all()
        return tuple(_row(row) for row in rows)


def _row(row: FriendRelationORM) -> RelationRow:
    return RelationRow(
        other_id=row.other_id,
        relation=FriendRelation(row.relation),
        since=stored_instant(row.since),
        set_aside=row.set_aside,
        where=None
        if row.made_from is None
        else Where(
            made_from=RequestOrigin(row.made_from),
            group_id=row.group_id,
            sport=None if row.sport is None else Sport(row.sport),
        ),
    )
