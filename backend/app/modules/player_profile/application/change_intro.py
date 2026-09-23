"""Replace the line a player wrote about themselves — or withdraw it.

**The day ADR-0170 §5 deferred to** (``docs/adr/0179`` §6): the intro becomes
editable with the tags and the photos, as one piece of work, and this is the
one of the three that needed a new event. ``IntroWritten`` stays the commit's;
what this appends is ``IntroChanged``, whose ``None`` is the withdrawal.

**The fence is the commit's, run here exactly as the commit runs it.**
``Intro.written`` trims, refuses a second line and a line over the cap, and
refuses contact — a phone-shaped run of digits, an email, a URL or a bare
domain, an ``@handle`` — with ``intro_not_admitted`` and one coarse reason,
before the store is asked anything (``domain/intro.py``). A blank is what it is
at the commit, *no line*: here that is a withdrawal rather than a skip, and the
aggregate's no-op rule makes withdrawing a line that was never written cost
nothing.

**Search records already kept quote the line as it stood at the deal**
(ADR-0104, as ADR-0170 accepted): nothing here rewrites a record, and the
candidate projection follows ``IntroChanged`` so the next deal reads the new
line — or none — off the row.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import ChangeIntroCommand
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.intro import Intro
from app.modules.player_profile.domain.ports import PlayerProfileRepository


class ChangeIntro:
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

    async def execute(self, command: ChangeIntroCommand) -> None:
        # The fence first, before the store is asked anything: a line carrying
        # contact is refused before a stream is replayed for it.
        intro = Intro.written(command.intro)

        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.change_intro(intro, occurred_at=instant(self._clock.now()))
        await self._profiles.save(profile)
        await self._uow.commit()
