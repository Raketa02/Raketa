"""Replace a player's weekly hours, whole — *Save your week*.

**The write the ``KEEP_THESE_TIMES`` prompt is answered by.** The engine notices
that a search ran on a week the profile does not hold and asks whether to keep
it; this is where a yes lands. Nothing in the matcher writes a profile — it asks,
and it accepts whatever answer comes back (``matchmaking/domain/prompts.py``).

**A cleared week is a legal value here.** ``WeeklyHours.edited`` is what the
week is built through rather than ``of_cells``, because the floor binds the
answer a player is *asked for* at the commit and not every later edit of it
(``domain/weekly_hours.py``). A player who unticks everything has told us their
week is not describable, which the matcher reads as *absent* and never as *never
free* (ADR-0102 part 3).

**Whole, never partial**, which is why the route is a ``PUT`` and why this takes
the hours rather than a diff. A blank week is a legal value, so *leave my week
alone* and *clear my week* would be the same request if either end could omit
the field.

**No idempotency key.** The same week twice lands the same state, and the
aggregate's no-op rule means the second appends nothing — there is nothing here
to deduplicate, which is exactly what the creating commit's key exists for and
this write does not need (``docs/adr/0089``).
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import SetWeeklyHoursCommand
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_profile.domain.weekly_hours import WeeklyHours


class SetWeeklyHours:
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

    async def execute(self, command: SetWeeklyHoursCommand) -> PlayerProfile:
        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.set_weekly_hours(
            WeeklyHours.edited(command.weekly_hours),
            occurred_at=instant(self._clock.now()),
        )
        # Saved even when the transition recorded nothing: the repository is a
        # no-op with an empty pending list, and a branch here would be this
        # layer keeping a second copy of the aggregate's own rule.
        await self._profiles.save(profile)
        await self._uow.commit()
        return profile
