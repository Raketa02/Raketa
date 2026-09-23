"""``SettledGameQuery``, answered by the ``games`` context.

The sibling of ``games_planned_game.py`` and the second method on the one arrow
that already ran this way. That one hands over an arrangement and learns back an
id; this one hands the id back and learns one word — *settled*. Neither context
learns the other's aggregates, and the composition root stays the only place that
decides who answers.

**It reads through ``GameRepository`` rather than a query port, because the join
already exists there.** ``for_challenge`` was built to make the opening
idempotent inside the accept's own transaction — *has this challenge already
opened a game* — and *has the game it opened settled* is the same lookup with a
standing folded on the end. A second read declaring the same join would be a
second place for *one arrangement is one game* to be true.

**It translates a standing into a boolean and nothing else.** ``SETTLED`` is
``games``' own set and stays there; what crosses this seam is which of the ids
the caller asked about are finished with. In particular the **three** settled
standings do not cross — a mutual mint has no use for the difference between a
confirmed score, an unscored evening and a game nobody ever said happened, and a
caller given the difference would eventually act on it.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.ports import GameRepository
from app.modules.games.domain.standing import SETTLED


@final
class GamesSettledGame:
    """*Which of these arrangements is nothing more going to happen to?*"""

    def __init__(self, games: GameRepository) -> None:
        self._games = games

    async def settled_among(
        self, challenge_ids: Collection[UUID], *, now: Instant
    ) -> frozenset[UUID]:
        """The subset whose game has settled — **and a raise is left to travel.**

        A read that could not answer must not come back as *none of these have
        settled*, which reads as *hold them all* and is a refusal nobody decided.
        The mint catches it and refuses the mint instead, which is the same
        outcome arrived at deliberately and in the one place that knows the
        refusal is silent (``docs/adr/0152`` §6).

        **The port is bulk; this implementation of it is a walk, and the
        difference is deliberate.** ``games`` offers one join and it is per
        challenge, so the loop is here rather than in the caller — which is the
        whole point of the set-shaped port: the cost is one adapter's to pay and
        one adapter's to fix, and the day it becomes a single statement nothing
        above this line moves. What it walks is one pair's mutual-born challenges
        in one sport, which is one until the first has settled and a second has
        been minted.
        """

        settled: set[UUID] = set()
        # Sorted, so that the reads happen in the same order on every process
        # and under every ``PYTHONHASHSEED`` (``docs/adr/0105``).
        for challenge_id in sorted(set(challenge_ids)):
            game = await self._games.for_challenge(challenge_id)
            if game is not None and game.standing_at(now) in SETTLED:
                settled.add(challenge_id)
        return frozenset(settled)
