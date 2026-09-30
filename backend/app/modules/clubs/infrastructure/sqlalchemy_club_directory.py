"""``ClubDirectory`` over the ``clubs`` search projection.

**"Anywhere in the field" is a scan**, and ``docs/adr/0182`` accepted that by
name: free at eight clubs and slow at eight thousand, with a trigram index as the
known next step. The query is folded here, by the function the stored copies
were folded by, and matched with ``LIKE`` escaped so that a ``%`` a player typed
is a percent sign.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.kernel import Sport
from app.modules.clubs.domain.folding import fold
from app.modules.clubs.domain.ports import ClubListing
from app.modules.clubs.infrastructure.club_model import ClubORM


class SqlAlchemyClubDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def listed(self, club_ids: Collection[UUID]) -> Mapping[UUID, ClubListing]:
        wanted = set(club_ids)
        if not wanted:
            return {}
        rows = (
            await self._session.scalars(select(ClubORM).where(ClubORM.id.in_(wanted)))
        ).all()
        return {row.id: _listing(row) for row in rows}

    async def inside(
        self,
        *,
        south: float,
        north: float,
        west: float,
        east: float,
    ) -> Sequence[ClubListing]:
        rows = (
            await self._session.scalars(
                select(ClubORM).where(
                    ClubORM.latitude.between(south, north),
                    ClubORM.longitude.between(west, east),
                )
            )
        ).all()
        return [_listing(row) for row in rows]

    async def matching(self, text: str) -> Sequence[ClubListing]:
        folded = fold(text)
        rows = (
            await self._session.scalars(
                select(ClubORM).where(
                    or_(
                        ClubORM.name_folded.contains(folded, autoescape=True),
                        ClubORM.district_folded.contains(folded, autoescape=True),
                    )
                )
            )
        ).all()
        return [_listing(row) for row in rows]


def _listing(row: ClubORM) -> ClubListing:
    return ClubListing(
        id=row.id,
        name=row.name,
        district=row.district,
        sports=tuple(Sport(code) for code in row.sports),
        latitude=row.latitude,
        longitude=row.longitude,
    )
