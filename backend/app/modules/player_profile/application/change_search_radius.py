"""Replace a player's Search radius, whole.

**The write the ``KEEP_THIS_RADIUS`` prompt is answered by**, and the same write
the *You* screen's slider will use when it exists: taking a relaxation rung and
widening on the profile are the same act at two commitments, and only one of them
is durable (``docs/adr/0099`` — *"nothing here writes your profile; the app
offers to save it afterwards"*).

**The bounds are re-checked**, through ``SearchRadius.chosen``, even though the
slider that produced the number cannot offer an illegal one. The bounds are
served so a client can build a control that only produces legal values, and a
control is not a validation (``docs/adr/0089``): it is absent from a replayed
request, from an older build, and from anything that is not the app.

**Accepting the prompt is what stops it.** ``KEEP_THIS_RADIUS`` is raised by a
run of searches that each took the same widening rung, so a profile that now
holds the widened radius takes no rung on the next search and the question stops
being asked — nothing clears it, and nothing here knows the prompt exists.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import (
    ChangeSearchRadiusCommand,
)
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.search_radius import SearchRadius


class ChangeSearchRadius:
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

    async def execute(self, command: ChangeSearchRadiusCommand) -> PlayerProfile:
        # The refusal first, before the store is asked anything: a radius that
        # was going to be refused should not cost a stream replay first.
        radius = SearchRadius.chosen(command.search_radius_km)

        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.change_search_radius(radius, occurred_at=instant(self._clock.now()))
        await self._profiles.save(profile)
        await self._uow.commit()
        return profile
