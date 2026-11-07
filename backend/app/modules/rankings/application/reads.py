"""The ranking's reads: a sport's General list as the reader sees it, and the
trophy's place on Home (``docs/adr/0203`` §2–§5; the screens §1, §4–§5).

**A read, recorded nowhere, and the clock is read once.** Who is listed — five
results, the last within the 90 days — is decided against one instant, so the
card, the podium and the rows can't disagree about who dropped off.

**The places are counted over every listed row.** A row the read leaves out —
an id nobody can name — keeps its place, so the places stay true; the hidden
and blocked rows of #772 will leave the same gaps.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, Sport, instant
from app.modules.rankings.domain.ports import (
    RankedFace,
    RankedFaces,
    RankingRows,
    SportLevels,
)
from app.modules.rankings.domain.ranking import (
    GENERAL_ENTRY,
    PAGE_SIZE,
    PODIUM_SIZE,
    Outcome,
    PlaceCard,
    RankingRow,
    card_of,
    latest_of,
    listed_since,
)


@final
@dataclass(frozen=True, slots=True)
class RankedRow:
    """One row the reader sees: its true place, the face, the form and the
    Level."""

    place: int
    player_id: UUID
    nickname: str
    photo_id: UUID | None
    photo_url: str | None
    #: The last results in the sport, oldest first.
    form: tuple[Outcome, ...]
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
    """``GET /rankings/{sport}?view=GENERAL``: the card, the podium and the
    first page."""

    def __init__(
        self,
        *,
        rows: RankingRows,
        faces: RankedFaces,
        levels: SportLevels,
        clock: Clock,
    ) -> None:
        self._rows = rows
        self._faces = faces
        self._levels = levels
        self._clock = clock

    async def execute(self, reader: UUID, sport: Sport) -> Ranking:
        now = instant(self._clock.now())
        listed = await _listed(self._rows, sport, now=now)
        own = next(
            (row for row in await self._rows.of_player(reader) if row.sport is sport),
            None,
        )
        card = card_of(
            own,
            holds_a_level=await self._levels.holds_a_level(reader, sport),
            place=_place_of(listed, reader),
            of=len(listed),
            now=now,
        )
        page = listed[:PAGE_SIZE]
        faces = await self._faces.faces_of([row.player_id for row in page])
        rows = tuple(
            ranked
            for place, row in enumerate(page, start=1)
            if (ranked := _ranked(row, place, faces, reader=reader)) is not None
        )
        return Ranking(
            sport=sport,
            read_at=now,
            card=card,
            listed_count=len(listed),
            podium=rows[:PODIUM_SIZE] if len(rows) >= PODIUM_SIZE else (),
            rows=rows,
        )


def _ranked(
    row: RankingRow,
    place: int,
    faces: Mapping[UUID, RankedFace],
    *,
    reader: UUID,
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
