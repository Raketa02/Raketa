"""Does this player have a Player profile?

The question onboarding's entry gate asks on every cold launch. It is a
*per-player* question with a per-player answer, which is exactly what narrows the
rating context's *"there is no onboarded player"* invariant rather than breaking
it: a profile is one per player because its contents are facts about a person,
and asking whether one exists is asking what it answers (``docs/adr/0090``).

**Answered from the stream, never from a projection.** The gate reads this
immediately after the commit that creates the profile, so a read model that has
not caught up would route a player who has just finished the social steps back
into step 1 — the same constraint the rating context's completion path already
carries (``docs/adr/0089``, *Harder*).

A use case for a boolean looks thin, and it is the thin thing on purpose: the
route that serves it belongs to the users context, and a use case is what lets
that route depend on a port rather than reach into this one's persistence.
"""

from __future__ import annotations

from uuid import UUID

from app.modules.player_profile.domain.ports import PlayerProfileRepository


class HasPlayerProfile:
    def __init__(self, *, profiles: PlayerProfileRepository) -> None:
        self._profiles = profiles

    async def execute(self, player_id: UUID) -> bool:
        return await self._profiles.exists_for(player_id=player_id)
