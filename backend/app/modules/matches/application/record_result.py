"""Put a score on the table, and settle one.

**Four facts and never a list** (ADR-0034): what is on the table, who put it
there, whether it is agreed, and how many proposals there have been. The
conversation itself is in the announcements, which is the shape the planned
playerEventsTracker reads it in and the reason ADR-0034 could afford a count.

**What the route asks, and what it permits, is ``Raketa02/Raketa#79``'s** — the
30-minute acceptance grace, the two `may` booleans, the permissive validator that
must never call a real 7-6 illegal, and the choice about settlement by silence.
Nothing here judges a scoreline; what is here is that the record can hold one and
that changing it says so out loud.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.matches.application.commands import (
    AgreeResultCommand,
    ProposeScoreCommand,
)
from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository


class ProposeScore:
    def __init__(
        self, matches: MatchRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._matches = matches
        self._uow = uow
        self._clock = clock

    async def execute(self, command: ProposeScoreCommand) -> Match:
        match = await self._matches.get(command.match_id)
        if match is None:
            raise MatchNotFound()
        # Only somebody who was on the court may say what happened on it, and
        # that is the **aggregate's** refusal rather than a guard here: it has to
        # find her side to apply ADR-0048's one-proposal-per-side cap, so a seat
        # she does not hold is refused on the way to a question it cannot
        # answer. A leaver's seat is empty by then, which is why her screen opens
        # and offers nothing (`Raketa02/Raketa#90`) rather than 404ing.
        match.propose_score(
            command.score, by=command.player_id, at=instant(self._clock.now())
        )
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored


class AgreeResult:
    """Settle the score — by agreement, or by the silence that confirms it."""

    def __init__(
        self, matches: MatchRepository, uow: UnitOfWork, clock: Clock
    ) -> None:
        self._matches = matches
        self._uow = uow
        self._clock = clock

    async def execute(self, command: AgreeResultCommand) -> Match:
        match = await self._matches.get(command.match_id)
        if match is None:
            raise MatchNotFound()

        match.agree_result(
            at=instant(self._clock.now()), by=command.player_id
        )
        stored = await self._matches.save(match)
        await self._uow.commit()
        return stored
