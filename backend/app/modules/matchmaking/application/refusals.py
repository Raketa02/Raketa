"""The two refusals about *you* that more than one surface owes, written once.

A held account may not search, deal or reset a deck; a sport the player holds no
rating in has no Level to gate against and no deck to deal again. The deal
refuses both through the workbench, and *Show them again* refuses both without
it — a reset writes one moment and should not have to bind the candidate index
to say no — so the refusals live here, where both reach the same words and the
same port, rather than in two places free to drift.

**The hold is a demand and is read as one**: through :func:`read_demand`, so it
fails closed like every gate, on the posture ``FAIL_POSTURE`` declares for it.
"""

from __future__ import annotations

from uuid import UUID

from app.kernel import Sport
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.errors import SportNotRated
from app.modules.matchmaking.domain.ports import AccountHoldQuery
from app.modules.rating.domain.ports import SkillRatingRepository
from app.modules.rating.domain.skill_rating import SkillRating
from app.shared.domain.errors import AccountHeld


async def rated_in(
    ratings: SkillRatingRepository, *, player_id: UUID, sport: Sport
) -> SkillRating:
    """This player's rating in this sport, or the ``409`` that says there is none."""

    held = await ratings.find_all_for(player_id=player_id)
    rated = next((rating for rating in held if rating.sport is sport), None)
    if rated is None:
        raise SportNotRated(f"the player holds no rating for {sport.value}")
    return rated


async def refuse_a_held_player(holds: AccountHoldQuery, player_id: UUID) -> None:
    """**The hold points both ways.** A held player can still sign in, and can
    do nothing on a Play surface."""

    held = await read_demand(AccountHoldQuery, lambda: holds.held_among([player_id]))
    if player_id in held:
        raise AccountHeld("this account is under a hold")
