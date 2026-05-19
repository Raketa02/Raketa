import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import engine_from_config, pool

# Make `application.*` importable both when alembic is invoked from the repo
# root and from inside the container (where `src/` is on PYTHONPATH already).
_REPO_ROOT = Path(__file__).resolve().parents[1]
_SRC = _REPO_ROOT / "src"
if _SRC.exists() and str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from application.core.config import get_settings  # noqa: E402
from application.core.database import Base  # noqa: E402
from application.domain.auth import entities as _auth  # noqa: E402,F401
from application.domain.user import entities as _user  # noqa: E402,F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def _resolve_sync_url() -> str:
    """Alembic runs sync — convert the asyncpg URL to psycopg2 and drop
    asyncpg-incompatible query params so the migration runner connects."""
    settings = get_settings()
    url = os.environ.get("ALEMBIC_DATABASE_URL") or settings.WRITER_DB_URL
    if url.startswith("postgresql+asyncpg://"):
        url = "postgresql://" + url[len("postgresql+asyncpg://"):]
    elif url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    return url


def run_migrations_offline() -> None:
    context.configure(
        url=_resolve_sync_url(),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    cfg = config.get_section(config.config_ini_section, {}) or {}
    cfg["sqlalchemy.url"] = _resolve_sync_url()
    connectable = engine_from_config(cfg, prefix="sqlalchemy.", poolclass=pool.NullPool)

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
