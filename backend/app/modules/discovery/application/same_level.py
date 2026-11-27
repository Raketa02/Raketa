"""*Same competitive level players*' two reads: **the row** on Home, and **See
all** (``docs/adr/0204`` §4, §7, §10; the home-rows mechanics §6, §9; #794).

**Worked out on each read** (call 11): the current levels are the projection's,
the % the Forecast's (``HowEven``), and who is connected, who is blocked and a
link to each face are asked live of their owners. **Hidden** — no card, no
sport — while the reader holds no level anywhere (Q23).

**Read outward from the reader's level, in widening windows**, never the whole
crowd at once. A window finds everybody within its width of the reader's level
in a sport compared; beyond it nobody reads more than the Forecast for a player
that far away, as sure as the surest player in the sport (``Reach``). So each
window **settles** the cards nobody beyond it could come before, in their final
order, and the read stops widening once it holds what it needs — the row its
ten, a page its twenty. The last window is everybody. A level-only index serves
each window; how sure the app is of one player's level is only known once it is
read, which is why a window settles less than it finds.

**Every candidate list leaves out** the reader, everybody the reader blocked or
who blocked the reader, players with *Show me to new people* off, accounts that
don't play and accounts that are gone (``docs/adr/0204`` §10): the projection's
``near`` holds all but the reader and the blocks, which are handed to it.

**A rested player is a gap** (#796; ``rest``): the rest count is asked once
for each ten the row takes, about the cards that could be fresh — good matches
the reader is not connected with — and nobody else, since a rest changes nothing
for them. See all rests nobody.

**The row's total** (#812; ``totals``) is everybody holding a level in one of
the reader's sports. The windows the row read already found them — all of them
once the last window is read, and a hundred is as far as a total counts — so
those cost nothing; a row that filled in a near window with fewer than a
hundred read asks one count, stopping at 100. **No window is read to count**,
and nobody is scored for it.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Final, final
from uuid import UUID

from app.kernel import Sport
from app.modules.discovery.application.on_screen import rested_among
from app.modules.discovery.domain.levels import CurrentLevel, Estimate
from app.modules.discovery.domain.ports import (
    BlocksEitherWay,
    Candidate,
    DirectoryFaces,
    HowEven,
    PlayerLevels,
    ReadersRelations,
    RestCount,
)
from app.modules.discovery.domain.relation import Relation
from app.modules.discovery.domain.rest import OnScreenRow
from app.modules.discovery.domain.same_level import (
    A_PAGE,
    ON_THE_ROW,
    Comparison,
    SameLevelPlayer,
    SameLevelKey,
    Reach,
    RowOfTen,
    compared,
    same_level_player,
)
from app.modules.discovery.domain.totals import COUNTED_UP_TO, capped

#: The windows a read widens through — the gap either side of the reader's
#: level in each sport compared — doubling from two hundredths. ``None`` is
#: everybody, the last.
WINDOWS: Final[tuple[float | None, ...]] = (
    0.02,
    0.04,
    0.08,
    0.16,
    0.32,
    0.64,
    1.28,
    2.56,
    None,
)


@final
@dataclass(frozen=True, slots=True)
class SameLevelCard:
    """One dark card: the face, the sport shown, every shared sport for the
    comparison sheet, and the reader's round friend button."""

    player_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    shown: Comparison
    #: Every shared sport, most even first.
    comparisons: tuple[Comparison, ...]
    relation: Relation


@final
@dataclass(frozen=True, slots=True)
class SameLevelRow:
    cards: tuple[SameLevelCard, ...]
    #: How many the row could show, counted up to 100 (``totals``).
    total: int


@final
@dataclass(frozen=True, slots=True)
class SameLevelPage:
    cards: tuple[SameLevelCard, ...]
    #: Where the next page starts; ``None`` on the last.
    next: SameLevelKey | None
    #: Every sport the reader shares with somebody — the pill's chips.
    sports: tuple[Sport, ...]


@final
@dataclass(frozen=True, slots=True)
class _Found:
    player: SameLevelPlayer
    nickname: str
    photo_id: UUID | None


@final
class _Widening:
    """The cards best first, a window at a time — each window's settled cards
    in their final order, ``None`` once everybody is read and handed out."""

    def __init__(
        self,
        *,
        levels: PlayerLevels,
        even: HowEven,
        mine: Mapping[Sport, CurrentLevel],
        in_sport: Sport | None,
        leaving_out: Collection[UUID],
    ) -> None:
        self._levels = levels
        self._even = even
        self._mine = mine
        self._in_sport = in_sport
        self._leaving_out = leaving_out
        self._around = {
            sport: level.mu
            for sport, level in mine.items()
            if in_sport is None or sport is in_sport
        }
        self._windows = iter(WINDOWS)
        self._least_doubt: Mapping[Sport, float] | None = None
        #: The widest window read so far; ``None`` before the first.
        self._last_width: float | None = None
        self._seen: set[UUID] = set()
        self._waiting: list[_Found] = []
        self._done = not self._around

    @property
    def read(self) -> int:
        """Everybody the windows have read so far, each once."""

        return len(self._seen)

    @property
    def read_everybody(self) -> bool:
        """The last window, everybody, is read: ``read`` is the whole crowd."""

        return self._done

    async def next_window(self) -> tuple[_Found, ...] | None:
        if self._done:
            return None
        width = next(self._windows)
        for candidate in await self._levels.near(
            self._around,
            within=width,
            beyond=self._last_width,
            compared_in=tuple(self._mine),
            leaving_out=self._leaving_out,
        ):
            if candidate.player_id in self._seen:
                continue
            self._seen.add(candidate.player_id)
            found = self._found(candidate)
            if found is not None:
                self._waiting.append(found)
        self._last_width = width
        self._waiting.sort(key=lambda one: one.player.key.order)
        if width is None:
            self._done = True
            settled, self._waiting = self._waiting, []
            return tuple(settled)
        if self._least_doubt is None:
            self._least_doubt = await self._levels.least_doubt(tuple(self._around))
        reach = self._reach(width, self._least_doubt)
        cut = next(
            (n for n, one in enumerate(self._waiting) if not reach.settles(one.player)),
            len(self._waiting),
        )
        settled, self._waiting = self._waiting[:cut], self._waiting[cut:]
        return tuple(settled)

    def _found(self, candidate: Candidate) -> _Found | None:
        player = same_level_player(
            candidate.player_id,
            compared(self._mine, candidate.levels, self._even.percent_even),
            in_sport=self._in_sport,
        )
        if player is None:
            return None
        return _Found(
            player=player, nickname=candidate.nickname, photo_id=candidate.photo_id
        )

    def _reach(self, width: float, least_doubt: Mapping[Sport, float]) -> Reach:
        """The most even anybody further than ``width`` away could read: a
        player exactly that far, in the sport compared that allows most, as
        sure as the surest player in it — the Forecast falls with the gap and
        with doubt, and nobody unread is surer than everybody."""

        return Reach(
            ceiling=max(
                self._even.percent_even(
                    sport,
                    self._mine[sport].estimate,
                    Estimate(mu=mu + width, sigma=least_doubt.get(sport, 0.0)),
                )
                for sport, mu in self._around.items()
            ),
            width=width,
        )


@final
class _Cards:
    """What both reads hand the screen, built the same way."""

    def __init__(self, *, relations: ReadersRelations, faces: DirectoryFaces) -> None:
        self._relations = relations
        self._faces = faces

    async def relations_of(
        self, reader: UUID, found: Sequence[_Found]
    ) -> Mapping[UUID, Relation]:
        if not found:
            return {}
        return await self._relations.relations_of(
            reader, [one.player.player_id for one in found]
        )

    async def of(
        self, found: Sequence[_Found], relations: Mapping[UUID, Relation]
    ) -> tuple[SameLevelCard, ...]:
        cards = []
        for one in found:
            player_id = one.player.player_id
            cards.append(
                SameLevelCard(
                    player_id=player_id,
                    nickname=one.nickname,
                    photo_id=one.photo_id,
                    photo_url=(
                        None
                        if one.photo_id is None
                        else await self._faces.photo_url(player_id, one.photo_id)
                    ),
                    shown=one.player.shown,
                    comparisons=one.player.comparisons,
                    relation=relations.get(player_id, Relation.NONE),
                )
            )
        return tuple(cards)


@final
class ReadSameLevel:
    """Home's row: ten cards, fresh good matches first, then the gaps."""

    def __init__(
        self,
        *,
        levels: PlayerLevels,
        even: HowEven,
        blocks: BlocksEitherWay,
        relations: ReadersRelations,
        rests: RestCount,
        faces: DirectoryFaces,
    ) -> None:
        self._levels = levels
        self._even = even
        self._blocks = blocks
        self._rests = rests
        self._cards = _Cards(relations=relations, faces=faces)

    async def execute(self, reader: UUID) -> SameLevelRow:
        mine = await self._levels.of_player(reader)
        if not mine:
            return SameLevelRow(cards=(), total=0)
        leaving_out = {reader, *await self._blocks.either_way(reader)}
        widening = _Widening(
            levels=self._levels,
            even=self._even,
            mine=mine,
            in_sport=None,
            leaving_out=leaving_out,
        )
        row = RowOfTen()
        taken: dict[UUID, _Found] = {}
        relations: dict[UUID, Relation] = {}
        while not row.full and (settled := await widening.next_window()) is not None:
            # Friends is asked about ten at a time, as the row takes them: one
            # wide window can settle thousands the row will never reach.
            for start in range(0, len(settled), ON_THE_ROW):
                if row.full:
                    break
                chunk = settled[start : start + ON_THE_ROW]
                relations.update(await self._cards.relations_of(reader, chunk))
                rested = await rested_among(
                    self._rests,
                    reader,
                    OnScreenRow.SAME_LEVEL,
                    [
                        one.player.player_id
                        for one in chunk
                        if row.may_be_fresh(
                            one.player, relation=relations[one.player.player_id]
                        )
                    ],
                )
                for one in chunk:
                    if row.full:
                        break
                    taken[one.player.player_id] = one
                    row.take(
                        one.player,
                        relation=relations[one.player.player_id],
                        rested=one.player.player_id in rested,
                    )
        return SameLevelRow(
            cards=await self._cards.of(
                [taken[player.player_id] for player in row.row()], relations
            ),
            total=await self._total(widening, mine, leaving_out),
        )

    async def _total(
        self,
        widening: _Widening,
        mine: Mapping[Sport, CurrentLevel],
        leaving_out: Collection[UUID],
    ) -> int:
        """Everybody holding a level in one of the reader's sports — what the
        windows read, once they read everybody or a hundred; otherwise one
        count, stopping at the cap. **Never another window.** The count is a
        later statement, so it may see somebody leave whom a window read: it
        never answers fewer than the windows did."""

        if widening.read_everybody or widening.read >= COUNTED_UP_TO:
            return capped(widening.read)
        counted = await self._levels.how_many_hold(
            tuple(mine), leaving_out=leaving_out, up_to=COUNTED_UP_TO
        )
        return capped(max(widening.read, counted))


@final
class ReadSameLevelPage:
    """See all: everybody sharing a sport, best % first, friends where they
    fall — everybody in one sport, re-compared there, when a sport is asked."""

    def __init__(
        self,
        *,
        levels: PlayerLevels,
        even: HowEven,
        blocks: BlocksEitherWay,
        relations: ReadersRelations,
        faces: DirectoryFaces,
    ) -> None:
        self._levels = levels
        self._even = even
        self._blocks = blocks
        self._cards = _Cards(relations=relations, faces=faces)

    async def execute(
        self, reader: UUID, *, sport: Sport | None, after: SameLevelKey | None
    ) -> SameLevelPage:
        mine = await self._levels.of_player(reader)
        if not mine:
            return SameLevelPage(cards=(), next=None, sports=())
        leaving_out = {reader, *await self._blocks.either_way(reader)}
        widening = _Widening(
            levels=self._levels,
            even=self._even,
            mine=mine,
            in_sport=sport,
            leaving_out=leaving_out,
        )
        page: list[_Found] = []
        while (
            len(page) <= A_PAGE
            and (settled := await widening.next_window()) is not None
        ):
            page += [
                one
                for one in settled
                if after is None or one.player.key.is_behind(after)
            ]
        shown = page[:A_PAGE]
        return SameLevelPage(
            cards=await self._cards.of(
                shown, await self._cards.relations_of(reader, shown)
            ),
            next=shown[-1].player.key if len(page) > A_PAGE else None,
            sports=await self._levels.shared_sports(mine, leaving_out=leaving_out),
        )
