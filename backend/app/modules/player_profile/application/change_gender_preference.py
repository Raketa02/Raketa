"""Record a new durable answer to *who am I willing to play with*.

The You tab's write (``docs/adr/0179`` §8) for the preference ADR-0096 §3 made
**durable rather than per search**: the gate it feeds is mutual, evaluated
against this player when somebody else searches and this player is not present,
which a per-search setting could not bind at all. A single search may narrow
this; nothing may widen past it.

**No-op on an unchanged value.** And what a change *does* — narrowing makes this
player invisible to the excluded side entirely, searchers who asked for anybody
included — is the client's to say at the moment of setting, from a reason code;
nothing here can enforce that, and the event says so.

**The projection follows, as it does for the commit.** ``GenderPreferenceChanged``
moves the index row, so the next search anybody else runs reads the narrowed
answer off it, and the searcher's own is read live off the aggregate — the two
directions a narrowing gates, and both follow one event. Seats already accepted
are facts, not candidates: nothing downstream treats this as a reason to undo an
agreement.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import (
    ChangeGenderPreferenceCommand,
)
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository


class ChangeGenderPreference:
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

    async def execute(self, command: ChangeGenderPreferenceCommand) -> None:
        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.change_gender_preference(
            command.gender_preference, occurred_at=instant(self._clock.now())
        )
        await self._profiles.save(profile)
        await self._uow.commit()
