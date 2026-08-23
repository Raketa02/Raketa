"""Composing shelves 4 and 5: a shared set, and a per-viewer order.

The one collaborator that reaches four ports, and the shape of the reach is
ADR-0068's split made literal — *membership is shared, the row is not*:

1. ask the cache for the set of ids under ``city : sport : kind``;
2. on a miss, ask the arrivals port and store what came back;
3. load the rows, which are never cached;
4. order them for **this** viewer and cap.

**Cache-aside here rather than a decorator around the port**, because the key is
a fact about the viewer and the port's question is not. A decorator would have to
be handed a city to file under, which would put a viewer's declared location into
a signature whose whole subject is a city-wide set — and the day two viewers in
one city disagreed about the key, the shared set would stop being shared.

**A shelf with nothing in it is absent.** Both of these can be genuinely empty —
a city where nobody arrived this month is a real city — and ADR-0070's asymmetry
says a shelf makes a claim, so it goes rather than appearing to claim there is
nobody worth meeting.

**Steps 3 and 4 are not behind the cache and cannot be**, and the cost is stated
rather than hidden: the row read and the Level read are both bounded by the
*cached set* rather than by the cap, because a cap can only be applied after an
order and both orders are computed from facts that live on the row. At launch
volume that is a handful of reads; a city that outgrows it wants a projection,
and ``ArrivalRows`` is where one lands.
"""

from __future__ import annotations

from functools import partial
from typing import Awaitable, Callable, Sequence
from uuid import UUID

from app.kernel import Instant, Minutes, Sport, minutes, shifted

from app.modules.now.domain.arrivals import (
    NEW_CLUB_WINDOW,
    NEW_CLUBS_CAP,
    NEW_PLAYER_WINDOW,
    NEW_PLAYERS_CAP,
    ArrivalKey,
    ArrivalKind,
    Candidate,
    NewClub,
    by_arrival,
    by_closeness,
)
from app.modules.now.domain.ports import (
    ArrivalRows,
    ArrivalSets,
    Levels,
    NewArrivals,
)
from app.modules.now.domain.screen import ClubCard, PersonCard, Shelf, Stamp
from app.modules.now.domain.vocabulary import ShelfCode


def _in_registry_order(sports: frozenset[Sport]) -> tuple[Sport, ...]:
    """The sports of a filter, in the registry's own order.

    ``all`` is a set and a set has no order, so composing over it directly would
    make the shelf's contents depend on hash iteration — reproducible within one
    process and not between two. The registry's order is the one order every
    other read in the product already uses.
    """

    return tuple(sport for sport in Sport if sport in sports)


class ComposeNewArrivals:
    """Shelf 4 and shelf 5, composed for one viewer at one instant."""

    def __init__(
        self,
        *,
        arrivals: NewArrivals,
        rows: ArrivalRows,
        levels: Levels,
        sets: ArrivalSets,
    ) -> None:
        self._arrivals = arrivals
        self._rows = rows
        self._levels = levels
        self._sets = sets

    async def compose(
        self,
        *,
        viewer: UUID,
        sports: frozenset[Sport],
        now: Instant,
        stamp: Stamp,
        city: str | None = None,
    ) -> tuple[Shelf, ...]:
        """The two shelves, in the server's order, absent when empty.

        ``city`` is the viewer's declared city and arrives as ``None`` from every
        caller today, because no context stores one (#102). It is a parameter
        rather than a value invented here so that the day it has a source, this
        composer is not the file being edited.
        """

        ordered = _in_registry_order(sports)
        players = await self._players(
            viewer=viewer, sports=ordered, now=now, stamp=stamp, city=city
        )
        clubs = await self._clubs(sports=ordered, now=now, stamp=stamp, city=city)

        shelves: list[Shelf] = []
        if players:
            shelves.append(Shelf(code=ShelfCode.NEW_PLAYERS, cards=players))
        if clubs:
            shelves.append(Shelf(code=ShelfCode.NEW_CLUBS, cards=clubs))
        return tuple(shelves)

    async def _players(
        self,
        *,
        viewer: UUID,
        sports: tuple[Sport, ...],
        now: Instant,
        stamp: Stamp,
        city: str | None,
    ) -> tuple[PersonCard, ...]:
        since = _back(now, NEW_PLAYER_WINDOW)
        best: dict[UUID, Candidate] = {}

        for sport in sports:
            key = ArrivalKey(city=city, sport=sport, kind=ArrivalKind.PLAYERS)
            found = await self._set(
                key, partial(self._arrivals.player_ids, sport=sport, since=since)
            )
            # A player is not new to herself, and a shelf that introduced her to
            # herself would be the one card on it she could learn nothing from.
            candidates = tuple(one for one in found if one != viewer)
            if not candidates:
                continue

            levels = await self._levels.at(sport=sport, players=(viewer, *candidates))
            mine = levels.get(viewer)
            # The set is up to fifteen minutes old and the rating read is live,
            # so a player can be in one and not the other. She is dropped here —
            # before the row read rather than after it — so a stale set costs one
            # rating read and never a row read as well, and so a player is never
            # printed at a Level the platform had to impute.
            rated = tuple(one for one in candidates if one in levels)
            if not rated:
                continue

            for row in await self._rows.players(player_ids=rated):
                level = levels[row.player_id]
                distance = None if mine is None else abs(level.value - mine.value)
                candidate = Candidate(player=row, level=level, distance=distance)
                held = best.get(row.player_id)
                if held is None or candidate.closer_than(held):
                    best[row.player_id] = candidate

        return tuple(
            PersonCard(
                player_id=candidate.player.player_id,
                stamp=stamp,
                nickname=candidate.player.nickname,
                level=candidate.level,
            )
            for candidate in by_closeness(best.values())[:NEW_PLAYERS_CAP]
        )

    async def _clubs(
        self,
        *,
        sports: tuple[Sport, ...],
        now: Instant,
        stamp: Stamp,
        city: str | None,
    ) -> tuple[ClubCard, ...]:
        since = _back(now, NEW_CLUB_WINDOW)
        found: list[UUID] = []

        for sport in sports:
            key = ArrivalKey(city=city, sport=sport, kind=ArrivalKind.CLUBS)
            for club_id in await self._set(
                key, partial(self._arrivals.club_ids, sport=sport, since=since)
            ):
                # A club selling two of the viewer's sports is one club, and the
                # shelf says *new*, which it is exactly once.
                if club_id not in found:
                    found.append(club_id)

        if not found:
            return ()

        rows: Sequence[NewClub] = await self._rows.clubs(club_ids=tuple(found))
        return tuple(
            ClubCard(
                club_id=club.club_id,
                stamp=stamp,
                name=club.name,
                distance_km=club.distance_km,
            )
            for club in by_arrival(rows)[:NEW_CLUBS_CAP]
        )

    async def _set(
        self,
        key: ArrivalKey,
        produce: Callable[[], Awaitable[tuple[UUID, ...]]],
    ) -> tuple[UUID, ...]:
        """Cache-aside over one key, and the only place the cache is touched.

        An empty answer is stored like any other. A city with no new clubs is a
        fact worth fifteen minutes as much as a city with six, and skipping the
        write would make the empty case the one that pays the full query on every
        single request.
        """

        held = await self._sets.get(key)
        if held is not None:
            return held
        found = await produce()
        await self._sets.put(key, found)
        return found


def _back(now: Instant, window: Minutes) -> Instant:
    """The far edge of a window that runs backwards from now."""

    return shifted(now, minutes(-window))
