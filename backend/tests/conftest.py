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

from app.bootstrap.composition import (  # noqa: E402
    forget_the_movable_clock,
)
from app.core.config import get_settings  # noqa: E402
from app.infrastructure.database.base import Base  # noqa: E402
from app.infrastructure.database.session import get_db  # noqa: E402
from app.main import create_app  # noqa: E402  (also registers ORM models)


@pytest.fixture(autouse=True)
def put_the_clock_back():
    """No test inherits another's scrub, and none has to remember to say so.

    The one real cost of ADR-0092 is written down in the issue that asked for
    it: *"a clock a request can move is a clock a test can forget to put back."*
    This is the answer, and it is autouse because a fixture each test opts into
    is the same discipline it replaces. Nothing builds a movable clock unless a
    test turns `CLOCK_SCRUBBABLE` on, so for the whole suite bar one file this
    costs a dictionary lookup.
    """

    forget_the_movable_clock()
    yield
    forget_the_movable_clock()


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
    }
