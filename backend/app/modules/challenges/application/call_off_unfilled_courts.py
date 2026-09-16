"""The hour loop — **the platform calls off a court still short of a player
when its moment passes** (``docs/adr/0175`` §3).

Nobody presses *Call it off* any more (``0175`` §1), and a game with a seat
open that nobody leaves and nobody fills had, without this, one end: the entry
window closing on it eight days after the arrangement — a ghost charged to the
players who stayed, their pairs held for as long as the court stood, and a
*needs a player* row nobody could clear. This loop is the exit that is nobody's
decision: at the agreed hour — or the end of the horizon, where no day was ever
agreed — such a court is called off, ``CALLED_OFF`` on the challenge with nobody
named and the game called off in the same transaction, on the two-streams shape
the departure already takes (``docs/adr/0172`` §1). Nobody is charged, the pair
releases, the room is destroyed, and the row keeps its day.

**Unlike the lapse loop, this one buys correctness and not only the record.**
A seat past its window reads as lapsed whether or not anything swept it; a
court past its hour does **not** read as called off until this writes it,
because the challenge's fold cannot read a plan and ``docs/adr/0172`` §1
refused to make its standing a read of the game's. What that costs is stated:
between the hour and the next tick the row reads *needs a player* with nothing
to press, for at most one interval.

**Candidates, then the fold, then the game.** ``LeftCourtQuery`` names every
court somebody left; the fold says which of those have been a game and are
``LINE_UP_INCOMPLETE``; and ``SeatableGameQuery`` — the moment guard the fill
and the departure already read — says which of *those* are past their hour or
already history. A court whose open seat a newcomer is still deciding on is
``AWAITING_ANSWERS`` and not named by the fold, on the rule the departure reads:
it is not short of a player until they say no or their day runs out, and the
next tick asks again. A court whose game is already history — its window closed
before this loop existed, or while it was down — is called off all the same,
so its pair releases and its row gets its day; the game keeps the end it
reached (``docs/adr/0163`` §6).

**One transaction per court, conflicts counted and stepped over**, for the
lapse loop's reasons exactly: ``docs/adr/0092`` runs a copy of this in every
API process with no lock, the candidates are derived from the log in one order,
and a conflict on one court must not stall the batch. Idempotent twice over:
the aggregate writes nothing on a court that is not ``LINE_UP_INCOMPLETE``, and
the loser of a race keeps what it committed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.challenges.domain.planned_game import PlannedGameHandover
from app.modules.challenges.domain.ports import ChallengeRepository, LeftCourtQuery
from app.modules.challenges.domain.seatable_game import (
    LineUpChange,
    SeatableGameQuery,
)
from app.modules.challenges.domain.standing import Standing


@final
@dataclass(frozen=True, slots=True)
class CalledOff:
    """What one run of the hour loop wrote down.

    ``courts`` is how many were called off — each one a court three people, or
    one, were waiting on and can stop waiting on. ``conflicts`` is courts
    another process reached first, kept apart for the lapse loop's reason: *the
    loop is doing nothing* and *the loop is losing every race* look the same
    from the count of courts alone.
    """

    courts: int
    conflicts: int

    def __post_init__(self) -> None:
        invariant(self.courts >= 0, f"{self.courts} courts")
        invariant(self.conflicts >= 0, f"{self.conflicts} conflicts")


@final
class CallOffUnfilledCourts:
    """One sweep of the courts whose hour has passed with a seat still open."""

    def __init__(
        self,
        *,
        clock: Clock,
        challenges: ChallengeRepository,
        left: LeftCourtQuery,
        games: SeatableGameQuery,
        planned_games: PlannedGameHandover,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._challenges = challenges
        self._left = left
        self._games = games
        self._planned_games = planned_games
        self._uow = unit_of_work

    async def execute(self) -> CalledOff:
        """Call off every court past its hour, one court at a time.

        The clock is read **once** for the whole run, for the lapse loop's
        reason: which courts this sweep finds past their hour is one instant's
        answer, and the ending each records is dated to it.
        """

        now = instant(self._clock.now())
        courts = conflicts = 0
        for challenge_id in await self._left.courts_somebody_left():
            outcome = await self._call_off(challenge_id, now=now)
            if outcome is None:
                conflicts += 1
            elif outcome:
                courts += 1
        return CalledOff(courts=courts, conflicts=conflicts)

    async def _call_off(self, challenge_id: UUID, *, now: Instant) -> bool | None:
        """Whether this court was called off, or ``None`` if somebody got
        there first.

        ``False`` is the ordinary answer: a candidate the fold says is not a
        game short of a player, or one whose hour is still ahead. Both cost a
        load and write nothing.
        """

        challenge = await self._challenges.load(challenge_id)
        if challenge is None:
            # The candidate read named a stream the load cannot find, which an
            # append-only log does not do. Stepped over rather than raised, so
            # one impossible row does not cost the rest of the batch.
            return False
        if not challenge.has_become_a_game():
            return False
        if challenge.standing_at(now) is not Standing.LINE_UP_INCOMPLETE:
            return False
        change = await self._games.line_up_change_on(challenge.id, now=now)
        if change is None or change is LineUpChange.ADMITTED:
            return False
        if not challenge.call_off_unfilled(occurred_at=now):
            return False
        try:
            await self._challenges.save(challenge)
            # **The game is told in this transaction**, so the ``CALLED_OFF``
            # on the challenge and the end on the game commit together or
            # neither does; a game already ended by its clock keeps its end.
            await self._planned_games.call_off(
                challenge_id=challenge.id, by=None, occurred_at=now
            )
            await self._uow.commit()
        except EventStreamVersionConflict:
            # Another process's copy of this loop, or a departure or a fill
            # that landed in the same second. This court is somebody else's
            # now; the rollback makes the session usable for the next one, and
            # the next tick re-derives this candidate.
            await self._uow.rollback()
            return None
        return True


__all__ = ["CallOffUnfilledCourts", "CalledOff"]
