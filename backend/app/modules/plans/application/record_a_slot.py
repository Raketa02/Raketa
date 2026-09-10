"""The four acts a player performs on a plan, and the two things they share.

**Three slot use cases and not one with a slot code**, because ADR-0144 has three
events and *setting a slot and moving one are the same event told with two
sentences*. What is genuinely shared is the shape — find the game, refuse a hold,
record, commit — and it is shared by inheritance from one base rather than by
three copies, which is where a fourth would arrive without the hold.

**The fourth act is the lock, and it reuses that base whole** (``docs/adr/0155``).
It is not a slot write and it records a different kind of fact, but everything
outside the aggregate call is identical — the same gate, the same hold in the same
place, the same save and commit — and *a hold refuses a lock exactly as it refuses
a slot write*, because a lock writes a line other people read. The fourth arriving
without the hold is the thing the base was written to prevent, and this is the
fourth.

**The gate is one question asked of ``games`` through one port**, and its two
answers are this context's two refusals: a game the reader is not on the court of
is ``plan_not_found``, and a game that has left its entry window is
``plan_is_history``. *The game leaving ``AWAITING_ENTRY`` is the only thing that
freezes the slots* (``docs/adr/0144``), and it is not a lock — once somebody has
said *we played*, the plan is history.

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
from app.modules.games.domain.ports import PlannableGame, PlanningCourt
from app.modules.plans.application.commands import (
    LockThePlanCommand,
    SetDayCommand,
    SetHourCommand,
    SetPlaceCommand,
)
from app.modules.plans.domain.errors import PlanIsHistory, PlanNotFound
from app.modules.plans.domain.plan import Plan
from app.modules.plans.domain.ports import AccountHoldQuery, PlanRepository
from app.shared.domain.errors import AccountHeld


class _RecordASlot:
    """What all three acts share: the gate, the hold, the load and the commit."""

    def __init__(
        self,
        *,
        plans: PlanRepository,
        court: PlanningCourt,
        holds: AccountHoldQuery,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._court = court
        self._holds = holds
        self._uow = uow
        self._clock = clock

    async def _yours(
        self, *, game_id: UUID, player_id: UUID, now: Instant
    ) -> PlannableGame:
        """That game, if this player is on its court and it is still being
        arranged.

        **Two refusals from one question**, and the order is the design. *You
        were not on that court* comes first and is a 404 carrying one code for
        two cases — no such game, and a game that is not yours — because
        separating them would answer *is this id real* about four strangers'
        evening. *That game is over* is a 409 and is only reachable by somebody
        who was there.
        """

        found = (await self._court.plannable_for(player_id, now=now)).get(game_id)
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

    async def _saved(self, plan: Plan) -> Plan:
        await self._plans.save(plan)
        await self._uow.commit()
        return plan


@final
class SetPlace(_RecordASlot):
    """*We are meeting here.* Short free text, one line, and nothing reads it."""

    async def execute(self, command: SetPlaceCommand) -> Plan:
        at = instant(self._clock.now())
        await self._yours(
            game_id=command.game_id, player_id=command.player_id, now=at
        )
        await self._not_held(command.player_id)
        plan = await self._plans.load(command.game_id)
        plan.record_place(place=command.place, by=command.player_id, occurred_at=at)
        return await self._saved(plan)


@final
class SetDay(_RecordASlot):
    """*We are playing on this day.* Clamped to the game's own horizon."""

    async def execute(self, command: SetDayCommand) -> Plan:
        at = instant(self._clock.now())
        game = await self._yours(
            game_id=command.game_id, player_id=command.player_id, now=at
        )
        await self._not_held(command.player_id)
        plan = await self._plans.load(command.game_id)
        plan.record_day(
            day=command.day,
            by=command.player_id,
            planned_at=game.planned_at,
            occurred_at=at,
        )
        return await self._saved(plan)


@final
class SetHour(_RecordASlot):
    """*We are playing at this time.* Thirty-minute steps, 06:00 to 23:00."""

    async def execute(self, command: SetHourCommand) -> Plan:
        at = instant(self._clock.now())
        await self._yours(
            game_id=command.game_id, player_id=command.player_id, now=at
        )
        await self._not_held(command.player_id)
        plan = await self._plans.load(command.game_id)
        plan.record_hour(
            hour=command.hour, by=command.player_id, occurred_at=at
        )
        return await self._saved(plan)


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
    """

    async def execute(self, command: LockThePlanCommand) -> Plan:
        at = instant(self._clock.now())
        await self._yours(
            game_id=command.game_id, player_id=command.player_id, now=at
        )
        await self._not_held(command.player_id)
        plan = await self._plans.load(command.game_id)
        plan.lock(by=command.player_id, occurred_at=at)
        return await self._saved(plan)


__all__ = ["LockThePlan", "SetDay", "SetHour", "SetPlace"]
