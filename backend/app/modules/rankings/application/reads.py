"""The ranking's reads: a sport's General list as the reader sees it, a page
of it, the reader's Friends table, and the trophy's places on Home
(``docs/adr/0203`` §2–§5; the screens §1, §4–§5).

**A read, recorded nowhere, and the clock is read once.** Who is listed — five
results, the last within the 90 days — and every chip are decided by **the
sport's General order** (``TheGeneralOrder``, #770): worked out in one pass,
kept for at most a minute and forgotten on the next ranking write in the sport.
So the card, the podium, the rows and every page read in that minute agree
about who dropped off.

**The places are counted over every listed row.** A row the read leaves out
keeps its place, so the places stay true: an id nobody can name, and — the
reader's ``Sight`` (#772) — a player hidden from General, in General, and
anybody a block stands between the reader and, whichever of them made it, in
either view, read live through ``BlocksEitherWay``. **A page is a slice of the
order**, its cursors the keys of the slice's first and last rows, so what a
reader may not see is dropped from the slice and never moves a cursor.

**The gap line names only rows the reader can see** — a row the reader's sight
lets through that somebody can name — so a hidden, blocked or nameless
neighbour is skipped and the line reads against the nearest one seen (the
mechanics §7.3). **A hidden reader's card has no gap line**: *Hidden from
General* and the switch stand in its place. **The podium is the first three
rows the reader sees**, each with its true place, and none with fewer.

**Friends is the same read over a table of its own** (``TheFriendsTable``,
#771): the reader and their friends with a result in the 90 days, worked out on
each read, places, chips and the gap line counted within it, and returned
whole. With no friend listed the card is the page — *just you*, or *no friend
listed* — and nothing is drawn below it.
"""

from __future__ import annotations

from collections.abc import AsyncIterator, Mapping
from dataclasses import dataclass
from typing import Final, NamedTuple, final
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant, invariant
from app.modules.rankings.application.friends_table import TheFriendsTable
from app.modules.rankings.application.general_order import TheGeneralOrder
from app.modules.rankings.domain.general_order import (
    ListedRow,
    OrderKey,
    Sight,
    Slice,
    first_page,
    page_after,
    page_around,
    page_before,
)
from app.modules.rankings.domain.ports import (
    HeldOrder,
    RankedFace,
    RankedFaces,
    RankingRows,
    BlocksEitherWay,
    SportLevels,
)
from app.modules.rankings.domain.ranking import (
    PODIUM_SIZE,
    Chip,
    GapLine,
    Outcome,
    PlaceCard,
    RankingView,
    card_of,
    friends_card_of,
    latest_of,
    player_above,
    player_below,
)

#: How many rows the gap line reads off the order at a time, walking away from
#: the reader for the nearest named one — almost always the first.
_NEIGHBOURS: Final = 8


@final
@dataclass(frozen=True, slots=True)
class RankedRow:
    """One row the reader sees: its true place, the face, the form, the chip
    and the Level."""

    place: int
    player_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    #: The last results in the sport, oldest first.
    form: tuple[Outcome, ...]
    chip: Chip
    hundredths: int
    is_you: bool


@final
@dataclass(frozen=True, slots=True)
class Ranking:
    sport: Sport
    view: RankingView
    #: The instant the read was made at.
    read_at: Instant
    card: PlaceCard
    #: How many are listed in the view — *of 13*.
    listed_count: int
    #: The first three rows, each with its true place — empty with fewer.
    podium: tuple[RankedRow, ...]
    #: General's first page, or the whole Friends table — empty when the card
    #: is the page (*just you*, *no friend listed*).
    rows: tuple[RankedRow, ...]
    #: The cursor the next page is read after; ``None`` when this is all, and
    #: always in Friends.
    next: OrderKey | None


@final
@dataclass(frozen=True, slots=True)
class GeneralPage:
    """A page of General: the slice's rows the reader sees, and the cursors
    either side of it."""

    sport: Sport
    listed_count: int
    rows: tuple[RankedRow, ...]
    #: The cursor the page before is read before; ``None`` at the top.
    previous: OrderKey | None
    #: The cursor the page after is read after; ``None`` at the bottom.
    next: OrderKey | None


class _Seen(NamedTuple):
    """A slice of the order — every row of it, which the cursors are taken
    from — the faces of the rows the reader sees, and those rows."""

    rows: tuple[ListedRow, ...]
    faces: dict[UUID, RankedFace]
    ranked: tuple[RankedRow, ...]


async def _seen(
    order: HeldOrder,
    page: Slice,
    faces: RankedFaces,
    *,
    sight: Sight,
) -> _Seen:
    """The slice, and the face of everybody on it the reader sees, asked in
    one question."""

    rows = await order.rows(page.start, page.stop)
    return await _seen_of(rows, faces, sight=sight)


async def _seen_of(
    rows: tuple[ListedRow, ...], faces: RankedFaces, *, sight: Sight
) -> _Seen:
    """These rows, and the face of everybody on them the reader sees, asked
    in one question — nobody they can't see is asked about."""

    seen = [row for row in rows if sight.sees(row)]
    known = dict(await faces.faces_of([row.player_id for row in seen]))
    return _Seen(
        rows=rows,
        faces=known,
        ranked=tuple(
            ranked
            for row in seen
            if (ranked := _ranked(row, known, reader=sight.reader)) is not None
        ),
    )


@final
class ReadRanking:
    """``GET /rankings/{sport}?view=…``: the card with its chip and gap line,
    the podium, and General's first page or the whole Friends table."""

    def __init__(
        self,
        *,
        general: TheGeneralOrder,
        friends: TheFriendsTable,
        faces: RankedFaces,
        levels: SportLevels,
        blocks: BlocksEitherWay,
        clock: Clock,
    ) -> None:
        self._general = general
        self._friends = friends
        self._faces = faces
        self._levels = levels
        self._blocks = blocks
        self._clock = clock

    async def execute(
        self, reader: UUID, sport: Sport, *, view: RankingView = RankingView.GENERAL
    ) -> Ranking:
        now = instant(self._clock.now())
        sight = await _sight_of(reader, view, self._blocks)
        if view is RankingView.FRIENDS:
            return await self._among_friends(reader, sport, now=now, sight=sight)
        read = await self._general.read(sport, now=now, reader=reader)
        order, mine = read.order, read.mine
        page = first_page(order.listed)
        seen = await _seen(order, page, self._faces, sight=sight)
        card = card_of(
            read.own,
            holds_a_level=await self._levels.holds_a_level(reader, sport),
            of=order.listed,
            placed=mine,
            gap_line=(
                # A hidden reader's card has *Hidden from General* instead.
                None
                if mine is None or mine.hidden
                else await self._gap_line(order, mine, seen.faces, sight)
            ),
        )
        return Ranking(
            sport=sport,
            view=RankingView.GENERAL,
            read_at=now,
            card=card,
            listed_count=order.listed,
            podium=await self._podium(order, page, seen, sight),
            rows=seen.ranked,
            next=seen.rows[-1].key if page.stop < order.listed else None,
        )

    async def _among_friends(
        self, reader: UUID, sport: Sport, *, now: Instant, sight: Sight
    ) -> Ranking:
        """The Friends view: the whole table and the card read within it —
        or, with no friend listed, the card alone."""

        read = await self._friends.read(sport, now=now, reader=reader)
        table, mine = read.table, read.mine
        seen = await _seen_of(table.order.rows, self._faces, sight=sight)
        card = friends_card_of(
            read.own,
            holds_a_level=await self._levels.holds_a_level(reader, sport),
            of=table.listed,
            friends_listed=read.friends_listed,
            placed=mine,
            gap_line=(
                None
                if mine is None
                else await self._gap_line(table, mine, seen.faces, sight)
            ),
        )
        shown = () if card.is_the_page else seen.ranked
        return Ranking(
            sport=sport,
            view=RankingView.FRIENDS,
            read_at=now,
            card=card,
            listed_count=table.listed,
            podium=_podium_of(shown),
            rows=shown,
            next=None,
        )

    async def _gap_line(
        self,
        order: HeldOrder,
        mine: ListedRow,
        faces: dict[UUID, RankedFace],
        sight: Sight,
    ) -> GapLine:
        """The nearest row the reader sees above them and the nearest below,
        measured from the reader's own row — or, in first place, *Top of the
        list* and nothing else. With nobody seen above a reader who isn't
        first, only the part about below reads."""

        if mine.place == 1:
            return GapLine(above=None, below=None, top_of_the_list=True)
        above = await _first(
            _seen_named(_walk_up(order, mine.place - 1), faces, self._faces, sight)
        )
        below = await _first(
            _seen_named(_walk_down(order, mine.place), faces, self._faces, sight)
        )
        return GapLine(
            above=None if above is None else player_above(mine, *above),
            below=None if below is None else player_below(mine, *below),
            top_of_the_list=False,
        )

    async def _podium(
        self, order: HeldOrder, page: Slice, seen: _Seen, sight: Sight
    ) -> tuple[RankedRow, ...]:
        """The first three rows the reader sees, each with its true place —
        off the first page, read on below it only when that page shows fewer
        than three — and none with fewer."""

        podium = list(seen.ranked[:PODIUM_SIZE])
        if len(podium) < PODIUM_SIZE and page.stop < order.listed:
            below = _seen_named(
                _walk_down(order, page.stop), seen.faces, self._faces, sight
            )
            async for row, _ in below:
                ranked = _ranked(row, seen.faces, reader=sight.reader)
                if ranked is not None:
                    podium.append(ranked)
                if len(podium) == PODIUM_SIZE:
                    break
        return _podium_of(tuple(podium))


async def _sight_of(reader: UUID, view: RankingView, blocks: BlocksEitherWay) -> Sight:
    """What the reader sees in the view — everybody a block stands between
    them and read live, once a read."""

    return Sight(
        reader=reader, view=view, blocked=await blocks.blocked_either_way(reader)
    )


async def _seen_named(
    rows: AsyncIterator[ListedRow],
    known: dict[UUID, RankedFace],
    faces: RankedFaces,
    sight: Sight,
) -> AsyncIterator[tuple[ListedRow, str]]:
    """Each of ``rows`` the reader sees that somebody can name, with the name,
    asking ``faces`` only of a row off the page — almost always the first one
    asked about, and never one the reader can't see. **Adds every face it
    asks for to ``known``**, so the walk below the reader never asks twice
    about a row the walk above already asked."""

    async for row in rows:
        if not sight.sees(row):
            continue
        if row.player_id not in known:
            known.update(await faces.faces_of([row.player_id]))
        face = known.get(row.player_id)
        if face is not None and face.nickname is not None:
            yield row, face.nickname


async def _first(
    named: AsyncIterator[tuple[ListedRow, str]],
) -> tuple[ListedRow, str] | None:
    async for one in named:
        return one
    return None


def _podium_of(ranked: tuple[RankedRow, ...]) -> tuple[RankedRow, ...]:
    """The first three rows the reader sees — none with fewer."""

    return ranked[:PODIUM_SIZE] if len(ranked) >= PODIUM_SIZE else ()


async def _walk_up(order: HeldOrder, above: int) -> AsyncIterator[ListedRow]:
    """The rows ahead of index ``above``, nearest first, read a few at a time."""

    stop = above
    while stop > 0:
        start = max(0, stop - _NEIGHBOURS)
        for row in reversed(await order.rows(start, stop)):
            yield row
        stop = start


async def _walk_down(order: HeldOrder, below: int) -> AsyncIterator[ListedRow]:
    """The rows from index ``below`` on, nearest first, read a few at a time."""

    start = below
    while start < order.listed:
        stop = min(order.listed, start + _NEIGHBOURS)
        for row in await order.rows(start, stop):
            yield row
        start = stop


@final
class ReadGeneralPage:
    """``GET /rankings/{sport}/general/rows``: a page of 50, after a cursor,
    before one, or with the reader in the middle — the first page with none,
    and with *around the reader* when the reader isn't listed."""

    def __init__(
        self,
        *,
        general: TheGeneralOrder,
        faces: RankedFaces,
        blocks: BlocksEitherWay,
        clock: Clock,
    ) -> None:
        self._general = general
        self._faces = faces
        self._blocks = blocks
        self._clock = clock

    async def execute(
        self,
        reader: UUID,
        sport: Sport,
        *,
        after: OrderKey | None = None,
        before: OrderKey | None = None,
        around_the_reader: bool = False,
    ) -> GeneralPage:
        invariant(
            sum((after is not None, before is not None, around_the_reader)) <= 1,
            "a page asked for in two places at once",
        )
        now = instant(self._clock.now())
        sight = await _sight_of(reader, RankingView.GENERAL, self._blocks)
        read = await self._general.read(sport, now=now, reader=reader)
        order = read.order
        if after is not None:
            page = page_after(await order.up_to(after), order.listed)
        elif before is not None:
            page = page_before(await order.ahead_of(before))
        elif around_the_reader and read.mine is not None:
            page = page_around(read.mine.place, order.listed)
        else:
            page = first_page(order.listed)
        seen = await _seen(order, page, self._faces, sight=sight)
        first, last = (seen.rows[0], seen.rows[-1]) if seen.rows else (None, None)
        return GeneralPage(
            sport=sport,
            listed_count=order.listed,
            rows=seen.ranked,
            previous=(
                None if page.start == 0 else after if first is None else first.key
            ),
            next=(
                None
                if page.stop >= order.listed
                else before
                if last is None
                else last.key
            ),
        )


def _ranked(
    row: ListedRow,
    faces: Mapping[UUID, RankedFace],
    *,
    reader: UUID,
) -> RankedRow | None:
    face = faces.get(row.player_id)
    if face is None or face.nickname is None:
        return None
    return RankedRow(
        place=row.place,
        player_id=row.player_id,
        nickname=face.nickname,
        photo_id=face.photo_id,
        photo_url=face.photo_url,
        form=row.form,
        chip=row.chip,
        hundredths=row.hundredths,
        is_you=row.player_id == reader,
    )


@final
@dataclass(frozen=True, slots=True)
class HomeRanking:
    """Home's trophy: the sport of the reader's latest result, in any sport,
    and their place in it in each view — ``None`` where they aren't listed,
    and in Friends where no friend is either (#771)."""

    sport: Sport
    general_place: int | None
    friends_place: int | None


@final
class ReadHomeRanking:
    """The trophy's sport and places, or ``None`` with no result anywhere. The
    view it shows is the phone's to remember (the mechanics §8), so both
    places are sent."""

    def __init__(
        self,
        *,
        rows: RankingRows,
        general: TheGeneralOrder,
        friends: TheFriendsTable,
        clock: Clock,
    ) -> None:
        self._rows = rows
        self._general = general
        self._friends = friends
        self._clock = clock

    async def execute(self, reader: UUID) -> HomeRanking | None:
        latest = latest_of(await self._rows.of_player(reader))
        if latest is None:
            return None
        now = instant(self._clock.now())
        general = await self._general.read(latest.sport, now=now, reader=reader)
        friends = await self._friends.read(latest.sport, now=now, reader=reader)
        return HomeRanking(
            sport=latest.sport,
            general_place=None if general.mine is None else general.mine.place,
            friends_place=friends.place,
        )
