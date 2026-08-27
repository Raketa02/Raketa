import os

# Configure environment *before* importing application modules so settings pick it up.
# `local` — there is no `test` environment. A test run happens on a developer's own
# machine or on a CI runner, both of which are somebody's laptop as far as this
# application is concerned. Adding a fifth name would be a name for a *test suite*,
# and the four names describe where the software runs.
os.environ.setdefault("APP_ENV", "local")
os.environ.setdefault("JWT_SECRET_KEY", "test-secret-do-not-use-in-prod")
os.environ.setdefault("WRITER_DB_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("DB_SSL_MODE", "disable")
os.environ.setdefault("ACCESS_TOKEN_EXPIRE_SECONDS", "900")
os.environ.setdefault("REFRESH_TOKEN_EXPIRE_SECONDS", "3600")
os.environ.setdefault("LOG_JSON", "false")

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.config import get_settings  # noqa: E402
from app.infrastructure.database.base import Base  # noqa: E402
from app.infrastructure.database.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402  (also registers ORM models)
from app.modules.player_profile.presentation.dependencies import (  # noqa: E402
    get_photo_storage,
)
from tests.unit.fake_photo_storage import InMemoryPhotoStorage  # noqa: E402


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
    return async_sessionmaker(db_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
def photo_storage():
    """The object store every API test runs against.

    Requested by name when a test wants to look at what was stored; overridden
    on `client` regardless, so **no test in this suite needs MinIO running** —
    which is the acceptance criterion, not a convenience. A suite that only
    passes with a container up is a suite CI cannot be trusted to run.
    """

    return InMemoryPhotoStorage()


@pytest_asyncio.fixture
async def client(session_factory, photo_storage):
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
    app.dependency_overrides[get_photo_storage] = lambda: photo_storage
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def valid_signup_payload():
    return {
        "email": "alice@example.com",
        "password1": "hunter22!",
        "password2": "hunter22!",
        "nickname": "alice",
        "adult_attested": True,
    }
