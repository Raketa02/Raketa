"""Replace a player's Social tags, whole.

**The You tab's write, and the first of the three ADR-0170 §5 said would arrive
together** (``docs/adr/0179`` §6, §8): the tags, the photos and the intro are
edited as one piece of work, so that no field is editable while the two beside
it are frozen.

**The vocabulary and the bounds are re-checked**, through
``SocialTagSelection.from_ids`` — the same constructor the commit builds
through, so the two write paths cannot come to two answers about which
selections are legal. The picker on the tab is the onboarding step reused whole
and cannot produce an illegal selection; it is re-checked anyway, because a
control is not a validation (``docs/adr/0089``).

**Whole, never partial**, for the week's reason — the selection is the answer —
and **no idempotency key**, for the radius's: the same selection twice lands the
same state, and the aggregate's no-op rule means the second appends nothing.
The candidate projection follows ``SocialTagsChanged`` as it always has
(``docs/adr/0110``), so the next deal reads the new tags off the row.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import ChangeSocialTagsCommand
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.social_tags import SocialTagSelection


class ChangeSocialTags:
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

    async def execute(self, command: ChangeSocialTagsCommand) -> PlayerProfile:
        # The refusal first, before the store is asked anything: a selection
        # that was going to be refused should not cost a stream replay first.
        selection = SocialTagSelection.from_ids(command.social_tag_ids)

        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.change_social_tags(selection, occurred_at=instant(self._clock.now()))
        # Saved even when the transition recorded nothing: the repository is a
        # no-op with an empty pending list, and a branch here would be this
        # layer keeping a second copy of the aggregate's own rule.
        await self._profiles.save(profile)
        await self._uow.commit()
        return profile
