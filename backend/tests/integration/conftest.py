"""Fixtures for the cases that need a real Postgres.

`tests/conftest.py` one level up hands every test an in-memory SQLite engine and
should keep doing so. Nothing here overrides it; the fixtures below are separate
names, taken only by tests that ask for them.
"""

import uuid
from typing import AsyncIterator, Callable, List

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from tests.integration import ddl
from tests.integration.postgres import (
    MISSING_IN_CI,
    SKIP_REASON,
    resolve_url,
    running_in_ci,
)


@pytest.fixture(scope="session")
def postgres_url() -> str:
    """The URL, or a stop — loud in CI, quiet on a laptop.

    `pytest.fail` rather than `pytest.skip` when `CI` is set. A skipped test
    reports as green, and green is the answer this suite must not be able to
    give without a database behind it.
    """
    url = resolve_url()
    if url is None:
        if running_in_ci():
            pytest.fail(MISSING_IN_CI, pytrace=False)
        pytest.skip(SKIP_REASON)
    return url


@pytest_asyncio.fixture
async def pg_engine(postgres_url: str) -> AsyncIterator[AsyncEngine]:
    """One engine per test, pooling nothing, with btree_gist installed.

    Function-scoped and `NullPool` on purpose, and the reason is not caution.
    `asyncio_mode = "auto"` gives each test its own event loop, and an asyncpg
    connection is bound to the loop that opened it — so a session-scoped engine
    hands the second test a connection belonging to the first test's dead loop.
    That surfaces as `got Future attached to a different loop` and a stream of
    `unknown protocol state` errors, which read as a broken database rather than
    as a fixture scope. Measured here before it was written this way.

    A connection per test is affordable at this size. If this directory ever
    grows enough for that to hurt, the fix is a session-scoped event loop, not a
    session-scoped engine on a function-scoped loop.

    The server is identified rather than assumed. A URL can be Postgres-shaped
    and reach something else — pgbouncer in a mode that refuses DDL, or a
    developer's CockroachDB — and the failure that produces further down reads
    as a broken test rather than as the wrong database.
    """
    engine = create_async_engine(postgres_url, poolclass=NullPool)
    try:
        async with engine.begin() as connection:
            banner = str(
                (await connection.execute(text("SELECT version()"))).scalar_one()
            )
            assert "PostgreSQL" in banner, (
                f"the integration suite reached {banner[:60]!r}, which is not "
                "PostgreSQL — these cases assert guarantees only PostgreSQL makes"
            )
            await connection.execute(text(ddl.BTREE_GIST))
        yield engine
    finally:
        await engine.dispose()


@pytest_asyncio.fixture
async def make_table(pg_engine: AsyncEngine) -> AsyncIterator[Callable[..., str]]:
    """Create throwaway relations under generated names; drop them afterwards.

    Generated names rather than fixed ones so a repeated or interrupted run
    cannot collide with its own leftovers, and so nothing here can ever be
    mistaken for a domain table. Everything created is dropped in reverse on the
    way out, including when the test fails.
    """
    created: List[str] = []

    async def _create(statement_for: Callable[[str], str], kind: str = "TABLE") -> str:
        name = f"pg_guarantee_{uuid.uuid4().hex[:12]}"
        async with pg_engine.begin() as connection:
            await connection.execute(text(statement_for(name)))
        created.append(f"{kind} {name}")
        return name

    try:
        yield _create
    finally:
        async with pg_engine.begin() as connection:
            for relation in reversed(created):
                await connection.execute(text(f"DROP {relation} CASCADE"))
