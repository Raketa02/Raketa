"""The Discovery context's ports, **each in its own words**.

One is the context's own storage — the directory (``PlayerDirectory``), not a
demand. The rest are its neighbours, each signed in ``infrastructure/`` over
what the neighbour publishes, wired by the composition root, each with a row in
``app/bootstrap/discovery_demands.py``:

- ``DirectorySources`` — what the owners hold about one account now: the
  nickname (``users``) and the profile's facts, which every entry is written
  from, live and in the rebuild;
- ``ReadersRelations`` — the reader's relation to each person on a row, from
  Friends' own read (a request the reader's block hides reads ``NONE``);
- ``BlocksEitherWay`` — everybody the reader blocked or who blocked the reader,
  whom no people row may show (``docs/adr/0204`` §2);
- ``LevelsHeld`` — every sport a person holds a level in, read live off the
  rating's published read, for New in Raketa's tiles;
- ``DirectoryFaces`` — a short-lived link to a photograph the directory names;
- ``LevelSources`` — what a player's rating stream in a sport stands at now,
  which every current-level entry is written from (#794);
- ``HowEven`` — **the Forecast for one player a side**, the one forecast
  function's: *Same competitive level*'s % even (#794).

The current levels (``PlayerLevels``, #794) are the context's own storage too.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.discovery.domain.directory import DirectoryEntry
from app.modules.discovery.domain.levels import CurrentLevel, Estimate
from app.modules.discovery.domain.new_in_raketa import Joiner
from app.modules.discovery.domain.relation import Relation


@runtime_checkable
class PlayerDirectory(Protocol):
    """The directory: one entry per account, and one row per tag.

    **Same session as the caller**: an entry saved is read by the read that
    follows it in the transaction.
    """

    async def save(self, entry: DirectoryEntry) -> None:
        """Write the entry whole — its tags replaced by the entry's."""
        ...

    async def forget(self, player_id: UUID) -> None:
        """An account that is gone: its entry and its tags go. Nothing to
        forget is no error."""
        ...

    async def who_joined(
        self,
        *,
        after: Instant,
        leaving_out: Collection[UUID],
        limit: int | None = None,
    ) -> tuple[Joiner, ...]:
        """Everybody who may be on a people row and joined **after**
        ``joined_after``, newest first: named, playing, *Show me to new people*
        on, and none of ``leaving_out`` (the reader and every block either
        way). At most ``limit``, when one is given."""
        ...


@runtime_checkable
class DirectorySources(Protocol):
    """The owners, asked about one account as they stand now."""

    async def entry_of(self, player_id: UUID) -> DirectoryEntry | None:
        """``None`` for an account that is gone — none was ever opened, or it
        was disabled — whose entry the directory forgets."""
        ...

    async def every_account(self) -> Sequence[UUID]:
        """Every account the store holds a stream for, oldest first — the
        rebuild's walk."""
        ...


@runtime_checkable
class ReadersRelations(Protocol):
    async def relations_of(
        self, reader: UUID, players: Collection[UUID]
    ) -> Mapping[UUID, Relation]:
        """The reader's relation to each of these — **everybody asked is
        answered**, ``NONE`` where nothing stands."""
        ...


@runtime_checkable
class BlocksEitherWay(Protocol):
    async def either_way(self, reader: UUID) -> frozenset[UUID]:
        """Everybody the reader blocked and everybody who blocked the reader,
        as one set: a row may not tell which. Raises rather than answering an
        empty set it can't stand behind — a row shown on that would suggest a
        blocked person."""
        ...


@final
@dataclass(frozen=True, slots=True)
class SportLevel:
    sport: Sport
    #: The published Level, as the rating committed it.
    level: float


@runtime_checkable
class LevelsHeld(Protocol):
    async def levels_of(
        self, player_ids: Collection[UUID]
    ) -> Mapping[UUID, tuple[SportLevel, ...]]:
        """Every sport each of these holds a level in, in the sports' own
        order. **Everybody asked is answered**: an unrated player with none."""
        ...


@runtime_checkable
class DirectoryFaces(Protocol):
    async def photo_url(self, player_id: UUID, photo_id: UUID) -> str:
        """A short-lived link to the photograph, signed as its owner. Signing
        is arithmetic: nothing asks whether the object is still there."""
        ...


@final
@dataclass(frozen=True, slots=True)
class Candidate:
    """Somebody a level window found, with their face and every level they
    hold among the sports the reader is compared in."""

    player_id: UUID
    nickname: str
    photo_id: UUID | None
    levels: tuple[CurrentLevel, ...]


@runtime_checkable
class PlayerLevels(Protocol):
    """Every player's current level per sport — one entry per player and
    sport, **indexed by sport and level** (#794).

    **Same session as the caller**, as the directory is.
    """

    async def save(self, level: CurrentLevel) -> None:
        """Write the entry — **unless the one stored has more results**: a
        fold read before a later move committed never takes the move back."""
        ...

    async def of_player(self, player_id: UUID) -> Mapping[Sport, CurrentLevel]:
        """Every sport this player holds a level in."""
        ...

    async def near(
        self,
        around: Mapping[Sport, float],
        *,
        within: float | None,
        beyond: float | None,
        compared_in: Collection[Sport],
        leaving_out: Collection[UUID],
    ) -> tuple[Candidate, ...]:
        """Everybody who may be on a people row — named, playing, *Show me to
        new people* on, none of ``leaving_out`` — holding a level in one of
        ``around``'s sports **within** ``within`` of the level given there
        (everybody, with ``None``) and further than ``beyond`` from it (``None``:
        no nearer window was read). Each with every level they hold in
        ``compared_in``, by player id."""
        ...

    async def shared_sports(
        self, sports: Collection[Sport], *, leaving_out: Collection[UUID]
    ) -> tuple[Sport, ...]:
        """Which of these sports at least one player who may be on a people row
        holds a level in, in the sports' own order."""
        ...

    async def least_doubt(self, sports: Collection[Sport]) -> Mapping[Sport, float]:
        """The least Uncertainty anybody holds in each of these sports — absent
        where nobody holds a level. Nobody a window has not read yet is surer,
        which is what bounds how even they could read."""
        ...


@runtime_checkable
class LevelSources(Protocol):
    """The rating, asked about a player's level as it stands now."""

    async def level_of(self, player_id: UUID, sport: Sport) -> CurrentLevel | None:
        """Where the player's rating in the sport stands — ``None`` for a sport
        they hold none in."""
        ...

    async def every_level(self) -> Sequence[CurrentLevel]:
        """Every rating there is, as it stands — the rebuild's walk, in the
        order the ratings were opened."""
        ...


@runtime_checkable
class HowEven(Protocol):
    def percent_even(self, sport: Sport, yours: Estimate, theirs: Estimate) -> int:
        """The Forecast for a game in ``sport`` with one player a side — in
        padel and badminton the two as opposite sides (call 8 of #790) — as the
        whole percent a game card prints. It falls with the gap and with either
        Uncertainty, within the forecast's own bounds. **Arithmetic, never a
        read.**"""
        ...
