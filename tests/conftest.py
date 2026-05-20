import os

# Configure environment *before* importing application modules so settings pick it up.
os.environ.setdefault("ENV", "test")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-do-not-use-in-prod")
os.environ.setdefault("WRITER_DB_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DB_SSL_MODE", "disable")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_SECONDS", "900")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_SECONDS", "3600")
os.environ.setdefault("LOG_JSON", "false")

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings  # noqa: E402
from app.infrastructure.database.base import Base  # noqa: E402
from app.infrastructure.database.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402  (also registers ORM models)


@pytest_asyncio.fixture
async def db_engine():
    # Per-test in-memory SQLite, single shared connection so each request sees
    # the same data. StaticPool gives all sessions the same underlying conn.
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def session_factory(db_engine):
    return sessionmaker(db_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def client(session_factory):
    get_settings.cache_clear()
    app = create_app()

    async def _get_db_override():
        async with session_factory() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = _get_db_override
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def valid_signup_payload():
    return {
        "email": "alice@example.com",
        "password1": "hunter22!",
        "password2": "hunter22!",
        "nickname": "alice",
    }
