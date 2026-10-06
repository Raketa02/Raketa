"""Move a player's Location area to the cell the phone's fix falls in.

**The cold start's write** (``docs/adr/0174`` §6). The client re-reads the
phone's position on every cold start and on return from the background after
more than a day, and puts it here silently. Everything that reads a location — a
group's area, a club's distance, the record — loads the profile and reads the
new cell on its next read, so nothing here tells anybody.

**The fix is rounded exactly as the commit rounds it** — ``LocationArea.around``,
the value object's own rule — before the aggregate is asked anything, so the
device's reading never reaches the stream and a fix that lands in the cell
already stored is, to the aggregate, no change at all: it records nothing and
the route still answers as if it had. That no-op is what makes the write safe
to send on every launch.

**Nothing else moves.** No reset, no prompt: a trip is a trip, and whatever
reads the area reads the new cell with everything else as it was.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import ChangeLocationCommand
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.location import LocationArea
from app.modules.player_profile.domain.ports import PlayerProfileRepository


class ChangeLocation:
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

    async def execute(self, command: ChangeLocationCommand) -> None:
        # The coarsening first, before the store is asked anything: from here
        # on only the cell exists. The bounds are the schema's to refuse; the
        # value object's invariant behind it is a backstop and not a refusal.
        area = LocationArea.around(command.latitude, command.longitude)

        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.change_location(area, occurred_at=instant(self._clock.now()))
        await self._profiles.save(profile)
        await self._uow.commit()
