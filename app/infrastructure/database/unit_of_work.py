from __future__ import annotations

from typing import Protocol, runtime_checkable

from sqlalchemy.ext.asyncio import AsyncSession


@runtime_checkable
class UnitOfWork(Protocol):
    """Transactional boundary port consumed by use cases.

    Use cases call `commit()` after a successful write; the FastAPI dependency
    that yields the underlying session handles rollback on exception.
    """

    async def commit(self) -> None: ...
    async def flush(self) -> None: ...
    async def rollback(self) -> None: ...


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
