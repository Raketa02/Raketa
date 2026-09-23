"""The four acts a player performs on a plan, and the two things they share.

**Three slot use cases and not one with a slot code**, because ADR-0144 has three
events and *setting a slot and moving one are the same event told with two
sentences*. What is genuinely shared is the shape — find the court, refuse a
hold, record, commit — and it is shared by inheritance from one base rather than
by three copies, which is where a fourth would arrive without the hold.

**The fourth act is the lock, and it reuses that base whole** (``docs/adr/0155``).
It is not a slot write and it records a different kind of fact, but everything
outside the aggregate call is identical — the same gate, the same hold in the same
place, the same save and commit — and *a hold refuses a lock exactly as it refuses
a slot write*, because a lock writes a line other people read. The fourth arriving
without the hold is the thing the base was written to prevent, and this is the
fourth.

**The gate is one question asked through one port**, and its two answers are
this context's two refusals: a court the reader holds no accepted seat on is
``plan_not_found``, and a court that is over is ``plan_is_history``. *The game
leaving ``AWAITING_ENTRY`` is the only thing that freezes the slots*
(``docs/adr/0144``) once there is a game, and before there is one the challenge
ending is (``docs/adr/0164`` §3) — neither is a lock. Once somebody has said *we
played*, or everybody has said no, the plan is history.

**The lock reads one more thing off the same answer** — whether the court is
whole — and hands it to the aggregate, which refuses on it with a code of its
own (``docs/adr/0164`` §5). The slot writes do not consult it: where, day and
hour are proposals anybody on the court may make and move, whole or not.

**Every answer here is a row**: the plan as it now stands beside the anchor its
horizon runs from, because a client draws the day chips from the anchor and a
write that answered the plan alone would send it back to the list for the one
number it needs.

**A hold refuses all four writes and refuses no read** (``docs/adr/0148`` §9). A
slot change — and a lock — writes a system line into a room other people are in,
so it is reach; but a hold must not erase an arrangement other people are already
inside, so the list read is ungated.

**A write of the value already there records nothing and answers 200**, and so
does a lock on a plan that is already locked. That belongs to the aggregate,
which pulls no events — so the save is a no-op and the commit closes a
transaction that wrote nothing. It is not a branch any of these use cases takes,
and there is deliberately no *did anything change* flag on the answer: the reply
is the plan as it now stands, which is the same answer either way.

**Nothing here is announced and nothing here subscribes.** The four events go on
the outbox like every other, and what turns them into lines in a room is a
context that this one does not know exists.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.plans.application.commands import (
    LockThePlanCommand,
    SetDayCommand,
    SetHourCommand,
    SetPlaceCommand,
)
from app.modules.plans.application.plan_row import PlanRow
from app.modules.plans.domain.errors import PlanIsHistory, PlanNotFound
from app.modules.plans.domain.plan import Plan
from app.modules.plans.domain.ports import (
    AccountHoldQuery,
    PlannableCourt,
    PlannableCourts,
    PlanRepository,
)
from app.shared.domain.errors import AccountHeld


class _RecordASlot:
    """What all four acts share: the gate, the hold, the load and the commit."""

    def __init__(
        self,
        *,
        plans: PlanRepository,
        courts: PlannableCourts,
        holds: AccountHoldQuery,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._courts = courts
        self._holds = holds
        self._uow = uow
        self._clock = clock

    async def _yours(
        self, *, challenge_id: UUID, player_id: UUID, now: Instant
    ) -> PlannableCourt:
        """That court, if this player holds an accepted seat on it and it is
        still being arranged.

        **Two refusals from one question**, and the order is the design. *You
        are not on that court* comes first and is a 404 carrying one code for
        three cases — no such challenge, a court that is not yours, and a seat
        you were asked to and have not said yes to — because separating them
        would answer *is this id real* about four strangers' evening, and would
        tell an invitee still deciding that there is a plan to read
        (``docs/adr/0164`` §3). *That court is over* is a 409 and is only
        reachable by somebody who was there.
        """

        found = (await self._courts.plannable_for(player_id, now=now)).get(
            challenge_id
        )
        if found is None:
            raise PlanNotFound()
        if not found.open_to_planning:
            raise PlanIsHistory()
        return found

    async def _not_held(self, player_id: UUID) -> None:
        """**After the gate, and never before it.** A stranger is told there is
        no such plan; telling them their account is held would be an answer about
        an arrangement they may not know exists."""

        if player_id in await self._holds.held_among((player_id,)):
            raise AccountHeld("This account is under a live hold.")

    async def _saved(self, plan: Plan, *, court: PlannableCourt) -> PlanRow:
        await self._plans.save(plan)
        await self._uow.commit()
        return PlanRow(plan=plan, anchor=court.anchor)


@final
class SetPlace(_RecordASlot):
    """*We are meeting here.* Short free text, one line, and nothing reads it."""

    async def execute(self, command: SetPlaceCommand) -> PlanRow:
        at = instant(self._clock.now())
        court = await self._yours(
            challenge_id=command.challenge_id, player_id=command.player_id, now=at
        )
        await self._not_held(command.player_id)
        plan = await self._plans.load(command.challenge_id)
        plan.record_place(place=command.place, by=command.player_id, occurred_at=at)
        return await self._saved(plan, court=court)


@final
class SetDay(_RecordASlot):
    """*We are playing on this day.* Clamped to the court's own horizon —
    measured from the send until the game exists, then from ``planned_at``."""

    async def execute(self, command: SetDayCommand) -> PlanRow:
        at = instant(self._clock.now())
        court = await self._yours(
            challenge_id=command.challenge_id, player_id=command.player_id, now=at
        )
        await self._not_held(command.player_id)
        plan = await self._plans.load(command.challenge_id)
        plan.record_day(
            day=command.day,
            by=command.player_id,
            anchor=court.anchor,
            occurred_at=at,
        )
        return await self._saved(plan, court=court)


@final
class SetHour(_RecordASlot):
    """*We are playing at this time.* Thirty-minute steps, 06:00 to 23:00."""

    async def execute(self, command: SetHourCommand) -> PlanRow:
        at = instant(self._clock.now())
        court = await self._yours(
            challenge_id=command.challenge_id, player_id=command.player_id, now=at
        )
        await self._not_held(command.player_id)
        plan = await self._plans.load(command.challenge_id)
        plan.record_hour(
            hour=command.hour, by=command.player_id, occurred_at=at
        )
        return await self._saved(plan, court=court)


@final
class LockThePlan(_RecordASlot):
    """*We are agreed.* **An act, and the base's fourth user.**

    ``docs/adr/0155``. Everything outside the aggregate call is the slot writes'
    exactly: the gate first, so a stranger is told there is no such plan; the
    hold after it, because a lock is reach into a room other people read; then
    the save and the commit, which write nothing at all when the plan was already
    locked.

    **It takes no value and answers the whole plan**, like the three beside it —
    a client draws the locked state off ``locked_at`` and needs nothing else back.

    **It is the one act that reads whether the court is whole** (``docs/adr/0164``
    §5), off the same answer the gate already holds, and hands it to the
    aggregate rather than deciding here: the aggregate is where the lock's
    other refusal lives, and two refusals of one act belong in one place so
    their order is one decision.
    """

    async def execute(self, command: LockThePlanCommand) -> PlanRow:
        at = instant(self._clock.now())
        court = await self._yours(
            challenge_id=command.challenge_id, player_id=command.player_id, now=at
        )
        await self._not_held(command.player_id)
        plan = await self._plans.load(command.challenge_id)
        plan.lock(by=command.player_id, occurred_at=at, court_is_whole=court.whole)
        return await self._saved(plan, court=court)


__all__ = ["LockThePlan", "SetDay", "SetHour", "SetPlace"]
