"""The production guard: what it refuses, where it is checked, and what it says.

Two halves, and the second is the one that matters. The function is easy to test
and easy to satisfy without the guard actually holding — so the cases below also
drive the **real command** in a subprocess, under a production environment, and
assert it refuses before it can reach a database. A guard that is only ever
called by a test that calls it is not known to be in the path.

The subprocess cases point ``WRITER_DB_URL`` at a port nothing listens on. A run
that reached the database would fail with a connection error; the assertion is
that it fails with ``SeedRefused`` instead, which is the difference between a
guard and a coincidence.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.core.config import ConfigurationError, Environment, Settings
from app.seeds.guard import (
    SEEDABLE,
    SEEDABLE_NAMES,
    SeedRefused,
    refuse_unless_seedable,
)

ROOT = Path(__file__).resolve().parents[2]

#: Values no legitimate refusal message has any reason to repeat.
POISON_PASSWORD = "hunter2-do-not-log-me"
POISON_DB_URL = f"postgresql+asyncpg://u:{POISON_PASSWORD}@db.example:5432/raketa"
POISON_SECRET = "s3cret-do-not-log-me"
POISON_REDIS_URL = f"redis://:{POISON_PASSWORD}@redis.example:6379/0"

#: A database nothing is listening on, so reaching it is a distinguishable
#: failure from refusing to try.
UNREACHABLE_DB_URL = "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/nowhere"


@pytest.fixture
def clean_env(monkeypatch):
    """Scrub every setting name, the way `tests/unit/test_settings.py` does.

    `conftest.py` sets `JWT_SECRET_KEY`, `WRITER_DB_URL` and `APP_ENV` for the
    suite, and inheriting them here would disarm the refusals in the direction a
    passing test cannot tell apart from a working guard.
    """

    for name in Settings.model_fields:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def build(**overrides) -> Settings:
    """Settings from nothing but the arguments given.

    `_env_file=None` so a developer with a real `backend/.env` on disk does not
    change what these cases mean.
    """

    return Settings(_env_file=None, **overrides)


def production(**overrides) -> Settings:
    """A production settings object that is otherwise entirely valid.

    Built with poison values, so every assertion about what a refusal does *not*
    say is asserted against a message that had something to leak.
    """

    return build(
        APP_ENV=Environment.PRODUCTION,
        JWT_SECRET_KEY=POISON_SECRET,
        PHOTO_STORAGE_SECRET_KEY=POISON_SECRET,
        # `APP_HOST` and `REDIS_URL` are here because every *deployed*
        # environment is asked for them, production included (#341) — not
        # because seeding has any interest in either.
        APP_HOST="10.0.0.1",
        WRITER_DB_URL=POISON_DB_URL,
        REDIS_URL=POISON_REDIS_URL,
        DB_SSL_MODE="require",
        ALLOW_ORIGINS=["https://raketa.example"],
        **overrides,
    )


# ---------------------------------------------------------------------------
# The refusal itself
# ---------------------------------------------------------------------------


def test_production_is_refused(clean_env):
    with pytest.raises(SeedRefused):
        refuse_unless_seedable(production())


@pytest.mark.parametrize(
    "environment",
    [Environment.LOCAL, Environment.DEVELOPMENT, Environment.STAGING],
)
def test_the_other_three_are_permitted(clean_env, environment):
    """Named one per case rather than looped over `SEEDABLE`, so a table that
    lost an entry cannot make this test agree with it."""

    settings = build(
        APP_ENV=environment,
        # The three a deployed environment refuses to start without. They are
        # configuration, not seeding — this case is about the seed guard.
        APP_HOST="127.0.0.1",
        WRITER_DB_URL=POISON_DB_URL,
        REDIS_URL=POISON_REDIS_URL,
    )

    refuse_unless_seedable(settings)  # does not raise


def test_every_environment_has_been_decided_about():
    """A fifth environment must be argued with, not inherited.

    `SEEDABLE` is written out rather than derived as "everything but
    production", so this is the assertion that the table still covers the enum.
    The module raises on import if it does not; this says so where a reader
    looks for it.
    """

    assert set(SEEDABLE) == set(Environment)


def test_the_refusal_names_the_variable_and_the_alternatives(clean_env):
    with pytest.raises(SeedRefused) as raised:
        refuse_unless_seedable(production())

    message = str(raised.value)
    assert "APP_ENV" in message
    assert Environment.PRODUCTION.value in message
    for name in SEEDABLE_NAMES.split(", "):
        assert name in message


def test_the_refusal_leaks_neither_secret_nor_password(clean_env):
    """A seed run's output goes wherever the operator's terminal goes."""

    with pytest.raises(SeedRefused) as raised:
        refuse_unless_seedable(production())

    message = str(raised.value)
    assert POISON_PASSWORD not in message
    assert POISON_SECRET not in message
    assert POISON_DB_URL not in message


def test_a_seed_refusal_is_not_a_value_error():
    """The same shape `ConfigurationError` takes, and for the same reason: this
    is a refusal to proceed, not a badly-typed argument that some caller might
    reasonably swallow with a parse failure."""

    assert issubclass(SeedRefused, RuntimeError)
    assert not issubclass(SeedRefused, ValueError)
    assert issubclass(ConfigurationError, RuntimeError)


async def test_run_refuses_the_settings_it_is_handed(clean_env):
    """The import checked the *process's* settings. This asks the same question
    of the object that decides which database is about to be written to — a
    caller that constructs its own settings does not get to skip it."""

    from app.seeds.runner import run

    with pytest.raises(SeedRefused):
        await run(production())


# ---------------------------------------------------------------------------
# Where it is checked: on import, in a real process
# ---------------------------------------------------------------------------


def _run(args: list[str], **env_overrides) -> subprocess.CompletedProcess:
    """A fresh interpreter with an environment built from scratch.

    Not `os.environ` plus overrides: pytest's own environment carries
    `APP_ENV=local` from `conftest.py`, which is the value these cases are
    trying to replace.
    """

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": str(ROOT),
        **env_overrides,
    }
    return subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_importing_the_package_refuses_in_production():
    """`import app.seeds` is enough. Reaching around the runner is not a way in,
    because a submodule import executes the package's `__init__` first."""

    result = _run(
        ["-c", "import app.seeds.catalog"],
        APP_ENV="production",
        JWT_SECRET_KEY=POISON_SECRET,
        PHOTO_STORAGE_SECRET_KEY=POISON_SECRET,
        APP_HOST="10.0.0.1",
        WRITER_DB_URL=UNREACHABLE_DB_URL,
        REDIS_URL=POISON_REDIS_URL,
        DB_SSL_MODE="require",
        ALLOW_CREDENTIALS="false",
    )

    assert result.returncode != 0
    assert "SeedRefused" in result.stderr
    assert POISON_SECRET not in result.stderr


def test_the_command_refuses_in_production_before_it_reaches_a_database():
    """The real entry point, with the database pointed at a closed port."""

    result = _run(
        ["-m", "app.seeds"],
        APP_ENV="production",
        JWT_SECRET_KEY=POISON_SECRET,
        PHOTO_STORAGE_SECRET_KEY=POISON_SECRET,
        APP_HOST="10.0.0.1",
        WRITER_DB_URL=UNREACHABLE_DB_URL,
        REDIS_URL=POISON_REDIS_URL,
        DB_SSL_MODE="require",
        ALLOW_CREDENTIALS="false",
    )

    assert result.returncode != 0
    assert "SeedRefused" in result.stderr
    assert "APP_ENV" in result.stderr
    # Refused rather than attempted. The guard fires while the *package* is
    # being imported, so `app.seeds.runner` — the only module here that knows
    # what a database driver is — is never reached, and no frame of the
    # traceback belongs to one.
    assert "sqlalchemy" not in result.stderr


def test_the_same_import_succeeds_in_local():
    """The control. Without it, every case above passes for a package that
    simply does not import."""

    result = _run(
        ["-c", "import app.seeds.catalog; print('imported')"],
        APP_ENV="local",
        JWT_SECRET_KEY="test-secret-do-not-use-in-prod",
        WRITER_DB_URL="sqlite+aiosqlite:///:memory:",
        DB_SSL_MODE="disable",
    )

    assert result.returncode == 0, result.stderr
    assert "imported" in result.stdout
