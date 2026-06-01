from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.unit_of_work import UnitOfWork


class AsyncSqlAlchemyUnitOfWork:
    """Thin adapter wrapping an `AsyncSession` so use cases don't depend on
    SQLAlchemy directly."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def commit(self) -> None:
        await self._session.commit()

    async def flush(self) -> None:
        await self._session.flush()

    async def rollback(self) -> None:
        await self._session.rollback()

    @property
    def session(self) -> AsyncSession:
        return self._session


__all__ = ["AsyncSqlAlchemyUnitOfWork", "UnitOfWork"]
