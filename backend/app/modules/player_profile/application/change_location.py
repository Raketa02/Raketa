"""Move a player's Location area to the cell the phone's fix falls in — or to
a club's, picked in its place.

**The cold start's write** (``docs/adr/0174`` §6), and *You › Where you play*'s
(``docs/adr/0200`` §10): a player who refused the phone's location picks a club
near where they play, and its point, rounded to the cell, is their area until a
reading in another cell replaces it. The client re-reads the
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
from app.modules.player_profile.application.location_source import area_of
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import ClubPoints, PlayerProfileRepository


class ChangeLocation:
    def __init__(
        self,
        *,
        profiles: PlayerProfileRepository,
        clubs: ClubPoints,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._profiles = profiles
        self._clubs = clubs
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ChangeLocationCommand) -> None:
        # The coarsening first, before the profile is asked anything: from
        # here on only the cell exists. The bounds are the schema's to refuse;
        # the value object's invariant behind it is a backstop and not a
        # refusal. A picked club is asked where it is, and one that is not in
        # Raketa is refused here.
        area = await area_of(command.location, self._clubs)

        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.change_location(area, occurred_at=instant(self._clock.now()))
        await self._profiles.save(profile)
        await self._uow.commit()
