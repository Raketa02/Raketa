from fastapi import FastAPI

from app.api.v1.router import api_router
from app.bootstrap.composition import (
    build_arrival_sets,
    build_clock,
    build_scoring_contexts,
)
from app.bootstrap.events import get_event_runtime
from app.core.config import Environment, Settings, get_settings
from app.core.exception_handlers import register_exception_handlers
from app.core.lifespan import build_lifespan
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.infrastructure.database import models as _models  # noqa: F401


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        # Production has no interactive documentation, and no way to re-enable it.
        # The old spelling let `DEBUG=true` bring it back; that allowance is gone
        # rather than adjusted, because the settings object now refuses to start in
        # production with debug on at all — so the state was unreachable anyway, and
        # an unreachable escape hatch is one a reader still has to reason about.
        docs_url=None if settings.APP_ENV is Environment.PRODUCTION else "/docs",
        redoc_url=None if settings.APP_ENV is Environment.PRODUCTION else "/redoc",
        lifespan=build_lifespan(settings),
    )

    # The lifespan's embedded delivery worker reads this. It is the process's
    # runtime — the same object request dependencies resolve — rather than a
    # second one built here: a worker dispatching through a different catalog
    # than the requests that wrote the events is a failure with no symptom until
    # an event goes undelivered.
    app.state.event_runtime = get_event_runtime()

    # The new-arrivals cache (ADR-0068). One per application rather than one per
    # request, because a cache nobody shares is a cache with no hits — and one
    # per *application* rather than a module singleton, so two apps in one
    # process (which is what a test run is) never answer from each other's
    # database. It expires and never invalidates, so there is nothing to reset.
    app.state.arrival_sets = build_arrival_sets(clock=build_clock())

    # The match scoring context cache (ADR-0068), on the same lifetime and for
    # the same reason — its value is being shared across every viewer looking at
    # one match. It takes no clock, because it has no TTL: the key is
    # `matchId : recordVersion`, so an entry is never stale and there is nothing
    # to expire. It is bounded by size instead, or a match played on Tuesday
    # would sit in memory until the process restarted.
    app.state.scoring_contexts = build_scoring_contexts()

    register_middleware(app, settings)
    register_exception_handlers(app)
    app.include_router(api_router)

    @app.get("/health", tags=["health"], summary="Liveness probe")
    async def health() -> dict:
        # Deliberately does not touch the DB — ALB / ECS health checks should
        # not destabilise on transient DB blips.
        return {"status": "ok"}

    return app


# Module-level app for uvicorn/gunicorn: `app.main:app`
app = create_app()
