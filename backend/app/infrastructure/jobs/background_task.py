"""What the lifespan starts and stops, named.

Two unrelated classes satisfy it — the outbox drain and every ``PeriodicJob`` —
and the lifespan holds them in one list because *start everything, stop
everything in reverse* is the same sentence for both. Without a name for that,
the list is a ``list`` of nothing in particular, and the shutdown path reaches
for ``getattr(task, "name", ...)`` because it cannot know what it is holding.

**A ``Protocol``, not a base class.** Neither implementer inherits anything, and
neither should have to: the shape is start, stop, and a name for the log line
that says which one did not stop cleanly.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class BackgroundTask(Protocol):
    """Something the application runs beside itself for as long as it lives."""

    @property
    def name(self) -> str:
        """What to call this in a log line. Stable, and unique per process."""
        ...

    def start(self) -> None:
        """Begin. **Idempotent** — a second call must not start a second loop."""
        ...

    async def stop(self) -> None:
        """Stop, waiting for work in flight up to a grace period.

        Tolerates never having been started, because the shutdown path runs over
        whatever was built and a disabled task is one that was not.
        """
        ...
