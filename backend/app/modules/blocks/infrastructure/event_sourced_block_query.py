"""``BlockQuery`` over the event log itself — no projection, and none coming.

**The index holds no block data at all** (``docs/adr/0095`` §4,
``docs/adr/0111``), so there is nowhere else this could read. The advisory copy
the input document proposed was dropped rather than deferred: a block is binary,
there is nothing for a ranker to lower, and a copy would have bought a
projection, its staleness window and its rebuild path in exchange for nothing.
What is left is two reads against live state, which is what a safety gate is
supposed to be.

**It reads the log through the session, not through ``DomainEventStore``.** The
pairwise question could go through the port — it is two keyed stream reads — but
the exclusion set cannot: it asks *every stream this player appears in, on either
side*, which is a disjunction over two payload fields and no aggregate-repository
port offers one. Splitting the two reads across two mechanisms would put half of
one question behind an abstraction and half of it not, so both are here, in the
adapter layer where SQL is allowed to live. Each event carries **both** player
ids (``domain/events.py``), which is what makes that read possible at all.

**Same session as the write.** A block taken a moment ago in the same transaction
is visible to a read that follows it, which is the ordinary expectation and the
one a separate connection would quietly break.

**Every failure becomes ``BlockStateUnavailable``** — ``docs/adr/0095`` §5's
*a gate that cannot be evaluated excludes*, made structural. This adapter has no
code path that returns an empty set or a ``False`` it did not measure, which is
the property the port promises and the one a later "make it resilient" change
would otherwise delete. The broad catch is deliberate: what a caller needs to
know is *this gate could not be evaluated*, and every way that can happen —
a dropped connection, a payload the codec cannot read, a column that moved —
means exactly that.

**Cost.** The pairwise read is one statement over two known stream ids, which
``ix_event_store_stream`` already serves. The exclusion set cannot be keyed —
a ``uuid5`` does not reverse — so it matches on the payload, and
``migrations/versions/0009_block_pair_lookup.py`` is the partial expression index
that keeps it from scanning every block on the platform. With it, both reads grow
with how many people this one player has blocked rather than with the size of the
city, which is the bound ADR-0095 §4 states as *tens of rows, not a scan*. The
index is PostgreSQL's; under the SQLite the suite runs on the same statement is
correct and unindexed, which is what a test-sized table wants anyway.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import fields
from typing import Collection
from uuid import UUID

from sqlalchemy import ColumnElement, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EventCodec
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.blocks.domain.block import Block
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.blocks.domain.events import (
    PlayerBlocked,
    PlayerBlockedNamingAScreen,
    PlayerUnblocked,
)
from app.modules.blocks.domain.ids import block_id
from app.modules.blocks.domain.ports import OwnBlock
from app.modules.blocks.infrastructure.event_sourced_block_repository import (
    BLOCK_AGGREGATE,
)
from app.shared.domain import DomainEvent


def _payload_key(name: str) -> str:
    """The JSON key the codec writes for this field, checked at import.

    The one read in this module that is not keyed by stream id matches on a
    *serialized field name*, which is the coupling the sibling repository's
    docstring says a deterministic id exists to avoid — and here it is
    unavoidable, because *every stream this player appears in* is a question
    about the payload. What is avoidable is it being **silent**: a renamed field
    would make the exclusion set come back empty, which reads as *nobody is
    blocked* and is the exact failure this module is written against.

    So the spelling is taken from the event classes rather than trusted, and a
    rename stops the process from starting instead of quietly emptying a safety
    gate. Every event class is checked — v1's too, which the store still holds —
    because the filter matches rows of any of them.
    """

    for event_cls in (PlayerBlocked, PlayerBlockedNamingAScreen, PlayerUnblocked):
        if name not in {field.name for field in fields(event_cls)}:
            raise RuntimeError(
                f"{event_cls.__name__} has no field {name!r}: the block "
                "exclusion query matches on it and would silently return "
                "nobody"
            )
    return name


_BLOCKER_KEY = _payload_key("blocker_id")
_BLOCKED_KEY = _payload_key("blocked_id")


class EventSourcedBlockQuery:
    """``BlockQuery`` over ``event_store``, folding each stream as it reads it."""

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    async def exclusions_for(self, player_id: UUID) -> frozenset[UUID]:
        """Whom this player must not be shown, both directions in one flat set."""

        streams = await self._streams(
            or_(
                EventStoreORM.payload[_BLOCKER_KEY].as_string() == str(player_id),
                EventStoreORM.payload[_BLOCKED_KEY].as_string() == str(player_id),
            )
        )
        excluded: set[UUID] = set()
        for events in streams.values():
            block = Block.from_history(events)
            if not block.is_standing:
                continue
            # Which side of this stream the player is on is the Block's own
            # question. Nothing downstream may branch on the answer — see the
            # port — so what leaves here is a flat set of other people.
            excluded.add(block.counterpart_of(player_id))
        return frozenset(excluded)

    async def blocked_between(self, first: UUID, second: UUID) -> bool:
        """Whether a standing block sits between these two, either way round.

        Two keyed ids and no scan: the ordered pair determines both stream ids,
        so this is the same read ``load`` does, twice, in one statement.
        """

        if first == second:
            return False
        streams = await self._streams(
            EventStoreORM.aggregate_id.in_(
                (block_id(first, second), block_id(second, first))
            )
        )
        return any(
            Block.from_history(events).is_standing for events in streams.values()
        )

    async def blocked_pairs_among(
        self, player_ids: Collection[UUID]
    ) -> frozenset[frozenset[UUID]]:
        """Every standing block between two of these people, in one statement.

        Both payload fields are matched against the **same** id list, which is
        what makes this one query rather than ``K²``: a stream qualifies when
        both of its ends are inside the line-up, and a block reaching outside it
        is somebody else's business. The pair comes back unordered because the
        Block itself is the only thing entitled to know which way round it was
        taken.

        Empty in, empty out — and that emptiness is **measured**, because a
        line-up of nobody has no pair for a block to sit between. Every other way
        of answering nothing raises, exactly as the two reads above do.
        """

        ids = sorted({str(one) for one in player_ids})
        if len(ids) < 2:
            return frozenset()
        streams = await self._streams(
            EventStoreORM.payload[_BLOCKER_KEY].as_string().in_(ids)
            & EventStoreORM.payload[_BLOCKED_KEY].as_string().in_(ids)
        )
        pairs: set[frozenset[UUID]] = set()
        for events in streams.values():
            block = Block.from_history(events)
            if block.is_standing:
                pairs.add(frozenset((block.blocker_id, block.blocked_id)))
        return frozenset(pairs)

    async def blocks_made_by(self, blocker_id: UUID) -> tuple[OwnBlock, ...]:
        """The blocks this player made and has not lifted, newest first.

        **Matched on the blocker's field alone**, so a stream where this player
        is the one blocked never enters the read: the direction is decided by
        the statement, and nothing below it has the other half to leak. Ties at
        one instant go by id, so the order is stable across reads.
        """

        streams = await self._streams(
            EventStoreORM.payload[_BLOCKER_KEY].as_string() == str(blocker_id)
        )
        standing = [
            block
            for block in (Block.from_history(events) for events in streams.values())
            if block.is_standing and block.blocker_id == blocker_id
        ]
        standing.sort(key=lambda block: str(block.blocked_id))
        standing.sort(key=lambda block: block.blocked_at, reverse=True)
        return tuple(
            OwnBlock(blocked_id=block.blocked_id, blocked_at=block.blocked_at)
            for block in standing
        )

    async def _streams(
        self, condition: ColumnElement[bool]
    ) -> dict[UUID, list[DomainEvent]]:
        """The matching streams, each in version order, decoded.

        The whole of this adapter's contact with the database and its codec, so
        the fail-closed translation is written once for all four reads. A
        caller of this method cannot get an answer that is quietly empty because
        something broke.

        **The fold is deliberately outside**, in the four methods above: a
        ``Block`` refusing an event it does not recognise is a bug in this
        codebase, and reporting it as *the gate is temporarily unavailable*
        would hide it behind a status a client is told to retry.
        """

        try:
            result = await self._session.execute(
                select(EventStoreORM)
                .where(
                    EventStoreORM.aggregate_type == BLOCK_AGGREGATE,
                    condition,
                )
                .order_by(EventStoreORM.version)
            )
            streams: dict[UUID, list[DomainEvent]] = defaultdict(list)
            for row in result.scalars().all():
                streams[row.aggregate_id].append(self._decode(row))
            return streams
        except Exception as exc:  # noqa: BLE001 — see the module docstring
            raise BlockStateUnavailable() from exc

    def _decode(self, row: EventStoreORM) -> DomainEvent:
        return self._codec.decode(
            SerializedEventEnvelope(
                id=row.id,
                event_type=row.event_type,
                schema_version=row.schema_version,
                payload=dict(row.payload),
                occurred_at=row.occurred_at,
                created_at=row.created_at,
            )
        )
