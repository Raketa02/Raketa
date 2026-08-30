"""The lapse loop — **it buys the record, not correctness.**

A seat past its answer window reads as lapsed at every instant, swept or not:
``standing.py`` folds the seats against the clock the caller supplies, so the
challenge already stands as ``LAPSED``, the pair rule has already released and
the matcher's gate is already open. Nothing here changes any of that, and a test
asserting it does would be asserting the wrong thing.

**What it buys is a denominator.** *Answers challenges* is a Strand over
challenges that got an answer inside their window, and a window that closed in
silence leaves nothing behind to count unless something writes it down. A
``SeatLapsed`` is that record — and it is emphatically **not** a
``SeatDeclined``, because somebody who said nothing made no judgement and a
Strand that filed silence as one would be measuring the wrong people.

**One transaction per challenge, and that is the interesting decision here.** The
sweep is a run rather than a command, and the unit it is a run *of* is one
challenge: everything a lapse touches is inside one stream, so nothing spans two
of them and a boundary drawn around the whole batch would buy no consistency
anybody wanted. What it would cost is the loop's ability to make progress —
``docs/adr/0092`` puts a copy of every job in every API process with no lock
between them, and the candidate list is derived from the clock, so N processes
walk the *same* challenges in the *same* order. One version conflict on one
challenge would roll back a whole run's records, and every process would keep
colliding at the same place. So a conflict is **counted and stepped over**, which
is the shape the photo re-review backfill already argues for a refusal about one
image: ending a run on one item stalls the job at that item.

**Idempotent, then, for two reasons rather than one.** The aggregate skips a seat
that already carries an answer, so the winner of a race and the next tick both
append nothing; and the loser of a race keeps the records it had already
committed. Nothing here holds a cursor, so a run that dies half-way is a run the
next tick re-derives in full from the clock.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    LapsingChallengeQuery,
)


@final
@dataclass(frozen=True, slots=True)
class Swept:
    """What one run of the lapse loop wrote down.

    ``seats`` is the denominator's own increment: invitations that ran out
    unanswered, which is what *answers challenges* is a rate over.

    ``challenges`` is how many games those seats were spread across, and the two
    together are the shape of the silence — forty seats over forty challenges is
    a platform nobody answers, and forty over four is four courts that never
    filled. It is the second figure and not a third, because *how the challenge
    now reads* is a question the run does not have to ask: a lapse changes no
    reading, so anything about a standing is as true before this loop as after
    it and belongs to whoever asks about standings.

    ``conflicts`` is challenges another process reached first. It is here rather
    than swallowed because *the loop is doing nothing* and *the loop is losing
    every race* have one symptom — a denominator that stops growing — and only
    one of them is somebody's problem.
    """

    seats: int
    challenges: int
    conflicts: int

    def __post_init__(self) -> None:
        invariant(
            0 <= self.challenges <= self.seats,
            f"{self.seats} lapsed seats over {self.challenges} challenges",
        )
        invariant(self.conflicts >= 0, f"{self.conflicts} conflicts")


@final
class LapseExpiredSeats:
    """One sweep of the challenges whose day has run out."""

    def __init__(
        self,
        *,
        clock: Clock,
        challenges: ChallengeRepository,
        lapsing: LapsingChallengeQuery,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._challenges = challenges
        self._lapsing = lapsing
        self._uow = unit_of_work

    async def execute(self) -> Swept:
        """Record every passed window, one challenge at a time.

        The clock is read **once** for the whole run, so which seats this sweep
        considers lapsed is one instant's answer rather than a slightly later one
        per challenge — the same reason a search stamps its own moment instead of
        asking again per candidate.
        """

        now = instant(self._clock.now())
        seats = challenges = conflicts = 0
        for challenge_id in await self._lapsing.may_have_lapsed(now=now):
            recorded = await self._record_lapses_in(challenge_id, now=now)
            if recorded is None:
                conflicts += 1
                continue
            if not recorded:
                continue
            seats += recorded
            challenges += 1
        return Swept(seats=seats, challenges=challenges, conflicts=conflicts)

    async def _record_lapses_in(
        self, challenge_id: UUID, *, now: Instant
    ) -> int | None:
        """How many seats this challenge owed, or ``None`` if somebody got there first.

        The three endings are three different facts and the caller counts them
        apart: a number is what was written, ``0`` is a candidate that turned out
        to owe nothing — the ordinary case, since the sweep's read names
        candidates rather than conclusions — and ``None`` is a race this process
        lost.
        """

        challenge = await self._challenges.load(challenge_id)
        if challenge is None:
            # The candidate read named a stream the load cannot find, which an
            # append-only log does not do. Stepping over it rather than raising
            # keeps one impossible row from costing the rest of the batch.
            return 0
        recorded = challenge.lapse(now=now)
        if not recorded:
            return 0
        try:
            await self._challenges.save(challenge)
            await self._uow.commit()
        except EventStreamVersionConflict:
            # Somebody appended to this stream between the load and the append —
            # another process's copy of this same loop, or an answer that landed
            # in the same second. Either way this challenge is somebody else's
            # now: the rollback is what makes the session usable for the next
            # one, and the next tick re-derives this candidate from the clock.
            await self._uow.rollback()
            return None
        return recorded
