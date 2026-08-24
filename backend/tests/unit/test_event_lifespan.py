from __future__ import annotations

from fastapi import FastAPI
import pytest

import app.core.lifespan as lifespan_module
from app.core.config import Settings


class _FakeWorker:
    def __init__(self) -> None:
        self.started = False
        self.stopped = False

    def start(self) -> None:
        self.started = True

    async def stop(self) -> None:
        self.stopped = True


@pytest.mark.asyncio
async def test_lifespan_starts_and_stops_embedded_worker(monkeypatch):
    settings = Settings(
        WRITER_DB_URL="sqlite+aiosqlite:///:memory:",
        EVENT_DELIVERY_WORKER_ENABLED=True,
    )
    app = FastAPI()
    app.state.event_runtime = object()
    # The application's own scoring-context cache, which the tick shares with
    # the request path (ADR-0068's key is `matchId : recordVersion`, so sharing
    # it cannot serve either a stale answer). Stood up here because the lifespan
    # hands it to the worker rather than letting it build a second one.
    app.state.scoring_contexts = object()
    worker = _FakeWorker()
    built: list[object] = []
    handed: list[object] = []
    disposed = False

    monkeypatch.setattr(lifespan_module, "init_engine", lambda settings: None)
    monkeypatch.setattr(lifespan_module, "get_engine", lambda: object())
    monkeypatch.setattr(
        lifespan_module, "async_sessionmaker", lambda *args, **kwargs: "sessions"
    )

    def build_worker(**kwargs):
        built.append(kwargs["event_runtime"])
        handed.append(kwargs["scoring_contexts"])
        return worker

    async def dispose_engine() -> None:
        nonlocal disposed
        disposed = True

    monkeypatch.setattr(lifespan_module, "build_event_delivery_worker", build_worker)
    monkeypatch.setattr(lifespan_module, "dispose_engine", dispose_engine)

    async with lifespan_module.build_lifespan(settings)(app):
        assert worker.started is True
        assert built == [app.state.event_runtime]
        assert handed == [app.state.scoring_contexts]
        assert app.state.event_delivery_worker is worker

    assert worker.stopped is True
    assert disposed is True


@pytest.mark.asyncio
async def test_lifespan_can_disable_embedded_worker(monkeypatch):
    settings = Settings(
        WRITER_DB_URL="sqlite+aiosqlite:///:memory:",
        EVENT_DELIVERY_WORKER_ENABLED=False,
    )
    app = FastAPI()
    app.state.event_runtime = object()
    disposed = False

    monkeypatch.setattr(lifespan_module, "init_engine", lambda settings: None)

    def unexpected_worker(**kwargs):
        raise AssertionError("worker must not be built when disabled")

    async def dispose_engine() -> None:
        nonlocal disposed
        disposed = True

    monkeypatch.setattr(
        lifespan_module, "build_event_delivery_worker", unexpected_worker
    )
    monkeypatch.setattr(lifespan_module, "dispose_engine", dispose_engine)

    async with lifespan_module.build_lifespan(settings)(app):
        assert not hasattr(app.state, "event_delivery_worker")

    assert disposed is True
