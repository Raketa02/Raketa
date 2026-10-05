"""``rebuild == tail`` — the one assertion the whole projection rests on.

Tail a fixture **incrementally**, in small batches, the way the reader runs at 1 s
against a log that is moving. Then empty the three tables and **rebuild the same
fixture from zero**, in batches large enough to swallow it whole. Require the two
tables to be identical.

That single property proves three things at once (``docs/adr/0110``): that the
projection is a **pure function of the log**, that ``docs/adr/0097``'s total order
does the job it was written for, and that ``docs/adr/0105``'s determinism has a
stable input. It is also what would actually be false if a projection had a bug —
a fold that read the row it was about to write, a column whose value depended on
which events happened to share a batch, a stamp that recorded the reader's
schedule instead of the log's shape.

**Never a wall-clock bound.** A five-minute assertion on a shared CI runner is a
flaky test that gets muted; the timing figure stays a metric the rebuild command
logs, and it is asserted here only to *exist*.
"""

from __future__ import annotations

from datetime import timedelta
from pathlib import Path
from uuid import uuid4

from sqlalchemy import inspect, select

from app.modules.matchmaking.infrastructure.rebuild_candidate_index import (
    RebuildCandidateIndex,
)
from app.modules.matchmaking.infrastructure.candidate_index_model import (
    CANDIDATE_INDEX_CURSOR,
    CandidateIndexCursorORM,
    CandidatePlayerFactsORM,
    CandidateRowORM,
)
from app.modules.player_profile.domain.events import (
    GenderChanged,
    GenderPreferenceChanged,
    LocationChanged,
    PhotosChanged,
    SearchRadiusChanged,
    SocialTagsChanged,
    WeeklyHoursSet,
)
from app.modules.auth.domain.events import RefreshTokenIssued, RefreshTokenRotated
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


async def _write_the_fixture(session_factory) -> list:
    """A log with every consumed contract in it, and the orderings that matter.

    Three players, deliberately unalike: one onboards and then edits everything;
    one is rated in two sports; one is rated **before** their profile commits,
    which is the ordering a fold that looked anything up would get wrong. Two
    events nothing projects sit in the middle, because a watermark that skipped
    them would be a watermark that meant something narrower than it says.
    """

    alice, bob, carol = uuid4(), uuid4(), uuid4()
    events = [
        profile_created(alice),
        opt_in(alice),
        rating_initialised(alice, sport="PADEL"),
        intent_declared(alice, sport="PADEL"),
        RefreshTokenIssued(uuid4(), alice, "jti", START, START, "player_app"),
        profile_created(bob),
        opt_in(bob),
        PhotosChanged(bob, ("one", "two"), START),
        rating_initialised(bob, sport="PADEL"),
        rating_initialised(bob, sport="TENNIS"),
        intent_declared(bob, sport="TENNIS", intent="SOCIAL"),
        SocialTagsChanged(alice, ("social_first", "competitive_edge"), START),
        WeeklyHoursSet(alice, ("3:19", "6:10"), START),
        LocationChanged(alice, 50.0619, 19.9369, START),
        SearchRadiusChanged(alice, 40, START),
        GenderChanged(alice, "NON_BINARY", START),
        GenderPreferenceChanged(alice, "SAME_GENDER_ONLY", START),
        # Carol's Level lands before her profile does. A fold that read the row
        # it was writing would leave her either half-built or missing.
        rating_initialised(carol, sport="SQUASH"),
        profile_created(carol),
        opt_in(carol),
        RefreshTokenRotated(bob, uuid4(), "old", uuid4(), "new", START, "player_app"),
        intent_declared(carol, sport="SQUASH", intent="EITHER"),
    ]
    for event in events:
        await append(session_factory, event)
    return events


async def _tables(session_factory) -> dict[str, list[dict[str, object]]]:
    """Both projected tables, as plain values, in a deterministic order.

    Read column by column through the mapper rather than compared as ORM objects:
    two rows loaded in two sessions are never the same object, and *identical*
    here has to mean every column of every row.
    """

    async with session_factory() as session:
        rows = (
            (
                await session.execute(
                    select(CandidateRowORM).order_by(
                        CandidateRowORM.player_id, CandidateRowORM.sport
                    )
                )
            )
            .scalars()
            .all()
        )
        facts = (
            (
                await session.execute(
                    select(CandidatePlayerFactsORM).order_by(
                        CandidatePlayerFactsORM.player_id
                    )
                )
            )
            .scalars()
            .all()
        )
        return {
            "candidate_row": [_columns(row) for row in rows],
            "candidate_player_facts": [_columns(row) for row in facts],
        }


def _columns(row: object) -> dict[str, object]:
    return {
        column.key: getattr(row, column.key)
        for column in inspect(type(row)).mapper.column_attrs
    }


async def _tail_incrementally(session_factory, *, batch_size: int) -> None:
    tail = build_tail(batch_size=batch_size)
    while True:
        async with session_factory() as session:
            report = await tail.tick(session)
        if report.events_applied == 0:
            return


async def test_rebuilding_from_zero_produces_the_table_tailing_produced(
    session_factory,
) -> None:
    await _write_the_fixture(session_factory)
    await _tail_incrementally(session_factory, batch_size=3)
    tailed = await _tables(session_factory)
    assert tailed["candidate_row"], "the fixture projected nothing at all"

    rebuilt_report = await RebuildCandidateIndex(
        session_factory=session_factory,
        tail=build_tail(),
        clock=TickingClock(),
    ).execute()

    assert await _tables(session_factory) == tailed
    assert rebuilt_report.snapshot_version == len(
        await _sequence_numbers(session_factory)
    )


async def test_the_batch_size_changes_nothing_about_the_answer(
    session_factory,
) -> None:
    """The stronger half of the same property, driven from the other direction.

    A rebuild differs from a tail only in its schedule, so *the schedule changes
    nothing* is what the equality above is really asserting — and asserting it
    across three different schedules is what stops one lucky batch boundary
    standing in for the claim.
    """

    await _write_the_fixture(session_factory)
    await _tail_incrementally(session_factory, batch_size=1)
    one_at_a_time = await _tables(session_factory)

    for batch_size in (2, 7, 1000):
        await RebuildCandidateIndex(
            session_factory=session_factory,
            tail=build_tail(batch_size=batch_size),
            clock=TickingClock(),
        ).execute()
        assert await _tables(session_factory) == one_at_a_time, batch_size


async def test_a_rebuild_resets_the_watermark_rather_than_deleting_it(
    session_factory,
) -> None:
    """*The projection has never run* and *the projection is broken* differ.

    A missing cursor row makes them look the same, which is the state a rebuild
    must not leave behind.
    """

    await _write_the_fixture(session_factory)
    await _tail_incrementally(session_factory, batch_size=5)

    await RebuildCandidateIndex(
        session_factory=session_factory, tail=build_tail(), clock=TickingClock()
    ).execute()

    async with session_factory() as session:
        cursor = (
            await session.execute(
                select(CandidateIndexCursorORM).where(
                    CandidateIndexCursorORM.projection == CANDIDATE_INDEX_CURSOR
                )
            )
        ).scalar_one()
    assert cursor.hole_at_sequence_no is None
    assert cursor.applied_through_sequence_no > 0


async def test_a_rebuild_over_an_empty_log_is_a_no_op_and_says_so(
    session_factory,
) -> None:
    report = await RebuildCandidateIndex(
        session_factory=session_factory, tail=build_tail(), clock=TickingClock()
    ).execute()

    assert (report.events_applied, report.rows_moved) == (0, 0)
    assert report.snapshot_version == 0


async def test_the_rebuild_reports_a_duration_and_nothing_asserts_a_bound_on_it(
    session_factory,
) -> None:
    """The five-minute figure is a metric the command logs, never a test.

    A wall-clock bound on a shared runner is a flaky test that gets muted, and a
    muted test is worse than none — so what is asserted is that the number
    exists and is a duration, not that it is small.
    """

    await _write_the_fixture(session_factory)

    report = await RebuildCandidateIndex(
        session_factory=session_factory, tail=build_tail(), clock=TickingClock()
    ).execute()

    assert report.seconds >= 0
    assert timedelta(seconds=report.seconds) >= timedelta(0)
    assert report.ticks >= 1


async def _sequence_numbers(session_factory) -> list[int]:
    from app.infrastructure.events.event_store_model import EventStoreORM

    async with session_factory() as session:
        return list(
            (await session.execute(select(EventStoreORM.sequence_no))).scalars().all()
        )


# ---------------------------------------------------------------------------
# Rebuild is a ``make`` target. There is no admin route.
# ---------------------------------------------------------------------------


def test_the_rebuild_is_reachable_as_a_make_target() -> None:
    """A repair nobody can run is not a repair.

    Asserted against the Makefile rather than trusted to a README line, because
    the promise this ticket makes to an engineer is that *a corrupt projection is
    a command, not an incident* — and a command that exists only in prose is an
    incident.
    """

    makefile = _backend() / "Makefile"
    text = makefile.read_text(encoding="utf-8")
    assert "rebuild-candidate-index:" in text
    assert "app.modules.matchmaking.infrastructure.rebuild_cli" in text


def test_nothing_that_serves_http_can_reach_the_rebuild() -> None:
    """**There is no admin route, and this is what makes that a fact.**

    A button that drops and rebuilds the index is a button eventually pressed in
    the wrong place (``docs/adr/0110``). The walk covers the API package and every
    module's presentation layer — the two places a route can be declared — and it
    reads the *source*, so a route added with a good reason goes red rather than
    shipping.
    """

    reaching = [
        str(path.relative_to(_backend()))
        for path in [
            *(_backend() / "app" / "api").rglob("*.py"),
            *(_backend() / "app" / "modules").glob("*/presentation/*.py"),
        ]
        if "RebuildCandidateIndex" in path.read_text(encoding="utf-8")
        or "rebuild_candidate_index" in path.read_text(encoding="utf-8")
    ]
    assert reaching == []


def _backend() -> Path:
    """The app root, found through a module rather than by counting ``..``s.

    A path counted in parents goes silently wrong the day the tests move, and a
    walk pointed at nothing finds no breach on any tree at all.
    """

    import app

    return Path(app.__file__).parent.parent
