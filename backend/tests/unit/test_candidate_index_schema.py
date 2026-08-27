"""The index's **tables**, checked against the same three claims its rows are.

``test_candidate_row_fence.py`` walks the in-memory type. This walks the schema,
because they are two different places the rule can break and a column outlives
the object that reads it: a table can carry a fact no ``CandidateRow`` field
exposes, and the day somebody adds a reader for it the fence would go red one
release too late.

The claims are ``docs/adr/0101``'s and ``the-candidate-index.md`` §3's, and both
are build-failing by intent.
"""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import Table

from app.infrastructure.database import models as _models  # noqa: F401
from app.infrastructure.database.base import Base
from app.modules.matchmaking.infrastructure.candidate_index_model import (
    CandidateIndexCursorORM,
    CandidatePlayerFactsORM,
    CandidateRowORM,
)
from tests.unit.test_candidate_row_fence import FORBIDDEN_WORDS
from tests.unit.test_scorable_candidate_fence import _words

INDEX_TABLES = (
    CandidateRowORM.__table__,
    CandidatePlayerFactsORM.__table__,
    CandidateIndexCursorORM.__table__,
)


def _columns(table: Table) -> list[str]:
    return [column.name for column in table.columns]


def test_the_index_is_keyed_on_a_player_and_a_sport_and_nothing_else() -> None:
    """``docs/adr/0101``: identity is ``(player_id, sport)``, never ``(…, area)``.

    An area in the key would make one person two candidates the moment they were
    reachable from two cells, and *who you are shown* would start depending on
    how the data happened to be laid out.
    """

    assert [
        column.name for column in CandidateRowORM.__table__.primary_key.columns
    ] == ["player_id", "sport"]


def test_no_table_in_the_index_carries_a_shard_key() -> None:
    """The partition is **derived**, so there is nothing for a conjunct to attach to.

    This is the one the schema can check and the type cannot fully: a column with
    no field reading it is invisible to a source walk and perfectly present in a
    migration.
    """

    offenders = [
        f"{table.name}.{column}"
        for table in INDEX_TABLES
        for column in _columns(table)
        if {"shard", "partition", "cell", "bucket"} & _words(column)
    ]
    assert offenders == []


def test_no_table_in_the_index_carries_a_forbidden_fact() -> None:
    """The same list the row's own fence walks, applied to the schema.

    ``gender`` is legitimately here and legitimately absent from that list
    (``docs/adr/0096``); a name, a photo, an email, a birthdate, a nationality or
    a live-truth fact is not.
    """

    offenders = [
        f"{table.name}.{column}"
        for table in INDEX_TABLES
        for column in _columns(table)
        if FORBIDDEN_WORDS & _words(column)
    ]
    assert offenders == []


def test_every_projected_table_carries_the_stamp_a_delta_refresh_reads() -> None:
    """One column, ``docs/adr/0110``'s, replacing §7.3's four-field row stamp.

    That stamp was designed against at-least-once HTTP delivery this design does
    not have; what survives has a different job, which is telling a refresh which
    rows moved.
    """

    for table in (CandidateRowORM.__table__, CandidatePlayerFactsORM.__table__):
        assert "applied_through_sequence_no" in _columns(table), table.name


def test_the_delta_refreshs_only_question_is_indexed() -> None:
    """*Which rows moved* runs every two seconds in every worker."""

    indexed = {
        tuple(column.name for column in index.columns)
        for index in CandidateRowORM.__table__.indexes
    }
    assert ("applied_through_sequence_no",) in indexed


def test_the_watermark_lives_in_exactly_one_row() -> None:
    """A single cursor, taken ``FOR UPDATE``, is the whole concurrency control.

    Keyed by the projection it belongs to rather than by ``id = 1``, so the row
    says what it is to somebody reading the table by hand and a second projection
    takes a second value rather than an integer nobody can interpret.
    """

    key = [
        column.name for column in CandidateIndexCursorORM.__table__.primary_key.columns
    ]
    assert key == ["projection"]


def test_the_index_tables_are_registered_for_migration_discovery() -> None:
    """A table Alembic cannot see is a table that exists only on a laptop."""

    assert {table.name for table in INDEX_TABLES} <= set(Base.metadata.tables)


def test_the_migration_creates_the_columns_the_models_declare() -> None:
    """The two halves of a schema change, checked against each other.

    ``Base.metadata`` is what the test suite creates its tables from and the
    migration is what production gets, so a column added to one and not the other
    is green everywhere except where it matters. The suite has run against
    SQLite-from-metadata since it existed, which is exactly why this drift is
    invisible without an assertion.

    The migration is **parsed rather than executed**: running it needs a
    PostgreSQL connection, and a check that only fires where a database is up is
    a check CI cannot be trusted to run.
    """

    import ast

    from app.modules.matchmaking.infrastructure import candidate_index_model

    migration = (
        Path(candidate_index_model.__file__).parent.parent.parent.parent.parent
        / "migrations"
        / "versions"
        / "0008_candidate_index.py"
    )
    declared = {
        call.args[0].value: sorted(
            column.args[0].value
            for column in call.args[1:]
            if getattr(column.func, "attr", "") == "Column"
        )
        for call in ast.walk(ast.parse(migration.read_text(encoding="utf-8")))
        if isinstance(call, ast.Call)
        and getattr(call.func, "attr", "") == "create_table"
    }

    assert declared == {
        table.name: sorted(column.name for column in table.columns)
        for table in INDEX_TABLES
    }


def test_the_source_a_search_will_bind_satisfies_the_port_it_binds() -> None:
    """The port is declared before its consumer arrives, and is checked anyway.

    ``docs/adr/0098``'s idiom — a demand with no registered implementation is a
    demand nobody notices going wrong — and the same failure is available here:
    ``CandidateSource`` names the one call a search makes, and a declaration
    nothing is checked against is a comment with a colon in it.
    """

    from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
    from app.modules.matchmaking.infrastructure.candidate_snapshot_source import (
        DatabaseCandidateSource,
    )

    assert isinstance(DatabaseCandidateSource, type)
    assert issubclass(DatabaseCandidateSource, CandidateSource)


def test_the_refresh_cadence_is_the_target_it_is_tuned_to() -> None:
    """§17's p50 and the interval that exists to meet it, kept in step.

    Two numbers that mean the same thing, in two files, is one of them going
    stale — and the one that would go stale silently is the **target**, because
    nothing reads it. This is what reads it.
    """

    from app.core.config import Settings
    from app.modules.matchmaking.domain.index_staleness import REFRESH_TARGET_P50

    cadence = Settings.model_fields["CANDIDATE_INDEX_REFRESH_INTERVAL_SECONDS"].default
    assert cadence == REFRESH_TARGET_P50


def test_every_column_a_movement_names_is_a_column_that_exists() -> None:
    """The hole under ``setattr(row, column, value)``.

    A movement carries column names as strings, and a declarative class has no
    ``__slots__`` — so ``setattr`` with a misspelt name **succeeds silently**,
    sets an attribute nothing persists, and the fact simply stops arriving in the
    index. No test of the fold would see it, because the fold's output is exactly
    right; no test of the schema would see it, because the column is fine. This
    is the join between them, and it is the reason the projection is allowed to
    speak in strings at all.
    """

    from app.modules.matchmaking.domain.candidate_projection import (
        CandidateRowMoved,
        PlayerFactsMoved,
        project,
    )
    from tests.unit.candidate_index_fixtures import ONE_OF_EACH_PROJECTED_CONTRACT

    facts_columns = {
        column.name for column in CandidatePlayerFactsORM.__table__.columns
    }
    row_columns = {column.name for column in CandidateRowORM.__table__.columns}

    unknown: list[str] = []
    named: set[str] = set()
    for event in ONE_OF_EACH_PROJECTED_CONTRACT:
        for movement in project(event):
            columns = (
                facts_columns if isinstance(movement, PlayerFactsMoved) else row_columns
            )
            assert isinstance(movement, (PlayerFactsMoved, CandidateRowMoved))
            named.update(movement.changes)
            unknown.extend(
                f"{type(event).__name__} → {column}"
                for column in movement.changes
                if column not in columns
            )

    assert unknown == []
    # And the walk reached something, so an empty fixture list cannot pass this
    # for the wrong reason.
    assert "social_tags" in named and "mu" in named


def test_the_walk_above_covers_every_contract_the_index_projects() -> None:
    """A contract with no instance is a column nobody checked.

    The failure the test above is otherwise open to: adding a contract to
    ``PROJECTED_CONTRACTS`` and forgetting the fixture leaves its columns
    unwalked, and the check goes on passing while covering less.
    """

    from app.modules.matchmaking.domain.candidate_projection import (
        PROJECTED_CONTRACTS,
    )
    from tests.unit.candidate_index_fixtures import ONE_OF_EACH_PROJECTED_CONTRACT

    assert {type(event) for event in ONE_OF_EACH_PROJECTED_CONTRACT} == set(
        PROJECTED_CONTRACTS
    )
