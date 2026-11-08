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
# `local` derives DEBUG, and at DEBUG the SQLite driver writes two lines per
# operation into every test's capture — about an eighth of the suite's time.
# The logging plugin stays: it is what `caplog` is.
os.environ.setdefault("LOG_LEVEL", "INFO")
# bcrypt's minimum. At production's twelve every sign-up, login and refresh costs a
# fifth of a second; three API files took 170 s at twelve and 19 s at four.
os.environ.setdefault("BCRYPT_ROUNDS", "4")

from datetime import datetime, timezone

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_clock  # noqa: E402
from app.application.mail.deliver_queued_mail import DeliverQueuedMail  # noqa: E402
from app.bootstrap.composition import (  # noqa: E402
    build_clock,
    build_pending_mail,
    build_unit_of_work,
)
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
from app.modules.notifications.infrastructure.push import (  # noqa: E402
    RecordingPush,
)
from app.modules.payments.infrastructure.fake_payments import (  # noqa: E402
    FakePayments,
)
from app.modules.payments.presentation.dependencies import (  # noqa: E402
    get_payment_provider,
)
from app.modules.player_profile.presentation.dependencies import (  # noqa: E402
    get_photo_review,
    get_photo_storage,
)
from app.modules.rankings.presentation.dependencies import (  # noqa: E402
    get_general_orders,
)
from tests.unit.fake_clock import MovableClock  # noqa: E402
from tests.unit.kept_orders import kept_orders_of  # noqa: E402
from tests.unit.fake_mailer import RecordingMailer  # noqa: E402
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

    # Postgres refuses a row whose foreign key names no row; SQLite accepts it
    # unless asked. A projection that wrote the child before its parent passed
    # every test here and failed every friends-game send on Postgres.
    @event.listens_for(engine.sync_engine, "connect")
    def _check_foreign_keys(dbapi_connection, _record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

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
def payments():
    """The payment provider every API test runs against: the in-process fake,
    fresh for each test (``docs/adr/0189`` §4).

    Overridden on ``client`` regardless, so **no test in this suite needs a
    Stripe key or a network** — the fake is held to Stripe's own demands in
    ``tests/demands/test_payments_demands.py``, which is what makes that safe.
    It confirms nothing on its own: a test says which card the player's phone
    entered (``phone_enters``), and reads what was asked of the provider off
    ``calls``.
    """

    return FakePayments()


@pytest.fixture
def pushes():
    """The push service every API test's outbox pushes a notice through: one
    that records and pushes nothing, fresh for each test (#549).

    **No test in this suite reaches Expo** — the Expo adapter is held to the
    same demands as this one over a loopback server in
    ``tests/demands/test_push_demands.py``. A test reads what each phone was
    pushed off ``to(token)`` after ``mailbox.drain()``, makes a phone forgotten
    with ``forget`` and the service unreachable with ``unavailable``.
    """

    return RecordingPush()


@pytest.fixture
def live_channel():
    """The ephemeral store the conversation stream publishes on and follows.

    **One fake for both clients**, unlike production, which holds two — the
    command pool and the subscriber's own, which differ in a read deadline this
    stand-in has no concept of (`docs/adr/0147` §5, #342). Two fakes here would
    be two message buses and a nudge would never reach a stream.

    Overridden on `client` regardless of whether a test asks for it, so **no test
    in this suite needs Redis running** — the acceptance criterion the object
    store above is held to too, and here it also means the real
    `RedisNudgePublisher` and `RedisNudgeSubscriber` run: the classes that decide
    the channel key and the frame's encoding are exercised rather than stubbed
    past.
    """

    return FakeRedis()


@pytest.fixture
def general_orders(session_factory):
    """Each sport's kept General order, **in memory** — the ephemeral store's
    in-memory equivalent, one per test database, so the outbox a test drains
    forgets the order its next request reads (``tests/unit/kept_orders.py``).

    Overridden on `client` regardless, so no test needs Redis for it either;
    the Redis adapter is held to the same contract over the fake server in
    ``tests/demands/test_general_order_demands.py``.
    """

    return kept_orders_of(session_factory)


@pytest_asyncio.fixture
async def app(
    session_factory,
    photo_storage,
    photo_review,
    live_channel,
    payments,
    general_orders,
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
    app.dependency_overrides[get_payment_provider] = lambda: payments
    # `ASGITransport` runs no lifespan, so nothing has initialised either Redis
    # client and `get_redis()` would raise. The live channel is the one reader
    # left (#579), and it runs over the fake rather than being stubbed past.
    app.dependency_overrides[get_redis] = lambda: live_channel
    app.dependency_overrides[get_redis_subscriber] = lambda: live_channel
    app.dependency_overrides[get_general_orders] = lambda: general_orders
    try:
        yield app
    finally:
        app.dependency_overrides.clear()


@pytest.fixture
def clock(app):
    """A **controllable clock**, overridden on the running application so every
    request in the test agrees about what time it is (``docs/adr/0186`` §5).

    Starts at the wall clock's now, so a test that never moves it behaves as one
    that never asked for it; ``clock.move(...)`` is how a one-hour expiry is
    checked without waiting an hour. A module that needs a different start
    declares its own ``clock`` fixture, which takes precedence over this one.
    """

    movable = MovableClock(datetime.now(timezone.utc))
    app.dependency_overrides[get_clock] = lambda: movable
    return movable


class Mailbox:
    """Every email the application has sent, read the way a person reads mail.

    **The queues are drained first**, each the way its worker drains it — the
    outbox, then the mail queue through the production ``DeliverQueuedMail``,
    into a recording mailer — so what a test reads is what a relay would have
    been handed, and nothing is asserted about which table was written
    (``docs/adr/0186`` §5).
    """

    def __init__(
        self, app, session_factory, mailer: RecordingMailer, pushes: RecordingPush
    ) -> None:
        self._app = app
        self._session_factory = session_factory
        self.mailer = mailer
        self._pushes = pushes

    def _clock(self):
        # The application's own clock — the ``clock`` fixture's when a test
        # moved time — so a retry waits on the same clock that queued it.
        return self._app.dependency_overrides.get(get_clock, build_clock)()

    async def drain(self) -> None:
        # Imported here: the outbox's drain lives with the players world, and
        # importing it at module load would drag that module into every test.
        from tests.api.players_world import deliver_the_outbox

        # The application's own provider, so a card released from the outbox
        # is released at the fake the test reads.
        payments = self._app.dependency_overrides.get(get_payment_provider)
        # And the test's push service, so a notice given is pushed where the
        # test reads it (#549).
        await deliver_the_outbox(
            self._session_factory,
            payments=payments() if payments else None,
            push=self._pushes,
        )
        while True:
            async with self._session_factory() as session:
                run = await DeliverQueuedMail(
                    pending=build_pending_mail(session),
                    mailer=self.mailer,
                    uow=build_unit_of_work(session),
                    clock=self._clock(),
                    batch_size=100,
                ).execute()
            if not run.sent and not run.failed:
                return

    async def sent(self):
        await self.drain()
        return list(self.mailer.sent)

    async def to(self, address: str):
        await self.drain()
        return self.mailer.to(address)


@pytest.fixture
def mailbox(app, session_factory, pushes) -> Mailbox:
    """The **recording mailer**, read after draining the queues."""

    return Mailbox(app, session_factory, RecordingMailer(), pushes)


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
        "adult_attested": True,
    }
