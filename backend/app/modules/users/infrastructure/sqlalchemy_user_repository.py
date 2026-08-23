from __future__ import annotations

from datetime import datetime
from typing import Optional, Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.domain.events import UserRegistered
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import (
    Authority,
    Email,
    HashedPassword,
    Nickname,
)
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM


def _to_domain(row: UserORM) -> User:
    return User(
        id=row.id,
        email=Email(row.email),
        nickname=Nickname(row.nickname),
        password_hash=HashedPassword(row.password_hash),
        authority=Authority(row.authority),
        is_admin=row.is_admin,
        is_active=row.is_active,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_orm(user: User) -> UserORM:
    return UserORM(
        id=user.id,
        email=user.email.value,
        nickname=user.nickname.value,
        password_hash=user.password_hash.value,
        authority=user.authority.value,
        is_admin=user.is_admin,
        is_active=user.is_active,
    )


def _projection_from_registered(event: UserRegistered) -> UserORM:
    return UserORM(
        id=event.user_id,
        email=event.email,
        nickname=event.nickname,
        password_hash=event.password_hash,
        authority=event.authority,
        is_admin=event.is_admin,
        is_active=event.is_active,
    )


class SqlAlchemyUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM).where(UserORM.id == user_id)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM).where(UserORM.email == email)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def get_by_nickname(self, nickname: str) -> Optional[User]:
        result = await self._session.execute(
            select(UserORM).where(UserORM.nickname == nickname)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def add(self, user: User) -> User:
        row = _to_orm(user)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def find_registered_since(self, moment: datetime) -> list[User]:
        result = await self._session.execute(
            select(UserORM)
            .where(UserORM.created_at >= moment)
            .order_by(UserORM.created_at.desc(), UserORM.nickname)
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def find_by_ids(self, user_ids: Sequence[UUID]) -> list[User]:
        if not user_ids:
            # `IN ()` is not portable and a round trip to learn nothing is a
            # round trip on the busiest read in the product.
            return []
        result = await self._session.execute(
            select(UserORM).where(UserORM.id.in_(list(user_ids)))
        )
        return [_to_domain(row) for row in result.scalars().all()]

    async def project_registered(self, event: UserRegistered) -> User:
        row = _projection_from_registered(event)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)
