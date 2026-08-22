"""A court cannot be taken twice for the same interval — asserted against
Postgres, because SQLite has no such thing to assert.

ADR-0035 makes losing inventory a *query result* rather than a race: two matches
racing for court 3 resolve as one winner and one answer, and there is one story
to tell the player. That guarantee is an `EXCLUDE USING gist` constraint. It has
no SQLite equivalent — not a slower one, none — so a suite that runs only on
SQLite can state the rule in a comment and enforce nothing.

Every case here is paired with the same insert against the same table with the
constraint removed. The pair is the evidence: refused with it, accepted without.
"""

import asyncio
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from tests.integration import ddl

pytestmark = pytest.mark.postgres

# SQLSTATE 23P01. Asserted by code rather than by message, because a message is
# localised and reworded between releases, and because "some IntegrityError" is
# satisfied by a primary-key collision — which is exactly how a test like this
# passes while testing nothing.
EXCLUSION_VIOLATION = "23P01"

NINE_AM = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)

# The range is built by Postgres from two `timestamptz` parameters rather than
# bound as a literal: asyncpg refuses a string for a range column outright
# (`list, tuple or Range object expected`), and the alternative — importing
# asyncpg's Range into the test — would tie the harness to the driver. `[)` is
# spelled out here rather than left to the default so the half-open bound is
# stated where somebody reads the insert, not inferred from `tstzrange`'s
# documentation. It is what lets a court freed at 18:00 be taken at 18:00.
INSERT = (
    "INSERT INTO {table} (id, court_id, during) "
    "VALUES (:id, :court, tstzrange(:start, :end, '[)'))"
)


def _hours(start: datetime, length: float) -> dict:
    return {"start": start, "end": start + timedelta(hours=length)}


async def _insert(engine, table: str, court: uuid.UUID, during: dict) -> None:
    async with engine.begin() as connection:
        await connection.execute(
            text(INSERT.format(table=table)),
            {"id": uuid.uuid4(), "court": court, **during},
        )


async def _count(engine, table: str) -> int:
    async with engine.begin() as connection:
        return (
            await connection.execute(text(f"SELECT count(*) FROM {table}"))
        ).scalar_one()


@pytest.mark.asyncio
async def test_overlapping_reservations_on_one_court_are_refused(pg_engine, make_table):
    table = await make_table(lambda name: ddl.reservation_table(name))
    court = uuid.uuid4()

    await _insert(pg_engine, table, court, _hours(NINE_AM, 1.5))

    with pytest.raises(IntegrityError) as exc:
        await _insert(
            pg_engine, table, court, _hours(NINE_AM + timedelta(minutes=30), 1.5)
        )

    assert getattr(exc.value.orig, "sqlstate", None) == EXCLUSION_VIOLATION, (
        "the second reservation was refused, but not by the exclusion constraint"
    )
    assert await _count(pg_engine, table) == 1


@pytest.mark.asyncio
async def test_without_the_constraint_the_same_overlap_is_accepted(
    pg_engine, make_table
):
    """The negative control, and the reason the case above is not vacuous.

    If this one also refused the row, the assertion above would be reporting some
    other rule — a primary key, a not-null — as the exclusion constraint.
    """
    table = await make_table(
        lambda name: ddl.reservation_table(name, constrained=False)
    )
    court = uuid.uuid4()

    await _insert(pg_engine, table, court, _hours(NINE_AM, 1.5))
    await _insert(pg_engine, table, court, _hours(NINE_AM + timedelta(minutes=30), 1.5))

    assert await _count(pg_engine, table) == 2


@pytest.mark.asyncio
async def test_the_same_interval_on_a_different_court_is_accepted(
    pg_engine, make_table
):
    """The constraint is per court. A rule that refused the second row here would
    be a rule that lets one club sell one hour a day."""
    table = await make_table(lambda name: ddl.reservation_table(name))
    during = _hours(NINE_AM, 1.5)

    await _insert(pg_engine, table, uuid.uuid4(), during)
    await _insert(pg_engine, table, uuid.uuid4(), during)

    assert await _count(pg_engine, table) == 2


@pytest.mark.asyncio
async def test_back_to_back_reservations_touching_at_one_instant_are_accepted(
    pg_engine, make_table
):
    """09:00-10:00 and 10:00-11:00 do not overlap.

    Load-bearing rather than incidental: `turnaroundMin` widens a Raketa-created
    reservation's *claimed* interval (#65), which only works as padding if the
    unpadded boundary is not already a collision.
    """
    table = await make_table(lambda name: ddl.reservation_table(name))
    court = uuid.uuid4()

    await _insert(pg_engine, table, court, _hours(NINE_AM, 1))
    await _insert(pg_engine, table, court, _hours(NINE_AM + timedelta(hours=1), 1))

    assert await _count(pg_engine, table) == 2


@pytest.mark.asyncio
async def test_two_transactions_racing_for_one_court_produce_one_winner(
    pg_engine, make_table
):
    """The harness can hold two connections open at once, and the constraint
    resolves the race rather than deadlocking it.

    This is what SQLite structurally cannot host: the API suite's in-memory
    database is one connection behind a `StaticPool`, so "two writers" is not a
    state it can be put in. The loser gets an error at the moment the winner
    commits — a query result, per ADR-0035 — not a lock timeout and not a half
    written row.
    """
    table = await make_table(lambda name: ddl.reservation_table(name))
    court = uuid.uuid4()
    first_inserted = asyncio.Event()

    async def hold_then_commit() -> None:
        async with pg_engine.connect() as connection:
            async with connection.begin():
                await connection.execute(
                    text(INSERT.format(table=table)),
                    {"id": uuid.uuid4(), "court": court, **_hours(NINE_AM, 2)},
                )
                first_inserted.set()
                # Held open so the challenger below is blocking on this row's
                # uncommitted key when the commit lands.
                await asyncio.sleep(0.25)

    async def challenge() -> None:
        # Bounded, so a future edit that stops the first writer reaching its
        # insert fails this test instead of hanging the whole suite. That is not
        # hypothetical — it is what the first run of this file did.
        await asyncio.wait_for(first_inserted.wait(), timeout=10)
        async with pg_engine.connect() as connection:
            async with connection.begin():
                await connection.execute(
                    text(INSERT.format(table=table)),
                    {
                        "id": uuid.uuid4(),
                        "court": court,
                        **_hours(NINE_AM + timedelta(hours=1), 2),
                    },
                )

    winner, loser = await asyncio.gather(
        hold_then_commit(), challenge(), return_exceptions=True
    )

    assert winner is None, f"the first writer should have committed, got {winner!r}"
    assert isinstance(loser, IntegrityError), (
        f"the second writer should have been refused, got {loser!r}"
    )
    assert getattr(loser.orig, "sqlstate", None) == EXCLUSION_VIOLATION
    assert await _count(pg_engine, table) == 1
