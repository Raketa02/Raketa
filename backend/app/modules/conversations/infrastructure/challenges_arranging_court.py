"""``ArrangingCourt``, answered by the ``challenges`` context.

**Half of *one rule read against two records*.** It answers about accepted seats
and nothing else: not who was invited, not who declined, and never a standing —
a standing is a fold over somebody else's seats and this context has no business
performing one.

**It reads through ``ChallengeRepository`` and ``ChallengeDirectory`` rather than
a query port of its own**, on ``games_settled_game.py``'s argument one arrow over:
the joins already exist there, and a second read declaring the same join would be
a second place for *who is on this court* to be true.

**A seat is accepted or it is not, and the clock does not enter into it.** A
seat's *lapse* is folded against a clock, but an acceptance is a thing somebody
did; membership is *the people who have agreed to be on this court right now*,
and somebody who accepted has not un-agreed by anybody else's window closing.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.kernel import Sport
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.ports import (
    ChallengeDirectory,
    ChallengeRepository,
)


@final
class ChallengesArrangingCourt:
    """*Who has agreed to be on this challenge's court?*"""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        directory: ChallengeDirectory,
    ) -> None:
        self._challenges = challenges
        self._directory = directory

    async def accepted_on(
        self, challenge_ids: Collection[UUID]
    ) -> Mapping[UUID, frozenset[UUID]]:
        courts: dict[UUID, frozenset[UUID]] = {}
        for challenge_id in sorted(set(challenge_ids)):
            challenge = await self._challenges.load(challenge_id)
            if challenge is None:
                continue
            courts[challenge_id] = _accepted(challenge)
        return courts

    async def accepted_by(self, player_id: UUID) -> frozenset[UUID]:
        return frozenset(
            challenge.challenge_id
            for challenge in await self._directory.seating(player_id)
            if player_id in _accepted(challenge)
        )

    async def sport_of(self, challenge_id: UUID) -> Sport | None:
        challenge = await self._challenges.load(challenge_id)
        return None if challenge is None else challenge.sport


def _accepted(challenge: Challenge) -> frozenset[UUID]:
    """Everybody on this court through a seat they said yes to.

    Folded here rather than asked of ``Challenge``, deliberately: an accessor on
    that aggregate would be a fact ``challenges`` published for one foreign
    reader's convenience, and this context is the one that calls the set
    *membership*. It is ``fill_seats``' own ``_live_on`` one context over — the
    same seats, read for a different question.
    """

    return frozenset(
        seat.player_id
        for seat in challenge.seats
        if seat.player_id is not None and seat.is_accepted()
    )
