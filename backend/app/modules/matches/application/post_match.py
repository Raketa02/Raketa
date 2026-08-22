"""Post a match: the constitutive facts, chosen once, with its seats.

**The club's policy is read here and copied onto the match.** ADR-0077 puts a
club value that must be honoured *as booked* on the match record as a
Constitutive fact rather than in a temporal query, so this is the one moment the
two contexts meet — and afterwards a situation is resolvable from one row-set
with no club fetch at all, which is what makes Now cheap (ADR-0034).

The category is checked against the club's own catalogue rather than trusted: a
match pointing at a category the club does not have is one that can never be
given a court, and finding that out at hold time would make it look like the
club had sold out.

**A posted match asks the hold ladder before it is stored**, which for an open
one is always *stand* — nobody has paid, so there is no tier to be in. A
**private** court is a different sentence: it belongs to whoever bought it from
its first instant (ADR-0031's hard rung), so posting one either claims a court or
finds none and the match is born ``inventoryLost``. That is ADR-0035's single
story told at the first moment anybody could ask, rather than at commitment with
three people's money already in it.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.clubs.domain.errors import ClubNotFound
from app.modules.clubs.domain.ports import ClubRepository
from app.modules.matches.application.commands import PostMatchCommand
from app.modules.matches.application.resolve_court_hold import ResolveCourtHold
from app.modules.matches.domain.match import Match
from app.modules.matches.domain.ports import MatchRepository
from app.shared.ids import new_uuid


class PostMatch:
    def __init__(
        self,
        matches: MatchRepository,
        clubs: ClubRepository,
        holds: ResolveCourtHold,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._matches = matches
        self._clubs = clubs
        self._holds = holds
        self._uow = uow
        self._clock = clock

    async def execute(self, command: PostMatchCommand) -> Match:
        club = await self._clubs.get(command.club_id)
        if club is None:
            raise ClubNotFound()
        # Raises `CategoryNotFound` if the club has no such category — the
        # club's own answer, rather than a foreign key failing three frames
        # later with nothing to tell a player.
        club.category(command.category_id)

        at = instant(self._clock.now())
        match = Match.post(
            match_id=new_uuid(),
            club_id=command.club_id,
            category_id=command.category_id,
            sport=command.sport,
            start=command.start,
            duration=command.duration,
            share=command.share,
            policy=club.policy_now.hold_policy(),
            at=at,
            counted=command.counted,
            kind=command.kind,
            pay_model=command.pay_model,
            open_seats=command.open_seats,
        )
        await self._holds.apply(match, at=at)
        stored = await self._matches.add(match)
        await self._uow.commit()
        return stored
