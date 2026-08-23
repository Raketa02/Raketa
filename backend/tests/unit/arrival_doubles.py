"""Hand-written stubs over Now's four arrival ports, per the repo's testing rule.

They record what they were asked as well as what they answered, because half of
what shelves 4 and 5 promise is about the *asking*: a set that was cached is a
set the arrivals port was not asked for a second time, and there is no other way
to see that from the outside.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Mapping, Sequence
from uuid import UUID, uuid4

from app.kernel import Instant, Sport, instant

from app.modules.now.domain.arrivals import ArrivalKey, NewClub, NewPlayer
from app.modules.now.domain.ports import ArrivalRows, ArrivalSets, Levels, NewArrivals
from app.modules.now.domain.screen import Level

AT: Instant = instant(datetime(2026, 8, 22, 17, 30, tzinfo=timezone.utc))


def days_ago(days: float) -> Instant:
    return instant(AT - timedelta(days=days))


def a_player(
    *, nickname: str = "someone", joined: Instant | None = None, who: UUID | None = None
) -> NewPlayer:
    return NewPlayer(
        player_id=who or uuid4(),
        nickname=nickname,
        joined_at=joined or days_ago(1),
    )


def a_club(
    *,
    name: str = "a club",
    joined: Instant | None = None,
    which: UUID | None = None,
    distance_km: int | None = None,
) -> NewClub:
    return NewClub(
        club_id=which or uuid4(),
        name=name,
        joined_at=joined or days_ago(1),
        distance_km=distance_km,
    )


class FakeNewArrivals(NewArrivals):
    """The membership half: who is new here, per sport."""

    def __init__(
        self,
        *,
        players: Mapping[Sport, tuple[UUID, ...]] | None = None,
        clubs: Mapping[Sport, tuple[UUID, ...]] | None = None,
    ) -> None:
        self._players = dict(players or {})
        self._clubs = dict(clubs or {})
        self.player_asks: list[tuple[Sport, Instant]] = []
        self.club_asks: list[tuple[Sport, Instant]] = []

    async def player_ids(self, *, sport: Sport, since: Instant) -> tuple[UUID, ...]:
        self.player_asks.append((sport, since))
        return self._players.get(sport, ())

    async def club_ids(self, *, sport: Sport, since: Instant) -> tuple[UUID, ...]:
        self.club_asks.append((sport, since))
        return self._clubs.get(sport, ())


class FakeArrivalRows(ArrivalRows):
    """The row half: what an inert card prints. Silently short on a stranger."""

    def __init__(
        self,
        *,
        players: Sequence[NewPlayer] = (),
        clubs: Sequence[NewClub] = (),
    ) -> None:
        self._players = {row.player_id: row for row in players}
        self._clubs = {row.club_id: row for row in clubs}
        self.player_asks: list[tuple[UUID, ...]] = []
        self.club_asks: list[tuple[UUID, ...]] = []

    async def players(self, *, player_ids: Sequence[UUID]) -> tuple[NewPlayer, ...]:
        self.player_asks.append(tuple(player_ids))
        return tuple(self._players[one] for one in player_ids if one in self._players)

    async def clubs(self, *, club_ids: Sequence[UUID]) -> tuple[NewClub, ...]:
        self.club_asks.append(tuple(club_ids))
        return tuple(self._clubs[one] for one in club_ids if one in self._clubs)


class FakeLevels(Levels):
    """A Level per player per sport; absent for a player rated at neither."""

    def __init__(
        self, held: Mapping[Sport, Mapping[UUID, Level]] | None = None
    ) -> None:
        self._held = {sport: dict(rows) for sport, rows in (held or {}).items()}
        self.asks: list[tuple[Sport, tuple[UUID, ...]]] = []

    async def at(
        self, *, sport: Sport, players: Sequence[UUID]
    ) -> Mapping[UUID, Level]:
        self.asks.append((sport, tuple(players)))
        rows = self._held.get(sport, {})
        return {one: rows[one] for one in players if one in rows}


class RecordingArrivalSets(ArrivalSets):
    """A dictionary that remembers every question and every answer stored."""

    def __init__(self) -> None:
        self.held: dict[str, tuple[UUID, ...]] = {}
        self.gets: list[str] = []
        self.puts: list[tuple[str, tuple[UUID, ...]]] = []

    async def get(self, key: ArrivalKey) -> tuple[UUID, ...] | None:
        self.gets.append(key.key)
        return self.held.get(key.key)

    async def put(self, key: ArrivalKey, ids: tuple[UUID, ...]) -> None:
        self.puts.append((key.key, ids))
        self.held[key.key] = ids


class StoppedClock:
    """A clock that answers one instant until it is told to move."""

    def __init__(self, at: Instant = AT) -> None:
        self.at = at

    def now(self) -> Instant:
        return self.at

    def advance(self, *, minutes: int = 0, seconds: int = 0) -> None:
        self.at = instant(self.at + timedelta(minutes=minutes, seconds=seconds))
