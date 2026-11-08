"""The Rankings context's ports, **each in its own words**.

Two are the context's own storage — the projection (``RankingRows``) and the
level history (``LevelHistory``), neither a demand — and one is the outside
world's: **the kept orders** (``GeneralOrders``, #770), each sport's General
order worked out and kept for a minute in the ephemeral store, lossy by design.
The rest are its neighbours, each signed in ``infrastructure/`` over what the neighbour
publishes, wired by the composition root, each with a row in
``app/bootstrap/ranking_demands.py``:

- ``RatingHistories`` — the rating's own events, which the rows are folded
  from: read off its streams as recorded, because a stream's durable event
  names are rating's published contract and a fold needs every move, which no
  read port of rating's carries;
- ``RankedFaces`` — a nickname from ``users``, a photograph from the Player
  profile;
- ``SportLevels`` — whether the reader holds a level in a sport, read live from
  the rating;
- ``ReadersFriends`` — the reader's friends now, from Friends' own friend list
  (#771), which the Friends view is worked out over;
- ``BlocksEitherWay`` — everybody a block stands between the reader and, either
  way round, read live from the blocks (#772): their rows are left out of
  each other's views;
- ``GeneralSwitches`` — a player's *Show me in General*, read live off their
  profile with the version it stands at (#772), which the projection follows.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport, invariant
from app.modules.rankings.domain.general_order import (
    GeneralOrder,
    ListedAndThen,
    ListedRow,
    OrderKey,
)
from app.modules.rankings.domain.ranking import (
    GeneralSwitch,
    LevelPoint,
    RankingRow,
    RatingHistory,
)


@runtime_checkable
class RankingRows(Protocol):
    """The projection: one row per player per sport.

    **Same session as the caller**: a row saved is read by the read that
    follows it in the transaction.
    """

    async def save(self, row: RankingRow) -> None:
        """Write the row a fold made. **A row is never replaced by one with
        fewer results**: results only ever add up, so a fold that read the
        stream before another delivery's move committed can't take that move
        back."""
        ...

    async def of_player(self, player_id: UUID) -> tuple[RankingRow, ...]:
        """The player's rows, every sport they have a result in."""
        ...

    async def follow(self, switch: GeneralSwitch) -> None:
        """**The player's rows follow their *Show me in General*** (#772): the
        switch is kept beside them, per player, so it holds in **every
        sport**, one with no row yet included — a switch turned before a first
        result holds when that result makes the row. **A switch read at an
        older version never replaces a newer one.**"""
        ...

    async def listed(
        self,
        sport: Sport,
        *,
        at_least: int,
        since: Instant,
        then: Instant,
        among: Collection[UUID] | None = None,
    ) -> tuple[ListedAndThen, ...]:
        """The rows with ``at_least`` results whose last settled after
        ``since``, **in the ranking's order**, best first — **each with its
        player's level-history point at ``then``** where their last result
        settled after it: their latest at or before it, or, for a player with
        none by then, their first. **A player with no result since stood then
        where they stand now**, and has no point here. **One pass**, so the
        order and every chip are worked out from one reading (#770). With
        ``among``, only those players' rows — a reader and their friends
        (#771). **Each says whether its player is hidden from General**
        (#772) — every row, whichever view reads it."""
        ...


@runtime_checkable
class LevelHistory(Protocol):
    """The level history: every point a rating's stream makes, **keyed by the
    event** that made it (``docs/adr/0203`` §10).

    **Same session as the caller**, as the projection is.
    """

    async def append(self, points: Sequence[LevelPoint]) -> int:
        """Every point not yet held — how many were new. **A point already held
        is left as it is**, so a redelivery, or a rebuild after live delivery,
        changes nothing."""
        ...

    async def points_at(
        self, sport: Sport, at: Instant, player_ids: Collection[UUID]
    ) -> Mapping[UUID, LevelPoint]:
        """Each player's point in the sport at ``at``: their **latest at or
        before it** — or, for a player with none by then, **their first**. A
        player with no point at all is left out."""
        ...


@runtime_checkable
class RatingHistories(Protocol):
    """The rating's record, which every row is folded from."""

    async def history_of(self, player_id: UUID, sport: Sport) -> RatingHistory | None:
        """The player's rating in the sport, every result on it in stream order;
        ``None`` for a sport they hold no rating in."""
        ...

    async def every_history(self) -> Sequence[RatingHistory]:
        """Every rating there is — **the rebuild's read**, walked in the order
        the streams were opened."""
        ...


@final
@dataclass(frozen=True, slots=True)
class RankedFace:
    """A nickname, whole and never with an @ (``docs/adr/0199`` §1), and a
    photograph — ``photo_id`` and ``photo_url`` exactly together. ``nickname``
    is ``None`` for an id nobody can name, and its row is left off."""

    player_id: UUID
    nickname: str | None = None
    photo_id: UUID | None = None
    photo_url: str | None = None

    def __post_init__(self) -> None:
        invariant(
            (self.photo_id is None) == (self.photo_url is None),
            f"a photograph with only half an address: {self!r}",
        )


@runtime_checkable
class RankedFaces(Protocol):
    async def faces_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, RankedFace]:
        """Everybody asked about is answered, in one question about the set."""
        ...


@runtime_checkable
class SportLevels(Protocol):
    async def holds_a_level(self, player_id: UUID, sport: Sport) -> bool:
        """Whether the player holds a level in the sport now, read live."""
        ...


@runtime_checkable
class ReadersFriends(Protocol):
    async def friends_of(self, reader: UUID) -> frozenset[UUID]:
        """**The reader's friends now** — the reader never among them, and
        nobody whose request is merely open either way. Read live, so a friend
        just added is in the next read, and one removed, or whose block's
        delivery ended the friendship, is not."""
        ...


@runtime_checkable
class BlocksEitherWay(Protocol):
    async def blocked_either_way(self, reader: UUID) -> frozenset[UUID]:
        """**Everybody a standing block sits between the reader and, whichever
        of them made it** — one flat set, so nothing here can tell which way
        round — read live, so a block made a moment ago hides its rows on the
        next read and a lifted one shows them again. **Raises rather than
        answer an empty set it cannot stand behind**: an empty set would show
        a blocked pair each other's rows."""
        ...


@runtime_checkable
class GeneralSwitches(Protocol):
    async def switch_of(self, player_id: UUID) -> GeneralSwitch | None:
        """The player's *Show me in General* as their profile stands now, read
        live, with the version it stands at — ``None`` for an id with no
        profile."""
        ...

    async def every_switch(self) -> Sequence[GeneralSwitch]:
        """Every profile's switch — **the rebuild's read**, one a player with
        no rating yet included, so a projection rebuilt from nothing holds the
        switch of everybody who could later be listed."""
        ...


class GeneralOrderLost(Exception):
    """A kept order could not be read to the end — the store went away
    mid-read. **The read works the order out again**: a kept order is a copy
    the projection can always make."""


@runtime_checkable
class HeldOrder(Protocol):
    """One kept order, read where it is kept: every read of it is of the same
    order, whatever was kept after it."""

    @property
    def worked_out_at(self) -> Instant: ...

    @property
    def listed(self) -> int:
        """How many rows the order holds — *of 480*."""
        ...

    async def rows(self, start: int, stop: int) -> tuple[ListedRow, ...]:
        """The rows from index ``start`` to ``stop``, best first."""
        ...

    async def place_of(self, player_id: UUID) -> int | None:
        """The player's place, or ``None`` when the order doesn't list them."""
        ...

    async def ahead_of(self, key: OrderKey) -> int:
        """How many rows stand strictly ahead of ``key`` in the order."""
        ...

    async def up_to(self, key: OrderKey) -> int:
        """How many rows stand ahead of ``key`` or at it."""
        ...


@runtime_checkable
class GeneralOrders(Protocol):
    """Each sport's General order, worked out and kept (``docs/adr/0203``
    §10). **Lossy**: an order that is gone is worked out again, so nothing
    here may fail a read — an adapter whose store is down holds nothing.

    **Every forget is counted**, and an order is kept with the count its pass
    began at: one kept at an older count — a pass that read the projection
    before a write, and kept after that write forgot — **is held by nobody**,
    so a write is never undone by a slow pass."""

    async def held(self, sport: Sport) -> HeldOrder | None:
        """The order last kept for the sport at the current count, however
        old — whether it is fresh enough to read is the reader's to judge —
        or ``None``."""
        ...

    async def forgotten(self, sport: Sport) -> int:
        """How many times the sport's order has been forgotten — what a pass
        reads before it reads the projection."""
        ...

    async def keep(self, order: GeneralOrder, *, forgotten: int) -> None:
        """Keep the order for its sport, in place of the one held — worked
        out by a pass that began at ``forgotten``."""
        ...

    async def forget(self, sport: Sport) -> None:
        """Forget the sport's order, and count it: a ranking write in it
        moved a row."""
        ...
