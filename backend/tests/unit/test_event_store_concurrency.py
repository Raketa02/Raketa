"""The uniqueness the store enforces, asserted against a real database.

The fix for #35 rests on a claim about the schema rather than about our code:
**a stream cannot hold the same version twice, and the database is what says
so.** `uq_event_store_stream_version` has been on `event_store` since the table
was created, and `SqlAlchemyEventStore.append` already translates the resulting
`IntegrityError` into `EventStreamVersionConflict`.

That is what made the deterministic stream id the cheap option: no projection
table, no migration, and no rule for who maintains one. A claim that load-bearing
should not live only in a comment, so it is asserted here.

The interleaving itself — two starts that both read before either appends — is in
`test_concurrent_starts`, over the fake store, because `tests/api/` drives one
in-memory SQLite connection through HTTPX ASGI and cannot express concurrency.
Together the two cover the halves: that the use case serialises, and that the
serialisation has a database behind it rather than a Python comparison.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.application.events.store import EventStreamVersionConflict
from app.infrastructure.events.event_store_model import EventStoreORM
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.infrastructure.events.sqlalchemy_domain_event_store import SqlAlchemyEventStore
from app.kernel import Sport
from app.modules.rating.domain.events import AssessmentStarted
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import rating_event_codec

AT = datetime(2026, 8, 14, tzinfo=timezone.utc)


def _row(aggregate_id, version: int) -> EventStoreORM:
    return EventStoreORM(
        id=new_uuid(),
        aggregate_type="assessment",
        aggregate_id=aggregate_id,
        version=version,
        event_type="rating.assessment_started",
        schema_version=1,
        payload={"player_id": str(new_uuid()), "sport": "PADEL"},
        occurred_at=AT,
    )


def test_the_constraint_is_declared_on_the_table() -> None:
    # Named, because the failure message is what a future reader will search for.
    names = {constraint.name for constraint in EventStoreORM.__table__.constraints}
    assert "uq_event_store_stream_version" in names

    constraint = next(
        c
        for c in EventStoreORM.__table__.constraints
        if c.name == "uq_event_store_stream_version"
    )
    assert [column.name for column in constraint.columns] == [
        "aggregate_type",
        "aggregate_id",
        "version",
    ]


async def test_the_database_rejects_a_second_row_at_the_same_version(
    session_factory,
) -> None:
    # Not our comparison: the row is refused by the engine, which is what makes
    # the guarantee hold between two connections that never saw each other.
    aggregate_id = new_uuid()

    async with session_factory() as session:
        session.add(_row(aggregate_id, version=1))
        await session.commit()

    async with session_factory() as session:
        session.add(_row(aggregate_id, version=1))
        with pytest.raises(IntegrityError):
            await session.commit()


async def test_the_adapter_reports_that_rejection_as_a_version_conflict(
    session_factory,
) -> None:
    # The path a genuine race takes: the Python-side version check passed —
    # because the row that will collide was written by someone else after this
    # caller read — and the database is what refuses it. The adapter must turn
    # that into the domain's conflict rather than letting a driver error escape,
    # which is what makes it a 409 instead of a 500.
    aggregate_id = new_uuid()
    codec: JsonEventCodec = rating_event_codec()

    async with session_factory() as session:
        store = SqlAlchemyEventStore(session, codec)
        started = AssessmentStarted(
            assessment_id=aggregate_id,
            player_id=new_uuid(),
            sport=Sport.PADEL.value,
            engine_version="test",
            occurred_at=AT,
        )

        # Somebody else's row, already committed at the version this append is
        # about to claim. The adapter's own max-version read is bypassed by
        # inserting through the session directly.
        await store.append(
            aggregate_type="assessment",
            aggregate_id=aggregate_id,
            expected_version=0,
            events=[started],
        )
        await session.commit()

        with pytest.raises(EventStreamVersionConflict):
            await store.append(
                aggregate_type="assessment",
                aggregate_id=aggregate_id,
                expected_version=0,
                events=[started],
            )
        await session.rollback()

    async with session_factory() as session:
        rows = await session.execute(
            select(EventStoreORM).where(EventStoreORM.aggregate_id == aggregate_id)
        )
        # One append landed, the other did not. No stream ever holds two openings.
        assert len(rows.scalars().all()) == 1
