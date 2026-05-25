from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import get_settings
from app.infrastructure.database.engine import get_engine, init_engine

_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _get_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        try:
            engine = get_engine()
        except RuntimeError:
            engine = init_engine(get_settings())
        _session_factory = async_sessionmaker(
            engine, expire_on_commit=False, autoflush=False
        )
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
