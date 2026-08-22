"""The timekeeper: one look at one match, and the batch the tick runs.

ADR-0076 and ``Raketa02/Raketa#72``. **A wake is a look, not an instruction.**
Nothing here reads why we were woken; the record and the clock are the whole
input, and what happens is whatever the ladder says *now*. That is the sentence
the rest of the design hangs off: a late look changes **when** we look and never
**what we find**, which is what makes at-least-once scheduling affordable with no
leader election, no distributed lock and no queue.

**There is no list of boundaries here, and there is deliberately no way to write
one.** The schedule is armed by ``kernel.next_wake`` on every write to the match
(``SqlAlchemyMatchRepository._columns``), and re-armed from the same function
when a look finds nothing. ADR-0076: *"Any future document that lists thresholds
for the timekeeper is a second ladder and should be deleted rather than
reconciled."* ``tests/unit/test_timekeeper_holds_no_thresholds.py`` reddens on
one appearing in this package.

**Today the ladder is the only actor, and that is a fact about the build rather
than about the design.** Eleven thresholds are scheduled; the hold ladder is the
one thing that has landed which *does* anything at a threshold. A wake that
crosses the commitment deadline underfull ought to cancel the match, and cannot
yet, because nothing writes that cancellation on its own — ``CancelMatch`` is a
command somebody sends. As those writers land they join this look, and the
schedule already wakes for them.
"""

from __future__ import annotations

import logging
from enum import Enum

from app.application.ports import UnitOfWork
from app.kernel import Clock, HoldMove, Instant, instant, next_wake

from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.domain.ports import MatchRepository, MatchSchedule
from app.modules.matches.domain.wake import MatchWake

logger = logging.getLogger(__name__)

#: How many due matches one tick takes. A ceiling on the work a single second
#: does, not a promise about latency: whatever is left is still due on the next
#: tick, because `next_wake_at <= now` does not stop being true.
WAKE_BATCH_SIZE = 100


class WakeOutcome(str, Enum):
    """What the look found. Returned for the log and for the tests, never stored."""

    #: The ladder had a move to make, and the match was written.
    ACTED = "acted"
    #: Nothing to do. The schedule was re-armed and nothing else was written —
    #: which is also what a **duplicate** wake produces, because the first one
    #: already moved the record.
    NOTHING_TO_DO = "nothingToDo"
    #: A real writer moved the match between the read and the re-arm, and stored
    #: its own schedule. Not an error and not a retry.
    OVERTAKEN = "overtaken"
    #: The match is no longer there.
    GONE = "gone"


class TakeMatchWake:
    """Look at one match, act on what is found, and point the schedule forward."""

    def __init__(
        self,
        matches: MatchRepository,
        schedule: MatchSchedule,
        holds: ResolveCourtHold,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._matches = matches
        self._schedule = schedule
        self._holds = holds
        self._uow = uow
        self._clock = clock

    async def execute(self, wake: MatchWake) -> WakeOutcome:
        """One look.

        ``wake`` is read for its **id** and for its key in the log line, and for
        nothing else. Its reason was computed at a past write and the match may
        have moved since; branching on it would act on an intention the record
        has stopped supporting, which ADR-0076 spends a section refusing.
        """

        now = instant(self._clock.now())
        match = await self._matches.get(wake.match_id)
        if match is None:
            return self._logged(wake, WakeOutcome.GONE)

        # Taken **before** the ladder acts, because acting mutates the aggregate
        # in memory: this is the version the row was read at, and it is what
        # `re_arm` guards on.
        as_read = match.version

        move = await self._holds.apply(match, at=now)
        if move is not HoldMove.STAND:
            # `save` recomputes the schedule from the record it is writing, so
            # the acting path arms itself and this one does not touch it.
            await self._matches.save(match)
            await self._uow.commit()
            return self._logged(wake, WakeOutcome.ACTED)

        # A look that finds nothing writes no *fact* — but it must still move the
        # moment, or the row stays due and the tick picks it up again a second
        # later, for ever. Strictly later than `now` by construction, so the
        # chain terminates rather than re-arming itself where it stands.
        armed = await self._schedule.re_arm(
            match_id=match.id,
            version=as_read,
            wake=next_wake(match.as_record(), now),
        )
        await self._uow.commit()
        return self._logged(
            wake, WakeOutcome.NOTHING_TO_DO if armed else WakeOutcome.OVERTAKEN
        )

    def _logged(self, wake: MatchWake, outcome: WakeOutcome) -> WakeOutcome:
        """The one place the idempotency key is used, and it is used as a name."""

        logger.info(
            "match-wake taken",
            extra={"wake": wake.key, "outcome": outcome.value},
        )
        return outcome


class MatchWakeBatch:
    """Every match due at this instant, looked at once each.

    The second of ADR-0076's *"three queries, one tick"*, hosted by the existing
    event worker. It is a batch rather than a stream for the same reason the
    outbox's is: one indexed query, a bounded slice of work, and whatever is left
    is still due next second.

    **One failed look does not stop the batch.** The matches in a tick are
    unrelated — a court held past its lapse at one club has nothing to do with a
    commitment deadline at another — so an exception is rolled back, logged
    against its own wake, and the rest are taken. Letting it escape would mean
    one match in a bad state could stop every court in the country being given
    back. The rollback is what makes *the rest are taken* true rather than
    hopeful: a session left holding a failed statement fails every look after it,
    and the batch would read as one broken match rather than as a broken tick.
    """

    def __init__(
        self,
        *,
        schedule: MatchSchedule,
        look: TakeMatchWake,
        uow: UnitOfWork,
        clock: Clock,
        batch_size: int = WAKE_BATCH_SIZE,
    ) -> None:
        self._schedule = schedule
        self._look = look
        self._uow = uow
        self._clock = clock
        self._batch_size = batch_size

    async def execute(self, *, worker_id: str) -> int:
        now: Instant = instant(self._clock.now())
        due = await self._schedule.due(now=now, limit=self._batch_size)
        taken = 0
        for wake in due:
            try:
                await self._look.execute(wake)
            except Exception:
                await self._uow.rollback()
                logger.exception(
                    "match-wake failed",
                    extra={"wake": wake.key, "worker_id": worker_id},
                )
                continue
            taken += 1
        return taken
