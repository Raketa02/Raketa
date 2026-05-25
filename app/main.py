from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import Settings, get_settings
from app.core.events import build_event_registry, register_handlers
from app.core.exception_handlers import register_exception_handlers
from app.core.lifespan import build_lifespan
from app.core.logging import configure_logging
from app.core.middleware import register_middleware
from app.infrastructure.database import models as _models  # noqa: F401
from app.shared.events import InProcessEventBus
##

def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)

    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs" if not settings.is_production or settings.DEBUG else None,
        redoc_url="/redoc" if not settings.is_production or settings.DEBUG else None,
        lifespan=build_lifespan(settings),
    )

    # Compose the events subsystem here (not in lifespan) so the registry and
    # bus exist as soon as `create_app` returns. Tests that drive the ASGI app
    # without running lifespan still need the registry to serialize outbox
    # records.
    app.state.event_registry = build_event_registry()
    app.state.event_bus = InProcessEventBus()
    register_handlers(app.state.event_bus)

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
