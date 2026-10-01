"""``PlayerFit`` by **the matcher's own pair rule**, never a copy of it.

Today's engine holds every pair on a court to three things, and only three —
the mask a line-up enumerates under (``matchmaking/domain/lineups.py``,
``docs/adr/0116``): **no block** either way, **mutual gender preference**, and
**Levels within the kind's window** — the ruleset's ``level_tolerance`` for the
kind, narrowed to the competitive one while either player is new
(``docs/adr/0113``). This adapter asks exactly those, through the two pure
functions the matcher and the send already share, over the live ruleset; so a
proposal and a line-up cannot come to two answers about one pair.

**Live facts, read now**: the blocks off the log, each person's gender, their
preference and when their profile was made off their own stream, and their
Level in the sport off rating's published read — not the candidate index, which
is a searcher's picture and may be a tick behind a block.

**Fails closed.** A person with no profile, or no rating in the sport, fits
nobody: the level gate cannot be evaluated, and *a gate that cannot be evaluated
excludes*. A block read that cannot be answered **raises**
(``BlockStateUnavailable``) rather than calling every pair unfit, because
*unfit* would take a card away for good and an outage is not a verdict.

**And the window one person's level rule makes** (#546): the Levels somebody
beside them may hold — the same tolerance, through the same function, narrowed
while they are new — around their Level off the same read. A post's range
starts there, so a post cannot promise a level the pair rule would refuse.
"""

from __future__ import annotations

from collections.abc import Collection
from itertools import combinations
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.ruleset import Ruleset
from app.kernel import Instant, Sport
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.domain.gates import level_close_enough, level_tolerance
from app.modules.player_profile.domain.mutual_preference import (
    preferences_are_mutual,
)
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.proposals.domain.post import LevelRange
from app.modules.rating.domain.ports import RatedPlayerQuery


@final
class MatcherPlayerFit:
    def __init__(
        self,
        *,
        blocks: BlockQuery,
        profiles: PlayerProfileRepository,
        ratings: RatedPlayerQuery,
        ruleset: Ruleset,
    ) -> None:
        self._blocks = blocks
        self._profiles = profiles
        self._ratings = ratings
        self._ruleset = ruleset

    async def unfit_pairs(
        self,
        player_ids: Collection[UUID],
        *,
        sport: Sport,
        kind: SearchMode,
        at: Instant,
    ) -> frozenset[frozenset[UUID]]:
        people = tuple(dict.fromkeys(player_ids))
        if len(people) < 2:
            return frozenset()
        blocked = await self._blocks.blocked_pairs_among(people)
        profiles: dict[UUID, PlayerProfile | None] = {
            person: await self._profiles.load(person) for person in people
        }
        levels = await self._ratings.estimates_for(people, sport=sport)
        unfit: set[frozenset[UUID]] = set()
        for one, other in combinations(people, 2):
            pair = frozenset((one, other))
            mine, theirs = profiles[one], profiles[other]
            my_level, their_level = levels.get(one), levels.get(other)
            if (
                pair in blocked
                or mine is None
                or theirs is None
                or my_level is None
                or their_level is None
                or not preferences_are_mutual(
                    one_gender=mine.gender,
                    one_preference=mine.gender_preference,
                    other_gender=theirs.gender,
                    other_preference=theirs.gender_preference,
                )
                or not level_close_enough(
                    mu_a=my_level.mu,
                    mu_b=their_level.mu,
                    a_created_at=mine.created_at,
                    b_created_at=theirs.created_at,
                    mode=kind,
                    ruleset=self._ruleset,
                    now=at,
                )
            ):
                unfit.add(pair)
        return frozenset(unfit)

    async def level_window(
        self, player_id: UUID, *, sport: Sport, kind: SearchMode, at: Instant
    ) -> LevelRange | None:
        profile = await self._profiles.load(player_id)
        level = (await self._ratings.estimates_for([player_id], sport=sport)).get(
            player_id
        )
        if profile is None or level is None:
            return None
        return LevelRange.around(
            level.mu,
            tolerance=level_tolerance(
                mode=kind,
                ruleset=self._ruleset,
                now=at,
                created_at=(profile.created_at,),
            ),
        )
