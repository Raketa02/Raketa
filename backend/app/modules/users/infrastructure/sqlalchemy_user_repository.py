from __future__ import annotations

from typing import Collection, Mapping, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.infrastructure.database.stored_time import stored_instant_or_none
from app.modules.users.domain.events import (
    AccountOpenedByInvitation,
    PasswordChanged,
    PasswordCleared,
    UserNamed,
    UserRegistered,
)
from app.modules.users.domain.ports import Naming
from app.modules.users.domain.user import User
from app.modules.users.domain.value_objects import (
    Authority,
    Email,
    HashedPassword,
    Name,
    Nickname,
)
from app.modules.users.infrastructure.sqlalchemy_user_model import UserORM


def _to_domain(row: UserORM) -> User:
    return User(
        id=row.id,
        email=Email(row.email),
        name=None if row.name is None else Name(row.name),
        nickname=None if row.nickname is None else Nickname(row.nickname),
        password_hash=(
            None if row.password_hash is None else HashedPassword(row.password_hash)
        ),
        authority=Authority(row.authority),
        is_admin=row.is_admin,
        is_active=row.is_active,
        credentials_changed_at=stored_instant_or_none(row.credentials_changed_at),
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


def _to_orm(user: User) -> UserORM:
    return UserORM(
        id=user.id,
        email=user.email.value,
        name=None if user.name is None else user.name.value,
        nickname=None if user.nickname is None else user.nickname.value,
        password_hash=None if user.password_hash is None else user.password_hash.value,
        authority=user.authority.value,
        is_admin=user.is_admin,
        is_active=user.is_active,
    )


def _projection_from_registered(event: UserRegistered) -> UserORM:
    return UserORM(
        id=event.user_id,
        email=event.email,
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

    async def find_disabled_among(
        self, user_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        ids = list(user_ids)
        if not ids:
            # `IN ()` is not portable SQL and SQLAlchemy warns rather than
            # answering; an empty ask has an empty answer without a round trip.
            return frozenset()
        result = await self._session.execute(
            select(UserORM.id).where(
                UserORM.id.in_(ids), UserORM.is_active.is_(False)
            )
        )
        return frozenset(result.scalars().all())

    async def find_namings_of(
        self, user_ids: Collection[UUID]
    ) -> Mapping[UUID, Naming]:
        ids = list(user_ids)
        if not ids:
            # `IN ()` is not portable SQL, exactly as above.
            return {}
        result = await self._session.execute(
            select(UserORM.id, UserORM.name, UserORM.nickname).where(
                UserORM.id.in_(ids),
                # An unnamed account is absent, not present with a blank: the
                # port promises the pair or nothing.
                UserORM.name.is_not(None),
                UserORM.nickname.is_not(None),
            )
        )
        return {
            row.id: Naming(name=row.name, nickname=row.nickname) for row in result
        }

    async def add(self, user: User) -> User:
        row = _to_orm(user)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def project_registered(self, event: UserRegistered) -> User:
        row = _projection_from_registered(event)
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def project_opened_by_invitation(
        self, event: AccountOpenedByInvitation
    ) -> User:
        row = UserORM(
            id=event.user_id,
            email=event.email,
            name=event.name,
            password_hash=event.password_hash,
            authority="USER",
            is_admin=False,
            is_active=True,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def project_named(self, event: UserNamed) -> User:
        row = await self._session.get(UserORM, event.user_id)
        if row is None:
            raise RuntimeError(
                f"the naming of {event.user_id} has no projection row to land on"
            )
        row.name = event.name
        row.nickname = event.nickname
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def project_password_changed(self, event: PasswordChanged) -> None:
        row = await self._session.get(UserORM, event.user_id)
        if row is None:
            raise RuntimeError(
                f"the password of {event.user_id} has no projection row to land on"
            )
        row.password_hash = event.password_hash
        row.credentials_changed_at = event.occurred_at
        await self._session.flush()

    async def project_password_cleared(self, event: PasswordCleared) -> None:
        row = await self._session.get(UserORM, event.user_id)
        if row is None:
            raise RuntimeError(
                f"the cleared password of {event.user_id} has no projection row "
                f"to land on"
            )
        row.password_hash = None
        row.credentials_changed_at = event.occurred_at
        await self._session.flush()
