"""The wall clock: the one adapter in the system that reads ambient time.

The `Clock` interface it satisfies lives in the kernel, and the separation is the
whole point (ADR-0022, ADR-0024). A module that wants to know *what a clock is*
imports `app.kernel`; only a composition root — `app/api/dependencies.py` and
`app/bootstrap/events.py` — imports this. While the two shared a module,
importing the abstraction dragged a live clock into scope, and nothing but
discipline stopped a use case from calling it.

**Everything above this line takes `now` as an input.** That is ADR-0015's first
purity rule, and it is what makes the system reproducible: a test fixes the
instant, a scrub moves it, and no code path anywhere disagrees about what time it
is within one command.
"""

from datetime import datetime, timezone

from app.kernel import Instant, instant


class SystemClock:
    """`Clock` port implementation — the host's clock, as a UTC `Instant`.

    Constructed through `instant()` rather than `Instant(...)`. The brand erases
    at runtime, so the direct call would typecheck and admit anything shaped like
    a datetime — including the naive value the type exists to refuse. The one
    place in the system that manufactures an instant from nothing is the one place
    that should be paying for the check.
    """

    def now(self) -> Instant:
        return instant(datetime.now(timezone.utc))
