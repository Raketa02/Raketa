"""The console's gate: what it refuses, where it is checked, and what it says.

The same two halves ``tests/unit/test_seed_guard.py`` is built from, and the
second is again the one that matters. The function is easy to satisfy without
the gate holding anywhere, so the cases below also drive **real processes** under
environments the console is not served in, and assert three things at once:
importing any module of the console refuses with the console's own refusal,
importing the *application* does not, and the app such a process builds routes
nothing at ``/dev``.

**It is served in ``local`` only** (``docs/adr/0194`` §1). The console acts as
seed accounts without signing in, so it is a door with no credential at all; on
any shared host anybody who reached the address could be any seeded player.

The third is not a nicety. ``create_app`` reads ``CONSOLE_SERVED`` in every
environment, so if the refusal lived in ``app/api/dev/__init__.py`` — where the
seed system puts its own — a production deployable would crash at startup
because it read its own dev tool. That is an outage, not a gate, and
``test_a_production_process_builds_an_app_without_it`` is what would notice.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from app.api.dev.gate import (
    CONSOLE_SERVED,
    CONSOLE_SERVED_NAMES,
    ConsoleRefused,
    refuse_unless_served,
)
from app.core.config import ConfigurationError, Environment, Settings

ROOT = Path(__file__).resolve().parents[2]

#: Values no legitimate refusal message has any reason to repeat.
POISON_PASSWORD = "hunter2-do-not-log-me"
POISON_DB_URL = f"postgresql+asyncpg://u:{POISON_PASSWORD}@db.example:5432/rakieta"
POISON_SECRET = "s3cret-do-not-log-me"
POISON_REDIS_URL = f"redis://:{POISON_PASSWORD}@redis.example:6379/0"

#: A database nothing is listening on, so reaching it is a distinguishable
#: failure from refusing to try.
UNREACHABLE_DB_URL = "postgresql+asyncpg://nobody:nothing@127.0.0.1:1/nowhere"


@pytest.fixture
def clean_env(monkeypatch):
    """Scrub every setting name, as `test_seed_guard.py` does.

    `conftest.py` sets `APP_ENV=local` for the suite, and inheriting it here
    would disarm the refusals in the direction a passing test cannot tell apart
    from a working gate.
    """

    for name in Settings.model_fields:
        monkeypatch.delenv(name, raising=False)
    return monkeypatch


def build(**overrides) -> Settings:
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
        # `APP_HOST`, `REDIS_URL`, the two sites and the mail relay are here
        # because every *deployed* environment is asked for them, production
        # included (#341, #504, #507) — not because the console gate has any interest
        # in any of them.
        APP_HOST="10.0.0.1",
        WRITER_DB_URL=POISON_DB_URL,
        REDIS_URL=POISON_REDIS_URL,
        PUBLIC_SITE_URL="https://rakieta.example",
        CLUB_WEBSITE_URL="https://clubs.rakieta.example",
        SMTP_HOST="smtp.rakieta.example",
        SMTP_SECURITY="starttls",
        MAIL_SENDER="Rakieta <no-reply@rakieta.example>",
        PAYMENTS_PROVIDER="stripe",
        STRIPE_SECRET_KEY="sk_guard_suite",
        STRIPE_PUBLISHABLE_KEY="pk_guard_suite",
        STRIPE_WEBHOOK_SECRET="whsec_guard_suite",
        STRIPE_CONNECT_WEBHOOK_SECRET="whsec_guard_suite_connect",
        DB_SSL_MODE="require",
        ALLOW_ORIGINS=["https://rakieta.example"],
        **overrides,
    )


# ---------------------------------------------------------------------------
# The refusal itself
# ---------------------------------------------------------------------------


def test_production_is_refused(clean_env):
    with pytest.raises(ConsoleRefused):
        refuse_unless_served(production())


def test_local_is_served(clean_env):
    refuse_unless_served(build(APP_ENV=Environment.LOCAL))  # does not raise


@pytest.mark.parametrize(
    "environment", [Environment.DEVELOPMENT, Environment.STAGING]
)
def test_the_deployed_environments_are_refused_too(clean_env, environment):
    """Named one per case rather than looped over `CONSOLE_SERVED`, so a table
    that gained an entry cannot make this test agree with it. The seed still
    runs in both (`SEEDABLE`); the console does not — the case two tables were
    kept for."""

    settings = build(
        APP_ENV=environment,
        APP_HOST="127.0.0.1",
        WRITER_DB_URL=POISON_DB_URL,
        REDIS_URL=POISON_REDIS_URL,
        PUBLIC_SITE_URL="https://rakieta.example",
        CLUB_WEBSITE_URL="https://clubs.rakieta.example",
        SMTP_HOST="smtp.rakieta.example",
        SMTP_SECURITY="starttls",
        MAIL_SENDER="Rakieta <no-reply@rakieta.example>",
        PAYMENTS_PROVIDER="stripe",
        STRIPE_SECRET_KEY="sk_guard_suite",
        STRIPE_PUBLISHABLE_KEY="pk_guard_suite",
        STRIPE_WEBHOOK_SECRET="whsec_guard_suite",
        STRIPE_CONNECT_WEBHOOK_SECRET="whsec_guard_suite_connect",
    )

    with pytest.raises(ConsoleRefused):
        refuse_unless_served(settings)


def test_every_environment_has_been_decided_about():
    """A fifth environment must be argued with, not inherited.

    `CONSOLE_SERVED` is written out rather than derived as "everything but
    production", so this is the assertion that the table still covers the enum.
    The module raises on import if it does not; this says so where a reader
    looks for it.
    """

    assert set(CONSOLE_SERVED) == set(Environment)


def test_it_is_a_second_table_and_not_the_seed_one():
    """A different question, and now a different answer: the seed runs in
    three environments, the console in one. Deriving one refusal from the other
    is what `app/seeds/guard.py`'s own comment argues against, and the two
    answering differently is the case two tables were kept for."""

    from app.seeds.guard import SEEDABLE

    assert CONSOLE_SERVED is not SEEDABLE
    assert [env for env, served in CONSOLE_SERVED.items() if served] == [
        Environment.LOCAL
    ]
    assert SEEDABLE[Environment.DEVELOPMENT] and SEEDABLE[Environment.STAGING]


def test_the_refusal_names_the_variable_and_the_alternatives(clean_env):
    with pytest.raises(ConsoleRefused) as raised:
        refuse_unless_served(production())

    message = str(raised.value)
    assert "APP_ENV" in message
    assert Environment.PRODUCTION.value in message
    for name in CONSOLE_SERVED_NAMES.split(", "):
        assert name in message


def test_the_refusal_leaks_neither_secret_nor_password(clean_env):
    with pytest.raises(ConsoleRefused) as raised:
        refuse_unless_served(production())

    message = str(raised.value)
    assert POISON_PASSWORD not in message
    assert POISON_SECRET not in message
    assert POISON_DB_URL not in message


def test_a_console_refusal_is_not_a_value_error():
    """The shape `SeedRefused` and `ConfigurationError` take, for their reason:
    this is a refusal to proceed, not a badly-typed argument."""

    assert issubclass(ConsoleRefused, RuntimeError)
    assert not issubclass(ConsoleRefused, ValueError)
    assert issubclass(ConfigurationError, RuntimeError)


# ---------------------------------------------------------------------------
# Where it is checked: on import, in a real process
# ---------------------------------------------------------------------------


def _run(args: list[str], **env_overrides) -> subprocess.CompletedProcess:
    """A fresh interpreter with an environment built from scratch.

    Not `os.environ` plus overrides: pytest's own environment carries
    `APP_ENV=local` from `conftest.py`, which is the value these cases replace.
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


PRODUCTION_ENV = {
    "APP_ENV": "production",
    "JWT_SECRET_KEY": POISON_SECRET,
    "PHOTO_STORAGE_SECRET_KEY": POISON_SECRET,
    "APP_HOST": "10.0.0.1",
    "WRITER_DB_URL": UNREACHABLE_DB_URL,
    "REDIS_URL": POISON_REDIS_URL,
    "PUBLIC_SITE_URL": "https://rakieta.example",
    "CLUB_WEBSITE_URL": "https://clubs.rakieta.example",
    "SMTP_HOST": "smtp.rakieta.example",
    "SMTP_SECURITY": "starttls",
    "MAIL_SENDER": "Rakieta <no-reply@rakieta.example>",
    "PAYMENTS_PROVIDER": "stripe",
    "STRIPE_SECRET_KEY": "sk_guard_suite",
    "STRIPE_PUBLISHABLE_KEY": "pk_guard_suite",
    "STRIPE_WEBHOOK_SECRET": "whsec_guard_suite",
    "STRIPE_CONNECT_WEBHOOK_SECRET": "whsec_guard_suite_connect",
    "DB_SSL_MODE": "require",
    "ALLOW_CREDENTIALS": "false",
}


#: The same process, deployed somewhere the seed may still run — so the seed's
#: own refusal would let an import through, and only the console's stops it.
DEVELOPMENT_ENV = {**PRODUCTION_ENV, "APP_ENV": "development"}
STAGING_ENV = {**PRODUCTION_ENV, "APP_ENV": "staging"}

#: Imports each module of the console in turn and prints the error each one
#: raised. A module whose import raised is not left in `sys.modules`, so every
#: one is imported afresh and reaches its own first line.
EVERY_CONSOLE_MODULE = """
import importlib, pathlib, json
here = pathlib.Path("app/api/dev")
raised = {}
for path in sorted(here.glob("*.py")):
    if path.stem in ("__init__", "gate"):
        continue
    try:
        importlib.import_module(f"app.api.dev.{path.stem}")
        raised[path.stem] = None
    except Exception as error:
        raised[path.stem] = type(error).__name__
print(json.dumps(raised))
"""


def test_importing_the_console_refuses_in_production():
    """`import app.api.dev.routes` is enough: the refusal is the module's first
    import, so there is no order of imports that reaches a router first."""

    result = _run(["-c", "import app.api.dev.routes"], **PRODUCTION_ENV)

    assert result.returncode != 0
    assert "ConsoleRefused" in result.stderr
    assert POISON_SECRET not in result.stderr


@pytest.mark.parametrize(
    "environment", [PRODUCTION_ENV, DEVELOPMENT_ENV, STAGING_ENV],
    ids=["production", "development", "staging"],
)
def test_every_module_of_the_console_refuses_with_its_own_refusal(environment):
    """The console is built from the seed's building blocks now (ADR-0194 §4),
    and `app/seeds/__init__` refuses on import too — but only in production.

    So the order is load-bearing: were any module of the console to reach the
    seed system before `refusal.py`, production would answer `SeedRefused` —
    `CONSOLE_SERVED` would be a second table nothing had ever proved fires — and
    development and staging, where the seed may run, would import the console
    without a word. Every module but `gate` and the package's `__init__` (which
    `create_app` reads everywhere) must answer the console's own refusal.
    """

    result = _run(["-c", EVERY_CONSOLE_MODULE], **environment)

    assert result.returncode == 0, result.stderr
    raised = json.loads(result.stdout)
    assert {
        "routes",
        "refusal",
        "accounts",
        "people",
        "club",
        "provider",
        "board",
        "situations",
        "jobs",
    } <= set(raised)
    assert raised == {module: "ConsoleRefused" for module in raised}


@pytest.mark.parametrize(
    "environment", [PRODUCTION_ENV, DEVELOPMENT_ENV, STAGING_ENV],
    ids=["production", "development", "staging"],
)
def test_a_process_it_is_not_served_in_builds_an_app_without_it(environment):
    """The routes are absent outside `local` — and the reason the refusal is not
    in the package's `__init__`: reading the gate must never be what takes a
    deployable down."""

    result = _run(
        [
            "-c",
            "from app.main import create_app;"
            " print(sorted({r.path for r in create_app().routes}))",
        ],
        **environment,
    )

    assert result.returncode == 0, result.stderr
    # Exact paths and prefixes, as the printed list quotes them —
    # ``/players/me/devices`` (#549) is no console.
    assert "'/dev'" not in result.stdout
    assert "'/dev/" not in result.stdout


#: A fifth environment, spelled as `app/core/config.py` spells the four. Patched
#: over `Environment` *before* the gate is imported, in a process of its own, so
#: the module under test reads it exactly as it would read a real fifth name.
A_FIFTH_ENVIRONMENT = """
import enum
import app.core.config as config


class Environment(enum.StrEnum):
    LOCAL = "local"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    SANDBOX = "sandbox"


config.Environment = Environment
import app.api.dev.gate
"""


def test_a_fifth_environment_refuses_to_import():
    """The day somebody names one, this table stops covering `Environment`.

    `test_every_environment_has_been_decided_about` asserts the table covers the
    enum *today*, which is a statement about a tree that already satisfies it —
    it would pass just as well if `_undecided` had been deleted. This drives a
    real fifth name through a real import and asserts the refusal, which is the
    thing the written-out table buys and the only reason it is worth its length.
    """

    result = _run(
        ["-c", A_FIFTH_ENVIRONMENT],
        APP_ENV="local",
        JWT_SECRET_KEY="test-secret-do-not-use-in-prod",
        WRITER_DB_URL="sqlite+aiosqlite:///:memory:",
        DB_SSL_MODE="disable",
    )

    assert result.returncode != 0
    assert "CONSOLE_SERVED" in result.stderr
    assert "sandbox" in result.stderr
    # Decided about, rather than defaulted. A gate that guessed would be one
    # nobody argued with.
    assert "Decide" in result.stderr


def test_the_same_import_succeeds_in_local():
    """The control. Without it, every case above passes for a module that simply
    does not import."""

    result = _run(
        ["-c", "import app.api.dev.routes; print('imported')"],
        APP_ENV="local",
        JWT_SECRET_KEY="test-secret-do-not-use-in-prod",
        WRITER_DB_URL="sqlite+aiosqlite:///:memory:",
        DB_SSL_MODE="disable",
    )

    assert result.returncode == 0, result.stderr
    assert "imported" in result.stdout
