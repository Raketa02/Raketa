"""The ranking's reads: a sport's General list as the reader sees it, and the
trophy's place on Home (``docs/adr/0203`` §2–§5; the screens §1, §4–§5).

**A read, recorded nowhere, and the clock is read once.** Who is listed — five
results, the last within the 90 days — is decided against one instant, so the
card, the podium and the rows can't disagree about who dropped off.

**The places are counted over every listed row.** A row the read leaves out —
an id nobody can name — keeps its place, so the places stay true; the hidden
and blocked rows of #772 will leave the same gaps.

**The chips are worked out together, over every listed row**: today's set in
today's order against the same set ordered by the level history exactly 7 days
earlier (``chips_of``). **The gap line names only rows the reader can see** —
here, a row somebody can name — so a nameless neighbour is skipped and the
line reads against the nearest named one (the mechanics §7.3).
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant
from app.modules.rankings.domain.ports import (
    LevelHistory,
    RankedFace,
    RankedFaces,
    RankingRows,
    SportLevels,
)
from app.modules.rankings.domain.ranking import (
    GENERAL_ENTRY,
    PAGE_SIZE,
    PODIUM_SIZE,
    Chip,
    GapLine,
    Outcome,
    PlaceCard,
    RankingRow,
    card_of,
    chips_of,
    chips_since,
    latest_of,
    listed_since,
    player_above,
    player_below,
)


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
    #: The instant who is listed was decided against.
    read_at: Instant
    card: PlaceCard
    #: How many are listed — *of 13*.
    listed_count: int
    #: The first three rows, each with its true place — empty with fewer.
    podium: tuple[RankedRow, ...]
    #: General's first page.
    rows: tuple[RankedRow, ...]


async def _listed(
    rows: RankingRows, sport: Sport, *, now: Instant
) -> tuple[RankingRow, ...]:
    return await rows.listed(sport, at_least=GENERAL_ENTRY, since=listed_since(now))


def _place_of(listed: tuple[RankingRow, ...], player_id: UUID) -> int | None:
    return next(
        (
            place
            for place, row in enumerate(listed, start=1)
            if row.player_id == player_id
        ),
        None,
    )


@final
class ReadRanking:
    """``GET /rankings/{sport}?view=GENERAL``: the card with its chip and gap
    line, the podium and the first page."""

    def __init__(
        self,
        *,
        rows: RankingRows,
        level_history: LevelHistory,
        faces: RankedFaces,
        levels: SportLevels,
        clock: Clock,
    ) -> None:
        self._rows = rows
        self._level_history = level_history
        self._faces = faces
        self._levels = levels
        self._clock = clock

    async def execute(self, reader: UUID, sport: Sport) -> Ranking:
        now = instant(self._clock.now())
        listed = await _listed(self._rows, sport, now=now)
        chips = chips_of(
            listed,
            await self._level_history.points_at(
                sport, chips_since(now), [row.player_id for row in listed]
            ),
            now=now,
        )
        own = next(
            (row for row in await self._rows.of_player(reader) if row.sport is sport),
            None,
        )
        page = listed[:PAGE_SIZE]
        faces = dict(await self._faces.faces_of([row.player_id for row in page]))
        place = _place_of(listed, reader)
        card = card_of(
            own,
            holds_a_level=await self._levels.holds_a_level(reader, sport),
            place=place,
            of=len(listed),
            now=now,
            chip=None if place is None else chips[reader],
            gap_line=(
                None if place is None else await self._gap_line(listed, place, faces)
            ),
        )
        rows = tuple(
            ranked
            for place, row in enumerate(page, start=1)
            if (
                ranked := _ranked(
                    row, place, faces, reader=reader, chip=chips[row.player_id]
                )
            )
            is not None
        )
        return Ranking(
            sport=sport,
            read_at=now,
            card=card,
            listed_count=len(listed),
            podium=rows[:PODIUM_SIZE] if len(rows) >= PODIUM_SIZE else (),
            rows=rows,
        )

    async def _gap_line(
        self,
        listed: tuple[RankingRow, ...],
        place: int,
        faces: dict[UUID, RankedFace],
    ) -> GapLine:
        """The nearest named row above the reader and the nearest below,
        measured from the reader's own row — or, in first place, *Top of the
        list* and nothing else."""

        if place == 1:
            return GapLine(above=None, below=None, top_of_the_list=True)
        mine = listed[place - 1]
        above = await self._nearest_named(reversed(listed[: place - 1]), faces)
        below = await self._nearest_named(listed[place:], faces)
        return GapLine(
            above=None if above is None else player_above(mine, *above),
            below=None if below is None else player_below(mine, *below),
            top_of_the_list=False,
        )

    async def _nearest_named(
        self, rows: Iterable[RankingRow], faces: dict[UUID, RankedFace]
    ) -> tuple[RankingRow, str] | None:
        """The first of ``rows`` somebody can name, asking the faces only of a
        row off the page — almost always the first one asked about. **Adds
        every face it asks for to ``faces``**, so the walk below the reader
        never asks twice about a row the walk above already asked."""

        for row in rows:
            if row.player_id not in faces:
                faces.update(await self._faces.faces_of([row.player_id]))
            face = faces.get(row.player_id)
            if face is not None and face.nickname is not None:
                return row, face.nickname
        return None


def _ranked(
    row: RankingRow,
    place: int,
    faces: Mapping[UUID, RankedFace],
    *,
    reader: UUID,
    chip: Chip,
) -> RankedRow | None:
    face = faces.get(row.player_id)
    if face is None or face.nickname is None:
        return None
    return RankedRow(
        place=place,
        player_id=row.player_id,
        nickname=face.nickname,
        photo_id=face.photo_id,
        photo_url=face.photo_url,
        form=row.form,
        chip=chip,
        hundredths=row.hundredths,
        is_you=row.player_id == reader,
    )


@final
@dataclass(frozen=True, slots=True)
class HomeRanking:
    """Home's trophy: the sport of the reader's latest result, in any sport,
    and their General place in it — ``None`` when they aren't listed there."""

    sport: Sport
    general_place: int | None


@final
class ReadHomeRanking:
    """The trophy's sport and place, or ``None`` with no result anywhere."""

    def __init__(self, *, rows: RankingRows, clock: Clock) -> None:
        self._rows = rows
        self._clock = clock

    async def execute(self, reader: UUID) -> HomeRanking | None:
        latest = latest_of(await self._rows.of_player(reader))
        if latest is None:
            return None
        now = instant(self._clock.now())
        listed = await _listed(self._rows, latest.sport, now=now)
        return HomeRanking(sport=latest.sport, general_place=_place_of(listed, reader))
