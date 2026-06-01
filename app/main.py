from fastapi import FastAPI

from app.api.v1.router import api_router
from app.bootstrap.events import build_event_runtime
from app.core.config import Settings, get_settings
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
        docs_url="/docs" if not settings.is_production or settings.DEBUG else None,
        redoc_url="/redoc" if not settings.is_production or settings.DEBUG else None,
        lifespan=build_lifespan(settings),
    )

    # Keep event contracts available for request dependency resolution even
    # when an ASGI test client does not execute lifespan startup.
    app.state.event_runtime = build_event_runtime()

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
