"""The Rankings context's ports, **each in its own words**.

Two are the context's own storage — the projection (``RankingRows``) and the
level history (``LevelHistory``), neither a demand. The rest are its
neighbours, each signed in ``infrastructure/`` over what the neighbour
publishes, wired by the composition root, each with a row in
``app/bootstrap/ranking_demands.py``:

- ``RatingHistories`` — the rating's own events, which the rows are folded
  from: read off its streams as recorded, because a stream's durable event
  names are rating's published contract and a fold needs every move, which no
  read port of rating's carries;
- ``RankedFaces`` — a nickname from ``users``, a photograph from the Player
  profile;
- ``SportLevels`` — whether the reader holds a level in a sport, read live from
  the rating.

Friends' friend list, blocks both ways and *Show me in General* arrive with
the tickets that read them (#771, #772).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant, Sport, invariant
from app.modules.rankings.domain.ranking import LevelPoint, RankingRow, RatingHistory


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

    async def listed(
        self, sport: Sport, *, at_least: int, since: Instant
    ) -> tuple[RankingRow, ...]:
        """The rows with ``at_least`` results whose last settled after
        ``since``, **in the ranking's order**, best first."""
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
