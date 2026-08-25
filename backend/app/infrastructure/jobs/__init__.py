"""Periodic jobs: work that runs on a clock rather than on a request.

**This is where the next one goes** (``docs/adr/0092``). The platform has two
kinds of background work and they are not the same kind. Draining the outbox is
a *queue*, and it polls: there is a table of pending rows and the worker's job
is to empty it as fast as it fills. A sweep is a *schedule*: nothing is waiting,
nobody is blocked, and the work exists because a period elapsed.

Both are the same loop, which is what lives here — start a task, do the work,
wait, stop cleanly on shutdown — and having written it twice is how a shutdown
path ends up correct in one copy and not the other.

To add a job: write the use case, then register it in
``app/bootstrap/jobs.py``. Nothing in this package knows what any job does.
"""

from app.infrastructure.jobs.background_task import BackgroundTask
from app.infrastructure.jobs.periodic_job import PeriodicJob

__all__ = ["BackgroundTask", "PeriodicJob"]
