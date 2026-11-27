"""``ReadersStakes`` by **the booked game's own stakes function** (#833;
``docs/adr/0207`` §6).

A competitive game's details print *If you win / If you lose* before the reader
answers, and promise it is what applies once the game is booked. So the pair is
read exactly where a booked game's pairing reads it — the matcher's
``at_stake_on_the_court``: ``rating``'s result-update rule, through
``AtStakeQuery``, side against side, failing soft — over the reader's
version's evenest sides. Nothing here prices anything.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.matchmaking.application.at_stake import at_stake_on_the_court
from app.modules.matchmaking.domain.ports import AtStakeQuery
from app.modules.proposals.domain.deck import Sides
from app.modules.proposals.domain.ports import Stakes


@final
class MatcherReadersStakes:
    def __init__(self, at_stake: AtStakeQuery) -> None:
        self._at_stake = at_stake

    async def at_stake(
        self, reader: UUID, *, sides: Sides, sport: Sport
    ) -> Stakes | None:
        priced = await at_stake_on_the_court(
            self._at_stake,
            player_id=reader,
            own_side=sides.yours,
            opposing_side=sides.theirs,
            sport=sport,
        )
        if priced is None:
            return None
        return Stakes(win_delta=priced.win_delta, loss_delta=priced.loss_delta)


__all__ = ["MatcherReadersStakes"]
