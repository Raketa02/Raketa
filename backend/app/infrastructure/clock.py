"""The two adapters in the system that read ambient time: the wall, and a scrub.

The `Clock` interface they satisfy lives in the kernel, and the separation is the
whole point (ADR-0022, ADR-0024). A module that wants to know *what a clock is*
imports `app.kernel`; only a composition root — `app/bootstrap/composition.py`
and `app/bootstrap/events.py` — imports this, which
`tests/unit/test_system_clock.py` walks the tree to keep true. While the two
shared a module, importing the abstraction dragged a live clock into scope, and
nothing but discipline stopped a use case from calling it.

**Everything above this line takes `now` as an input.** That is ADR-0015's first
purity rule, and it is what makes the system reproducible: a test fixes the
instant, a scrub moves it, and no code path anywhere disagrees about what time it
is within one command.

`ScrubbableClock` is the *scrub* in that sentence, arriving here rather than in
a test after ADR-0092: the seeded week is a fixed week and a developer had no
way to stand inside it. Which of the two a process runs on is decided once, in
`app/bootstrap/composition.py`, from a setting that refuses to be on anywhere
but `local`. **Nothing above this line can tell them apart**, and that is the
property the whole design rests on — a use case takes a `Clock`, and a clock
somebody moved is still a clock.
"""

from datetime import datetime, timezone

from app.kernel import Clock, Instant, Seconds, instant, moved, seconds


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


class ScrubbableClock:
    """`Clock` port implementation — the host's clock, displaced.

    **A developer's clock, and never anybody else's.** It exists because the
    seeded week is a fixed week in September 2026 and the product had no way to
    stand inside it (`Raketa02/Raketa#134`): two of the thirteen seeded matches
    — a played match waiting for a score, and a score waiting for an answer —
    are true only between Tuesday 21:00 and Wednesday 21:00 on that week, so the
    two screens ADR-0048 specifies could not be reached by signing in on any
    day. The settings object refuses to build one outside `local`.

    **It displaces time; it does not stop it.** `now()` is the base clock plus a
    whole number of seconds, so a scrub to Tuesday evening is Tuesday evening
    and then, a minute later, a minute past it. Everything that is a deadline
    stays a deadline: a seat claim's five minutes lapse while somebody watches,
    `next_wake_at` comes due and the delivery worker's tick moves. A clock
    frozen at an instant would show the week and animate none of it, and the
    states worth looking at are exactly the ones a boundary is about to end.

    Two reads still cannot disagree by more than the wall clock's own elapsed
    time, which is what ADR-0015's *one read per command* already assumes — a
    scrub between two reads inside one command is the only way to break that,
    and it takes an HTTP request timed into a microsecond gap on a laptop.

    The displacement is whole seconds because the kernel's `moved` is the one
    place an instant may be moved at all and its currency is `Seconds`. A scrub
    to 21:30 therefore keeps the host's own sub-second phase — it reads 21:30
    and some microseconds, exactly as the wall clock reads a second and some
    microseconds. Nothing in the system compares below the minute (`ADR-0015`'s
    engines refuse a `now` carrying seconds at all), and a displacement rounded
    to the second is one a person can read in a log line.
    """

    def __init__(self, base: Clock, *, displaced_by: Seconds = seconds(0)) -> None:
        self._base = base
        self._displaced_by = displaced_by

    @property
    def displaced_by(self) -> Seconds:
        """How far from the host's clock this one is running. Zero is the wall."""

        return self._displaced_by

    def now(self) -> Instant:
        return moved(self._base.now(), self._displaced_by)

    def base_now(self) -> Instant:
        """What the host's clock says, for a reader that wants to see both."""

        return self._base.now()

    def scrub_to(self, moment: Instant) -> Seconds:
        """Make `now()` answer `moment`, and keep running from there.

        Returns the displacement it settled on, so a caller can report it rather
        than compute the same subtraction a second time.
        """

        self._displaced_by = seconds(
            round((moment - self._base.now()).total_seconds())
        )
        return self._displaced_by

    def release(self) -> Seconds:
        """Give the host's clock back. Returns the displacement given up."""

        given_up = self._displaced_by
        self._displaced_by = seconds(0)
        return given_up
