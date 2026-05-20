from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.infrastructure.database.engine import get_engine, init_engine

_session_factory: Optional[sessionmaker] = None


def _get_factory() -> sessionmaker:
    global _session_factory
    if _session_factory is None:
        try:
            engine = get_engine()
        except RuntimeError:
            engine = init_engine(get_settings())
        _session_factory = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
        )
    return _session_factory


def reset_session_factory() -> None:
    """Drop the cached factory — used by tests after engine re-init."""
    global _session_factory
    _session_factory = None


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = _get_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
