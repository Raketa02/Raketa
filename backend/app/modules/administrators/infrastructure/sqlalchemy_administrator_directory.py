"""``AdministratorDirectory`` over the ``administrators`` row."""

from __future__ import annotations

from collections.abc import Collection, Sequence
from typing import Optional
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import stored_instant_or_none
from app.kernel import Instant
from app.modules.administrators.domain.administrator import AdministratorState
from app.modules.administrators.domain.ports import AdministratorListing
from app.modules.administrators.infrastructure.administrator_model import (
    AdministratorORM,
)
from app.modules.users.domain.value_objects import Email


class SqlAlchemyAdministratorDirectory:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def of_club(self, club_id: UUID) -> Sequence[AdministratorListing]:
        return await self._listings(
            AdministratorORM.club_id == club_id,
            AdministratorORM.state != AdministratorState.REMOVED.value,
        )

    async def active_for(self, account_id: UUID) -> Sequence[AdministratorListing]:
        return await self._listings(
            AdministratorORM.account_id == account_id,
            AdministratorORM.state == AdministratorState.ACTIVE.value,
        )

    async def active_at(
        self, club_id: UUID, account_id: UUID
    ) -> Optional[AdministratorListing]:
        found = await self._listings(
            AdministratorORM.club_id == club_id,
            AdministratorORM.account_id == account_id,
            AdministratorORM.state == AdministratorState.ACTIVE.value,
        )
        return found[0] if found else None

    async def active_among(
        self, administrator_ids: Collection[UUID]
    ) -> Sequence[AdministratorListing]:
        wanted = set(administrator_ids)
        if not wanted:
            return []
        return await self._listings(
            AdministratorORM.id.in_(wanted),
            AdministratorORM.state == AdministratorState.ACTIVE.value,
        )

    async def invited_as(self, email: Email) -> Sequence[AdministratorListing]:
        return await self._listings(
            AdministratorORM.email == email.value,
            AdministratorORM.state == AdministratorState.INVITED.value,
        )

    async def record_use(self, administrator_id: UUID, *, at: Instant) -> None:
        await self._session.execute(
            update(AdministratorORM)
            .where(AdministratorORM.id == administrator_id)
            .values(last_used_at=at)
        )

    async def _listings(self, *conditions) -> list[AdministratorListing]:
        rows = (
            await self._session.scalars(select(AdministratorORM).where(*conditions))
        ).all()
        return [_listing(row) for row in rows]


def _listing(row: AdministratorORM) -> AdministratorListing:
    return AdministratorListing(
        id=row.id,
        club_id=row.club_id,
        email=row.email,
        name=row.name,
        state=AdministratorState(row.state),
        account_id=row.account_id,
        expires_at=stored_instant_or_none(row.expires_at),
        last_used_at=stored_instant_or_none(row.last_used_at),
    )
