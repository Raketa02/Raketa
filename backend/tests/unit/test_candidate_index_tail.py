"""The tail reader against a real log: what it applies, and what it refuses to.

The pure half of the reader's reasoning is driven exhaustively in
``test_candidate_index_tail_plan.py``. This is the other half — the transaction,
the cursor, the stamps and the two tables — and it runs against SQLite, where
there is **no snapshot horizon and no concurrent appender**. So it asserts
contiguity and never gap-stepping, which is a place this suite is weaker than
production (``docs/adr/0110``) rather than a gap nobody noticed.
"""

from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.modules.matchmaking.infrastructure.candidate_index_model import (
    CANDIDATE_INDEX_CURSOR,
    CandidateIndexCursorORM,
    CandidatePlayerFactsORM,
    CandidateRowORM,
)
from app.modules.player_profile.domain.events import (
    PhotosChanged,
    SearchRadiusChanged,
    SocialTagsChanged,
)
from tests.unit.candidate_index_fixtures import (
    START,
    TickingClock,
    append,
    build_tail,
    intent_declared,
    opt_in,
    profile_created,
    rating_initialised,
)


async def _tick(session_factory, tail):
    async with session_factory() as session:
        return await tail.tick(session)


async def _cursor(session_factory) -> CandidateIndexCursorORM:
    async with session_factory() as session:
        return (
            await session.execute(
                select(CandidateIndexCursorORM).where(
                    CandidateIndexCursorORM.projection == CANDIDATE_INDEX_CURSOR
                )
            )
        ).scalar_one()


async def _rows(session_factory) -> list[CandidateRowORM]:
    async with session_factory() as session:
        return list(
            (
                await session.execute(
                    select(CandidateRowORM).order_by(CandidateRowORM.sport)
                )
            )
            .scalars()
            .all()
        )


async def test_a_full_onboarding_becomes_one_row_and_one_set_of_facts(
    session_factory,
) -> None:
    player = uuid4()
    await append(session_factory, profile_created(player))
    await append(session_factory, opt_in(player))
    await append(session_factory, rating_initialised(player))
    await append(session_factory, intent_declared(player))

    report = await _tick(session_factory, build_tail())

    assert report.events_applied == 4
    assert report.snapshot_version == 4

    rows = await _rows(session_factory)
    assert [(str(row.sport), row.mu, row.declared_intent) for row in rows] == [
        ("PADEL", 2.71, "COMPETITIVE")
    ]
    async with session_factory() as session:
        facts = await session.get(CandidatePlayerFactsORM, player)
    assert facts is not None
    assert facts.social_tags == ["competitive_edge"]
    assert facts.availability == ["1:MORNING"]
    assert (facts.area_latitude, facts.area_longitude) == (52.23, 21.01)
    assert facts.search_radius_km == 12
    assert facts.proposals_opt_in is True
    assert facts.gender == "FEMALE"
    assert facts.profile_created_at is not None


async def test_a_second_tick_over_the_same_log_applies_nothing(
    session_factory,
) -> None:
    """The cursor **is** the idempotency; there is no delivery to defend against."""

    player = uuid4()
    await append(session_factory, profile_created(player))
    tail = build_tail()

    first = await _tick(session_factory, tail)
    second = await _tick(session_factory, tail)

    assert (first.events_applied, second.events_applied) == (1, 0)
    assert second.snapshot_version == first.snapshot_version


async def test_the_reader_stamps_when_it_last_knew_it_was_caught_up(
    session_factory,
) -> None:
    """Stamped every tick, advance or not.

    A healthy reader over a quiet log advances nothing, and a dead one looks
    identical if you only watch the cursor — so staleness is measured from this
    rather than from the watermark.
    """

    tail = build_tail(clock=TickingClock())
    await _tick(session_factory, tail)
    first = (await _cursor(session_factory)).caught_up_at
    await _tick(session_factory, tail)
    second = (await _cursor(session_factory)).caught_up_at

    assert second > first


async def test_a_hole_stops_the_batch_at_the_contiguous_prefix(
    session_factory,
) -> None:
    """101 is present and 100 is not, so 101 is not applied.

    ``sequence_no`` is assigned at ``INSERT`` and not at ``COMMIT``, so a
    transaction holding 100 may still commit — and a watermark that had already
    counted 101 would be a lie about what the reader has seen.
    """

    player = uuid4()
    await append(session_factory, profile_created(player), sequence_no=1)
    await append(session_factory, rating_initialised(player), sequence_no=3)

    report = await _tick(session_factory, build_tail())

    assert report.events_applied == 1
    assert report.snapshot_version == 1
    assert await _rows(session_factory) == []


async def test_a_hole_is_never_stepped_over_where_there_is_no_horizon(
    session_factory,
) -> None:
    """**SQLite.** The wait has no way to end, and the reader says so by waiting.

    Recorded rather than papered over: the gap-stepping path is exercised against
    PostgreSQL or not at all (``docs/adr/0110``), and what stands in for it here
    is the pure walk in ``test_candidate_index_tail_plan.py``.
    """

    player = uuid4()
    await append(session_factory, profile_created(player), sequence_no=1)
    await append(session_factory, rating_initialised(player), sequence_no=3)
    tail = build_tail()

    await _tick(session_factory, tail)
    await _tick(session_factory, tail)

    cursor = await _cursor(session_factory)
    assert cursor.applied_through_sequence_no == 1
    assert cursor.hole_at_sequence_no is None
    assert cursor.hole_settles_at is None


async def test_a_hole_that_fills_lets_the_batch_run_on(session_factory) -> None:
    player = uuid4()
    await append(session_factory, profile_created(player), sequence_no=1)
    await append(session_factory, rating_initialised(player), sequence_no=3)
    tail = build_tail()
    await _tick(session_factory, tail)

    await append(session_factory, opt_in(player), sequence_no=2)
    report = await _tick(session_factory, tail)

    assert report.events_applied == 2
    assert report.snapshot_version == 3


async def test_a_profile_edit_restamps_every_one_of_that_players_rows(
    session_factory,
) -> None:
    """The facts are per player and the rows are per ``(player, sport)``.

    A delta refresh asks one question of one table — *which rows moved* — and
    this is what makes that the right question after an edit that touched neither
    Level.
    """

    player = uuid4()
    await append(session_factory, profile_created(player))
    await append(session_factory, rating_initialised(player, sport="PADEL"))
    await append(session_factory, rating_initialised(player, sport="TENNIS"))
    tail = build_tail()
    await _tick(session_factory, tail)
    before = {
        row.sport: row.applied_through_sequence_no
        for row in await _rows(session_factory)
    }

    await append(session_factory, SocialTagsChanged(player, ("social_first",), START))
    await _tick(session_factory, tail)

    after = {
        row.sport: row.applied_through_sequence_no
        for row in await _rows(session_factory)
    }
    assert set(after) == {"PADEL", "TENNIS"}
    assert all(after[sport] > before[sport] for sport in after)


async def test_a_row_is_stamped_with_the_event_that_moved_it_not_the_batch_end(
    session_factory,
) -> None:
    """The stamp is independent of how the log was cut into batches.

    That is what makes ``rebuild == tail`` an equality over whole tables rather
    than over the columns somebody remembered to exclude — a rebuild reads the
    same log in far larger batches, and a batch-end stamp would differ on every
    row while the projection was perfectly correct.
    """

    player = uuid4()
    stranger = uuid4()
    await append(session_factory, profile_created(player))
    await append(session_factory, rating_initialised(player))
    radius = await append(session_factory, SearchRadiusChanged(player, 30, START))
    await append(session_factory, profile_created(stranger))

    report = await _tick(session_factory, build_tail())

    rows = await _rows(session_factory)
    assert [row.applied_through_sequence_no for row in rows] == [radius]
    assert report.snapshot_version > radius


async def test_an_event_the_index_does_not_read_still_advances_the_watermark(
    session_factory,
) -> None:
    """``snapshot_version`` describes the **log**, not this projection's interest.

    It means *everything up to and including this is applied*, and an event that
    moves nothing has been applied exactly as completely as one that moves a row.
    """

    player = uuid4()
    await append(session_factory, PhotosChanged(player, ("a", "b"), START))

    report = await _tick(session_factory, build_tail())

    assert (report.events_applied, report.rows_moved) == (1, 0)
    assert report.snapshot_version == 1
    async with session_factory() as session:
        assert await session.get(CandidatePlayerFactsORM, player) is None


async def test_a_rating_before_the_profile_still_lands_and_waits(
    session_factory,
) -> None:
    """The fold may not look anything up, so ordering cannot change the answer.

    A row with no profile behind it is kept rather than dropped — it is not a
    candidate and never reaches a snapshot, and dropping it would mean replaying
    the log in a different order produced a different table.
    """

    player = uuid4()
    await append(session_factory, rating_initialised(player))
    await _tick(session_factory, build_tail())

    rows = await _rows(session_factory)
    assert [row.mu for row in rows] == [2.71]
    async with session_factory() as session:
        assert await session.get(CandidatePlayerFactsORM, player) is None


async def test_the_tick_holds_together_on_the_session_the_lifespan_builds(
    db_engine,
) -> None:
    """``autoflush=False`` — what runs in production, and what the fixtures do not.

    The default session factory flushes before every ``get``, so a row created by
    one event and moved again by the next is found either way. The lifespan builds
    its factory with ``autoflush=False``, where it would not be — and the tick
    would insert a duplicate against a two-column primary key. The suite's own
    fixture cannot see that, so this test builds the other one.
    """

    lifespan_sessions = async_sessionmaker(
        db_engine, expire_on_commit=False, autoflush=False
    )
    player = uuid4()
    await append(lifespan_sessions, profile_created(player))
    await append(lifespan_sessions, rating_initialised(player))
    # The second rating for the same pair: created by one event in the batch and
    # moved again by another, which is the pair of writes that needs the row to
    # be the same object both times.
    await append(lifespan_sessions, rating_initialised(player))
    await append(lifespan_sessions, SearchRadiusChanged(player, 30, START))

    report = await _tick(lifespan_sessions, build_tail())

    assert report.events_applied == 4
    async with lifespan_sessions() as session:
        rows = (
            (await session.execute(select(CandidateRowORM))).scalars().all()
        )
    assert len(rows) == 1
    assert rows[0].applied_through_sequence_no == 4
