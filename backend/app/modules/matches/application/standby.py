"""Joining the queue: the write with no surface, and why it exists anyway.

ADR-0087 gives *leaving* standby a route and says nothing about joining, because
the prototype's waitlist toggle is a **match-screen** control and the match
screen is out of scope — ADR-0083 already removed the buttons whose destination
went with it. So in v1 nothing a player taps puts her on a standby list, and the
one thing that does is the seed catalog (``Raketa02/Raketa#96``'s demo week).

**It is a use case rather than a line of SQL in the seeds** because seeds
execute use cases, never SQL: a seeded standby place has to be written by the
same code a request would run, or the seeded week is developed against a state
the product cannot reach. When a join surface arrives — the standing rule that
*"auto-joins matching standby lists"* is the named candidate — this is the write
it calls.

**It refuses on a match that does not exist and on nothing else.** Queueing for
a match that is over, cancelled or full is not a mistake: full is the ordinary
reason to queue at all, and a place on a match that then ends costs nothing and
is read by nobody, because the cascade only ever asks a match that has just lost
a seat. Refusing here would be a second answer to *is this match still a game*,
which the ladder already gives.

**It does not commit**, on the rule every other Matches use case follows: the
transaction boundary is the caller's, so a seed run writes a whole week in one.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.kernel import Clock, instant

from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.ports import MatchRepository, StandbyPlaces


@dataclass(frozen=True)
class JoinStandbyCommand:
    """*Tell me if a seat frees on this match.*"""

    match_id: UUID
    player_id: UUID


class JoinStandby:
    """Put a player on a match's queue, idempotently."""

    def __init__(
        self,
        *,
        matches: MatchRepository,
        standby: StandbyPlaces,
        clock: Clock,
    ) -> None:
        self._matches = matches
        self._standby = standby
        self._clock = clock

    async def execute(self, command: JoinStandbyCommand) -> None:
        """Queue her, or leave her queued. Answers nothing either way.

        The match is loaded to be **refused when it is absent** and for no other
        reason — the place is a row about a pair, and nothing on the aggregate
        decides whether it may exist.
        """

        if await self._matches.get(command.match_id) is None:
            raise MatchNotFound()
        await self._standby.join(
            match_id=command.match_id,
            player_id=command.player_id,
            at=instant(self._clock.now()),
        )
