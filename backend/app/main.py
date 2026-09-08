from fastapi import FastAPI

from app.api.dev.gate import CONSOLE_SERVED
from app.api.streaming import restore_stream_item_types
from app.api.v1.router import api_router
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

    register_middleware(app, settings)
    register_exception_handlers(app)
    app.include_router(api_router)

    # The dev console. The gate is imported unconditionally and the router only
    # here, inside the `if`: `app/api/dev/routes.py` refuses on import, and a
    # module that raises on import cannot also be the thing that decides whether
    # to import it. A production deployable that crashes at startup because it
    # read its own dev tool is not a gate, it is an outage.
    if CONSOLE_SERVED[settings.APP_ENV]:
        from app.api.dev.routes import dev_api_router

        app.include_router(dev_api_router)

    # After every `include_router` above, and before anything serves or
    # generates a document: a streaming route's item type does not survive being
    # included, and both the wire and the contract need it back. See
    # `app/api/streaming.py`.
    restore_stream_item_types(app)

    @app.get("/health", tags=["health"], summary="Liveness probe")
    async def health() -> dict:
        # Deliberately does not touch the DB — ALB / ECS health checks should
        # not destabilise on transient DB blips.
        return {"status": "ok"}

    return app


# Module-level app for uvicorn/gunicorn: `app.main:app`
app = create_app()
