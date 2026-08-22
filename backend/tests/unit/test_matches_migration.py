"""The Matches migration and the Matches models emit the same schema.

The sibling `test_clubs_migration.py` states the argument in full and this file
inherits it: two things describe these tables — `Base.metadata`, which the whole
fast suite is tested against, and `migrations/versions/0009_matches.py`, which is
what a real database gets. Nothing else compares them, and a guarantee present in
one and absent from the other is worse than not having it, because the suite
reads as though it were enforced.

**Nothing here is PostgreSQL-only**, which is the difference from `0008`. The
partial unique index that keeps one player to one seat has a SQLite spelling and
gets one, so the fast suite enforces the rule a real database enforces. That is
also why the predicate is asserted directly: two files could agree perfectly
about `match_seats` while the index was partial over the wrong rows in both.

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
from app.modules.matches.infrastructure import sqlalchemy_match_models as declared

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations" / "versions" / "0009_matches.py"

MATCH_TABLES = ("matches", "match_seats", "match_vacancies")

INDEXES = {
    "ix_matches_club_id": ("matches", ("club_id",), False),
    "ix_matches_start": ("matches", ("start",), False),
    "ix_match_seats_match_id": ("match_seats", ("match_id",), False),
    "ix_match_seats_player_id": ("match_seats", ("player_id",), False),
    "uq_match_seats_one_per_player": (
        "match_seats",
        ("match_id", "player_id"),
        True,
    ),
    "ix_match_vacancies_match_id": ("match_vacancies", ("match_id",), False),
}


def _stand_in_for_the_clubs_tables(metadata: sa.MetaData) -> None:
    """`clubs` and `club_court_categories`, as the foreign keys need them.

    Migration 0007 created them and this one only points at them, so the
    recorder's metadata has never heard of either — and an unresolvable foreign
    key stops the DDL compiling before anything is compared.
    """

    for table in ("clubs", "club_court_categories"):
        sa.Table(
            table,
            metadata,
            sa.Column("id", UUIDType(binary=False), primary_key=True),
        )


class _Recorder:
    """Stands in for `alembic.op`, collecting what `upgrade()` asks for."""

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

    def execute(self, statement: str) -> None:  # pragma: no cover - none issued
        self.executed.append(str(statement))

    def get_bind(self) -> Any:  # pragma: no cover - nothing is dialect-guarded
        class _Bind:
            dialect = postgresql.dialect()

        return _Bind()

    def drop_table(self, name: str) -> None:  # pragma: no cover - upgrade only
        raise AssertionError("upgrade() must not drop a table")


@pytest.fixture(scope="module")
def migrated() -> _Recorder:
    spec = importlib.util.spec_from_file_location("matches_migration", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    recorder = _Recorder()
    module.op = recorder
    module.upgrade()
    return recorder


@pytest.fixture(scope="module")
def migration_module() -> Any:
    spec = importlib.util.spec_from_file_location("matches_migration_raw", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _table_ddl(table: sa.Table) -> str:
    return str(CreateTable(table).compile(dialect=postgresql.dialect())).strip()


def _index_ddl(index: sa.Index) -> str:
    return str(CreateIndex(index).compile(dialect=postgresql.dialect())).strip()


# --- the tables -------------------------------------------------------------


def test_the_migration_creates_exactly_the_match_tables(migrated):
    assert set(migrated.created) == set(MATCH_TABLES)


@pytest.mark.parametrize("name", MATCH_TABLES)
def test_each_table_matches_the_model_it_stands_for(migrated, name):
    assert _table_ddl(migrated.metadata.tables[name]) == _table_ddl(
        Base.metadata.tables[name]
    )


def test_every_index_matches_the_model_it_stands_for(migrated):
    from_migration = {index.name: _index_ddl(index) for index in migrated.indexes}
    from_models = {
        index.name: _index_ddl(index)
        for name in MATCH_TABLES
        for index in Base.metadata.tables[name].indexes
    }

    assert from_migration == from_models


@pytest.mark.parametrize("name", sorted(INDEXES))
def test_the_declared_indexes_are_present(migrated, name):
    """The comparison above proves the two sides agree; this proves what they
    agree *about*. Deleting an index from both files would satisfy equality."""

    table, columns, unique = INDEXES[name]
    index = next(i for i in migrated.indexes if i.name == name)
    assert index.table.name == table
    assert tuple(column.name for column in index.columns) == columns
    assert bool(index.unique) is unique


# --- the two rules the database keeps ---------------------------------------


def test_one_player_holds_one_seat_and_the_index_is_partial(
    migrated, migration_module
):
    """Every empty seat has a null player, and there are three in a fresh padel
    match — so a plain unique index would allow exactly one of them."""

    assert migration_module.SEAT_OCCUPIED == declared.SEAT_OCCUPIED
    index = next(
        i for i in migrated.indexes if i.name == declared.ONE_SEAT_PER_PLAYER
    )
    ddl = _index_ddl(index)

    assert "UNIQUE" in ddl
    assert f"WHERE {declared.SEAT_OCCUPIED}" in ddl


def test_a_seat_is_its_position(migrated):
    """`uq_match_seats_position` rides in the table, not in an index call."""

    ddl = _table_ddl(migrated.metadata.tables["match_seats"])

    assert "uq_match_seats_position" in ddl
    assert "UNIQUE (match_id, seat_index)" in ddl


def test_the_match_row_stores_nothing_a_reader_could_derive(migrated):
    """The five kinds' own test, at the schema. No `filled`, no seat count, no
    court, no situation, no phase."""

    columns = set(migrated.metadata.tables["matches"].c.keys())

    for derived in (
        "filled",
        "seat_count",
        "seats",
        "is_full",
        "situation",
        "phase",
        "state",
        "status",
        "court_id",
        "reservation_id",
        "hold_kind",
        "next_wake_at",
    ):
        assert derived not in columns, f"`matches.{derived}` is derivable"


def test_the_policy_snapshot_is_on_the_match(migrated):
    """ADR-0077: a club value honoured *as booked* is a Constitutive fact on the
    match, not a temporal query — which is what makes a situation one row-set."""

    columns = set(migrated.metadata.tables["matches"].c.keys())

    assert {
        "policy_window_minutes",
        "policy_join_cut_minutes",
        "policy_max_hold_age_minutes",
        "policy_prob_hold",
    } <= columns


def test_the_version_is_on_the_match_and_is_the_concurrency_guard(migrated):
    version = migrated.metadata.tables["matches"].c["version"]

    assert not version.nullable
    assert version.server_default is not None


def test_a_vacancy_carries_no_settlement(migrated):
    """Settlement and occupancy are independent axes (ADR-0033), so a hole holds
    no amount, no outcome and no player."""

    columns = set(migrated.metadata.tables["match_vacancies"].c.keys())

    assert columns == {"id", "match_id", "seat_index", "vacated_at", "filled_at"}


def test_the_migration_follows_the_courts_one(migration_module):
    assert migration_module.revision == "0009_matches"
    assert migration_module.down_revision == "0008_courts"


def test_the_migration_issues_no_dialect_specific_ddl(migrated):
    """Unlike `0008`, this one has no PostgreSQL-only guarantee — so the fast
    suite enforces every rule a real database does."""

    assert migrated.executed == []
