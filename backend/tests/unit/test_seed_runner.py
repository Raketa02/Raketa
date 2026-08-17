"""The seed path: what it may not do, what it writes, and that the command runs.

Three claims, and each fails differently.

1. **Nothing in the seed path writes a table directly** — a structural walk,
   because that is the failure this system exists to prevent and a green suite
   would look identical afterwards. An `INSERT` into `users` produces an account
   that signs in perfectly and has no event stream behind it; the seeded data and
   the system's own account of that data then disagree, and only a replay ever
   says so.
2. **The aggregates it creates have real event streams** — asserted by reading
   the store, which is the one place the answer is not a matter of opinion. That
   the streams *replay* is `tests/api/test_seeds.py`'s, through the API, because
   a replay is only interesting where something depends on it.
3. **The command itself runs** — `python -m app.seeds`, twice, against a real
   database file. A seed system nobody has invoked from a shell is a library.
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path
from uuid import UUID

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import create_async_engine

from app.infrastructure.database.base import Base
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.auth.presentation.schemas import LoginRequest
from app.modules.users.domain.value_objects import Email, Nickname, RawPassword
from app.modules.users.presentation.schemas import UserResponse
from app.seeds import catalog
from app.seeds.catalog import (
    ACCOUNTS,
    RESERVED_TLD,
    SEED_EMAIL_DOMAIN,
    SEED_PASSWORD,
    SeedAccount,
)
from app.seeds.runner import SeededAccount, report, seed

ROOT = Path(__file__).resolve().parents[2]

#: Every module in the seed path. A glob, so a file added tomorrow is walked on
#: the day it exists — and the count is asserted rather than trusted, because a
#: glob that matches nothing passes silently and reads as a rule that held.
SEED_MODULES = sorted((ROOT / "app" / "seeds").glob("*.py"))

#: The four TLDs RFC 2606 §2 reserves, in one sentence, forever. No registry
#: will sell a name under any of them.
RFC2606_RESERVED_TLDS = frozenset({".test", ".example", ".invalid", ".localhost"})

#: SQLAlchemy's statement constructors. Importing one into the seed path is how
#: "just this once, it is only a fixture row" starts.
SQL_CONSTRUCTORS = frozenset(
    {"select", "insert", "update", "delete", "text", "table", "column"}
)

#: What a session is called here — `build_user_repository(session)` is the only
#: thing the seed path does with one.
SESSION_NAMES = frozenset({"session", "db", "conn", "connection"})

#: Session methods that reach a table. Matched against a *receiver* rather than
#: bare, because `execute` is also what a use case is asked to do — and asking a
#: use case to execute is the entire point of this package.
SESSION_WRITES = frozenset(
    {"add", "add_all", "merge", "delete", "execute", "scalars", "flush"}
)


def imported(path: Path) -> set[tuple[str, str]]:
    """`(module, name)` for every import in the file, `import x` included."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    found: set[tuple[str, str]] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            found.update((alias.name, alias.name) for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            found.update((node.module, alias.name) for alias in node.names)
    return found


def session_calls(path: Path) -> set[str]:
    """Every `session.method(...)` called in the file, by receiver name."""

    tree = ast.parse(path.read_text(encoding="utf-8"))
    return {
        f"{node.func.value.id}.{node.func.attr}"
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id in SESSION_NAMES
        and node.func.attr in SESSION_WRITES
    }


# ---------------------------------------------------------------------------
# 1. No direct table writes
# ---------------------------------------------------------------------------


def test_the_walk_has_something_to_walk():
    """The lesson a wildcard fence paid for: a glob matching nothing is a rule
    that holds vacuously and reads exactly like one that holds."""

    names = {path.name for path in SEED_MODULES}
    assert names == {
        "__init__.py",
        "__main__.py",
        "catalog.py",
        "guard.py",
        "runner.py",
    }


@pytest.mark.parametrize("path", SEED_MODULES, ids=lambda p: p.name)
def test_no_seed_module_imports_an_orm_model_or_a_statement(path):
    for module, name in imported(path):
        assert "infrastructure.database.models" not in module, path.name
        assert not module.endswith("_model"), path.name
        assert ".infrastructure" not in module or module.endswith(
            "database.engine"
        ), f"{path.name} imports an adapter's internals: {module}"
        if module == "sqlalchemy" or module.startswith("sqlalchemy."):
            assert name not in SQL_CONSTRUCTORS, f"{path.name} imports {name}"


@pytest.mark.parametrize("path", SEED_MODULES, ids=lambda p: p.name)
def test_no_seed_module_writes_through_a_session(path):
    """`session.add(...)` is the one-line version of the thing this system
    exists to refuse — and it is a line that works.

    Matched on the receiver's name, which is what the codebase calls a session.
    That is narrower than it sounds: reaching a table under another name means
    importing a statement or an ORM model, and the walk above refuses both.
    """

    offending = session_calls(path)
    assert not offending, f"{path.name} calls {sorted(offending)}"


# ---------------------------------------------------------------------------
# The catalog
# ---------------------------------------------------------------------------


def test_every_address_is_on_a_reserved_tld():
    """The point of the rule is that no registry can ever sell the name.

    `RFC2606_RESERVED_TLDS` is written out here rather than read from the
    catalog, because a test that checks a constant against itself agrees with
    every value that constant could take — a mutation run put that hole here,
    and `.com` passed. Which of the four is used, and why it is not `.test`, is
    `test_the_boundary_schemas_accept_every_seeded_address`.
    """

    assert RESERVED_TLD in RFC2606_RESERVED_TLDS
    assert SEED_EMAIL_DOMAIN.endswith(RESERVED_TLD)
    for account in ACCOUNTS:
        assert account.email.endswith(RESERVED_TLD)


def test_every_account_is_named_for_its_state():
    """The address is derived from the name, so an account cannot be called one
    thing and reachable at another."""

    for account in ACCOUNTS:
        assert account.email == f"{account.slug}@{SEED_EMAIL_DOMAIN}"
        assert account.nickname == account.slug
        assert account.description


def test_the_catalog_is_addressable_by_the_domain():
    """The values the registration endpoint would be handed, asked of the same
    value objects it validates them with."""

    RawPassword(SEED_PASSWORD)
    for account in ACCOUNTS:
        assert Email(account.email).value == account.email
        assert Nickname(account.nickname).value == account.nickname


def test_an_unaddressable_catalog_is_refused_before_anything_is_written(
    monkeypatch,
):
    """The check runs at import, so a bad entry never reaches a half-done run.

    What this pins is that the check *works*; that it is *called* on import is
    not separately asserted, and removing the call alone leaves this suite green
    — every property it enforces is asserted directly above. The call is what
    turns a mid-run failure into a legible one, not the only thing standing
    between the catalog and a bad address.
    """

    monkeypatch.setattr(
        catalog,
        "ACCOUNTS",
        (SeedAccount(slug="a", sport=ACCOUNTS[0].sport, description="too short"),),
    )

    with pytest.raises(ValueError, match="nickname"):
        catalog._refuse_an_impossible_catalog()


def test_the_boundary_schemas_accept_every_seeded_address():
    """The domain is not the only thing with an opinion about an address.

    `LoginRequest` and `UserResponse` are `pydantic.EmailStr`, which refuses any
    TLD on `email-validator`'s special-use list — `.test` among them. That is why
    `RESERVED_TLD` is `.example` and not the `.test` the ticket names: a seeded
    account nobody can sign in as is not an account.

    Asserted here, at the boundary, so that a dependency bump which adds
    `example` to that list fails by name instead of as a 422 in an API test.
    """

    for account in ACCOUNTS:
        assert LoginRequest(email=account.email, password=SEED_PASSWORD)
        assert UserResponse(
            id=UUID(int=0),
            email=account.email,
            nickname=account.nickname,
            authority="USER",
            is_admin=False,
            is_active=True,
        )


# ---------------------------------------------------------------------------
# 2. Real event streams, and the same state twice
# ---------------------------------------------------------------------------


async def _streams(session) -> dict[str, int]:
    rows = await session.execute(
        select(EventStoreORM.aggregate_type, func.count())
        .group_by(EventStoreORM.aggregate_type)
    )
    return {aggregate: count for aggregate, count in rows.all()}


async def test_seeding_writes_an_event_stream_for_every_aggregate(session_factory):
    """The whole argument for going through the use cases, in one assertion: a
    directly-written row would leave these empty and everything else identical."""

    async with session_factory() as session:
        seeded = await seed(session)
        streams = await _streams(session)

    assert len(seeded) == len(ACCOUNTS)
    assert streams.get("user", 0) >= len(ACCOUNTS)
    assert streams.get("assessment", 0) >= len(ACCOUNTS)


async def test_re_running_leaves_the_same_state(session_factory):
    """Not "does not crash": the same ids, and a second run that says it created
    nothing."""

    async with session_factory() as session:
        first = await seed(session)
        streams_after_first = await _streams(session)
        second = await seed(session)
        streams_after_second = await _streams(session)

    assert [entry.player_id for entry in first] == [
        entry.player_id for entry in second
    ]
    assert [entry.assessment_id for entry in first] == [
        entry.assessment_id for entry in second
    ]
    assert all(entry.registered for entry in first)
    assert not any(entry.registered for entry in second)
    assert not any(entry.assessment_started for entry in second)
    assert all(entry.already_present for entry in second)
    assert streams_after_first == streams_after_second, "a re-run appended events"


def test_the_report_names_the_address_the_password_and_the_state():
    """What a developer reads. Built from the run rather than from the catalog,
    so it cannot describe an account the run did not touch."""

    account = ACCOUNTS[0]
    lines = report(
        (
            SeededAccount(
                account=account,
                player_id=UUID(int=1),
                assessment_id=UUID(int=2),
                registered=True,
                assessment_started=True,
            ),
        )
    )
    text = "\n".join(lines)

    assert account.email in text
    assert SEED_PASSWORD in text
    assert account.description in text
    assert "created" in text
    assert str(UUID(int=2)) in text


# ---------------------------------------------------------------------------
# 3. The command runs
# ---------------------------------------------------------------------------


async def test_the_command_seeds_a_real_database_and_is_idempotent(tmp_path):
    """`python -m app.seeds`, twice, against a database on disk.

    The subprocess is the point. Everything above imports the runner and calls
    it; this is the entry point `make seed` invokes, with the schema created the
    way a migration would have left it and nothing of the test process shared
    with it.
    """

    database = tmp_path / "seed.db"
    url = f"sqlite+aiosqlite:///{database}"

    engine = create_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    env = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "PYTHONPATH": str(ROOT),
        "APP_ENV": "local",
        "JWT_SECRET_KEY": "test-secret-do-not-use-in-prod",
        "WRITER_DB_URL": url,
        "DB_SSL_MODE": "disable",
    }

    def run_command() -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "-m", "app.seeds"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=180,
        )

    first = run_command()
    assert first.returncode == 0, first.stderr
    assert ACCOUNTS[0].email in first.stdout
    assert "[created]" in first.stdout

    second = run_command()
    assert second.returncode == 0, second.stderr
    assert "[already present]" in second.stdout
    assert "[created]" not in second.stdout
