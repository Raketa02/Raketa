"""The exposure roll — the one loop §14.5 leaves this ticket to build.

**What it does is one thing: publish, per sport, what *shown more often than
most* means this week.** The rung that reads it docks a player shown more times
than the week's ninetieth percentile, and a percentile is a fact about a
distribution: computing one per search would put an unbounded read on the
request path to answer a question whose answer barely moves within an hour.

**What it deliberately does not do is roll a bucket**, despite the name §14.5
gave it. The bucket is ``expo:{sport}:{week}`` and the week is a function of
``now``, so next week's bucket is a different key that starts empty and this
week's expires on its own. There is no window to open, no flag to flip and no
old bucket to delete. That is the same argument that struck the newcomer-window
loop — *a stored flag goes stale hourly; a date does not* — and it is written
here because a job whose name promises work it does not do is a job somebody
later adds the work back into.

**Idempotent and safe beside itself**, which is what ``docs/adr/0092`` requires
before a job may be registered at all. It is a **reader** that writes one derived
scalar: two runs racing cannot lose an appearance because neither touches one,
and two runs over an unchanged bucket publish the identical number. A run that
straddles a new appearance publishes a scalar one tick stale, which the next
tick converges on — and which is already the accepted staleness of an hourly
figure.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from app.kernel import Clock, Sport
from app.modules.matchmaking.domain.exposure_roll import busy_threshold_of
from app.modules.matchmaking.domain.ledgers import ExposureLedger, ExposureWeek, week_of


@dataclass(frozen=True)
class ExposureRollReport:
    """What one roll saw and published. **The job's only output.**

    ``players_counted`` is what separates *the roll ran and the city was quiet*
    from *the roll ran against a ledger that answered nothing*, which are the two
    states a fail-soft ledger makes indistinguishable everywhere else. It is
    logged for exactly that reason.
    """

    week: ExposureWeek
    players_counted: int
    thresholds: Mapping[Sport, int]


class RollExposure:
    """Recompute the busy threshold per sport, and publish it."""

    def __init__(self, *, exposure: ExposureLedger, clock: Clock) -> None:
        self._exposure = exposure
        self._clock = clock

    async def execute(self) -> ExposureRollReport:
        week = week_of(self._clock.now())
        players_counted = 0
        thresholds: dict[Sport, int] = {}

        # Every sport, one at a time, because a sport whose bucket cannot be read
        # must not take the others' rolls with it — the ledger degrades to an
        # empty bucket per call, and an empty bucket already means *publish
        # nothing*.
        for sport in Sport:
            counts = await self._exposure.all_times_shown(sport=sport, week=week)
            players_counted += len(counts)
            threshold = busy_threshold_of(list(counts.values()))
            if threshold is None:
                # Nobody has been shown in this sport this week, so *more often
                # than most* has no answer. Publishing a zero would put the whole
                # pool above the threshold in the one state the floor's lifting
                # rungs exist for.
                continue
            await self._exposure.publish_busy_threshold(
                sport=sport, week=week, threshold=threshold
            )
            thresholds[sport] = threshold

        return ExposureRollReport(
            week=week,
            players_counted=players_counted,
            thresholds=thresholds,
        )
