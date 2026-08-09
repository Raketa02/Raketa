from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.refresh_token import RefreshToken
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_model import (
    RefreshTokenORM,
)


def _to_domain(row: RefreshTokenORM) -> RefreshToken:
    return RefreshToken(
        id=row.id,
        user_id=row.user_id,
        token_hash=row.token_hash,
        jti=row.jti,
        refresh_expires_at=row.refresh_expires_at,
        is_valid=row.is_valid,
        revoked_at=row.revoked_at,
        created_at=row.created_at,
        updated_at=row.updated_at,
    )


class SqlAlchemyRefreshTokenRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def add(self, token: RefreshToken) -> RefreshToken:
        row = RefreshTokenORM(
            id=token.id,
            user_id=token.user_id,
            token_hash=token.token_hash,
            jti=token.jti,
            refresh_expires_at=token.refresh_expires_at,
            is_valid=token.is_valid,
            revoked_at=token.revoked_at,
        )
        self._session.add(row)
        await self._session.flush()
        await self._session.refresh(row)
        return _to_domain(row)

    async def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        result = await self._session.execute(
            select(RefreshTokenORM).where(RefreshTokenORM.jti == jti)
        )
        row = result.scalar_one_or_none()
        return _to_domain(row) if row else None

    async def revoke(self, token: RefreshToken, *, now: datetime) -> None:
        result = await self._session.execute(
            select(RefreshTokenORM).where(RefreshTokenORM.jti == token.jti)
        )
        row = result.scalar_one_or_none()
        if row is None:
            return
        row.is_valid = False
        row.revoked_at = now
        await self._session.flush()
