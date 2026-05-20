import ssl
from typing import Optional, Union
from urllib.parse import urlsplit, urlunsplit

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from app.core.config import Settings


def _to_asyncpg_url(url: str) -> str:
    """Normalise a Postgres URL to the asyncpg driver and strip libpq-only
    query params (`sslmode`, `sslrootcert`, ...) that asyncpg cannot parse.
    Non-Postgres URLs pass through untouched."""
    if url.startswith("postgresql://"):
        url = "postgresql+asyncpg://" + url[len("postgresql://"):]
    elif url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://"):]

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


def _build_db_ssl_context(settings: Settings) -> Union[bool, ssl.SSLContext]:
    """asyncpg sentinel: False = no TLS. Otherwise return a configured context."""
    mode = (settings.DB_SSL_MODE or "disable").lower()
    if mode in {"disable", "allow", ""}:
        return False

    ctx = ssl.create_default_context(cafile=settings.DB_SSL_ROOT_CERT_PATH)
    if mode == "require":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
    elif mode == "verify-ca":
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_REQUIRED
    else:  # verify-full
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED

    if settings.DB_SSL_CLIENT_CERT_PATH and settings.DB_SSL_CLIENT_KEY_PATH:
        ctx.load_cert_chain(
            certfile=settings.DB_SSL_CLIENT_CERT_PATH,
            keyfile=settings.DB_SSL_CLIENT_KEY_PATH,
        )
    return ctx


def create_engine(settings: Settings) -> AsyncEngine:
    url = _to_asyncpg_url(settings.WRITER_DB_URL)
    connect_args: dict = {}

    if url.startswith("postgresql+asyncpg://"):
        connect_args["ssl"] = _build_db_ssl_context(settings)

    kwargs: dict = {
        "echo": settings.DB_ECHO,
        "pool_pre_ping": True,
        "connect_args": connect_args,
    }
    if not url.startswith("sqlite"):
        kwargs["pool_size"] = settings.DB_POOL_SIZE
        kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
    return create_async_engine(url, **kwargs)


_engine: Optional[AsyncEngine] = None


def init_engine(settings: Settings) -> AsyncEngine:
    global _engine
    _engine = create_engine(settings)
    return _engine


def get_engine() -> AsyncEngine:
    if _engine is None:
        raise RuntimeError("engine not initialised — call init_engine() first")
    return _engine


async def dispose_engine() -> None:
    global _engine
    if _engine is not None:
        await _engine.dispose()
        _engine = None
