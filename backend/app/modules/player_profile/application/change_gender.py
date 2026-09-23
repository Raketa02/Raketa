"""Record a new answer to the gender question.

*Self-declared, freely changed* (``docs/adr/0096``): the aggregate has had
``change_gender`` from the day the field existed, and this is its first caller
in ``app/`` — the You tab's *Who you play with* row (``docs/adr/0179`` §8),
which opens on the answer already given because the owner's own read now serves
it (§4).

**No-op on an unchanged value**, like every preference beside it; and **a first
answer on a pre-question profile is a change**, because there is no value to be
equal to — which is what makes ADR-0096's *existing players are asked on next
open* reachable from this route at all. Nothing is re-validated: a ``Gender``
is a closed set the boundary selected from, and ``PREFER_NOT_TO_SAY`` is an
answer like the others.

The candidate projection follows ``GenderChanged`` as it always has, so the
mutual gate reads the new answer on the next search either side runs.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import ChangeGenderCommand
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository


class ChangeGender:
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

    async def execute(self, command: ChangeGenderCommand) -> None:
        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.change_gender(command.gender, occurred_at=instant(self._clock.now()))
        await self._profiles.save(profile)
        await self._uow.commit()
