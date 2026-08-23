"""`0013_category_cover`'s `upgrade()`, executed against a real table.

**Why this exists.** ADR-0090 puts the roof on the category and takes the answer
for rows that already exist from where the fact has been living — the category's
free-text *name*. That is the one place in the product allowed to read a domain
fact out of copy, precisely because it happens once, in a diff somebody reviewed,
and never on a read path.

Once is also what makes it worth a test. A `LIKE` pattern, a `lower()` and the
order of two statements are three things that can be quietly wrong, and the
symptom is not an error — it is a padel court in Kraków silently claiming a roof
it does not have, in November, on the spine of every card. There is no second
chance to notice: the migration runs, and afterwards the names it read are just
names again.

**It drives `upgrade()` rather than the statements**, and that distinction was
measured rather than assumed. A first version executed `_BACKFILL` and `_DEFAULT`
directly and was **green** with `op.execute(_DEFAULT)` deleted from `upgrade()`
and green again with the two statements swapped — it asserted that the SQL was
right and nothing at all about the migration. So the recorder below performs the
DDL and the data statements for real, in the order `upgrade()` asks for them.

**And it makes SQLite's `LIKE` case-sensitive, which is the whole reason the
`lower()` is there.** SQLite folds ASCII case in `LIKE` by default and PostgreSQL
does not, so a backfill missing its `lower()` matches `Padel · Indoor` here and
misses it on the only database this migration will ever run against. A fast test
standing in for a real one has to stand in for *its* semantics; without the
pragma this suite would have been reporting on a dialect nobody deploys.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

ROOT = Path(__file__).resolve().parents[2]
MIGRATION = ROOT / "migrations" / "versions" / "0013_category_cover.py"

#: Every name the seed catalog authors, plus the two shapes that decide the
#: rule: a name that says nothing at all, and one that says *Indoor*. The first
#: is three of the nine real ones — a squash court and two badminton halls — and
#: the second is the capital a club will write and nobody will see coming.
NAMES = {
    "Padel · indoor": "indoor",
    "Padel · Mondo, indoor": "indoor",
    "Padel · Wall, outdoor": "outdoor",
    "Tennis · outdoor": "outdoor",
    "Squash · glass back": "outdoor",
    "Badminton · hall A": "outdoor",
    "Padel · Indoor": "indoor",
    "Padel": "outdoor",
}


class _Live:
    """`alembic.op`, performed against a connection instead of recorded.

    `alter_column` is the one operation not performed: SQLite cannot add a `NOT
    NULL` to a column in place, and what that statement is *for* — an honest
    constraint with no server default — is asserted below off the instruction it
    was given rather than off a table SQLite would have to be rebuilt to carry.
    """

    def __init__(self, connection: sa.Connection) -> None:
        self._connection = connection
        self.added: list[sa.Column] = []
        self.altered: list[tuple[str, str, dict]] = []

    def add_column(self, table: str, column: sa.Column) -> None:
        self.added.append(column)
        kind = column.type.compile(dialect=sqlite.dialect())
        self._connection.execute(
            sa.text(f"ALTER TABLE {table} ADD COLUMN {column.name} {kind}")
        )

    def execute(self, statement) -> None:
        self._connection.execute(statement)

    def alter_column(self, table: str, name: str, **kw) -> None:
        self.altered.append((table, name, kw))


@pytest.fixture
def migration():
    """Loaded per test, because two of them assign to its `op`."""

    spec = importlib.util.spec_from_file_location("category_cover", MIGRATION)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def upgraded(migration):
    """The table 0007 leaves behind, taken through `upgrade()` for real."""

    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        # PostgreSQL's `LIKE` is case-sensitive and SQLite's is not. The
        # migration runs on the former; this test would otherwise report on the
        # latter, and the `lower()` that makes the two agree would be untested.
        connection.execute(sa.text("PRAGMA case_sensitive_like = ON"))
        connection.execute(
            sa.text(
                "CREATE TABLE club_court_categories "
                "(id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
            )
        )
        for index, name in enumerate(NAMES):
            connection.execute(
                sa.text(
                    "INSERT INTO club_court_categories (id, name) VALUES (:id, :name)"
                ),
                {"id": index, "name": name},
            )

        migration.op = _Live(connection)
        migration.upgrade()

        rows = connection.execute(
            sa.text("SELECT name, cover FROM club_court_categories")
        ).all()
    return dict(rows)


@pytest.mark.parametrize("name", sorted(NAMES))
def test_each_name_is_backfilled_to_the_cover_it_declares(upgraded, name):
    assert upgraded[name] == NAMES[name]


def test_a_name_that_declares_nothing_never_claims_a_roof(upgraded):
    """The default is a decision and not a coin toss.

    Telling a player a court is outdoor when it has a roof costs her a match she
    would have wanted; telling her it is indoor when it has none costs her a
    soaking in ADR-0073's own November. Asserted separately from the table above
    so that flipping the default is one red test with the reason attached,
    rather than three rows quietly changing value.
    """

    assert upgraded["Squash · glass back"] == "outdoor"
    assert upgraded["Padel"] == "outdoor"


def test_no_row_is_left_without_a_cover(upgraded):
    """What makes the `NOT NULL` at the end of `upgrade()` apply rather than raise.

    The column arrives nullable precisely so the honest constraint can be added
    afterwards with no server default; a backfill that missed a shape would turn
    that into a migration which fails half way, on a live database.
    """

    assert None not in upgraded.values()
    assert set(upgraded) == set(NAMES)


def test_the_column_arrives_with_no_server_default_and_is_then_made_not_null(
    migration,
):
    """A server default is the fabricated observation ADR-0090 removed.

    It would mean a row inserted without a cover silently becomes outdoor — the
    same defect as the missing field, arriving through the schema instead. Which
    is also why the column cannot simply arrive `NOT NULL`: the three statements
    are what buy an honest constraint, and dropping the third leaves the model
    and the database disagreeing about a column that is now nullable on disk.
    """

    engine = sa.create_engine("sqlite://")
    with engine.begin() as connection:
        connection.execute(
            sa.text(
                "CREATE TABLE club_court_categories "
                "(id INTEGER PRIMARY KEY, name TEXT NOT NULL)"
            )
        )
        recorder = _Live(connection)
        migration.op = recorder
        migration.upgrade()

    assert [column.name for column in recorder.added] == ["cover"]
    assert recorder.added[0].server_default is None
    assert recorder.added[0].nullable is True
    assert recorder.altered == [
        (
            "club_court_categories",
            "cover",
            {"existing_type": recorder.altered[0][2]["existing_type"],
             "nullable": False},
        )
    ]
