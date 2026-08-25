"""The loop every scheduled job runs on (``docs/adr/0092``).

Three properties, and each one is silent when it is wrong: the work happens, a
failure does not stop the loop, and shutdown is clean. The third is the one a
test suite normally lets rot — a job whose task is never awaited on the way out
produces a warning in a log nobody reads and a container that takes its grace
period to die.

Nothing here sleeps for an interval. The intervals are long and the assertions
wait on an event the job itself sets, so the test finishes as soon as the
behaviour has happened rather than as soon as a timer says so.
"""

from __future__ import annotations

import asyncio

from app.infrastructure.jobs import PeriodicJob


async def test_the_work_runs_without_waiting_for_the_first_interval():
    """A daily job on a laptop would otherwise never be seen to run at all."""

    ran = asyncio.Event()
    job = PeriodicJob(name="test-job", interval_seconds=3600, run=_setting(ran))

    job.start()
    await asyncio.wait_for(ran.wait(), timeout=1)
    await job.stop()


async def test_a_failing_run_does_not_stop_the_loop():
    """The failure mode this exists to prevent: one unreachable dependency at
    07:00 and the job never runs again for the life of the process."""

    attempts: list[int] = []
    second_attempt = asyncio.Event()

    async def failing() -> None:
        attempts.append(len(attempts))
        if len(attempts) == 1:
            raise RuntimeError("the object store was unreachable")
        second_attempt.set()

    job = PeriodicJob(name="test-job", interval_seconds=0.01, run=failing)

    job.start()
    await asyncio.wait_for(second_attempt.wait(), timeout=1)
    await job.stop()

    assert len(attempts) >= 2


async def test_stopping_ends_the_loop_and_leaves_no_task_behind():
    ran = asyncio.Event()
    job = PeriodicJob(name="test-job", interval_seconds=0.01, run=_setting(ran))

    job.start()
    await asyncio.wait_for(ran.wait(), timeout=1)
    await job.stop()

    ran.clear()
    await asyncio.sleep(0.05)
    assert not ran.is_set(), "the loop kept running after stop"


async def test_a_run_that_hangs_is_cancelled_rather_than_holding_shutdown_open(
    monkeypatch,
):
    """A stuck network call must not hold a container's shutdown open forever.

    The grace period is monkeypatched rather than waited out — five real seconds
    in a unit suite is how a suite stops being run.
    """

    import app.infrastructure.jobs.periodic_job as module

    monkeypatch.setattr(module, "SHUTDOWN_GRACE_SECONDS", 0.05)
    started = asyncio.Event()

    async def hanging() -> None:
        started.set()
        await asyncio.Event().wait()

    job = PeriodicJob(name="test-job", interval_seconds=0.01, run=hanging)

    job.start()
    await asyncio.wait_for(started.wait(), timeout=1)
    await asyncio.wait_for(job.stop(), timeout=1)


async def test_starting_twice_does_not_run_two_loops():
    runs: list[None] = []
    ran = asyncio.Event()

    async def counting() -> None:
        runs.append(None)
        ran.set()

    job = PeriodicJob(name="test-job", interval_seconds=3600, run=counting)

    job.start()
    job.start()
    await asyncio.wait_for(ran.wait(), timeout=1)
    await job.stop()

    assert runs == [None], "start() is idempotent; a second call built a second loop"


async def test_stopping_one_that_never_started_is_not_an_error():
    """Shutdown runs whatever the lifespan built, and a disabled job is one it
    did not — so the `finally` that stops jobs must tolerate this."""

    await PeriodicJob(
        name="test-job", interval_seconds=1, run=_setting(asyncio.Event())
    ).stop()


def _setting(event: asyncio.Event):
    async def run() -> None:
        event.set()

    return run
