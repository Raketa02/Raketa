"""Resolving the Postgres the integration suite runs against — and refusing to
pretend it does not need one.

Two guarantees the Now section stands on cannot be expressed in SQLite: a
reservation's overlapping-interval exclusion, and the partial unique index that
keeps exactly one open row per club-policy series. The API suite runs on
in-memory SQLite with `StaticPool` because that is what makes two thousand tests
fast, and nothing here proposes changing it. This directory is where a case that
genuinely needs Postgres lives instead.

**The failure this module exists to refuse is the silent skip.** The pattern
already in the tree — `tests/unit/test_sqlalchemy_event_store.py` skips unless
`EVENT_TEST_DATABASE_URL` is set — runs in CI today only because the workflow
happens to set that variable. Delete the line and the test goes quietly green
without executing, which is the exact shape of "a guarantee that silently stops
being enforced", and worse than one never claimed.

So the requirement is keyed on `CI`, **not** on a variable the workflow sets.
GitHub Actions sets `CI=true` itself; a pull request that removes the Postgres
service or the URL from `.github/workflows/ci.yml` therefore turns these tests
red rather than turning them off. Keying the requirement on `POSTGRES_TEST_URL`
would have been self-defeating: removing the variable would remove the
requirement to have it.

On a developer's own machine, where Docker may not be running, the cases skip
and say how to get a database.
"""

import os
from typing import Optional

# The URL is taken from the first of these that names a Postgres database. The
# explicit one is first so a developer can point the integration suite somewhere
# other than the application's own writer database; the other two are the
# variables CI already sets, so a pipeline that has a Postgres service reachable
# never has to be told twice.
URL_VARIABLES = ("POSTGRES_TEST_URL", "WRITER_DB_URL", "EVENT_TEST_DATABASE_URL")

_POSTGRES_SCHEMES = ("postgresql://", "postgresql+asyncpg://", "postgres://")

SKIP_REASON = (
    "No Postgres for the integration suite. Start one with `make up` and set "
    "POSTGRES_TEST_URL, e.g. "
    "POSTGRES_TEST_URL=postgresql+asyncpg://raketa_user:raketa_pwd@localhost:5432/raketa"
)

MISSING_IN_CI = (
    "CI is set but no Postgres URL was resolvable from "
    + ", ".join(URL_VARIABLES)
    + ". These cases assert guarantees SQLite cannot express — an interval "
    "exclusion constraint and a partial unique index — so skipping them in a "
    "pipeline would report a guarantee as enforced while enforcing nothing. "
    "Restore the `postgres` service and its URL in .github/workflows/ci.yml."
)


def to_asyncpg_url(url: str) -> str:
    """Normalise a Postgres URL onto the async driver the suite connects with.

    Deliberately a copy of the rule in `app/infrastructure/database/engine.py`
    rather than an import of it: the harness is what checks the application's
    behaviour, and a harness that reaches into the code under test to decide how
    to connect cannot report that code broken.
    """
    if url.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url[len("postgresql://") :]
    if url.startswith("postgres://"):
        return "postgresql+asyncpg://" + url[len("postgres://") :]
    return url


def is_postgres_url(url: str) -> bool:
    return url.startswith(_POSTGRES_SCHEMES)


def running_in_ci(environ: Optional[dict] = None) -> bool:
    """Whether this is a pipeline rather than somebody's laptop.

    `CI` is set by GitHub Actions, and by every other runner worth naming, so it
    is the one signal about this run that the repository's own workflow file
    cannot switch off. `0`, `false` and the empty string are read as *no*, since
    a developer who exports `CI=0` to silence some other tool has not asked for
    a Postgres.
    """
    raw = (environ if environ is not None else os.environ).get("CI", "")
    return raw.strip().lower() not in ("", "0", "false", "no")


def resolve_url(environ: Optional[dict] = None) -> Optional[str]:
    """The Postgres URL for the integration suite, or None if there is none.

    A variable holding a non-Postgres URL counts as *no URL* rather than as a
    URL to try: `WRITER_DB_URL` is SQLite for the whole API suite, and
    connecting an interval-exclusion test to SQLite would fail with a syntax
    error that reads like a broken test rather than like a missing database.
    """
    env = environ if environ is not None else os.environ
    for name in URL_VARIABLES:
        value = (env.get(name) or "").strip()
        if value and is_postgres_url(value):
            return to_asyncpg_url(value)
    return None
