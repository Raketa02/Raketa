"""Turn *Show me in General* on or off (``docs/adr/0203`` §7, #772).

The You tab's switch, on *On your card*: *Players who don't know you can see
your place, open your record and send you a request.* **On by default**; written
at once, with no Save. **No-op on an unchanged value.**

**The ranking follows through the outbox**: Rankings hears
``player_profile.ranking_visibility_set`` and keeps the switch beside its rows,
for every sport, so a hidden player's row leaves everybody else's General with
its place kept. What it stops is new — a request already made through the
ranking stays open.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import (
    SetRankingVisibilityCommand,
)
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository


class SetRankingVisibility:
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

    async def execute(self, command: SetRankingVisibilityCommand) -> None:
        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.set_ranking_visibility(
            command.visibility, occurred_at=instant(self._clock.now())
        )
        await self._profiles.save(profile)
        await self._uow.commit()
