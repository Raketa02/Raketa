"""``GeneralSwitches`` over the Player profile's own repository — **signed
here**, so the arrow runs ``rankings → player_profile``, as the faces' does
(#772; ``docs/adr/0203`` §7): a player's *Show me in General*, folded from
their profile's stream as it stands, with the version it stands at.

**Read live, never off the event that announced it**, so whichever delivery
of a turn runs last writes what the profile says now, and the version lets
the projection refuse a read older than the one it holds. **Every switch** is
every profile stream the store holds, oldest first — the one read that
crosses streams, as the rating's ``every_history`` is — each folded whole.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import final
from uuid import UUID

from app.application.ports import DomainEventStore
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.ranking_visibility import RankingVisibility
from app.modules.player_profile.infrastructure.event_sourced_player_profile_repository import (  # noqa: E501
    PLAYER_PROFILE_AGGREGATE,
)
from app.modules.rankings.domain.ranking import GeneralSwitch


@final
class ProfileGeneralSwitches:
    def __init__(
        self, *, profiles: PlayerProfileRepository, event_store: DomainEventStore
    ) -> None:
        self._profiles = profiles
        self._event_store = event_store

    async def switch_of(self, player_id: UUID) -> GeneralSwitch | None:
        profile = await self._profiles.load(player_id)
        return None if profile is None else _switch(profile)

    async def every_switch(self) -> Sequence[GeneralSwitch]:
        switches = []
        for player_id in await self._event_store.find_aggregate_ids_by_first_event(
            aggregate_type=PLAYER_PROFILE_AGGREGATE, payload_equals={}
        ):
            profile = await self._profiles.load(player_id)
            if profile is not None:
                switches.append(_switch(profile))
        return tuple(switches)


def _switch(profile: PlayerProfile) -> GeneralSwitch:
    return GeneralSwitch(
        player_id=profile.player_id,
        hidden=profile.ranking_visibility is RankingVisibility.HIDDEN,
        version=profile.version,
    )
