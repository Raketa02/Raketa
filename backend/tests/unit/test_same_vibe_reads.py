"""*Same vibe*'s two reads over hand-written stubs (#795): the row reads the
order a batch at a time and stops once §9's rule is full, and See all is a
page of the plain order with the next page's key. **A rested good match is a
gap** (#796), and the rest count is asked only about the cards that could be
fresh."""

from __future__ import annotations

from collections.abc import Collection, Mapping
from uuid import UUID

from app.kernel import Sport
from app.modules.discovery.application.same_vibe import (
    A_BATCH,
    ReadSameVibe,
    ReadSameVibePage,
)
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.rest import RESTS_AFTER, OnScreenRow
from app.modules.discovery.domain.same_vibe import VibeKey, VibePlayer, vibe_player

READER = UUID(int=10**6)
MINE = frozenset({"A", "B", "C", "D", "E", "F"})


class StandInDirectory:
    """``alike`` over a list, in the order, with every call recorded."""

    def __init__(self, players: list[VibePlayer]) -> None:
        self._players = sorted(players, key=lambda one: one.key.order)
        self.asked: list[tuple[VibeKey | None, int]] = []

    async def tags_of(self, player_id: UUID) -> frozenset[str]:
        return MINE if player_id == READER else frozenset()

    async def alike(
        self,
        mine: frozenset[str],
        *,
        leaving_out: Collection[UUID],
        sport: Sport | None,
        after: VibeKey | None,
        limit: int,
    ) -> tuple[VibePlayer, ...]:
        self.asked.append((after, limit))
        behind = [
            one
            for one in self._players
            if one.player_id not in leaving_out
            and (after is None or one.key.is_behind(after))
        ]
        return tuple(behind[:limit])

    async def sports_alike(
        self, mine: frozenset[str], *, leaving_out: Collection[UUID]
    ) -> tuple[Sport, ...]:
        return (Sport.PADEL,)


class StandInRelations:
    def __init__(self, friends: set[UUID]) -> None:
        self._friends = friends
        self.asked: list[int] = []

    async def relations_of(
        self, reader: UUID, players: Collection[UUID]
    ) -> Mapping[UUID, Relation]:
        self.asked.append(len(players))
        return {
            one: Relation.FRIEND if one in self._friends else Relation.NONE
            for one in players
        }


class NoBlocks:
    async def either_way(self, reader: UUID) -> frozenset[UUID]:
        return frozenset()


class NoFaces:
    async def photo_url(self, player_id: UUID, photo_id: UUID) -> str:
        raise AssertionError("nobody here has a photograph")


class StandInRests:
    """The rest count of the reader's Same vibe row, every question recorded."""

    def __init__(self, rested: set[UUID] | None = None) -> None:
        self._rested = rested or set()
        self.asked: list[set[UUID]] = []

    async def came_on_screen(self, viewer, row, players, *, day) -> None:
        raise AssertionError("a read reports nothing")

    async def days_on_screen(
        self, viewer: UUID, row: OnScreenRow, players: Collection[UUID]
    ) -> Mapping[UUID, int]:
        assert (viewer, row) == (READER, OnScreenRow.SAME_VIBE)
        self.asked.append(set(players))
        return {one: RESTS_AFTER for one in players if one in self._rested}

    async def forget(self, player_id: UUID) -> None:
        raise AssertionError("a read forgets nothing")


def sharing(n: int, shared: int) -> VibePlayer:
    found = vibe_player(
        UUID(int=n), f"p{n}", None, sorted(MINE)[:shared] + ["X"], mine=MINE
    )
    assert found is not None
    return found


def the_row(directory, relations, rests=None) -> ReadSameVibe:
    return ReadSameVibe(
        directory=directory,
        blocks=NoBlocks(),
        relations=relations,
        rests=StandInRests() if rests is None else rests,
        faces=NoFaces(),
    )


async def test_friends_filling_the_first_batch_are_read_past_to_the_fresh():
    friends = [sharing(n, 6) for n in range(1, A_BATCH + 6)]
    strangers = [sharing(100 + n, 2) for n in range(3)]
    directory = StandInDirectory([*friends, *strangers])
    relations = StandInRelations({one.player_id for one in friends})

    cards = await the_row(directory, relations).execute(READER)

    assert [card.nickname for card in cards] == [
        *(one.nickname for one in strangers),
        *(one.nickname for one in friends[:7]),
    ]
    assert len(directory.asked) == 2
    assert directory.asked[1][0] == friends[A_BATCH - 1].key


async def test_one_batch_does_when_the_row_fills_inside_it():
    directory = StandInDirectory([sharing(n, 3) for n in range(1, 40)])
    relations = StandInRelations(set())

    cards = await the_row(directory, relations).execute(READER)

    assert len(cards) == 10
    assert directory.asked == [(None, A_BATCH)]
    assert relations.asked == [A_BATCH]


async def test_a_rested_match_waits_in_a_gap_behind_every_fresh_one():
    first, *others = [sharing(n, 6 - n % 3) for n in range(1, 15)]
    directory = StandInDirectory([first, *others])
    rests = StandInRests({first.player_id})

    cards = await the_row(directory, StandInRelations(set()), rests).execute(READER)

    assert first.player_id not in {card.player_id for card in cards}
    assert len(cards) == 10


async def test_only_cards_that_could_be_fresh_are_asked_about_their_rest():
    friend = sharing(1, 6)
    fresh = sharing(2, 3)
    weak = sharing(3, 1)
    directory = StandInDirectory([friend, fresh, weak])
    rests = StandInRests({fresh.player_id})

    cards = await the_row(
        directory, StandInRelations({friend.player_id}), rests
    ).execute(READER)

    assert rests.asked == [{fresh.player_id}]
    # Rested, the one fresh match is a gap: the three in the order.
    assert [card.nickname for card in cards] == ["p1", "p2", "p3"]


async def test_a_reader_with_no_tags_reads_nothing():
    directory = StandInDirectory([sharing(1, 3)])

    assert await the_row(directory, StandInRelations(set())).execute(UUID(int=1)) == ()
    assert directory.asked == []


async def test_see_all_is_a_page_and_the_key_behind_it():
    players = [sharing(n, 1 + n % 3) for n in range(1, 26)]
    directory = StandInDirectory(players)
    read = ReadSameVibePage(
        directory=directory,
        blocks=NoBlocks(),
        relations=StandInRelations(set()),
        faces=NoFaces(),
    )

    first = await read.execute(READER, sport=None, after=None)
    second = await read.execute(READER, sport=None, after=first.next)

    ordered = sorted(players, key=lambda one: one.key.order)
    assert [card.player_id for card in first.cards] == [
        one.player_id for one in ordered[:20]
    ]
    assert first.next == ordered[19].key
    assert [card.player_id for card in second.cards] == [
        one.player_id for one in ordered[20:]
    ]
    assert second.next is None
    assert first.sports == (Sport.PADEL,)
