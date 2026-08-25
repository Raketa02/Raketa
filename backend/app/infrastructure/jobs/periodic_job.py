"""One named coroutine, run on an interval until the process stops.

**The whole of the platform's scheduling, deliberately** (``docs/adr/0092``).
No cron, no beat process, no leader election: an ``asyncio`` task hosted by the
API, exactly as the outbox worker already was, because a second deployable to
run one six-hourly job is a second thing to build, monitor and keep in step with
the application's own code.

The consequence is the constraint every job here inherits: **with N API
processes running, a job runs N times per interval, and at unrelated moments.**
That is not a bug to be fixed with a lock — it is the price of not owning a
scheduler, and it is why ``docs/adr/0092`` requires a job to be idempotent and
safe beside itself *before* it may be registered. A job that cannot say that is
not one this mechanism can run.

**A failing run never stops the loop.** The exception is logged with the job's
name and the next tick happens on time. A sweep that could not reach the object
store this morning is a sweep that runs again tonight; a loop that died on it is
one that silently stops doing its work and looks identical from outside.
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable, Mapping
from contextlib import suppress
from typing import Any

logger = logging.getLogger(__name__)

#: How long ``stop`` waits for a run in flight before cancelling it. The same
#: five seconds the outbox worker has always used: long enough for a tick that
#: is nearly done, short enough that a container shutdown is not held open by a
#: job that is stuck on a network call.
SHUTDOWN_GRACE_SECONDS = 5.0


class PeriodicJob:
    """Runs `run` every `interval_seconds`, as a background task."""

    def __init__(
        self,
        *,
        name: str,
        interval_seconds: float,
        run: Callable[[], Awaitable[Any]],
        log_context: Mapping[str, Any] | None = None,
    ) -> None:
        self._name = name
        self._interval_seconds = interval_seconds
        self._run = run
        self._log_context = dict(log_context or {})
        self._stop_event = asyncio.Event()
        self._task: asyncio.Task[None] | None = None

    @property
    def name(self) -> str:
        return self._name

    @property
    def interval_seconds(self) -> float:
        return self._interval_seconds

    def start(self) -> None:
        if self._task is not None:
            return
        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop(), name=self._name)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._stop_event.set()
        try:
            await asyncio.wait_for(self._task, timeout=SHUTDOWN_GRACE_SECONDS)
        except asyncio.TimeoutError:
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task
        finally:
            self._task = None

    async def run_once(self) -> None:
        """Do the work now, on the caller's task, and let it raise.

        The loop's own tick swallows failures because there is nobody to hand
        one to; a caller that asked for a single run *is* somebody, so this does
        not. Its caller today is the test that asserts what a job actually does,
        and having it is what keeps that test off a private method.
        """

        await self._run()

    async def _loop(self) -> None:
        logger.info("periodic job started", extra=self._extra())
        try:
            while not self._stop_event.is_set():
                # **The first run is immediate**, before the first wait. On a
                # job measured in hours that is the only thing that makes it
                # observable at all on a laptop, where nobody leaves the API up
                # that long — and a job that is safe to run beside itself is by
                # construction safe to run again at every restart.
                try:
                    await self._run()
                except Exception:
                    # Logged and swallowed: see the module docstring. The next
                    # tick is the recovery, and there is nothing here that could
                    # usefully be re-raised into an event loop nobody awaits.
                    logger.exception("periodic job failed", extra=self._extra())
                try:
                    await asyncio.wait_for(
                        self._stop_event.wait(), timeout=self._interval_seconds
                    )
                except asyncio.TimeoutError:
                    # The interval elapsed rather than a stop arriving, which is
                    # the ordinary path round this loop.
                    pass
        finally:
            logger.info("periodic job stopped", extra=self._extra())

    def _extra(self) -> dict[str, Any]:
        return {"job": self._name, **self._log_context}
