"""``AtStakeQuery``, real at last — the rating engine's own rule, read forward.

**The matcher does not compute this and this class does not either.** It reads two
Levels through ``rating``'s narrow read port and hands them to
``engines/racketskill/results.stakes``, which is the same function that moves a
Level when the game is actually played. That identity is the whole point of the
port: a card promising ``+0,07`` and an update delivering something else would be
the explainability failure ``docs/adr/0098`` and ``docs/adr/0139`` both exist to
prevent, and it is not a state two callers of one function can reach.

**A ``None`` here means one thing and it is measured.** Either party unrated in
this sport is *we have nothing to price this against*, and the card omits the
block — never a pair of zeros, which would claim a counted game against this
opponent moves the searcher's Level by nothing.

**It prices the pairing it is showing you.** In a doubles sport the game will be a
four and the other two seats are unknown when the card is drawn, so the figure is
read as *you against this person* with that sport's own share applied — the same
weighting the real result will carry. What it cannot know is who the partners turn
out to be, and averaging against an imaginary one would be inventing the very
thing the read has no basis for.

**Cost.** One stream replay per player, memoised for the life of the adapter — one
request — so a shortlist of twenty pays twenty-one reads rather than forty. The
searcher is read once because every row asks about the same one.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.engines.racketskill.core import SkillEstimate
from app.engines.racketskill.update_v1 import information_share, stakes
from app.kernel import Sport
from app.modules.matchmaking.domain.ports import AtStake
from app.modules.rating.domain.ports import RatedPlayerQuery


@final
class RatingResultUpdateRule:
    """``AtStakeQuery`` over ``rating``'s Levels and its own update rule."""

    def __init__(self, ratings: RatedPlayerQuery) -> None:
        self._ratings = ratings
        self._known: dict[tuple[UUID, Sport], SkillEstimate | None] = {}

    async def counted_game_deltas(
        self, *, searcher_id: UUID, opponent_id: UUID, sport: Sport
    ) -> AtStake | None:
        searcher = await self._estimate(searcher_id, sport)
        opponent = await self._estimate(opponent_id, sport)
        if searcher is None or opponent is None:
            return None

        at_stake = stakes(
            player=searcher,
            opposition=opponent,
            share=information_share(sport),
        )
        # Constructed rather than trusted: the invariant is asserted in two
        # places on purpose, once where the pair is produced and once where it
        # crosses into the matcher, because the two would be the same assertion
        # only for as long as nothing sat between them.
        return AtStake(win_delta=at_stake.win, loss_delta=at_stake.loss)

    async def _estimate(
        self, player_id: UUID, sport: Sport
    ) -> SkillEstimate | None:
        key = (player_id, sport)
        if key not in self._known:
            found = await self._ratings.estimates_for([player_id], sport=sport)
            self._known[key] = found.get(player_id)
        return self._known[key]


__all__ = ["RatingResultUpdateRule"]
