"""The Matches migration and the Matches models emit the same schema.

The sibling `test_clubs_migration.py` states the argument in full and this file
inherits it: two things describe these tables — `Base.metadata`, which the whole
fast suite is tested against, and `migrations/versions/0009_matches.py`, which is
what a real database gets. Nothing else compares them, and a guarantee present in
one and absent from the other is worse than not having it, because the suite
reads as though it were enforced.

**Nothing here is PostgreSQL-only**, which is the difference from `0008`. Both
partial indexes — one player to one seat, and the timekeeper's due rows — have a
SQLite spelling and get one, so the fast suite enforces the rules a real database
enforces. That is also why each predicate is asserted directly: two files could
agree perfectly while an index was partial over the wrong rows in both.

**Every migration that touches these tables is applied, in order**, because what
is being compared against is `Base.metadata` at head. A file left off the list
would make the models look as though they had drifted; worse, a *new* migration
left off would compare head's models against a schema two versions old and pass
by never seeing the difference.

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
VERSIONS = ROOT / "migrations" / "versions"
MIGRATION = VERSIONS / "0009_matches.py"
SCHEDULE_MIGRATION = VERSIONS / "0010_match_schedule.py"
DEPARTURES_MIGRATION = VERSIONS / "0011_match_departures.py"
CLAIMS_MIGRATION = VERSIONS / "0012_match_seat_claims.py"
CLOSED_AT_MIGRATION = VERSIONS / "0014_match_closed_at.py"

#: In the order Alembic applies them.
MIGRATIONS = (
    MIGRATION,
    SCHEDULE_MIGRATION,
    DEPARTURES_MIGRATION,
    CLAIMS_MIGRATION,
    # `0013` is Clubs' and touches none of these tables; the chain still applies
    # it, and this list is only the migrations that describe *this* schema.
    CLOSED_AT_MIGRATION,
)

MATCH_TABLES = (
    "matches",
    "match_seats",
    "match_vacancies",
    "match_departures",
    "match_seat_claims",
)

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
    "ix_matches_due_wake": ("matches", ("next_wake_at",), False),
    "ix_match_departures_match_id": ("match_departures", ("match_id",), False),
    "ix_match_departures_player_id": (
        "match_departures",
        ("player_id",),
        False,
    ),
    "ix_match_seat_claims_match_id": (
        "match_seat_claims",
        ("match_id",),
        False,
    ),
    #: **Not unique**, on either shape somebody might reach for. Over
    #: `(player_id)` a unique index would have to spell *live* as *unended* and
    #: would refuse a player on the strength of a row nobody had closed; over
    #: `(match_id, seat_index)` it would refuse the legitimate second claim on a
    #: seat whose previous claim expired — and the write it would refuse is the
    #: one that reaps it. Two claims on one seat are impossible already, and the
    #: `version` column on `matches` is what makes them so.
    "ix_match_seat_claims_unended": (
        "match_seat_claims",
        ("player_id", "expires_at"),
        False,
    ),
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

    def add_column(self, table: str, column: sa.Column[Any]) -> None:
        self.metadata.tables[table].append_column(column)

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


def _loaded(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def migrated() -> _Recorder:
    recorder = _Recorder()
    for path in MIGRATIONS:
        module = _loaded(path, f"migration_{path.stem}")
        module.op = recorder
        module.upgrade()
    return recorder


@pytest.fixture(scope="module")
def migration_module() -> Any:
    return _loaded(MIGRATION, "matches_migration_raw")


@pytest.fixture(scope="module")
def schedule_migration_module() -> Any:
    return _loaded(SCHEDULE_MIGRATION, "match_schedule_migration_raw")


@pytest.fixture(scope="module")
def departures_migration_module() -> Any:
    return _loaded(DEPARTURES_MIGRATION, "match_departures_migration_raw")


@pytest.fixture(scope="module")
def claims_migration_module() -> Any:
    return _loaded(CLAIMS_MIGRATION, "match_seat_claims_migration_raw")


def _table_ddl(table: sa.Table) -> str:
    return str(CreateTable(table).compile(dialect=postgresql.dialect())).strip()


def _index_ddl(index: sa.Index) -> str:
    return str(CreateIndex(index).compile(dialect=postgresql.dialect())).strip()


# --- the tables -------------------------------------------------------------


def test_the_migrations_create_exactly_the_match_tables(migrated):
    """Five tables across four files — `0010` adds columns and creates none."""

    assert set(migrated.created) == set(MATCH_TABLES)
    assert len(migrated.created) == len(MATCH_TABLES)


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
    court, no situation, no phase.

    **`next_wake_at` was on this list and has come off it**, which is a decision
    and not a relaxation. It is derived — `kernel.next_wake` computes it from the
    row it sits on — and ADR-0076 stores it anyway, because the question it
    answers is asked the other way round: not *when does this match next change*
    for one match in hand, but *which matches change in the next second* over the
    whole table. A function cannot be indexed. Everything else on this list is
    read one match at a time and stays derived.
    """

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
    ):
        assert derived not in columns, f"`matches.{derived}` is derivable"


def test_the_schedule_is_two_columns_and_neither_is_a_situation(migrated):
    """A moment and a label. ADR-0076: the handler re-derives, so there is
    nothing here to act on and nothing here that is an instruction."""

    columns = migrated.metadata.tables["matches"].c

    assert columns["next_wake_at"].nullable
    assert columns["wake_reason"].nullable
    assert isinstance(columns["next_wake_at"].type, sa.DateTime)
    assert columns["next_wake_at"].type.timezone


def test_the_due_index_is_partial_over_the_rows_that_have_a_moment(
    migrated, schedule_migration_module
):
    """Partial on `next_wake_at IS NOT NULL`, and **not** on the four
    cancellation flags.

    Both spell *non-terminal* today. The second is a restatement of rungs 1-4 in
    SQL — a second ladder (ADR-0040) in the one place nothing type-checks it —
    and it fails silently: the predicate here over-covers by a page, while a
    drifted copy of terminality leaves a due row unindexed and a club's court
    held for ever.
    """

    assert schedule_migration_module.SCHEDULED == declared.SCHEDULED
    index = next(i for i in migrated.indexes if i.name == declared.DUE_WAKE)
    ddl = _index_ddl(index)

    assert "UNIQUE" not in ddl
    assert f"WHERE {declared.SCHEDULED}" in ddl
    for flag in ("club_cancelled", "weather", "form_cancelled", "inventory_lost"):
        assert flag not in ddl, "terminality is restated in SQL"


def test_the_unended_claims_index_is_partial_and_not_unique(
    migrated, claims_migration_module
):
    """Partial over `ended_at IS NULL`, and deliberately **not** unique.

    *Live* is unended **and** not yet expired, and the second half cannot be an
    index predicate because it needs a clock. That asymmetry is the right way
    round — the index over-covers by the rows a reaper has not reached, which
    costs a page — where a *unique* index over the same predicate would have to
    spell *live* as *unended* and would refuse a player on the strength of a row
    nobody had got round to closing.
    """

    assert claims_migration_module.CLAIM_UNENDED == declared.CLAIM_UNENDED
    index = next(i for i in migrated.indexes if i.name == declared.UNENDED_CLAIMS)
    ddl = _index_ddl(index)

    assert "UNIQUE" not in ddl
    assert f"WHERE {declared.CLAIM_UNENDED}" in ddl


def test_a_claim_names_a_seat_and_never_touches_the_seat_row(migrated):
    """ADR-0081 in the schema: the seat under a live claim is untouched.

    `match_seats` gains nothing at all here — no `claimed_by`, no `claimed_until`
    — because a claim is not a seat state and columns there would be that
    decision reversed where nothing would ever re-argue it.
    """

    seats = migrated.metadata.tables["match_seats"]

    assert "claim" not in " ".join(seats.c.keys())
    assert set(seats.c.keys()) == {
        "id", "match_id", "seat_index", "player_id", "paid", "taken_at",
    }


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


def test_a_departure_carries_its_own_settlement(migrated):
    """The other half of ADR-0033: the hole above holds no money, and the money
    is here — with the seat as the only field the two share."""

    columns = set(migrated.metadata.tables["match_departures"].c.keys())

    assert columns == {
        "id",
        "match_id",
        "seat_index",
        "player_id",
        "departed_at",
        "quoted",
        "amount_grosze",
        "outcome",
        "settled_at",
    }


def test_the_amount_is_nullable_because_a_reversal_names_none(migrated):
    """ADR-0072's two payload forms, at the schema. Null is *nothing was taken*
    and the domain refuses a zero, because *nothing was taken* and *nothing has
    come back yet* are opposite sentences a blank cannot tell apart."""

    columns = migrated.metadata.tables["match_departures"].c

    assert columns["amount_grosze"].nullable
    assert columns["amount_grosze"].server_default is None
    assert not columns["quoted"].nullable
    assert not columns["player_id"].nullable


def test_an_unsettled_departure_has_no_outcome_and_no_moment(migrated):
    """Both null together while her money is undecided, and the direction they
    move in afterwards is the domain type's — a `CHECK` cannot see the old
    value, so nothing here claims to enforce it."""

    columns = migrated.metadata.tables["match_departures"].c

    assert columns["outcome"].nullable
    assert columns["settled_at"].nullable


def test_a_player_may_leave_the_same_match_twice(migrated):
    """No unique index on `(match_id, player_id)`: she may be talked back in and
    leave again, and each leaving is its own money."""

    for index in migrated.indexes:
        if index.table.name != "match_departures":
            continue
        assert not index.unique


def test_the_departures_migration_follows_the_schedule_one(
    departures_migration_module,
):
    assert departures_migration_module.revision == "0011_match_departures"
    assert departures_migration_module.down_revision == "0010_match_schedule"


def test_the_migration_follows_the_courts_one(migration_module):
    assert migration_module.revision == "0009_matches"
    assert migration_module.down_revision == "0008_courts"


def test_the_migration_issues_no_dialect_specific_ddl(migrated):
    """Unlike `0008`, this one has no PostgreSQL-only guarantee — so the fast
    suite enforces every rule a real database does."""

    assert migrated.executed == []
