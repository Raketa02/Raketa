"""*Same competitive level*'s reads widen level windows rather than score the
whole crowd (#794) — **and must come to exactly what scoring everybody would**.

Random crowds, sure and unsure levels across the four sports, clamped at the
forecast's floor and ceiling: the row and every See all page, read through the
windows over an in-memory store that answers ``near`` as the SQL does, are held
to the brute force — every candidate compared, sorted, the row filled from the
whole order. The % is the matcher's own forecast.
"""

from __future__ import annotations

import random
from collections.abc import Collection, Mapping
from uuid import UUID

import pytest

from app.bootstrap.composition import build_how_even
from app.kernel import Sport
from app.modules.discovery.application.same_level import (
    ReadSameLevel,
    ReadSameLevelPage,
)
from app.modules.discovery.domain.levels import Band, CurrentLevel
from app.modules.discovery.domain.ports import Candidate
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.same_level import (
    SameLevelPlayer,
    RowOfTen,
    compared,
    same_level_player,
)

READER = UUID(int=0)
BAND = Band(name="Established", lower=2.7, upper=3.8)


class InMemoryLevels:
    """``PlayerLevels`` as the SQL answers it — the rings inclusive of their
    width and exclusive of the last one read."""

    def __init__(self, levels: list[CurrentLevel]) -> None:
        self._levels = levels
        self.windows_read = 0

    async def save(self, level: CurrentLevel) -> None:
        raise NotImplementedError

    async def of_player(self, player_id: UUID) -> Mapping[Sport, CurrentLevel]:
        return {one.sport: one for one in self._levels if one.player_id == player_id}

    async def near(
        self,
        around: Mapping[Sport, float],
        *,
        within: float | None,
        beyond: float | None,
        compared_in: Collection[Sport],
        leaving_out: Collection[UUID],
    ) -> tuple[Candidate, ...]:
        self.windows_read += 1

        def in_ring(level: CurrentLevel) -> bool:
            if level.sport not in around:
                return False
            mu = around[level.sport]
            inside = within is None or (mu - within <= level.mu <= mu + within)
            outside = beyond is None or (
                level.mu < mu - beyond or level.mu > mu + beyond
            )
            return inside and outside

        found = {
            one.player_id
            for one in self._levels
            if in_ring(one) and one.player_id not in leaving_out
        }
        return tuple(
            Candidate(
                player_id=player_id,
                nickname=f"p{player_id.int}",
                photo_id=None,
                levels=tuple(
                    one
                    for one in self._levels
                    if one.player_id == player_id and one.sport in compared_in
                ),
            )
            for player_id in sorted(found, key=lambda one: one.int)
        )

    async def least_doubt(self, sports: Collection[Sport]) -> Mapping[Sport, float]:
        least: dict[Sport, float] = {}
        for one in self._levels:
            if one.sport in sports:
                least[one.sport] = min(least.get(one.sport, one.sigma), one.sigma)
        return least

    async def shared_sports(
        self, sports: Collection[Sport], *, leaving_out: Collection[UUID]
    ) -> tuple[Sport, ...]:
        return tuple(
            sport
            for sport in Sport
            if sport in sports
            and any(
                one.sport is sport and one.player_id not in leaving_out
                for one in self._levels
            )
        )


class NoBlocks:
    async def either_way(self, reader: UUID) -> frozenset[UUID]:
        return frozenset()


class Relations:
    def __init__(self, relations: Mapping[UUID, Relation]) -> None:
        self._relations = relations

    async def relations_of(
        self, reader: UUID, players: Collection[UUID]
    ) -> Mapping[UUID, Relation]:
        return {one: self._relations.get(one, Relation.NONE) for one in players}


class Faces:
    async def photo_url(self, player_id: UUID, photo_id: UUID) -> str:
        return f"https://photos/{photo_id}"


def a_crowd(seed: int, size: int) -> tuple[list[CurrentLevel], dict[UUID, Relation]]:
    """The reader in two or three sports; everybody else in one to four, with
    levels bunched as two decimals — so ties in % and in gap are common — and
    doubt from a settled player's to a questionnaire's."""

    draw = random.Random(seed)
    # Half the crowds are a launch's — nobody sure — so the least doubt, not
    # a perfect certainty, is what bounds a window.
    doubts = (
        [0.0, 0.08, 0.13, 0.13, 0.3, 0.8, 0.9] if seed % 2 else [0.65, 0.7, 0.84, 0.98]
    )
    levels = [
        CurrentLevel(
            player_id=READER,
            sport=sport,
            mu=round(draw.uniform(1.5, 4.5), 2),
            sigma=draw.choice([0.08, 0.13, 0.3, 0.8]),
            band=BAND,
            results=0,
        )
        for sport in draw.sample(list(Sport), draw.choice([2, 3]))
    ]
    relations: dict[UUID, Relation] = {}
    for n in range(1, size + 1):
        player = UUID(int=n)
        for sport in draw.sample(list(Sport), draw.randint(1, 4)):
            levels.append(
                CurrentLevel(
                    player_id=player,
                    sport=sport,
                    mu=round(draw.uniform(1.0, 5.0), 2),
                    sigma=draw.choice(doubts),
                    band=BAND,
                    results=0,
                )
            )
        relations[player] = draw.choice(
            [Relation.NONE] * 6 + [Relation.FRIEND, Relation.SENT, Relation.ASKED_YOU]
        )
    return levels, relations


def best_first_by_brute_force(
    levels: list[CurrentLevel], in_sport: Sport | None
) -> list[SameLevelPlayer]:
    even = build_how_even()
    mine = {one.sport: one for one in levels if one.player_id == READER}
    players = {one.player_id for one in levels} - {READER}
    matches = [
        same_level_player(
            player,
            compared(
                mine,
                [one for one in levels if one.player_id == player],
                even.percent_even,
            ),
            in_sport=in_sport,
        )
        for player in players
    ]
    return sorted(
        (one for one in matches if one is not None), key=lambda one: one.key.order
    )


@pytest.mark.parametrize("seed", range(12))
async def test_every_see_all_page_is_the_brute_force_order(seed):
    levels, relations = a_crowd(seed, size=90)
    store = InMemoryLevels(levels)
    read = ReadSameLevelPage(
        levels=store,
        even=build_how_even(),
        blocks=NoBlocks(),
        relations=Relations(relations),
        faces=Faces(),
    )
    mine = {one.sport for one in levels if one.player_id == READER}

    for in_sport in [None, *mine]:
        walked = []
        after = None
        while True:
            page = await read.execute(READER, sport=in_sport, after=after)
            walked += page.cards
            if page.next is None:
                break
            after = page.next
        expected = best_first_by_brute_force(levels, in_sport)
        assert [(one.player_id, one.shown) for one in walked] == [
            (one.player_id, one.shown) for one in expected
        ]
        assert all(
            card.comparisons == player.comparisons
            for card, player in zip(walked, expected, strict=True)
        )


@pytest.mark.parametrize("seed", range(40))
async def test_the_row_is_the_brute_force_row(seed):
    levels, relations = a_crowd(seed, size=random.Random(seed).choice([5, 30, 200]))
    store = InMemoryLevels(levels)
    read = ReadSameLevel(
        levels=store,
        even=build_how_even(),
        blocks=NoBlocks(),
        relations=Relations(relations),
        faces=Faces(),
    )

    cards = await read.execute(READER)

    row = RowOfTen()
    for player in best_first_by_brute_force(levels, None):
        if row.full:
            break
        row.take(player, relation=relations[player.player_id], rested=False)
    assert [(card.player_id, card.shown) for card in cards] == [
        (player.player_id, player.shown) for player in row.row()
    ]
    assert [card.relation for card in cards] == [
        relations[card.player_id] for card in cards
    ]


async def test_a_crowd_around_the_reader_is_read_in_its_nearest_windows():
    """Four hundred sure players spread over the scale: the row of ten is
    settled long before the window takes in everybody."""

    draw = random.Random(7)
    levels = [
        CurrentLevel(
            player_id=READER,
            sport=Sport.PADEL,
            mu=2.71,
            sigma=0.13,
            band=BAND,
            results=9,
        )
    ] + [
        CurrentLevel(
            player_id=UUID(int=n),
            sport=Sport.PADEL,
            mu=round(draw.uniform(1.0, 5.0), 2),
            sigma=0.13,
            band=BAND,
            results=9,
        )
        for n in range(1, 401)
    ]
    store = InMemoryLevels(levels)
    read = ReadSameLevel(
        levels=store,
        even=build_how_even(),
        blocks=NoBlocks(),
        relations=Relations({}),
        faces=Faces(),
    )

    cards = await read.execute(READER)

    assert len(cards) == 10
    assert store.windows_read <= 4
