"""*New in Rakieta*'s two reads: **the row** on Home, and **See all**
(``docs/adr/0204`` §5, §10; the home-rows mechanics §7).

**Worked out on each read** (call 11): the directory lists who joined inside
the 30 days, and everything else — who is connected, every sport a joiner
holds a level in, a link to each face — is asked live of its owner. The clock
is read once per read, so the row and its *Joined …* lines agree.

**Every candidate list leaves out** the reader, everybody the reader blocked
or who blocked the reader, players with *Show me to new people* off, accounts
that don't play and accounts that are gone (``docs/adr/0204`` §10): the
directory's ``joiners`` holds all but the reader and the blocks, which are
handed to it.

**The row's total** (#812; ``totals``) is everybody new: the row itself when it
came back short of ten, and otherwise one count over the month, stopping at
100.

**See all reads every joiner's levels**, because its sport pill offers only
sports at least one joiner holds a level in, and a sport keeps only the
players rated in it: one read per joiner and sport, through the rating's
published read, over the 30 days' sign-ups. #794's level projection, indexed by
sport, is where that goes when the month's joiners outgrow it.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport
from app.modules.discovery.domain.new_in_rakieta import (
    ON_THE_ROW,
    Joiner,
    JoinerKey,
    days_since,
    new_since,
    newest_first,
    on_the_row,
    page_after,
)
from app.modules.discovery.domain.ports import (
    BlocksEitherWay,
    DirectoryFaces,
    PlayerDirectory,
    ReadersRelations,
    SportLevel,
    LevelsHeld,
)
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.totals import COUNTED_UP_TO, capped


@final
@dataclass(frozen=True, slots=True)
class JoinerCard:
    """One tile: the face, *Joined …*, every sport with a level, and the
    reader's round friend button."""

    player_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    joined_at: Instant
    #: Warsaw days since they joined: ``0`` is *Joined today*.
    days_since_joined: int
    levels: tuple[SportLevel, ...]
    relation: Relation


@final
@dataclass(frozen=True, slots=True)
class NewInRakietaRow:
    cards: tuple[JoinerCard, ...]
    #: How many joiners the row could show, counted up to 100 (``totals``).
    total: int


@final
@dataclass(frozen=True, slots=True)
class NewInRakietaPage:
    cards: tuple[JoinerCard, ...]
    #: Where the next page starts; ``None`` on the last.
    next: JoinerKey | None
    #: Every sport at least one joiner holds a level in — the pill's chips.
    sports: tuple[Sport, ...]


@final
class _Cards:
    """What both reads hand the screen, built the same way."""

    def __init__(
        self,
        *,
        relations: ReadersRelations,
        levels: LevelsHeld,
        faces: DirectoryFaces,
    ) -> None:
        self._relations = relations
        self._levels = levels
        self._faces = faces

    async def of(
        self,
        reader: UUID,
        joiners: Sequence[Joiner],
        *,
        now: Instant,
        relations: Mapping[UUID, Relation] | None = None,
        levels: Mapping[UUID, tuple[SportLevel, ...]] | None = None,
    ) -> tuple[JoinerCard, ...]:
        ids = [one.player_id for one in joiners]
        if relations is None:
            relations = await self.relations_of(reader, ids)
        if levels is None:
            levels = await self.levels_of(ids)
        cards = []
        for one in joiners:
            url = (
                None
                if one.photo_id is None
                else await self._faces.photo_url(one.player_id, one.photo_id)
            )
            cards.append(
                JoinerCard(
                    player_id=one.player_id,
                    nickname=one.nickname,
                    photo_id=one.photo_id,
                    photo_url=url,
                    joined_at=one.joined_at,
                    days_since_joined=days_since(one.joined_at, now),
                    levels=levels.get(one.player_id, ()),
                    relation=relations.get(one.player_id, Relation.NONE),
                )
            )
        return tuple(cards)

    async def relations_of(
        self, reader: UUID, ids: Sequence[UUID]
    ) -> Mapping[UUID, Relation]:
        if not ids:
            return {}
        return await self._relations.relations_of(reader, ids)

    async def levels_of(
        self, ids: Sequence[UUID]
    ) -> Mapping[UUID, tuple[SportLevel, ...]]:
        if not ids:
            return {}
        return await self._levels.levels_of(ids)


@final
class ReadNewInRakieta:
    """Home's row: the 10 newest, unconnected first, then sent, then friends."""

    def __init__(
        self,
        *,
        directory: PlayerDirectory,
        blocks: BlocksEitherWay,
        relations: ReadersRelations,
        levels: LevelsHeld,
        faces: DirectoryFaces,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._blocks = blocks
        self._cards = _Cards(relations=relations, levels=levels, faces=faces)
        self._clock = clock

    async def execute(self, reader: UUID) -> NewInRakietaRow:
        now = self._clock.now()
        leaving_out = {reader, *await self._blocks.either_way(reader)}
        newest = await self._directory.who_joined(
            after=new_since(now), leaving_out=leaving_out, limit=ON_THE_ROW
        )
        relations = await self._cards.relations_of(
            reader, [one.player_id for one in newest]
        )
        # A row short of ten is everybody new: its total costs nothing. The
        # count is a later statement, so it may see somebody leave whom the
        # row shows: it never answers fewer than the row holds.
        everybody = len(newest)
        if everybody == ON_THE_ROW:
            everybody = max(
                everybody,
                await self._directory.how_many_joined(
                    after=new_since(now), leaving_out=leaving_out, up_to=COUNTED_UP_TO
                ),
            )
        return NewInRakietaRow(
            cards=await self._cards.of(
                reader, on_the_row(newest, relations), now=now, relations=relations
            ),
            total=capped(everybody),
        )


@final
class ReadNewInRakietaPage:
    """See all: every joiner, newest first, in pages — one sport's alone
    when a sport is asked."""

    def __init__(
        self,
        *,
        directory: PlayerDirectory,
        blocks: BlocksEitherWay,
        relations: ReadersRelations,
        levels: LevelsHeld,
        faces: DirectoryFaces,
        clock: Clock,
    ) -> None:
        self._directory = directory
        self._blocks = blocks
        self._cards = _Cards(relations=relations, levels=levels, faces=faces)
        self._clock = clock

    async def execute(
        self, reader: UUID, *, sport: Sport | None, after: JoinerKey | None
    ) -> NewInRakietaPage:
        now = self._clock.now()
        everyone = newest_first(
            await self._directory.who_joined(
                after=new_since(now),
                leaving_out={reader, *await self._blocks.either_way(reader)},
            )
        )
        levels = await self._cards.levels_of([one.player_id for one in everyone])
        held = {
            one.player_id: {level.sport for level in levels.get(one.player_id, ())}
            for one in everyone
        }
        listed = (
            everyone
            if sport is None
            else tuple(one for one in everyone if sport in held[one.player_id])
        )
        page = page_after(listed, after)
        return NewInRakietaPage(
            cards=await self._cards.of(reader, page.joiners, now=now, levels=levels),
            next=page.next,
            sports=tuple(
                one for one in Sport if any(one in sports for sports in held.values())
            ),
        )
