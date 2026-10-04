from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.auth.domain.audience import Audience
from app.modules.auth.domain.refresh_token import RefreshToken
from app.modules.auth.infrastructure.sqlalchemy_refresh_token_model import (
    RefreshTokenORM,
)


#: The column each audience's account is recorded in — **the one place the
#: two are paired**. Each audience has one kind of account behind it
#: (``auth/domain/audience.py``), so the column a row fills is also the audience
#: its token was issued for; the table's check constraint guarantees exactly one.
_HOLDER_COLUMN: dict[Audience, str] = {
    Audience.PLAYER_APP: "user_id",
    Audience.CLUB: "club_account_id",
}


def _holder_of(row: RefreshTokenORM) -> tuple[UUID, Audience]:
    """Whose the row is, read off the one column it fills."""

    for audience, column in _HOLDER_COLUMN.items():
        account_id = getattr(row, column)
        if account_id is not None:
            return account_id, audience
    raise RuntimeError(f"refresh token {row.id} names no account")


def _to_domain(row: RefreshTokenORM) -> RefreshToken:
    account_id, audience = _holder_of(row)
    return RefreshToken(
        id=row.id,
        account_id=account_id,
        audience=audience,
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
            token_hash=token.token_hash,
            jti=token.jti,
            refresh_expires_at=token.refresh_expires_at,
            is_valid=token.is_valid,
            revoked_at=token.revoked_at,
        )
        setattr(row, _HOLDER_COLUMN[token.audience], token.account_id)
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

    async def valid_tokens_of(
        self, account_id: UUID, *, audience: Audience
    ) -> list[RefreshToken]:
        holder = getattr(RefreshTokenORM, _HOLDER_COLUMN[audience])
        result = await self._session.execute(
            select(RefreshTokenORM)
            .where(holder == account_id, RefreshTokenORM.is_valid.is_(True))
            .order_by(RefreshTokenORM.created_at, RefreshTokenORM.id)
        )
        return [_to_domain(row) for row in result.scalars().all()]
