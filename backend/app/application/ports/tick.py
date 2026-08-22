"""One unit of work the background tick runs, whoever owns it.

ADR-0076 puts the timekeeper's lookup on the worker the outbox already has —
*"no new interval and no second process"* — which leaves the worker holding two
jobs that have nothing to do with each other. This is the whole of what it needs
to know about either.

**Stated as a port so that shared infrastructure does not import a context.**
The worker lives in ``app/infrastructure/events/``; the wake batch lives in
``app/modules/matches/application/``. A direct import would make the process's
tick depend on one racket-sport context, and the third job (the notification
channel's, ``Raketa02/Raketa#84``) would add a second. The composition root is
where a tick learns whose work it is running.
"""

from typing import Protocol, runtime_checkable


@runtime_checkable
class TickWork(Protocol):
    """A bounded slice of due work, taken once per tick.

    Returns how much it took, for the log. ``worker_id`` names who took it —
    the outbox's leases are keyed on it, and a wake's log line carries it beside
    the idempotency key.
    """

    async def execute(self, *, worker_id: str) -> int: ...
