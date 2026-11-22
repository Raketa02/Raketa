"""``PlayedWith`` over the games' record and Friends (``docs/adr/0207`` §3,
#831): **who among these people is no new face to whom**.

Two facts, each its owner's, read through each owner's own published read:

- **played a game together** — Games' ``PlayedTogetherQuery``, the court of a
  game played by ``now`` (``Game.was_played_at``), one read for everybody asked
  however many games they share;
- **friends** — Friends' ``ReadRelations.friends_among``, **from each person's
  own side**, as every face reads it: Friends has no question about two other
  people (``friends.md``), and this is no reason to give it one. A friendship
  is on both sides, so each person is asked only about the people nobody asked
  about them yet: at most one statement per person in ``players`` — in a job,
  the members a For-fun table could hold, beside the week and the Games &
  money the proposer already reads per member; on a deck read, the three still
  on a For-fun rescue offered to more than it is dealt to.

**What crosses back is pairs and nothing more**: no game, no sport, no date,
no relation but *known*. The answer builds a For-fun table and is never shown.
"""

from __future__ import annotations

from collections.abc import Collection
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.modules.friends.application.reads import ReadRelations
from app.modules.games.domain.ports import PlayedTogetherQuery


@final
class GamesAndFriendsPlayedWith:
    def __init__(self, games: PlayedTogetherQuery, friends: ReadRelations) -> None:
        self._games = games
        self._friends = friends

    async def known_pairs(
        self, players: Collection[UUID], *, among: Collection[UUID], now: Instant
    ) -> frozenset[frozenset[UUID]]:
        askers, others = set(players), set(among)
        known = {
            pair
            for pair in await self._games.played_together_among(
                askers | others, now=now
            )
            if _between(pair, askers, others)
        }
        #: The askers asked about the people in ``others`` already.
        asked: set[UUID] = set()
        # In one order on every process, so the reads run alike (ADR-0105).
        for one in sorted(askers, key=str):
            # Asked about ``one`` already, if they are among ``others``.
            rest = others - {one} - (asked if one in others else set())
            asked.add(one)
            if rest:
                known.update(
                    frozenset((one, friend))
                    for friend in await self._friends.friends_among(one, rest)
                )
        return frozenset(known)


def _between(pair: frozenset[UUID], askers: set[UUID], others: set[UUID]) -> bool:
    """Whether a pair is one of ``askers`` and one of ``others``."""

    one, other = pair
    return (one in askers and other in others) or (other in askers and one in others)
