"""**Get your level — once per account, ever** (#727; ``docs/adr/0200`` §7; the
mechanics §17.2, Q126).

*Get your level so your groups can deal you games.* — to an account in at least
one group, player or official, whose first group join was a day ago and which
holds no Skill rating in any sport. Nothing announces that a day has passed
since a join, so this is no event's to tell and the teller's table cannot hold
it: a job runs it, as *How did it go?* is run (``asking.py``), over the accounts
whose earliest join **among the groups they are in now** fell
``GET_YOUR_LEVEL_AFTER`` ago, within ``GET_YOUR_LEVEL_WITHIN`` of it —
**candidates**, each asked whether it was ever told and whether it holds a
rating.

**Told a day after the join, whenever the run comes to it**, under a key of the
account's — so every process tells it on one day's stream, and a second run
tells nothing again: two at once collide on the player's day and the second is
stepped over. **Once per account, not once per join**: an account told it on
any day is never told again, so leaving the first group for a later one, whose
join is then the earliest, asks nothing twice. Each account is its own
transaction. Always on: nobody chose it, and nobody can switch it off.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.notifications.application.telling import GiveNotice
from app.modules.notifications.domain.notices import (
    GET_YOUR_LEVEL_AFTER,
    GET_YOUR_LEVEL_WITHIN,
    NoticeKind,
    get_your_level,
)
from app.modules.notifications.domain.ports import (
    GroupJoiners,
    NoticeDirectory,
    RatedAccounts,
)


@dataclass(frozen=True, slots=True)
class Told:
    #: Accounts told *Get your level*.
    players: int
    #: Accounts another process was telling at that moment, stepped over.
    conflicts: int


@final
class TellGetYourLevel:
    def __init__(
        self,
        *,
        joiners: GroupJoiners,
        ratings: RatedAccounts,
        notices: NoticeDirectory,
        give: GiveNotice,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._joiners = joiners
        self._ratings = ratings
        self._notices = notices
        self._give = give
        self._uow = uow
        self._clock = clock

    async def execute(self) -> Told:
        due_by = instant(instant(self._clock.now()) - GET_YOUR_LEVEL_AFTER)
        joined = await self._joiners.first_joined(
            after=instant(due_by - GET_YOUR_LEVEL_WITHIN), by=due_by
        )
        waiting = set(joined) - await self._notices.told(
            NoticeKind.GET_YOUR_LEVEL, joined
        )
        unrated = waiting - await self._ratings.rated_among(waiting)
        told = conflicts = 0
        # In a stable order, so two processes take the day streams alike.
        for player in sorted(unrated, key=str):
            try:
                if await self._give.execute(
                    player,
                    get_your_level(player),
                    at=instant(joined[player] + GET_YOUR_LEVEL_AFTER),
                ):
                    await self._uow.commit()
                    told += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return Told(players=told, conflicts=conflicts)
