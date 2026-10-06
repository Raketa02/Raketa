"""The clock a seed run injects, and why a seed run has to inject one.

``build_clock()`` returns ``SystemClock``, and on a fresh database that makes a
**settled** player unreachable: every profile the seed commits is committed
*now*, ADR-0113's window compares ``now - profile_created_at`` against fourteen
days, and so everybody the seed writes is a newcomer. Newness changes the *gate*
— the level tolerance for the whole pairing — and a gate cannot be seen without
both sides of it present, so a cohort committed through the wall clock is a
cohort that cannot exhibit the one rule it was built to make visible.

**This is not going around the aggregate.** ``Clock`` is a port, the commit is
the same use case a request runs, and the event it appends carries the instant
the port handed it. ``docs/adr/0029`` is honoured rather than bent: seed data
still goes through aggregates, and what is injected is an adapter the domain
already takes.

**One demand this creates, stated here because it is easy to miss.** Backdated
event timestamps are **not** monotonic with ``sequence_no``: the log is appended
in run order and the instants inside it walk backwards and forwards. Nothing
downstream may order on ``occurred_at`` and expect the log's order —
``tests/unit/test_seed_cohort.py`` asserts the two genuinely disagree after a
run, so the assumption fails as a test rather than as a projection that quietly
reorders itself.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Final, final

from app.kernel import Clock, Instant, instant
from app.modules.matchmaking.domain.level_window import NEWCOMER_WINDOW

#: ADR-0113's window, **read and never moved**. Spelled in days because that
#: is the unit the seed's own refusal prints and the unit a member's row is
#: written in, and taking it from the matcher rather than restating it is what
#: makes a change to the window move the fixture instead of silently
#: disagreeing with it.
NEWCOMER_WINDOW_DAYS: Final = NEWCOMER_WINDOW.days


@final
@dataclass(frozen=True, slots=True)
class FixedClock:
    """A clock stopped at one instant. **A port, not a patch.**

    Frozen, so a run cannot advance one by accident half way through an account
    and leave two of its events on two different days for no reason anybody
    wrote down.
    """

    at: Instant

    def now(self) -> Instant:
        return self.at


def days_before(now: Instant, days: int) -> FixedClock:
    """A clock stopped ``days`` before ``now``. **The whole of backdating.**

    Spelled as a function of the run's own *now* rather than of a fixed calendar
    instant, because the ages this produces are what ADR-0113's window is
    measured against — and a fixed instant would age past that window as the
    repository got older, which is exactly the failure the runner refuses by
    name instead.
    """

    return FixedClock(at=instant(now - timedelta(days=days)))


def hours_before(now: Instant, hours: int) -> FixedClock:
    """A clock stopped ``hours`` before ``now``. **Backdating, at the finer unit.**

    :func:`days_before` is the unit the population is written in — a profile's age
    is compared against a window measured in days, and nothing there needs an
    hour. The loop's own states do: a result is confirmed six hours after the
    score was proposed and an ended game keeps its card for twenty-four, so *this
    evening* and *yesterday evening* are two different cards and a day apart is
    too coarse to name either.

    The same function of the run's own *now* rather than of a calendar instant,
    and for :func:`days_before`'s reason.
    """

    return FixedClock(at=instant(now - timedelta(hours=hours)))


def age_in_days(now: Instant, then: Instant) -> int:
    """How old something committed at ``then`` is. **Whole days, floored.**

    The unit the refusal prints, and the unit ADR-0113's window is written in,
    so the number in the failure message and the number the gate compares are
    the same number read the same way.
    """

    return (now - then).days


def read_clock(clock: Clock) -> Instant:
    """This run's one *now*, read once and passed.

    A run that read the wall clock twice could straddle midnight between writing
    a cohort and asserting over it, which would move an age by a day for reasons
    having nothing to do with the fixture.
    """

    return clock.now()
