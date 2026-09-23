"""Answer the proposals question again, from the profile screen.

**The one write on this surface that always records.** Every other transition
here is a preference and a no-op when nothing moved; this one is a consent, and
*the player was asked again, against these words, on this surface, and answered
the same way* is a fact a consent log has to be able to evidence
(``domain/consent.py``, ``docs/adr/0089``). So a re-affirmation appends a second
``ProposalsOptInAnswered``, and there is deliberately no branch here to stop it.

**The surface is the route's and never the body's.** The commit records
``ONBOARDING`` because the commit is the end of onboarding; this records
``PROFILE`` because the You tab is where it is pressed — and a client that could
assert the surface could assert a consent it never gathered on a screen it never
showed. ``copy_version`` is the client's, because the words are: the boundary
bounds its length, and ``answerable_copy_version`` inside the transition is the
backstop.

**Reachable only through a committed profile.** The commit is the first answer
and there is no path to a profile without one, so a player answering here is
always answering *again*.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.player_profile.application.commands import (
    AnswerProposalsOptInCommand,
)
from app.modules.player_profile.domain.errors import PlayerProfileNotFound
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.profile import PlayerProfile


class AnswerProposalsOptIn:
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

    async def execute(self, command: AnswerProposalsOptInCommand) -> PlayerProfile:
        profile = await self._profiles.load(command.player_id)
        if profile is None:
            raise PlayerProfileNotFound()

        profile.answer_proposals_opt_in(
            accepted=command.accepted,
            copy_version=command.copy_version,
            surface=command.surface,
            occurred_at=instant(self._clock.now()),
        )
        await self._profiles.save(profile)
        await self._uow.commit()
        return profile
