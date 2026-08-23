"""ADR-0030's command log: the window, the prune, and the collision.

Three claims, and none of them is visible from a route:

1. **The window is applied on the read.** A row past twenty-four hours is not a
   replay whether or not anything has deleted it, so correctness never waits on
   a sweep — asserted a minute either side of the boundary.
2. **The prune runs on the write.** ADR-0030 names *"a new thing to prune"* as
   this decision's cost, and a scheduled job would be a second moving part with
   its own failure mode and nothing watching it. One indexed delete per
   destructive command, scoped to **that** command's rows.
3. **The key collides at the door.** `(command, key)` is the primary key, so a
   second client choosing the same key is refused by the database rather than
   by a read-then-write race — and the flush is what makes that happen where
   somebody wrote a statement instead of at a commit nobody wrote.

Driven against the real SQLite the fast suite already stands up, because every
one of them is a property of the table rather than of a fake.
"""

from __future__ import annotations

import importlib.util
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
import sqlalchemy as sa
from sqlalchemy import func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.schema import CreateIndex, CreateTable

from app.application.ports import COMMAND_LOG_WINDOW_HOURS, LoggedCommand
from app.infrastructure.database.base import Base
from app.infrastructure.database.command_log_model import CommandLogORM
from app.infrastructure.database.sqlalchemy_command_log import SqlAlchemyCommandLog
from app.kernel import Instant, hours, instant, minutes, shifted

NOW: Instant = instant(datetime(2026, 8, 22, 12, 0, tzinfo=timezone.utc))
A_MINUTE = minutes(1)
COMMAND = "departure"


def an_entry(**kwargs) -> LoggedCommand:
    return LoggedCommand(
        **{
            "command": COMMAND,
            "key": "key-1",
            "player_id": uuid4(),
            "result": "reversed",
            "recorded_at": NOW,
            **kwargs,
        }
    )


async def _rows(session) -> int:
    return await session.scalar(select(func.count()).select_from(CommandLogORM))


async def test_a_key_answers_for_the_command_it_was_first_sent_with(
    session_factory,
) -> None:
    entry = an_entry()

    async with session_factory() as session:
        log = SqlAlchemyCommandLog(session)
        await log.remember(entry)
        await session.commit()

        found = await log.recall(command=COMMAND, key="key-1", now=NOW)

    assert found is not None
    assert found.player_id == entry.player_id
    assert found.result == "reversed"
    assert found.recorded_at == NOW


async def test_a_key_nobody_has_used_answers_nothing(session_factory) -> None:
    async with session_factory() as session:
        found = await SqlAlchemyCommandLog(session).recall(
            command=COMMAND, key="never-sent", now=NOW
        )

    assert found is None


async def test_a_key_answers_only_for_its_own_command(session_factory) -> None:
    """Half the key is the command's name, so two acts never share a namespace."""

    async with session_factory() as session:
        log = SqlAlchemyCommandLog(session)
        await log.remember(an_entry())
        await session.commit()

        assert await log.recall(command="result", key="key-1", now=NOW) is None


async def test_the_window_is_twenty_four_hours_and_it_closes_on_the_read(
    session_factory,
) -> None:
    """Asserted a minute either side, because a region is not a boundary."""

    async with session_factory() as session:
        log = SqlAlchemyCommandLog(session)
        await log.remember(an_entry(recorded_at=NOW))
        await session.commit()

        edge = shifted(NOW, hours(COMMAND_LOG_WINDOW_HOURS))
        assert await log.recall(command=COMMAND, key="key-1", now=edge) is not None
        assert (
            await log.recall(command=COMMAND, key="key-1", now=shifted(edge, A_MINUTE))
            is None
        )


async def test_an_expired_row_is_answered_as_never_seen_and_not_deleted(
    session_factory,
) -> None:
    """A read that writes cannot be taken inside somebody else's transaction.

    The row stays until the next write of its own command sweeps it, and the
    answer is already correct — which is what makes the sweep opportunistic
    rather than load-bearing.
    """

    async with session_factory() as session:
        log = SqlAlchemyCommandLog(session)
        await log.remember(an_entry(recorded_at=NOW))
        await session.commit()

        long_after = shifted(NOW, hours(48))
        assert await log.recall(command=COMMAND, key="key-1", now=long_after) is None
        assert await _rows(session) == 1


async def test_the_prune_runs_on_the_write_and_only_over_its_own_command(
    session_factory,
) -> None:
    """One indexed delete per destructive command, scoped to that command.

    A busy act must never walk another act's rows, and an act nobody sends must
    never have its rows swept by somebody else's traffic — that would make the
    table's contents depend on which route happened to be busy.
    """

    async with session_factory() as session:
        log = SqlAlchemyCommandLog(session)
        await log.remember(an_entry(key="stale", recorded_at=NOW))
        await log.remember(an_entry(command="result", key="stale-too", recorded_at=NOW))
        await session.commit()

        await log.remember(an_entry(key="fresh", recorded_at=shifted(NOW, hours(48))))
        await session.commit()

        assert await log.recall(command=COMMAND, key="stale", now=NOW) is None
        # The other command's row is untouched, however old it is.
        assert await log.recall(command="result", key="stale-too", now=NOW) is not None
        assert await _rows(session) == 2


async def test_a_row_inside_the_window_survives_a_later_write(session_factory) -> None:
    """The sweep is an expiry and not a truncation."""

    async with session_factory() as session:
        log = SqlAlchemyCommandLog(session)
        await log.remember(an_entry(key="first", recorded_at=NOW))
        await session.commit()

        await log.remember(an_entry(key="second", recorded_at=shifted(NOW, hours(1))))
        await session.commit()

        assert await _rows(session) == 2


async def test_one_key_cannot_be_written_twice_and_it_fails_where_it_was_written(
    session_factory,
) -> None:
    """The key is the primary key, so the collision is the database's answer.

    It is flushed rather than left pending, so it raises at the statement
    somebody wrote instead of at a commit nobody did.
    """

    async with session_factory() as session:
        log = SqlAlchemyCommandLog(session)
        await log.remember(an_entry())
        await session.commit()

        with pytest.raises(IntegrityError):
            await log.remember(an_entry(player_id=uuid4()))


async def test_neither_operation_commits(session_factory) -> None:
    """The log row joins the transaction its command is written in.

    A log that could disagree with the write it describes is the one state that
    makes a replay dangerous rather than merely useless — so an uncommitted
    write leaves nothing behind.
    """

    async with session_factory() as session:
        await SqlAlchemyCommandLog(session).remember(an_entry())
        await session.rollback()

    async with session_factory() as session:
        assert await _rows(session) == 0


# --- the migration and the model describe one table -------------------------
#
# Two things describe `command_log`: `Base.metadata`, which is what the fast
# suite builds a SQLite database from, and `0015_command_log.py`, which is what
# a real database gets. Nothing else compares them, and a primary key present in
# one and absent from the other is a guarantee that holds in every test and in
# nothing else — which is worse than not having it, because the suite reads as
# though it were enforced. The shape is `test_clubs_migration.py`'s.


class _Recorder:
    """Stands in for `alembic.op`, collecting what `upgrade()` asks for."""

    def __init__(self) -> None:
        self.metadata = sa.MetaData()
        self.indexes: list[sa.Index] = []

    def create_table(self, name: str, *columns, **kw) -> None:
        sa.Table(name, self.metadata, *columns, **kw)

    def create_index(self, name, table, columns, unique=False, **kw) -> None:
        self.indexes.append(
            sa.Index(
                name,
                *(self.metadata.tables[table].c[column] for column in columns),
                unique=unique,
                **kw,
            )
        )

    def drop_table(self, name: str) -> None:  # pragma: no cover - upgrade only
        raise AssertionError("upgrade() must not drop a table")


@pytest.fixture(scope="module")
def migrated() -> _Recorder:
    path = (
        Path(__file__).resolve().parents[2]
        / "migrations"
        / "versions"
        / "0015_command_log.py"
    )
    spec = importlib.util.spec_from_file_location("command_log_migration", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    module.op = recorder = _Recorder()
    module.upgrade()
    return recorder


def _ddl(subject) -> str:
    statement = (
        CreateIndex(subject) if isinstance(subject, sa.Index) else CreateTable(subject)
    )
    return str(statement.compile(dialect=postgresql.dialect())).strip()


def test_the_migration_creates_the_table_the_model_describes(migrated) -> None:
    assert list(migrated.metadata.tables) == ["command_log"]
    assert _ddl(migrated.metadata.tables["command_log"]) == _ddl(
        Base.metadata.tables["command_log"]
    )


def test_the_migration_creates_the_index_the_model_describes(migrated) -> None:
    """The prune's index, and a prune with no index is a table scan per write."""

    model = list(Base.metadata.tables["command_log"].indexes)
    assert [_ddl(one) for one in migrated.indexes] == [_ddl(one) for one in model]


def test_the_key_is_the_primary_key_on_both_sides(migrated) -> None:
    """Named rather than derived, so it going missing from *both* sides fails.

    A comparison alone would call that agreement — and it is the one constraint
    ADR-0030 actually asks for.
    """

    for table in (
        migrated.metadata.tables["command_log"],
        Base.metadata.tables["command_log"],
    ):
        assert [column.name for column in table.primary_key.columns] == [
            "command",
            "key",
        ]
