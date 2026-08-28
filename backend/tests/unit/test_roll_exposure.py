"""The exposure roll: one scalar per sport per week, and nothing else.

What is asserted here is mostly what the roll **does not** do. It opens no
bucket, closes no window, deletes nothing and writes no player's row — the week
is a function of ``now`` and the previous week expires on its own — so a
regression in this job looks like a job that started doing work rather than one
that stopped.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

from app.kernel import Sport, instant
from app.modules.matchmaking.application.roll_exposure import RollExposure
from app.modules.matchmaking.domain.ledgers import week_of
from tests.unit.fake_ledgers import InMemoryExposureLedger, MovableClock

NOW = instant(datetime(2026, 8, 26, 12, 0, tzinfo=timezone.utc))
WEEK = week_of(NOW)


def build_roll() -> tuple[RollExposure, InMemoryExposureLedger, MovableClock]:
    clock = MovableClock(NOW)
    exposure = InMemoryExposureLedger(clock)
    return RollExposure(exposure=exposure, clock=clock), exposure, clock


async def _show(exposure, sport, week, counts: dict) -> None:
    for player_id, times in counts.items():
        await exposure.record_shown(
            sport=sport, week=week, player_ids=[player_id] * times
        )


async def test_an_empty_week_publishes_nothing():
    """Nothing has happened, so *shown more often than most* has no answer.

    Publishing a zero would put every player in the pool above the threshold in
    the exact state the floor's lifting rungs exist for.
    """

    roll, exposure, _ = build_roll()

    report = await roll.execute()

    assert report.thresholds == {}
    for sport in Sport:
        assert await exposure.busy_threshold(sport=sport, week=WEEK) is None


async def test_the_threshold_is_published_for_the_sport_it_was_measured_in():
    roll, exposure, _ = build_roll()
    await _show(
        exposure,
        Sport.PADEL,
        WEEK,
        {uuid4(): 1, uuid4(): 1, uuid4(): 2, uuid4(): 9},
    )

    report = await roll.execute()

    assert report.thresholds == {Sport.PADEL: 9}
    assert await exposure.busy_threshold(sport=Sport.PADEL, week=WEEK) == 9
    assert await exposure.busy_threshold(sport=Sport.TENNIS, week=WEEK) is None


async def test_every_sport_is_rolled():
    roll, exposure, _ = build_roll()
    for sport in Sport:
        await _show(exposure, sport, WEEK, {uuid4(): 3})

    report = await roll.execute()

    assert set(report.thresholds) == set(Sport)
    assert report.players_counted == len(Sport)


async def test_the_roll_reads_the_week_it_is_running_in():
    """The bucket is derived from ``now``. There is nothing to open or close."""

    roll, exposure, clock = build_roll()
    await _show(exposure, Sport.PADEL, WEEK, {uuid4(): 4})

    report = await roll.execute()
    assert report.week == WEEK

    clock.advance(days=7)
    later = await roll.execute()

    assert later.week != WEEK
    assert later.thresholds == {}


async def test_running_it_twice_publishes_the_same_answer():
    """Idempotent, which is what ``docs/adr/0092`` requires before registering it.

    With N API processes the job runs N times per interval at unrelated moments,
    and there is no lock. What makes that safe is that a re-run over an unchanged
    bucket writes the identical scalar.
    """

    roll, exposure, _ = build_roll()
    await _show(exposure, Sport.PADEL, WEEK, {uuid4(): 1, uuid4(): 2, uuid4(): 7})

    first = await roll.execute()
    second = await roll.execute()

    assert first.thresholds == second.thresholds
    assert await exposure.busy_threshold(sport=Sport.PADEL, week=WEEK) == 7


async def test_the_roll_never_writes_a_players_row():
    """Safe beside itself, for the reason that matters: it is a reader.

    Two rolls racing cannot lose an appearance, because neither of them touches
    one. The only thing either writes is a scalar derived from what it read.
    """

    roll, exposure, _ = build_roll()
    shown = uuid4()
    await _show(exposure, Sport.PADEL, WEEK, {shown: 3})

    await roll.execute()
    await roll.execute()

    counts = await exposure.times_shown(
        sport=Sport.PADEL, week=WEEK, player_ids=[shown]
    )
    assert counts[shown] == 3


async def test_a_ledger_that_answers_nothing_rolls_nothing_and_does_not_raise():
    """The job inherits the ledger's posture rather than restating it.

    A fail-soft ledger degrades to an empty bucket, and an empty bucket already
    means *publish nothing* — so an outage costs the roll its tick and nothing
    else, with no branch here that had to know about Redis.
    """

    from app.modules.matchmaking.infrastructure.fail_soft_ledgers import (
        FailSoftExposureLedger,
    )
    from app.modules.matchmaking.infrastructure.redis_ledgers import (
        RedisExposureLedger,
    )
    from tests.unit.fake_redis import BrokenRedis

    exposure = FailSoftExposureLedger(RedisExposureLedger(BrokenRedis()))
    roll = RollExposure(exposure=exposure, clock=MovableClock(NOW))

    report = await roll.execute()

    assert report.thresholds == {}
    assert report.players_counted == 0
