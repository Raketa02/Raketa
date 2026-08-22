"""The Courts migration and the Courts models emit the same schema.

The sibling `test_clubs_migration.py` states the argument in full and this file
inherits it: two things describe these tables — `Base.metadata`, which the whole
fast suite is tested against, and `migrations/versions/0008_courts.py`, which is
what a real database gets. Nothing else compares them, and a guarantee present in
one and absent from the other is worse than not having it, because the suite
reads as though it were enforced.

**What is different here, and it is the whole point of this context.** The
exclusion constraint is not in `Base.metadata` at all: `EXCLUDE USING gist` has
no SQLite spelling, so it is attached by a dialect-scoped `after_create` listener
and issued by the migration as raw DDL. That means the DDL comparison next door
cannot see it — two files could agree perfectly about `reservations` while the
constraint the table exists for was in neither. So this file asserts the string
**itself**, in both places, and asserts what it says: keyed on the court,
testing overlap rather than adjacency, half-open, and partial over the live rows.

No database is touched, so this runs on every `make check`.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database import models as _models  # noqa: F401  (registers)
from app.infrastructure.database.base import Base
from app.modules.courts.infrastructure import sqlalchemy_court_models as declared

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations" / "versions" / "0008_courts.py"

COURT_TABLES = ("reservations", "bookings")

INDEXES = {
    "ix_reservations_club_id": ("reservations", ("club_id",)),
    "ix_reservations_court_id": ("reservations", ("court_id",)),
    "ix_bookings_club_id": ("bookings", ("club_id",)),
    "ix_bookings_player_id": ("bookings", ("player_id",)),
}


def _stand_in_for_the_clubs_tables(metadata: sa.MetaData) -> None:
    """`clubs` and `club_court_categories`, as the foreign keys need them.

    Migration 0007 created them and this one only points at them, so the
    recorder's metadata has never heard of either — and an unresolvable foreign
    key stops the DDL compiling before anything is compared. Only the name and
    the referenced column matter to a `REFERENCES` clause, so a stand-in is
    exactly as good here as the real declaration and does not pull 0007 into
    this file's blast radius.
    """

    for table in ("clubs", "club_court_categories"):
        sa.Table(
            table,
            metadata,
            sa.Column("id", UUIDType(binary=False), primary_key=True),
        )


class _Recorder:
    """Stands in for `alembic.op`, collecting what `upgrade()` asks for.

    Wider than the Clubs one by exactly two methods: `execute`, because the
    constraint this context turns on is raw DDL, and `get_bind`, because that
    DDL is guarded by dialect. The bind reports PostgreSQL, so what is recorded
    is what a real database is given.
    """

    def __init__(self) -> None:
        self.metadata = sa.MetaData()
        self.indexes: list[sa.Index] = []
        self.executed: list[str] = []
        self.created: list[str] = []
        _stand_in_for_the_clubs_tables(self.metadata)

    def create_table(self, name: str, *columns: Any, **kw: Any) -> None:
        sa.Table(name, self.metadata, *columns, **kw)
        self.created.append(name)

    def create_index(
        self,
        name: str,
        table: str,
        columns: list[str],
        unique: bool = False,
        **kw: Any,
    ) -> None:
        self.indexes.append(
            sa.Index(
                name,
                *(self.metadata.tables[table].c[column] for column in columns),
                unique=unique,
                **kw,
            )
        )

    def execute(self, statement: str) -> None:
        self.executed.append(str(statement))

    def get_bind(self) -> Any:
        class _Bind:
            dialect = postgresql.dialect()

        return _Bind()

    def drop_table(self, name: str) -> None:  # pragma: no cover - upgrade only
        raise AssertionError("upgrade() must not drop a table")


@pytest.fixture(scope="module")
def migrated() -> _Recorder:
    spec = importlib.util.spec_from_file_location("courts_migration", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    recorder = _Recorder()
    module.op = recorder
    module.upgrade()
    return recorder


@pytest.fixture(scope="module")
def migration_module() -> Any:
    spec = importlib.util.spec_from_file_location("courts_migration_raw", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _table_ddl(table: sa.Table) -> str:
    return str(CreateTable(table).compile(dialect=postgresql.dialect())).strip()


def _index_ddl(index: sa.Index) -> str:
    return str(CreateIndex(index).compile(dialect=postgresql.dialect())).strip()


# --- the tables -------------------------------------------------------------


def test_the_migration_creates_exactly_the_court_tables(migrated):
    assert set(migrated.created) == set(COURT_TABLES)


@pytest.mark.parametrize("name", COURT_TABLES)
def test_each_table_matches_the_model_it_stands_for(migrated, name):
    assert _table_ddl(migrated.metadata.tables[name]) == _table_ddl(
        Base.metadata.tables[name]
    )


def test_every_index_matches_the_model_it_stands_for(migrated):
    from_migration = {index.name: _index_ddl(index) for index in migrated.indexes}
    from_models = {
        index.name: _index_ddl(index)
        for name in COURT_TABLES
        for index in Base.metadata.tables[name].indexes
    }

    assert from_migration == from_models


@pytest.mark.parametrize("name", sorted(INDEXES))
def test_the_declared_indexes_are_present(migrated, name):
    """The comparison above proves the two sides agree; this proves what they
    agree *about*. Deleting an index from both files would satisfy equality."""

    table, columns = INDEXES[name]
    index = next(i for i in migrated.indexes if i.name == name)
    assert index.table.name == table
    assert tuple(column.name for column in index.columns) == columns


# --- the constraint the context exists for ----------------------------------


def test_the_migration_issues_the_exclusion_constraint(migrated):
    assert declared.RESERVATION_EXCLUSION_DDL in migrated.executed


def test_the_migration_creates_btree_gist_before_the_constraint(migrated):
    """`court_id WITH =` needs an operator class GiST does not carry for uuid.

    Order matters and is asserted: the extension has to exist before the
    constraint that uses it, and a migration that got them the wrong way round
    would fail on a fresh database and nowhere else.
    """

    assert declared.BTREE_GIST_DDL in migrated.executed
    assert migrated.executed.index(declared.BTREE_GIST_DDL) < migrated.executed.index(
        declared.RESERVATION_EXCLUSION_DDL
    )


def test_the_two_files_spell_the_constraint_identically(migration_module):
    """The migration carries its own copy — a migration that imports application
    code is a migration that changes meaning when the code does. So the copies
    are compared instead, in every part."""

    assert migration_module.RESERVATION_EXCLUSION_DDL == (
        declared.RESERVATION_EXCLUSION_DDL
    )
    assert migration_module.BTREE_GIST_DDL == declared.BTREE_GIST_DDL
    assert migration_module.LIVE_CLAIM == declared.LIVE_CLAIM
    assert migration_module.RESERVATION_EXCLUSION == declared.RESERVATION_EXCLUSION


def test_the_constraint_says_what_adr_0035_decided():
    """Four properties, each of which is a different constraint if it changes.

    Written out rather than compared to a copy, because two files agreeing on
    the wrong DDL is exactly what the comparison above cannot catch.
    """

    ddl = declared.RESERVATION_EXCLUSION_DDL

    # Scoped to one court. Without it a club sells one hour a day, site-wide.
    assert "court_id WITH =" in ddl
    # Overlap, not adjacency: `-|-` would collide back-to-back reservations and
    # let overlapping ones through.
    assert "WITH &&" in ddl
    assert "-|-" not in ddl
    # Half-open, so a court freed at 18:00 and taken at 18:00 do not overlap —
    # which is what lets `turnaroundMin` widen a claim by padding.
    assert "tstzrange(claimed_from, claimed_to, '[)')" in ddl
    # Partial over the live rows, which is what makes *released, never deleted*
    # affordable.
    assert ddl.endswith("WHERE (released_at IS NULL)")


def test_no_availability_count_is_stored_anywhere(migrated):
    """*"Availability is a projection over reservations, never a stored number."*

    Stated where it can fail. ADR-0035 rejected the counter alternative by name,
    and the way a counter arrives is not a design review — it is one column on
    one table, added because a query looked slow.
    """

    columns = {
        column.name
        for name in COURT_TABLES
        for column in migrated.metadata.tables[name].columns
    }
    for banned in ("available", "availability", "free_courts", "remaining", "capacity"):
        assert not any(banned in column for column in columns), columns
