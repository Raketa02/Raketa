"""Turn *Show me to new people* on or off (``docs/adr/0204`` §2, #791).

The You tab's switch: *Players you don't share a group or a game with can find
you on Home, open your record and send you a request.* **On by default**;
written at once, with no Save. **No-op on an unchanged value.**

**Nobody follows it through the outbox**: the record's admission and Friends'
ask read it live off the profile, so a player who turns it off is closed to
strangers on their next tap. What it stops is new — a request already sent
stays open. The ranking never reads it.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import (
    SetShowMeToNewPeopleCommand,
)
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository


class SetShowMeToNewPeople:
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

    async def execute(self, command: SetShowMeToNewPeopleCommand) -> None:
        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.set_show_me_to_new_people(
            command.on, occurred_at=instant(self._clock.now())
        )
        await self._profiles.save(profile)
        await self._uow.commit()
