"""What the API starts beside itself, and — the half that rots — what it stops.

Both kinds of background work are here, because the claim is about the lifespan
and not about either of them: the outbox drain and the scheduled jobs are
started together, stopped together, and each can be turned off without the other
(``docs/adr/0092``).

**The disabled cases are the load-bearing ones.** `init_engine` is stubbed out
here, so a lifespan that reached for an engine when nothing wanted a session
would fail loudly rather than pass — which is exactly the mistake that would
otherwise ship: building a session factory unconditionally works everywhere the
database is up, and turns "all background work off" into a startup crash.
"""

from __future__ import annotations

from fastapi import FastAPI
import pytest

import app.core.lifespan as lifespan_module
from app.bootstrap.jobs import SCALE_PRESSURE_JOB
from app.core.config import Settings


class _FakeWorker:
    def __init__(self, name: str = "fake") -> None:
        self.name = name
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


def _settings(**overrides) -> Settings:
    return Settings(WRITER_DB_URL="sqlite+aiosqlite:///:memory:", **overrides)


@pytest.fixture
def stub_engine(monkeypatch):
    """No engine, no session factory, and a disposal a test can observe."""

    disposal: list[bool] = []

    monkeypatch.setattr(lifespan_module, "init_engine", lambda settings: None)
    monkeypatch.setattr(lifespan_module, "get_engine", lambda: object())
    # The lifespan asks the composition root for its session factory now, so
    # that is the name a test with no engine has to stand in for.
    monkeypatch.setattr(
        lifespan_module, "build_background_session_factory", lambda engine: "sessions"
    )

    async def dispose_engine() -> None:
        disposal.append(True)

    monkeypatch.setattr(lifespan_module, "dispose_engine", dispose_engine)
    return disposal


@pytest.fixture
def no_jobs(monkeypatch):
    monkeypatch.setattr(lifespan_module, "build_scheduled_jobs", lambda **_: [])


# ---------------------------------------------------------------------------
# The outbox drain
# ---------------------------------------------------------------------------


async def test_lifespan_starts_and_stops_embedded_worker(
    monkeypatch, stub_engine, no_jobs
):
    settings = _settings(EVENT_DELIVERY_WORKER_ENABLED=True)
    app = FastAPI()
    app.state.event_runtime = object()
    worker = _FakeWorker()
    built: list[object] = []

    def build_worker(**kwargs):
        built.append(kwargs["event_runtime"])
        return worker

    monkeypatch.setattr(lifespan_module, "build_event_delivery_worker", build_worker)

    async with lifespan_module.build_lifespan(settings)(app):
        assert worker.started is True
        assert built == [app.state.event_runtime]
        assert app.state.event_delivery_worker is worker

    assert worker.stopped is True
    assert stub_engine == [True]


async def test_lifespan_can_disable_embedded_worker(monkeypatch, stub_engine, no_jobs):
    settings = _settings(EVENT_DELIVERY_WORKER_ENABLED=False)
    app = FastAPI()
    app.state.event_runtime = object()

    def unexpected_worker(**kwargs):
        raise AssertionError("worker must not be built when disabled")

    monkeypatch.setattr(
        lifespan_module, "build_event_delivery_worker", unexpected_worker
    )

    async with lifespan_module.build_lifespan(settings)(app):
        assert not hasattr(app.state, "event_delivery_worker")

    assert stub_engine == [True]


# ---------------------------------------------------------------------------
# The scheduled jobs
# ---------------------------------------------------------------------------


async def test_a_scheduled_job_is_started_and_stopped_with_the_application(
    monkeypatch, stub_engine
):
    settings = _settings(EVENT_DELIVERY_WORKER_ENABLED=False)
    app = FastAPI()
    app.state.event_runtime = object()
    job = _FakeWorker("uncommitted-photo-sweep")
    passed: list[dict] = []

    def build_jobs(**kwargs):
        passed.append(kwargs)
        return [job]

    monkeypatch.setattr(lifespan_module, "build_scheduled_jobs", build_jobs)

    async with lifespan_module.build_lifespan(settings)(app):
        assert job.started is True
        assert passed[0]["session_factory"] == "sessions"

    assert job.stopped is True


async def test_no_background_work_at_all_reaches_for_no_engine(monkeypatch):
    """With everything off, the lifespan must not build a session factory.

    `get_engine` raises here exactly as it does before `init_engine` has run, so
    an unconditional factory is a startup crash rather than an unused object.
    """

    settings = _settings(
        EVENT_DELIVERY_WORKER_ENABLED=False,
        PHOTO_SWEEP_ENABLED=False,
        PHOTO_REVIEW_BACKFILL_ENABLED=False,
        CANDIDATE_INDEX_ENABLED=False,
        EXPOSURE_ROLL_ENABLED=False,
        INTENT_DRIFT_ENABLED=False,
        GRID_STALENESS_ENABLED=False,
        INTEREST_EXPIRY_ENABLED=False,
        CHALLENGE_LAPSE_ENABLED=False,
    )
    app = FastAPI()
    app.state.event_runtime = object()
    disposed: list[bool] = []

    def refuse_engine():
        raise RuntimeError("engine not initialised — call init_engine() first")

    async def dispose_engine() -> None:
        disposed.append(True)

    monkeypatch.setattr(lifespan_module, "init_engine", lambda settings: None)
    monkeypatch.setattr(lifespan_module, "get_engine", refuse_engine)
    monkeypatch.setattr(lifespan_module, "dispose_engine", dispose_engine)

    async with lifespan_module.build_lifespan(settings)(app):
        # The scoring histogram's probe is the one job left, and it is the same
        # claim the redis assertion below makes: it reads this process's own
        # counters, so it needs no session, no store and no engine. Everything
        # that would have reached for a factory is gone.
        assert [job.name for job in app.state.scheduled_jobs] == [SCALE_PRESSURE_JOB]
        assert app.state.scoring_meter is not None
        # The index's own source is one of the things that must not have been
        # built: it takes a session factory, and building one is what this test
        # exists to prove did not happen.
        assert app.state.candidate_source is None
        # The ephemeral store is **not** the same claim, and the difference is
        # the point: it needs no session, so it is opened whatever is switched
        # off. A request path resolves its ledgers through this client, and a
        # job's toggle may not decide whether a Play surface has one.
        assert app.state.redis is not None

    assert disposed == [True]


async def test_the_two_photo_jobs_are_registered_by_default(monkeypatch, stub_engine):
    """The default configuration runs both. A job nobody wired up is a decision
    recorded in an ADR and absent from the running system.

    Both, in one test, because they walk the **same bucket** and the pairing is
    the thing worth seeing: the sweep deletes what no profile names, the
    backfill re-reviews what nobody looked at, and neither takes a lock
    (``docs/adr/0092``, ``docs/adr/0132``).
    """

    settings = _settings(EVENT_DELIVERY_WORKER_ENABLED=False)
    app = FastAPI()
    app.state.event_runtime = object()

    async with lifespan_module.build_lifespan(settings)(app):
        names = [job.name for job in app.state.scheduled_jobs]

    assert "uncommitted-photo-sweep" in names
    assert "photo-review-backfill" in names


async def test_the_outbox_drain_is_not_published_as_a_scheduled_job(
    monkeypatch, stub_engine
):
    """`app.state.scheduled_jobs` answers *which jobs is this process running*.

    The outbox drain is started and stopped beside them and is not one: it
    empties a queue as fast as it fills rather than running because an interval
    elapsed (`backend/CONTEXT.md` — *Scheduled job*). It is reachable as
    `app.state.event_delivery_worker`, which is a different question.
    """

    settings = _settings(EVENT_DELIVERY_WORKER_ENABLED=True)
    app = FastAPI()
    app.state.event_runtime = object()
    worker = _FakeWorker("event-delivery-worker")
    job = _FakeWorker("uncommitted-photo-sweep")

    monkeypatch.setattr(
        lifespan_module, "build_event_delivery_worker", lambda **_: worker
    )
    monkeypatch.setattr(lifespan_module, "build_scheduled_jobs", lambda **_: [job])

    async with lifespan_module.build_lifespan(settings)(app):
        assert [j.name for j in app.state.scheduled_jobs] == [job.name]
        assert worker.started is True

    assert worker.stopped is True and job.stopped is True


async def test_scheduled_jobs_is_an_empty_list_when_nothing_is_registered(
    monkeypatch, stub_engine, no_jobs
):
    """Present and empty, never absent — an attribute that only sometimes
    exists is one every reader has to guard against."""

    settings = _settings(EVENT_DELIVERY_WORKER_ENABLED=False)
    app = FastAPI()
    app.state.event_runtime = object()

    async with lifespan_module.build_lifespan(settings)(app):
        assert app.state.scheduled_jobs == []


# ---------------------------------------------------------------------------
# Shutdown, which is where a forgotten task holds a connection open
# ---------------------------------------------------------------------------


async def test_one_task_that_refuses_to_stop_does_not_strand_the_others(
    monkeypatch, stub_engine
):
    """A background task the shutdown path abandons keeps a pooled connection
    past `dispose_engine`, and the symptom is a container that dies slowly
    rather than anything that looks like a bug."""

    settings = _settings(EVENT_DELIVERY_WORKER_ENABLED=False)
    app = FastAPI()
    app.state.event_runtime = object()
    survivor = _FakeWorker("second")

    class _Refuses(_FakeWorker):
        async def stop(self) -> None:
            raise RuntimeError("stuck on a network call")

    monkeypatch.setattr(
        lifespan_module,
        "build_scheduled_jobs",
        lambda **_: [survivor, _Refuses("first")],
    )

    async with lifespan_module.build_lifespan(settings)(app):
        pass

    assert survivor.stopped is True
    assert stub_engine == [True], "the engine was disposed anyway"


# ---------------------------------------------------------------------------
# The ephemeral store
# ---------------------------------------------------------------------------


async def test_the_ephemeral_store_is_opened_and_closed_with_the_application(
    monkeypatch, stub_engine, no_jobs
):
    """One pool per process, and the process is what ends it.

    A client the shutdown path forgets holds its connections open past
    `dispose_engine`, which is the same shutdown bug the engine has and looks
    the same from outside: a container that takes its whole grace period to die.
    """

    client = object()
    opened: list[Settings] = []
    closed: list[bool] = []

    def init_redis(settings):
        opened.append(settings)
        return client

    async def close_redis() -> None:
        closed.append(True)

    monkeypatch.setattr(lifespan_module, "init_redis", init_redis)
    monkeypatch.setattr(lifespan_module, "get_redis", lambda: client)
    monkeypatch.setattr(lifespan_module, "close_redis", close_redis)

    settings = _settings(
        EVENT_DELIVERY_WORKER_ENABLED=False, EXPOSURE_ROLL_ENABLED=False
    )
    app = FastAPI()
    app.state.event_runtime = object()

    async with lifespan_module.build_lifespan(settings)(app):
        # Opened even with the roll off, which is the assertion: the pool is the
        # process's, and only its *readers* are behind flags.
        assert opened == [settings]
        assert app.state.redis is client
        assert closed == []

    assert closed == [True]


async def test_the_store_is_closed_after_the_engine_and_after_the_jobs(
    monkeypatch, stub_engine
):
    """Order, because closing a pool under a live job is the whole hazard."""

    order: list[str] = []
    job = _FakeWorker("exposure-roll")

    async def stop() -> None:
        order.append("job")
        job.stopped = True

    job.stop = stop  # type: ignore[method-assign]
    monkeypatch.setattr(lifespan_module, "build_scheduled_jobs", lambda **_: [job])
    monkeypatch.setattr(lifespan_module, "init_redis", lambda settings: object())
    monkeypatch.setattr(lifespan_module, "get_redis", object)

    async def close_redis() -> None:
        order.append("redis")

    async def dispose_engine() -> None:
        order.append("engine")

    monkeypatch.setattr(lifespan_module, "close_redis", close_redis)
    monkeypatch.setattr(lifespan_module, "dispose_engine", dispose_engine)

    app = FastAPI()
    app.state.event_runtime = object()

    async with lifespan_module.build_lifespan(
        _settings(EVENT_DELIVERY_WORKER_ENABLED=False, EXPOSURE_ROLL_ENABLED=True)
    )(app):
        pass

    assert order == ["job", "engine", "redis"]
