"""Record a new answer to *whom will I share a court with*, by reliability.

The Player reliability screen's switch (``docs/adr/0195`` §6, #661): *Play only
with players of at least High reliability*, or *at least Medium*, or off. A
preference beside the gender preference, and like it **durable, never per game**:
the pair rule asks it whenever somebody else's game is being made.

**No-op on an unchanged value**, and a band the switch does not offer is refused
before the store is asked.

**From then on, both ways**: the proposer, the deck, posting, rescues and the
details ask the pair rule of every pair live (``proposals``' ``MatcherPlayerFit``).
Yeses already given stand — the yes guard on a yes coming back and the fill's
re-check leave this clause out — and nothing downstream undoes a booked game.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import (
    SetReliabilityMinimumCommand,
)
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository


class SetReliabilityMinimum:
    def __init__(
        self,
        *,
        profiles: PlayerProfileRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._profiles = profiles
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SetReliabilityMinimumCommand) -> None:
        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.set_reliability_minimum(
            command.minimum, occurred_at=instant(self._clock.now())
        )
        await self._profiles.save(profile)
        await self._uow.commit()
