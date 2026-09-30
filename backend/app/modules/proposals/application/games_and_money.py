"""You › Account › **Games & money** (the mechanics §17.1; the screens A7.1): read
it, and save it as the player taps.

**One write for both values**, as the screen saves them: a stepper press sends
the ceiling it already shows, and a chip sends the week. The same answer twice
records nothing, so a screen that saves on every tap costs no event per tap.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.proposals.application.commands import SetGamesAndMoneyCommand
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.ports import GamesAndMoneyRepository


@final
class ReadGamesAndMoney:
    def __init__(self, *, settings: GamesAndMoneyRepository) -> None:
        self._settings = settings

    async def execute(self, player_id: UUID) -> GamesAndMoney:
        return await self._settings.load(player_id)


@final
class SetGamesAndMoney:
    def __init__(
        self, *, settings: GamesAndMoneyRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._settings = settings
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SetGamesAndMoneyCommand) -> GamesAndMoney:
        settings = await self._settings.load(command.player_id)
        settings.set(
            games_per_week=command.games_per_week,
            most_ill_pay_grosze=command.most_ill_pay_grosze,
            at=instant(self._clock.now()),
        )
        await self._settings.save(settings)
        await self._uow.commit()
        return settings
