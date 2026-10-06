"""``AtStakeQuery``, real — the rating engine's own rule, read forward.

**The matcher does not compute this and this class does not either.** It reads
Levels through ``rating``'s narrow read port and hands them to
``engines/racketskill/results.stakes``, which is the same function that moves a
Level when the game is actually played. That identity is the whole point of the
port: a screen promising ``+0,07`` and an update delivering something else would
be the explainability failure ``docs/adr/0098`` and ``docs/adr/0139`` both exist
to prevent, and it is not a state two callers of one function can reach.

**It prices a court the way the result will be priced** (``docs/adr/0161``). A
booked game's line-up is frozen, so nothing is unknown, and the read here is
``settle_results.py``'s own arithmetic run forward, **including what it does
about an unrated seat**: each side is folded to one player by ``one_side`` over
the people on it who hold a rating, the pair is read off that, and it is the
same pair for everybody on the side. A side nobody on it is rated in is nothing
to price against, and a reader with no Level has nothing to move — those two are
the absences, and a court with one unrated seat beside a rated one is priced
against the rated one alone, because that is exactly what the update will do.

**A ``None`` here is measured** — never a pair of zeros, which would claim a
counted game moves the reader's Level by nothing. The head-to-head read a search
card drew, *you against this person*, went with the searches (#579).

**Cost.** One stream replay per player, memoised for the life of the adapter —
one request.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from app.engines.racketskill.core import SkillEstimate
from app.engines.racketskill.update_v1 import information_share, one_side, stakes
from app.kernel import Sport, invariant
from app.modules.matchmaking.domain.ports import AtStake
from app.modules.rating.domain.ports import RatedPlayerQuery


@final
class RatingResultUpdateRule:
    """``AtStakeQuery`` over ``rating``'s Levels and its own update rule."""

    def __init__(self, ratings: RatedPlayerQuery) -> None:
        self._ratings = ratings
        self._known: dict[tuple[UUID, Sport], SkillEstimate | None] = {}

    async def counted_game_deltas_on_court(
        self,
        *,
        player_id: UUID,
        own_side: Collection[UUID],
        opposing_side: Collection[UUID],
        sport: Sport,
    ) -> AtStake | None:
        invariant(
            player_id in own_side,
            "a court priced for somebody who is not on the side it is priced from",
        )
        if await self._estimate(player_id, sport) is None:
            # Nothing to move: the pair is a claim about this player's Level.
            return None
        ours = await self._side(own_side, sport)
        theirs = await self._side(opposing_side, sport)
        if ours is None or theirs is None:
            return None
        at_stake = stakes(
            player=ours, opposition=theirs, share=information_share(sport)
        )
        # Constructed rather than trusted: the invariant is asserted in two
        # places on purpose, once where the pair is produced and once where it
        # crosses into the matcher, because the two would be the same assertion
        # only for as long as nothing sat between them.
        return AtStake(win_delta=at_stake.win, loss_delta=at_stake.loss)

    async def _side(
        self, player_ids: Collection[UUID], sport: Sport
    ) -> SkillEstimate | None:
        """One side as one player, over whoever on it holds a rating.

        ``None`` for a side nobody on it is rated in — *there is nothing to
        price the other side against*, in ``settle_results``' own words — and
        the rated members' fold otherwise, which is the fold the update makes.

        **Walked sorted**, so the fold is the same fold on every process
        (``docs/adr/0105``) — and so the side is the same side however a caller
        happened to list it.
        """

        estimates = [
            estimate
            for one in sorted(set(player_ids))
            if (estimate := await self._estimate(one, sport)) is not None
        ]
        return one_side(estimates) if estimates else None

    async def _estimate(
        self, player_id: UUID, sport: Sport
    ) -> SkillEstimate | None:
        key = (player_id, sport)
        if key not in self._known:
            found = await self._ratings.estimates_for([player_id], sport=sport)
            self._known[key] = found.get(player_id)
        return self._known[key]


__all__ = ["RatingResultUpdateRule"]
