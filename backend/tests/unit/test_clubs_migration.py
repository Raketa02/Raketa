"""The Clubs migration and the Clubs models emit the same schema.

**Why this exists.** Two things describe the Clubs tables: `Base.metadata`, which
is what `tests/conftest.py` builds a SQLite database from and therefore what the
whole fast suite is tested against, and `migrations/versions/0007_clubs.py`, which
is what a real database actually gets. Nothing else compares them. A partial
unique index present in one and absent from the other is a guarantee that holds
in every test and in nothing else — which is worse than not having it, because
the suite reads as though it were enforced.

**How.** The migration module is loaded and its `upgrade()` is run against a
recorder standing in for `alembic.op`, which collects the tables and indexes it
asks for. Those are rebuilt as SQLAlchemy objects and their DDL is compiled for
PostgreSQL and compared, string for string, with the DDL the models compile to.
No database is touched, so this runs on every `make check`.

It covers **only the Clubs tables**, deliberately: migrations 0001–0006 predate
the models they created in one case and were hand-edited in others, and asserting
about them here would be asserting somebody else's history is tidy. The rule this
states is for the tables it created.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.schema import CreateIndex, CreateTable

from app.infrastructure.database.base import Base
from app.infrastructure.database import models as _models  # noqa: F401  (registers)

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations" / "versions" / "0007_clubs.py"

CLUB_TABLES = (
    "clubs",
    "club_card_offsets",
    "club_policies",
    "club_payout_destinations",
    "club_court_categories",
    "club_court_catalogue",
)

#: The four partial unique indexes. Named here rather than derived, so one going
#: missing from *both* sides — which a comparison alone would call agreement —
#: fails as well.
PARTIAL_UNIQUE_INDEXES = {
    "uq_club_policies_open_row": ("club_policies", ("club_id",), "valid_to IS NULL"),
    "uq_club_payout_destinations_open_row": (
        "club_payout_destinations",
        ("club_id",),
        "valid_to IS NULL",
    ),
    "uq_club_court_catalogue_open_row": (
        "club_court_catalogue",
        ("court_id",),
        "valid_to IS NULL",
    ),
    "uq_club_court_categories_live_name": (
        "club_court_categories",
        ("club_id", "name"),
        "retired_at IS NULL",
    ),
}


class _Recorder:
    """Stands in for `alembic.op`, collecting what `upgrade()` asks for."""

    def __init__(self) -> None:
        self.metadata = sa.MetaData()
        self.indexes: list[sa.Index] = []

    def create_table(self, name: str, *columns: Any, **kw: Any) -> None:
        sa.Table(name, self.metadata, *columns, **kw)

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

    def drop_table(self, name: str) -> None:  # pragma: no cover - upgrade only
        raise AssertionError("upgrade() must not drop a table")


@pytest.fixture(scope="module")
def migrated() -> _Recorder:
    spec = importlib.util.spec_from_file_location("clubs_migration", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    recorder = _Recorder()
    module.op = recorder
    module.upgrade()
    return recorder


def _table_ddl(table: sa.Table) -> str:
    return str(CreateTable(table).compile(dialect=postgresql.dialect())).strip()


def _index_ddl(index: sa.Index) -> str:
    return str(CreateIndex(index).compile(dialect=postgresql.dialect())).strip()


def test_the_migration_creates_exactly_the_club_tables(migrated):
    assert set(migrated.metadata.tables) == set(CLUB_TABLES)


@pytest.mark.parametrize("name", CLUB_TABLES)
def test_each_table_matches_the_model_it_stands_for(migrated, name):
    assert _table_ddl(migrated.metadata.tables[name]) == _table_ddl(
        Base.metadata.tables[name]
    )


def test_every_index_matches_the_model_it_stands_for(migrated):
    from_migration = {index.name: _index_ddl(index) for index in migrated.indexes}
    from_models = {
        index.name: _index_ddl(index)
        for name in CLUB_TABLES
        for index in Base.metadata.tables[name].indexes
    }

    assert from_migration == from_models


@pytest.mark.parametrize("name", sorted(PARTIAL_UNIQUE_INDEXES))
def test_the_partial_unique_indexes_are_present_and_partial(migrated, name):
    """The comparison above proves the two sides agree; this proves what they
    agree *about*. Deleting the index from both files would satisfy equality."""

    table, columns, predicate = PARTIAL_UNIQUE_INDEXES[name]
    index = next(i for i in migrated.indexes if i.name == name)

    assert index.table.name == table
    assert tuple(column.name for column in index.columns) == columns
    assert index.unique is True
    ddl = _index_ddl(index)
    assert ddl.endswith(f"WHERE {predicate}"), ddl
