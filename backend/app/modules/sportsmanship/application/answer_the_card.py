"""Answering one card, in four steps and no side effects.

1. Ask ``games`` whether this is **a settled court of the caller's**, and get the
   other people on it. Nothing is refused before this, because everything after
   it is a question about a court that exists.
2. Refuse a card that has already been answered. **This is what *submitting
   closes it* costs**, and it is checked rather than left to a primary key: a
   database integrity error is a 500, and a player tapping submit twice on a slow
   connection deserves an answer rather than an outage.
3. Build the card, which is where every rule about *who may be on it* lives.
4. Write it and commit.

**Nothing is emitted and nothing subscribes** (``docs/adr/0154``). No domain
event, no outbox row, no notification to the person who was rated — least of all
to them. The published figure is a fold over the rows this writes, computed when
somebody opens a record, and there is nothing anywhere that has to be told a card
was answered.

**Nothing is returned.** The return type is the contract as much as the route's
``204`` is: a use case that answered something would be a shape a route could be
tempted to render, and *no individual rating reaches anybody* would become a
matter of route discipline rather than of what exists.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.sportsmanship.application.commands import AnswerTheCardCommand
from app.modules.sportsmanship.domain.card import SportsmanshipCard
from app.modules.sportsmanship.domain.errors import (
    ThisGameIsNotYoursToRate,
    YouHaveAlreadyRatedThisGame,
)
from app.modules.sportsmanship.domain.ports import SettledCourts, SportsmanshipLedger


@final
class AnswerTheCard:
    """One card: answered once, stored, and never read back to anybody."""

    def __init__(
        self,
        *,
        clock: Clock,
        courts: SettledCourts,
        ledger: SportsmanshipLedger,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._courts = courts
        self._ledger = ledger
        self._uow = unit_of_work

    async def execute(self, command: AnswerTheCardCommand) -> None:
        now = self._clock.now()
        court = await self._courts.court_of(
            command.game_id, player_id=command.rater_id, now=now
        )
        if court is None:
            raise ThisGameIsNotYoursToRate()
        if await self._ledger.has_been_answered(
            game_id=command.game_id, rater_id=command.rater_id
        ):
            raise YouHaveAlreadyRatedThisGame()

        await self._ledger.record(
            SportsmanshipCard.answered(court=court, given=command.given, at=now)
        )
        await self._uow.commit()
