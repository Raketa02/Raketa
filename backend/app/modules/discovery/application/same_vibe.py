"""*Same vibe players*' two reads: **the row** on Home, and **See all**
(``docs/adr/0204`` §6, §7, §10; the home-rows mechanics §8, §9; #795).

**Worked out on each read** (call 11): the directory's tags are counted against
the reader's in SQL, most in common first, and who is connected, who is
blocked and a link to each face are asked live of their owners. **Skill plays
no part**: no level is read, so a reader with none sees the row too (Q14) —
only See all's sport filter and its pill read the current levels.

**The row reads the order a batch at a time** and asks Friends about each
batch, until §9's rule is full: ten fresh, or ten in all once a card below two
shared tags has come. A reader whose friends crowd the top reads a batch more,
and nobody reads the whole crowd.

**Every candidate list leaves out** the reader, everybody the reader blocked or
who blocked the reader, players with *Show me to new people* off, accounts that
don't play and accounts that are gone (``docs/adr/0204`` §10): the directory's
``alike`` holds all but the reader and the blocks, which are handed to it.

**A rested player is a gap** (#796; ``rest``): the rest count is asked once a
batch, about the cards that could be fresh — good matches the reader is not
connected with — and nobody else, since a rest changes nothing for them. See
all rests nobody.

**The row's total** (#812; ``totals``) is everybody sharing a tag, counted by
the first batch's own pass over the tag rows — read from the top, so what it
lists is everybody — and never by a second pass or by reading more batches.
A later batch, and See all, count nothing.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import Sport, invariant
from app.modules.discovery.application.on_screen import rested_among
from app.modules.discovery.domain.ports import (
    BlocksEitherWay,
    DirectoryFaces,
    PlayerDirectory,
    ReadersRelations,
    RestCount,
)
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.rest import OnScreenRow
from app.modules.discovery.domain.same_vibe import (
    A_PAGE,
    ON_THE_ROW,
    RowOfTen,
    VibeKey,
    VibePlayer,
)
from app.modules.discovery.domain.totals import capped

#: How many cards the row reads in order at a time — one statement, and one
#: question to Friends, each. Two rows' worth, so a reader with a friend or two
#: near the top still reads once.
A_BATCH: Final = 2 * ON_THE_ROW


@final
@dataclass(frozen=True, slots=True)
class SameVibeCard:
    """One pale tile: the face, the vibe %, the tags in common, and the
    reader's round friend button."""

    player_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    vibe_percent: int
    #: The tags both hold, in the vocabulary's order — the green chips.
    shared_tags: tuple[str, ...]
    relation: Relation

    @property
    def in_common(self) -> int:
        return len(self.shared_tags)


@final
@dataclass(frozen=True, slots=True)
class SameVibeRow:
    cards: tuple[SameVibeCard, ...]
    #: How many the row could show, counted up to 100 (``totals``).
    total: int


@final
@dataclass(frozen=True, slots=True)
class SameVibePage:
    cards: tuple[SameVibeCard, ...]
    #: Where the next page starts; ``None`` on the last.
    next: VibeKey | None
    #: Every sport at least one listed player holds a level in — the pill.
    sports: tuple[Sport, ...]


@final
class _Cards:
    """What both reads hand the screen, built the same way."""

    def __init__(self, *, relations: ReadersRelations, faces: DirectoryFaces) -> None:
        self._relations = relations
        self._faces = faces

    async def relations_of(
        self, reader: UUID, players: Sequence[VibePlayer]
    ) -> Mapping[UUID, Relation]:
        if not players:
            return {}
        return await self._relations.relations_of(
            reader, [one.player_id for one in players]
        )

    async def of(
        self, players: Sequence[VibePlayer], relations: Mapping[UUID, Relation]
    ) -> tuple[SameVibeCard, ...]:
        cards = []
        for one in players:
            cards.append(
                SameVibeCard(
                    player_id=one.player_id,
                    nickname=one.nickname,
                    photo_id=one.photo_id,
                    photo_url=(
                        None
                        if one.photo_id is None
                        else await self._faces.photo_url(one.player_id, one.photo_id)
                    ),
                    vibe_percent=one.percent,
                    shared_tags=one.shared_tags,
                    relation=relations.get(one.player_id, Relation.NONE),
                )
            )
        return tuple(cards)


@final
class ReadSameVibe:
    """Home's row: ten cards, fresh good matches first, then the gaps."""

    def __init__(
        self,
        *,
        directory: PlayerDirectory,
        blocks: BlocksEitherWay,
        relations: ReadersRelations,
        rests: RestCount,
        faces: DirectoryFaces,
    ) -> None:
        self._directory = directory
        self._blocks = blocks
        self._rests = rests
        self._cards = _Cards(relations=relations, faces=faces)

    async def execute(self, reader: UUID) -> SameVibeRow:
        mine = await self._directory.tags_of(reader)
        if not mine:
            return SameVibeRow(cards=(), total=0)
        leaving_out = {reader, *await self._blocks.either_way(reader)}
        row = RowOfTen()
        relations: dict[UUID, Relation] = {}
        # The first batch is read from the top, so what it lists is everybody
        # sharing a tag: it alone counts, in its own pass.
        first = await self._directory.alike(
            mine,
            leaving_out=leaving_out,
            sport=None,
            after=None,
            limit=A_BATCH,
            counting=True,
        )
        everybody = invariant(first.listed, "a counted batch says how many it lists")
        batch = first.players
        while True:
            relations.update(await self._cards.relations_of(reader, batch))
            rested = await rested_among(
                self._rests,
                reader,
                OnScreenRow.SAME_VIBE,
                [
                    one.player_id
                    for one in batch
                    if row.may_be_fresh(one, relation=relations[one.player_id])
                ],
            )
            for one in batch:
                if row.full:
                    break
                row.take(
                    one,
                    relation=relations[one.player_id],
                    rested=one.player_id in rested,
                )
            if row.full or len(batch) < A_BATCH:
                break
            batch = (
                await self._directory.alike(
                    mine,
                    leaving_out=leaving_out,
                    sport=None,
                    after=batch[-1].key,
                    limit=A_BATCH,
                )
            ).players
        return SameVibeRow(
            cards=await self._cards.of(row.row(), relations), total=capped(everybody)
        )


@final
class ReadSameVibePage:
    """See all: everybody sharing a tag, most in common first, friends where
    they fall — those holding a level in one sport, when a sport is asked."""

    def __init__(
        self,
        *,
        directory: PlayerDirectory,
        blocks: BlocksEitherWay,
        relations: ReadersRelations,
        faces: DirectoryFaces,
    ) -> None:
        self._directory = directory
        self._blocks = blocks
        self._cards = _Cards(relations=relations, faces=faces)

    async def execute(
        self, reader: UUID, *, sport: Sport | None, after: VibeKey | None
    ) -> SameVibePage:
        mine = await self._directory.tags_of(reader)
        if not mine:
            return SameVibePage(cards=(), next=None, sports=())
        leaving_out = {reader, *await self._blocks.either_way(reader)}
        found = (
            await self._directory.alike(
                mine,
                leaving_out=leaving_out,
                sport=sport,
                after=after,
                limit=A_PAGE + 1,
            )
        ).players
        shown = found[:A_PAGE]
        return SameVibePage(
            cards=await self._cards.of(
                shown, await self._cards.relations_of(reader, shown)
            ),
            next=shown[-1].key if len(found) > A_PAGE else None,
            sports=await self._directory.sports_alike(mine, leaving_out=leaving_out),
        )
