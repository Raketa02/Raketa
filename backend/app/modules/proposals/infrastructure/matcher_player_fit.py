"""``PlayerFit`` by **the matcher's own pair rule**, never a copy of it.

Every pair on a court is held to four things, and only four — the mask the old
line-ups enumerated under (``docs/adr/0116``): **no block** either way, **mutual
gender preference**, **Levels within the kind's window** — the ruleset's
``level_tolerance`` for the kind, narrowed to the competitive one while either
player is new (``docs/adr/0113``) — and, since #661, **the reliability filter**
both ways: neither player's minimum above the other's band, *New* passing every
minimum (``docs/adr/0195`` §6). This adapter asks exactly those, through three
pure functions — ``player_profile``'s mutual preference, the matcher's level
window (``matchmaking/domain/level_window.py``) and the engine's
``passes_reliability_minimum`` — over the live ruleset, so a proposal, a fill and
a rescue cannot come to two answers about one pair.

**Live facts, read now**: the blocks off the log, each person's gender, their
preference, their filter and when their profile was made off their own stream,
their Level in the sport off rating's published read, and — only where somebody
among them has a filter on — everybody's points off ``player_score``'s. **Each
person's points are folded at most once per deal**: at one instant this adapter
remembers whose it has read, so a deck read that asks for its cards, the
reader's rescues and then the whole pool folds nobody twice, and
``unfit_pairs_by_kind`` serves every kind with one reading. The composition root
builds it per request and per job run, and another instant reads afresh. Never a
projection that may be a tick behind a block.

**A yes already given is asked without the filter** (``reliability_filter=False``):
the fill's re-check and a paused yes coming back. The filter acts on what is
dealt and joined from then on, so switching it on — or dropping below somebody's
— takes nobody out of a game they chose.

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

from collections.abc import Collection, Mapping, Sequence
from itertools import combinations
from typing import final
from uuid import UUID

from app.engines.matchfit.core import SearchMode, passes_reliability_minimum
from app.engines.matchfit.ruleset import Ruleset
from app.kernel import Instant, Sport
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.domain.level_window import (
    level_close_enough,
    level_tolerance,
)
from app.modules.player_profile.domain.mutual_preference import (
    preferences_are_mutual,
)
from app.modules.player_profile.domain.ports import PlayerProfileRepository
from app.modules.player_profile.domain.profile import PlayerProfile
from app.modules.player_score.domain.points import PlayerScore
from app.modules.player_score.domain.ports import PublishedScoreQuery
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
        scores: PublishedScoreQuery,
    ) -> None:
        self._blocks = blocks
        self._profiles = profiles
        self._ratings = ratings
        self._ruleset = ruleset
        self._scores = scores
        #: Whose points were folded at ``_read_at`` — this deal's, and no other.
        self._read: dict[UUID, PlayerScore] = {}
        self._read_at: Instant | None = None

    async def unfit_pairs(
        self,
        player_ids: Collection[UUID],
        *,
        sport: Sport,
        kind: SearchMode,
        at: Instant,
        reliability_filter: bool = True,
    ) -> frozenset[frozenset[UUID]]:
        unfit = await self._unfit(
            player_ids,
            sport=sport,
            kinds=(kind,),
            at=at,
            reliability_filter=reliability_filter,
        )
        return unfit[kind]

    async def unfit_pairs_by_kind(
        self,
        player_ids: Collection[UUID],
        *,
        sport: Sport,
        kinds: Sequence[SearchMode],
        at: Instant,
        reliability_filter: bool = True,
    ) -> Mapping[SearchMode, frozenset[frozenset[UUID]]]:
        return await self._unfit(
            player_ids,
            sport=sport,
            kinds=kinds,
            at=at,
            reliability_filter=reliability_filter,
        )

    async def _unfit(
        self,
        player_ids: Collection[UUID],
        *,
        sport: Sport,
        kinds: Sequence[SearchMode],
        at: Instant,
        reliability_filter: bool,
    ) -> dict[SearchMode, frozenset[frozenset[UUID]]]:
        """Every read once, then each kind's pairs — the kinds differ only in
        the level window's tolerance."""

        people = tuple(dict.fromkeys(player_ids))
        if len(people) < 2 or not kinds:
            return {kind: frozenset() for kind in kinds}
        blocked = await self._blocks.blocked_pairs_among(people)
        profiles: dict[UUID, PlayerProfile | None] = {
            person: await self._profiles.load(person) for person in people
        }
        levels = await self._ratings.estimates_for(people, sport=sport)
        filtered = (
            await self._kept_apart_by_reliability(profiles, at=at)
            if reliability_filter
            else frozenset()
        )
        unfit: dict[SearchMode, set[frozenset[UUID]]] = {kind: set() for kind in kinds}
        for one, other in combinations(people, 2):
            pair = frozenset((one, other))
            mine, theirs = profiles[one], profiles[other]
            my_level, their_level = levels.get(one), levels.get(other)
            if (
                pair in blocked
                or pair in filtered
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
            ):
                for kind in kinds:
                    unfit[kind].add(pair)
                continue
            for kind in kinds:
                if not level_close_enough(
                    mu_a=my_level.mu,
                    mu_b=their_level.mu,
                    a_created_at=mine.created_at,
                    b_created_at=theirs.created_at,
                    mode=kind,
                    ruleset=self._ruleset,
                    now=at,
                ):
                    unfit[kind].add(pair)
        return {kind: frozenset(pairs) for kind, pairs in unfit.items()}

    async def _kept_apart_by_reliability(
        self, profiles: Mapping[UUID, PlayerProfile | None], *, at: Instant
    ) -> frozenset[frozenset[UUID]]:
        """The pairs either of whose filter the other's band does not pass.
        **Nobody's points are read unless somebody here has a filter on**, and
        then everybody's, once."""

        minimums = {
            person: profile.reliability_minimum
            for person, profile in profiles.items()
            if profile is not None
        }
        if not any(minimums.values()):
            return frozenset()
        scores = await self._points_of(list(minimums), at=at)

        def passes(minimum_of: UUID, score: PlayerScore) -> bool:
            return passes_reliability_minimum(
                minimums[minimum_of], band=score.band, is_new=score.is_new
            )

        return frozenset(
            frozenset((one, other))
            for one, other in combinations(minimums, 2)
            if not passes(one, scores[other]) or not passes(other, scores[one])
        )

    async def _points_of(
        self, people: Sequence[UUID], *, at: Instant
    ) -> Mapping[UUID, PlayerScore]:
        """Their points at ``at``, folding only those not folded at it yet."""

        if at != self._read_at:
            self._read, self._read_at = {}, at
        unread = [person for person in people if person not in self._read]
        if unread:
            self._read.update(await self._scores.scores_for(unread, now=at))
        return {person: self._read[person] for person in people}

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
