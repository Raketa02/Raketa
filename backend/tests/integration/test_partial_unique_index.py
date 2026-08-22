"""Exactly one open row per club-policy series — asserted against Postgres.

`ClubPolicy` is versioned whole (#64), so *what was the hold cap on Friday at
16:00* has one answer: a change closes the current row and opens a new one. The
invariant that makes the question answerable is that a series has at most one
open row at a time, and the thing that enforces it is a unique index with a
`WHERE closed_at IS NULL` clause.

SQLite has partial indexes, so this one is not impossible there the way the
interval exclusion is — it is merely not what production runs, and the two
disagree about enough (uuid comparison, `timestamptz`, index-level locking under
concurrent inserts) that an assertion passing on SQLite says nothing about the
constraint the migration will actually create. It belongs here for the same
reason, one step weaker.

As next door, every case is paired with the same insert against the same table
with uniqueness removed.
"""

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.integration import ddl

pytestmark = pytest.mark.postgres

# SQLSTATE 23505, for the reason given next door: "some IntegrityError" is a
# claim satisfied by the primary key.
UNIQUE_VIOLATION = "23505"

FRIDAY_1600 = datetime(2026, 9, 4, 16, 0, tzinfo=timezone.utc)


async def _open_row(
    engine, table: str, club: uuid.UUID, max_hold_age: int
) -> uuid.UUID:
    row_id = uuid.uuid4()
    async with engine.begin() as connection:
        await connection.execute(
            text(
                f"INSERT INTO {table} (id, club_id, max_hold_age, closed_at) "
                "VALUES (:i, :c, :m, NULL)"
            ),
            {"i": row_id, "c": club, "m": max_hold_age},
        )
    return row_id


async def _close(engine, table: str, row_id: uuid.UUID) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text(f"UPDATE {table} SET closed_at = :t WHERE id = :i"),
            {"t": FRIDAY_1600, "i": row_id},
        )


async def _open_rows(engine, table: str, club: uuid.UUID) -> int:
    async with engine.begin() as connection:
        return (
            await connection.execute(
                text(
                    f"SELECT count(*) FROM {table} "
                    "WHERE club_id = :c AND closed_at IS NULL"
                ),
                {"c": club},
            )
        ).scalar_one()


async def _series(make_table, *, constrained: bool = True) -> str:
    table = await make_table(ddl.club_policy_table)
    await make_table(
        lambda index: ddl.one_open_row_per_series(
            table, index, constrained=constrained
        ),
        "INDEX",
    )
    return table


@pytest.mark.asyncio
async def test_a_second_open_row_for_one_club_is_refused(pg_engine, make_table):
    table = await _series(make_table)
    club = uuid.uuid4()

    await _open_row(pg_engine, table, club, max_hold_age=120)

    with pytest.raises(IntegrityError) as exc:
        await _open_row(pg_engine, table, club, max_hold_age=0)

    assert getattr(exc.value.orig, "sqlstate", None) == UNIQUE_VIOLATION, (
        "the second open row was refused, but not by the partial unique index"
    )
    assert await _open_rows(pg_engine, table, club) == 1


@pytest.mark.asyncio
async def test_without_uniqueness_the_second_open_row_is_accepted(
    pg_engine, make_table
):
    """The negative control. Without it, the case above would still pass if the
    `WHERE` clause were wrong and no row ever qualified."""
    table = await _series(make_table, constrained=False)
    club = uuid.uuid4()

    await _open_row(pg_engine, table, club, max_hold_age=120)
    await _open_row(pg_engine, table, club, max_hold_age=0)

    assert await _open_rows(pg_engine, table, club) == 2


@pytest.mark.asyncio
async def test_closing_the_open_row_lets_the_next_version_open(pg_engine, make_table):
    """The ordinary path, and the one a plain unique index would refuse: a club
    that has changed its policy twice has two rows carrying its id."""
    table = await _series(make_table)
    club = uuid.uuid4()

    first = await _open_row(pg_engine, table, club, max_hold_age=120)
    await _close(pg_engine, table, first)
    await _open_row(pg_engine, table, club, max_hold_age=0)

    assert await _open_rows(pg_engine, table, club) == 1
    async with pg_engine.begin() as connection:
        total = (
            await connection.execute(
                text(f"SELECT count(*) FROM {table} WHERE club_id = :c"), {"c": club}
            )
        ).scalar_one()
    assert total == 2, "the closed row is history and must survive the change"


@pytest.mark.asyncio
async def test_many_closed_rows_for_one_club_are_accepted(pg_engine, make_table):
    """The whole reason the index is partial. `max_hold_age` moves 120 -> 60 -> 0
    and the series keeps every step."""
    table = await _series(make_table)
    club = uuid.uuid4()

    for cap in (120, 60):
        row = await _open_row(pg_engine, table, club, max_hold_age=cap)
        await _close(pg_engine, table, row)
    await _open_row(pg_engine, table, club, max_hold_age=0)

    assert await _open_rows(pg_engine, table, club) == 1


@pytest.mark.asyncio
async def test_two_clubs_may_each_hold_an_open_row(pg_engine, make_table):
    """The uniqueness is per series, not global."""
    table = await _series(make_table)
    first, second = uuid.uuid4(), uuid.uuid4()

    await _open_row(pg_engine, table, first, max_hold_age=120)
    await _open_row(pg_engine, table, second, max_hold_age=0)

    assert await _open_rows(pg_engine, table, first) == 1
    assert await _open_rows(pg_engine, table, second) == 1
