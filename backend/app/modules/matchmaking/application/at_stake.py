"""What a counted result on a court would do to one player's Level — **one
reading, two readers** (#833; ``docs/adr/0207`` §6).

A booked game's pairing prints *If you win / If you lose* beside its forecast
(``GamesCourtPairing``, ``docs/adr/0161``), and a competitive game still
filling prints the same pair in its details, before the reader answers
(``proposals``' ``MatcherReadersStakes``). The second is a promise about the
first — *the stakes seen are the stakes that apply once booked* — so both read
it here, through this one function: ``rating``'s result-update rule read forward
over the court **side against side**, under the posture ``AtStakeQuery``
declared.

**It fails soft**, like every at-stake read: a Level store that cannot answer
costs the block and never the screen, so a failure is ``None``, the same
absence as *nothing to move* and *nothing to price against*.
"""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from app.kernel import Sport, invariant
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.ports import AtStake, AtStakeQuery


async def at_stake_on_the_court(
    at_stake: AtStakeQuery,
    *,
    player_id: UUID,
    own_side: Sequence[UUID],
    opposing_side: Sequence[UUID],
    sport: Sport,
) -> AtStake | None:
    """The pair a counted result on this court would deliver to ``player_id``,
    who stands on ``own_side`` — or ``None``, never a pair of zeros.

    **The court is handed to the rule in one order**, whoever asks: the player
    first, their partners sorted, the other side sorted (``docs/adr/0105``). A
    side is a set, and the rule folds it in the order it is walked, so two
    callers handing it one court in two orders could disagree in the last
    digit — and the details promise the booked game's pair, not one beside it.
    """

    invariant(player_id in own_side, "stakes for somebody not on their own side")
    ours = [player_id, *sorted(set(own_side) - {player_id})]
    theirs = sorted(opposing_side)
    return await read_demand(
        AtStakeQuery,
        lambda: at_stake.counted_game_deltas_on_court(
            player_id=player_id,
            own_side=ours,
            opposing_side=theirs,
            sport=sport,
        ),
        stood_down=None,
    )


__all__ = ["at_stake_on_the_court"]
