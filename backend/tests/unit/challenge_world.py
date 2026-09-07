"""The doubles a send is exercised against, in one place.

Every collaborator here is a **hand-written stub implementing the port**, which is
this suite's rule for a port with no adapter worth running in a unit test. Two of
them are more than that and say so: ``StubBlocks`` can be told to raise, because a
gate that cannot be evaluated is half of what fail-closed means, and
``StubProfiles`` can simply not hold somebody, because a court is built out of an
index whose rows outlive the profiles they were folded from.

**Everybody is admissible until a test says otherwise.** A fixture whose default
was *refused* would make every green assertion here an accident.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.challenges.application.court_safety import CourtSafety
from app.modules.challenges.domain.ports import CourtOrigin
from app.modules.player_profile.domain.availability import Window
from app.modules.player_profile.domain.gender import Gender, GenderPreference


@dataclass
class StubBlocks:
    """The pairwise mask, and the outage that must not read as an empty one."""

    pairs: set[frozenset[UUID]] | None = None
    unavailable: bool = False

    async def blocked_pairs_among(
        self, player_ids: Collection[UUID]
    ) -> frozenset[frozenset[UUID]]:
        if self.unavailable:
            raise BlockStateUnavailable("the block mask could not be read")
        wanted = set(player_ids)
        return frozenset(
            pair for pair in (self.pairs or set()) if pair <= wanted
        )

    async def exclusions_for(self, player_id: UUID) -> frozenset[UUID]:
        return frozenset(
            other
            for pair in (self.pairs or set())
            if player_id in pair
            for other in pair
            if other != player_id
        )

    async def blocked_between(self, first: UUID, second: UUID) -> bool:
        return frozenset({first, second}) in (self.pairs or set())


@dataclass
class StubHolds:
    held: frozenset[UUID] = frozenset()

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        return self.held & frozenset(player_ids)


@dataclass
class StubAccounts:
    disabled: frozenset[UUID] = frozenset()

    async def find_disabled_among(
        self, user_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        return self.disabled & frozenset(user_ids)


@dataclass(frozen=True)
class StubProfile:
    """The two fields the mutual gate reads, and nothing else.

    A whole ``PlayerProfile`` would drag a commit, a location and a grid into a
    test about a gender preference, and none of that is what the gate reads.
    """

    gender: Gender | None
    gender_preference: GenderPreference


@dataclass
class StubProfiles:
    profiles: dict[UUID, StubProfile] | None = None

    async def load(self, player_id: UUID) -> StubProfile | None:
        return (self.profiles or {}).get(player_id)


@dataclass
class StubOrigins:
    """The search a court claims to have come from.

    ``known`` is the set of searches this stand-in will place people from; a
    search outside it answers ``None``, which is the four-cases-one-code refusal
    the real adapter makes.
    """

    known: set[UUID]
    sport: Sport = Sport.PADEL
    mode: SearchMode | None = SearchMode.FOR_FUN
    window: Window = Window.WEEKEND

    async def court_origin(
        self,
        *,
        search_id: UUID,
        organiser_id: UUID,
        invitee_ids: Collection[UUID],
    ) -> CourtOrigin | None:
        if search_id not in self.known:
            return None
        return CourtOrigin(
            sport=self.sport,
            mode=self.mode,
            window=self.window,
            positions=_positions(invitee_ids),
        )


def _positions(invitee_ids: Collection[UUID]) -> Mapping[UUID, int]:
    return {
        player_id: position
        for position, player_id in enumerate(sorted(invitee_ids), start=1)
    }


def everybody_admissible(players: Collection[UUID]) -> dict[UUID, StubProfile]:
    """A profile per player, all of them asking for anybody.

    ``ANY`` on both sides is the pair that never reads a gender at all, which is
    what makes a test about a *block* a test about a block.
    """

    return {
        player_id: StubProfile(
            gender=Gender.WOMAN, gender_preference=GenderPreference.ANY
        )
        for player_id in players
    }


def a_safe_court(
    players: Collection[UUID],
    *,
    blocks: StubBlocks | None = None,
    holds: StubHolds | None = None,
    accounts: StubAccounts | None = None,
    profiles: StubProfiles | None = None,
) -> CourtSafety:
    """``CourtSafety`` over stubs that admit everybody unless told otherwise."""

    return CourtSafety(
        blocks=blocks or StubBlocks(),
        holds=holds or StubHolds(),
        accounts=accounts or StubAccounts(),
        profiles=profiles or StubProfiles(everybody_admissible(players)),
    )
