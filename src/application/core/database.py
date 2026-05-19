from typing import AsyncGenerator
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from application.core.config import Settings, get_settings
from application.core.ssl import build_db_ssl_context

Base = declarative_base()


def _to_asyncpg_url(url: str) -> str:
    """Normalise a Postgres URL to the asyncpg driver and strip libpq-only
    query params (`sslmode`, `sslrootcert`, …) that asyncpg cannot parse.
    Non-Postgres URLs pass through untouched."""
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]

    if not url.startswith("postgresql+asyncpg://"):
        return url

    parts = urlsplit(url)
    if parts.query:
        keep = [
            kv
            for kv in parts.query.split("&")
            if kv
            and not kv.lower().startswith(
                ("sslmode=", "sslrootcert=", "sslcert=", "sslkey=")
            )
        ]
        url = urlunsplit(
            (parts.scheme, parts.netloc, parts.path, "&".join(keep), parts.fragment)
        )
    return url


def create_engine_and_session(settings: Settings):
    url = _to_asyncpg_url(settings.WRITER_DB_URL)
    connect_args: dict = {}

    if url.startswith("postgresql+asyncpg://"):
        ssl_obj = build_db_ssl_context(settings)
        if ssl_obj is not False:
            connect_args["ssl"] = ssl_obj
        else:
            connect_args["ssl"] = False

    engine_kwargs: dict = {
        "echo": settings.DB_ECHO,
        "pool_pre_ping": True,
        "connect_args": connect_args,
    }
    if not url.startswith("sqlite"):
        engine_kwargs["pool_size"] = settings.DB_POOL_SIZE
        engine_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    engine = create_async_engine(url, **engine_kwargs)
    session_factory = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False, autoflush=False
    )
    return engine, session_factory


_engine = None
_session_factory = None


def init_engine(settings: Settings):
    global _engine, _session_factory
    _engine, _session_factory = create_engine_and_session(settings)
    return _engine, _session_factory


def get_session_factory():
    global _engine, _session_factory
    if _session_factory is None:
        init_engine(get_settings())
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
