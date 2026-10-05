import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import Connection, engine_from_config, pool, text

# Make `app.*` importable whether alembic runs from the repo root or from the
# /home/app working directory inside the container.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from app.core.config import get_settings  # noqa: E402
from app.infrastructure.database.base import Base  # noqa: E402
from app.infrastructure.database import models as _models  # noqa: E402,F401

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
        url = "postgresql://" + url[len("postgresql+asyncpg://") :]
    elif url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    return url


#: How long a revision id may be. Alembic sizes its version column at 32
#: characters, and two of this repository's ids are longer —
#: ``0036_payment_customers_and_notices`` and
#: ``0038_a_card_can_lose_its_court_hour`` — so Postgres refused to record them
#: and ``alembic upgrade`` failed there on every database (SQLite enforces no
#: ``VARCHAR`` length, which is why no test saw it). The column is made wide
#: enough before Alembic reads it, rather than the ids renamed, so a database
#: that holds either id already reads it as it is.
_REVISION_ID_LENGTH = 64


def _a_version_table_wide_enough(connection: Connection) -> None:
    if connection.dialect.name != "postgresql":
        return
    connection.execute(
        text(
            "CREATE TABLE IF NOT EXISTS alembic_version ("
            f"version_num VARCHAR({_REVISION_ID_LENGTH}) NOT NULL, "
            "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
        )
    )
    connection.execute(
        text(
            "ALTER TABLE alembic_version ALTER COLUMN version_num "
            f"TYPE VARCHAR({_REVISION_ID_LENGTH})"
        )
    )
    connection.commit()


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
        _a_version_table_wide_enough(connection)
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
