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

from app.bootstrap.composition import build_clock  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.infrastructure.database.base import Base  # noqa: E402
from app.infrastructure.database.session import get_db  # noqa: E402
from app.infrastructure.redis_client import (  # noqa: E402
    get_redis,
    get_redis_subscriber,
)
from app.main import create_app  # noqa: E402  (also registers ORM models)
from app.modules.player_profile.infrastructure.passthrough_photo_review import (  # noqa: E402,E501
    PassThroughPhotoReview,
)
from app.modules.matchmaking.infrastructure.candidate_snapshot_source import (  # noqa: E402,E501
    DatabaseCandidateSource,
)
from app.modules.matchmaking.presentation.dependencies import (  # noqa: E402
    get_candidate_source,
    get_exposure_ledger,
    get_prompt_ledger,
    get_suppression_ledger,
)
from app.modules.player_profile.presentation.dependencies import (  # noqa: E402
    get_photo_review,
    get_photo_storage,
)
from tests.unit.fake_ledgers import (  # noqa: E402
    InMemoryExposureLedger,
    InMemoryPromptLedger,
    InMemorySuppressionLedger,
)
from tests.unit.fake_redis import FakeRedis  # noqa: E402
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


@pytest.fixture
def photo_review():
    """The reviewer every API test runs against, and it concludes nothing.

    Overridden on `client` for the same reason the store is: **no test in this
    suite needs the photo-review sidecar running.** A CLIP container is a
    gigabyte of model weights, and a suite that only passes with one up is a
    suite CI cannot be trusted to run.

    It is a pass-through rather than a flagging stub because a review verdict is
    not what any of these tests is about — the ones that *are* about it request
    this fixture and replace it, and the rule itself is asserted over floats in
    `tests/unit/test_photo_review_policy.py`.
    """

    return PassThroughPhotoReview()


@pytest.fixture
def exposure_ledger():
    """The exposure ledger every API test runs against.

    Overridden on `client` regardless of whether a test asks for it, so **no
    test in this suite needs Redis running** — which is the acceptance criterion
    and not a convenience, exactly as it is for the object store above.

    A ledger is the worse of the two to get wrong. A missing object store fails
    a request; a missing ledger answers *nothing was shown to anybody*, which is
    a perfectly plausible answer, so a suite silently talking to no Redis at all
    would look green and prove nothing.
    """

    return InMemoryExposureLedger(build_clock())


@pytest.fixture
def suppression_ledger():
    """The suppression ledger every API test runs against. See above."""

    return InMemorySuppressionLedger(build_clock())


@pytest.fixture
def prompt_ledger():
    """The prompt ledger every API test runs against. See above."""

    return InMemoryPromptLedger(build_clock())


@pytest.fixture
def live_channel():
    """The ephemeral store the conversation stream publishes on and follows.

    **One fake for both clients**, unlike production, which holds two — the
    command pool and the subscriber's own, which differ in a read deadline this
    stand-in has no concept of (`docs/adr/0147` §5, #342). Two fakes here would
    be two message buses and a nudge would never reach a stream.

    Overridden on `client` regardless of whether a test asks for it, so **no test
    in this suite needs Redis running** — the same acceptance criterion the
    ledgers above are held to, and here it also means the real
    `RedisNudgePublisher` and `RedisNudgeSubscriber` run: the classes that decide
    the channel key and the frame's encoding are exercised rather than stubbed
    past.
    """

    return FakeRedis()


@pytest.fixture
def candidate_source(session_factory):
    """The one candidate index this process has, for the length of one test.

    **One per process** is `docs/adr/0112`'s rule, and the lifespan is where the
    one normally lives — but `ASGITransport` does not run a lifespan, so under
    this seam nothing owns it. This fixture is that owner.

    It is the **real** adapter over the test's own engine rather than a stub, so
    a search here walks the same decode, the same bound container and the same
    staleness ladder a request does. A test that wants rows in it seeds the log,
    tails it, and calls `refresh()`.
    """

    return DatabaseCandidateSource(
        session_factory=session_factory, empty_at=build_clock().now()
    )


@pytest_asyncio.fixture
async def app(
    session_factory,
    photo_storage,
    photo_review,
    exposure_ledger,
    suppression_ledger,
    prompt_ledger,
    candidate_source,
    live_channel,
):
    """The application every API test drives, with its seams already replaced.

    Requested by name only by a test that needs to replace **one more** seam for
    itself — the conversation stream's dead-subscriber path is the case that
    earned this fixture, since *the bus is gone* cannot be expressed by any
    request. Every other test wants `client` and never sees this.
    """

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
    app.dependency_overrides[get_photo_review] = lambda: photo_review
    app.dependency_overrides[get_exposure_ledger] = lambda: exposure_ledger
    app.dependency_overrides[get_suppression_ledger] = lambda: suppression_ledger
    app.dependency_overrides[get_prompt_ledger] = lambda: prompt_ledger
    app.dependency_overrides[get_candidate_source] = lambda: candidate_source
    # `ASGITransport` runs no lifespan, so nothing has initialised either Redis
    # client and `get_redis()` would raise. The ledgers above are overridden one
    # layer higher and never reach it; the live channel deliberately is not.
    app.dependency_overrides[get_redis] = lambda: live_channel
    app.dependency_overrides[get_redis_subscriber] = lambda: live_channel
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def client(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture
def valid_signup_payload():
    return {
        "email": "alice@example.com",
        "password1": "hunter22!",
        "password2": "hunter22!",
        "nickname": "alice",
        "adult_attested": True,
    }
