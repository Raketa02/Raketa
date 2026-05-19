import ssl
from typing import Optional, Union

from application.core.config import Settings


def build_db_ssl_context(settings: Settings) -> Union[bool, ssl.SSLContext]:
    """Build an SSL context for the asyncpg PostgreSQL driver.

    Returns False to disable SSL (asyncpg's documented sentinel for "no TLS"),
    or an SSLContext configured per DB_SSL_MODE. Client certs are loaded only
    when both DB_SSL_CLIENT_CERT_PATH and DB_SSL_CLIENT_KEY_PATH are present.
    """
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
    else:  # verify-full (default safe path)
        ctx.check_hostname = True
        ctx.verify_mode = ssl.CERT_REQUIRED

    if settings.DB_SSL_CLIENT_CERT_PATH and settings.DB_SSL_CLIENT_KEY_PATH:
        ctx.load_cert_chain(
            certfile=settings.DB_SSL_CLIENT_CERT_PATH,
            keyfile=settings.DB_SSL_CLIENT_KEY_PATH,
        )
    return ctx


def build_http_ssl_context(settings: Settings) -> Optional[ssl.SSLContext]:
    """Build an SSL context for outbound HTTPS clients (aiohttp, httpx).

    Returns None if no custom CA / client cert is configured (system trust store
    is then used by the caller). Loads a custom root CA and optional client cert
    when paths are configured.
    """
    ca_path = settings.EXTERNAL_SSL_ROOT_CA_PATH
    client_cert = settings.CLIENT_CERT_PATH
    client_key = settings.CLIENT_KEY_PATH
    if not any([ca_path, client_cert]):
        return None

    ctx = (
        ssl.create_default_context(cafile=ca_path)
        if ca_path
        else ssl.create_default_context()
    )
    ctx.check_hostname = True
    ctx.verify_mode = ssl.CERT_REQUIRED
    if client_cert and client_key:
        ctx.load_cert_chain(certfile=client_cert, keyfile=client_key)
    return ctx
