"""**All four are asked *How did it go?* when a Competitive booked game's hour
ends** (#663; ``docs/adr/0195`` §5, the mechanics §15.2).

A clock passing announces nothing, so this is no event's to tell, and the
teller's table cannot hold it: a job runs it every thirty seconds, over the
booked games whose hour ended within ``ASKED_WITHIN`` — **candidates**, each read
off its court.

**Only a game still waiting for its score is asked**: nobody has said they
played, nobody is awaited or Didn't come, it was not called off nor short, and
it is not For fun, which asks nobody anything.

**Told at the hour's end, whenever the run comes to it**, under a key of the
game's — so the day it is told on is the same for every process, and a second
run, here or in another process, tells nothing again: two at once collide on a
player's day and the second is stepped over. Each game is its own transaction.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.notifications.application.telling import GiveNotice, notice_about
from app.modules.notifications.domain.notices import ASKED_WITHIN, NoticeKind, Opens
from app.modules.notifications.domain.ports import EndedHours, GameBriefs, GameCourts


@dataclass(frozen=True, slots=True)
class Asked:
    #: Games whose players were asked.
    games: int
    #: Games another process was telling at that moment, stepped over.
    conflicts: int


@final
class AskHowDidItGo:
    def __init__(
        self,
        *,
        hours: EndedHours,
        courts: GameCourts,
        games: GameBriefs,
        give: GiveNotice,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._hours = hours
        self._courts = courts
        self._games = games
        self._give = give
        self._uow = uow
        self._clock = clock

    async def execute(self) -> Asked:
        now = instant(self._clock.now())
        asked = conflicts = 0
        for booking_id in await self._hours.ended(
            after=instant(now - ASKED_WITHIN), by=now
        ):
            try:
                if await self._ask(booking_id, now=now):
                    await self._uow.commit()
                    asked += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return Asked(games=asked, conflicts=conflicts)

    async def _ask(self, booking_id: UUID, *, now: Instant) -> bool:
        court = await self._courts.of_booking(booking_id, at=now)
        if court is None or not court.competitive or not court.awaiting_a_score:
            return False
        game = await self._games.about(booking_id, at=now)
        if game is None:
            return False
        notice = notice_about(
            NoticeKind.HOW_DID_IT_GO,
            game,
            key=f"{NoticeKind.HOW_DID_IT_GO}:{booking_id}",
            opens=Opens.RESULT,
        )
        told = False
        # In a stable order, so two processes take the day streams alike.
        for player in sorted(court.sides, key=str):
            told |= await self._give.execute(player, notice, at=court.hour_ends_at)
        return told
