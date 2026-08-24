"""``Results`` over the Matches aggregate.

The one file in Now that knows a result is a ``Score`` on a ``Match``, that
putting one up and agreeing with one are two methods on it, and that ADR-0048's
whole permission set is enforced there rather than here. Everything above it asks
in Now's words and is told nothing back: what the screen says afterwards comes
from re-reading the match, not from what this returned.

**It composes the existing write rather than reassembling it**, which is the
shape ``DeparturesThroughMatches`` and ``money.SeatsThroughMatches`` already take
over the same aggregate. ``Match.propose_score`` decides on its own whether a
score is an entry, a correction or a counter — the caller states a score and a
player, and never which of the three it thinks this is.

**No hold ladder here, and that is the difference from the departure adapter.**
Nothing about a result moves a seat, so no tier can be entered or left and there
is no court to give back: the ladder is asked on writes that change the roster,
and asking it on one that cannot would be a look with nothing to find.

**It does not commit.** The score, its announcement and the answer the route
composes afterwards close together or they do not close at all.
"""

from __future__ import annotations

from typing import Sequence
from uuid import UUID

from app.kernel import Instant

from app.modules.matches.domain.errors import MatchNotFound
from app.modules.matches.domain.ports import MatchRepository
from app.modules.matches.domain.score import Score, SetScore


class ResultsThroughMatches:
    """A score put on the table, and one agreed with."""

    def __init__(self, *, matches: MatchRepository) -> None:
        self._matches = matches

    async def propose(
        self,
        *,
        match_id: UUID,
        player_id: UUID,
        sets: Sequence[tuple[int, int]],
        at: Instant,
    ) -> None:
        match = await self._matches.get(match_id)
        if match is None:
            raise MatchNotFound()
        match.propose_score(
            Score(tuple(SetScore(side_a=a, side_b=b) for a, b in sets)),
            by=player_id,
            at=at,
        )
        await self._matches.save(match)

    async def accept(
        self, *, match_id: UUID, player_id: UUID, at: Instant
    ) -> None:
        match = await self._matches.get(match_id)
        if match is None:
            raise MatchNotFound()
        # `by` is who accepted, and the aggregate reads it for ADR-0048's
        # opposing-side rule. `None` there is the timekeeper's silence, and this
        # path can never produce one — a route always has somebody tapping.
        match.agree_result(at=at, by=player_id)
        await self._matches.save(match)
