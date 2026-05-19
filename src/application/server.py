from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import entities so they register on Base.metadata for Alembic / create_all
from application.api.v1.routers import auth as auth_router
from application.api.v1.routers import health as health_router
from application.api.v1.routers import users as users_router
from application.core.config import Settings, get_settings
from application.core.database import init_engine
from application.core.exceptions import register_exception_handlers
from application.core.logging import configure_logging
from application.domain.auth import entities as _auth_entities  # noqa: F401
from application.domain.user import entities as _user_entities  # noqa: F401


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    configure_logging(settings)
    init_engine(settings)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        # No DB schema bootstrap here — Alembic owns the schema.
        yield

    app = FastAPI(
        title=settings.TITLE,
        description=settings.DESCRIPTION,
        version=settings.VERSION,
        docs_url="/docs" if not settings.is_production or settings.DEBUG else None,
        redoc_url="/redoc" if not settings.is_production or settings.DEBUG else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOW_ORIGINS,
        allow_credentials=settings.ALLOW_CREDENTIALS,
        allow_methods=settings.ALLOW_METHODS,
        allow_headers=settings.ALLOW_HEADERS,
    )

    register_exception_handlers(app)

    app.include_router(health_router.router)
    app.include_router(users_router.router)
    app.include_router(auth_router.router)

    return app


# Module-level app for uvicorn/gunicorn: `application.server:app`
app = create_app()
