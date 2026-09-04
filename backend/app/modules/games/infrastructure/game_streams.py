"""Finding the game streams to fold. **Two reads, and only one starts from a player.**

Every read this context had until ``docs/adr/0139`` started the same way — *which
streams seat this person* — and they differ only in what they fold the answer
into: the pairs, a count, the last five results, or the whole aggregate for a
screen. Written once, because the interesting half is a **coupling to a
serialized field name**, and a coupling like that written twice is one that gets
fixed in one place.

The second read starts from **nobody**, and is at the bottom of this file. The
rating context walks confirmed results forward and has no player to ask about
until it has folded the game.

**The match is a substring, and it is the same decision ``challenges`` made.**
The court crosses the wire as one code per seating (``lineup.py``), so a player is
inside an array of strings rather than in a scalar column of their own — and JSON
array containment is PostgreSQL's ``@>`` and SQLite's ``json_each``, which are not
one statement. A uuid is 36 characters of hex and hyphens with no other meaning in
a seating code, so a substring match on it is exact in the only sense that matters
here.

**Two statements, not one.** The first finds the streams by matching the
serialized court; the second reads those streams whole. They cannot be one,
because a ``ResultProposed`` row carries no court and dropping it would fold a
game whose scores had gone missing — the failure would look like a game nobody
ever entered.

**Cost.** Bounded by how many games the platform has ever recorded, because a
substring match cannot use a B-tree. The index that fixes it is PostgreSQL's,
over a table with no rows on a platform with no deployed environment, and it
belongs with the first query that measures it.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import fields
from typing import Collection
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EventCodec
from app.infrastructure.events.event_store_model import EventStoreORM
from app.modules.games.domain.events import GamePlanned
from app.modules.games.infrastructure.event_sourced_game_repository import (
    GAME_AGGREGATE,
)
from app.shared.domain import DomainEvent


def _seatings_key(name: str) -> str:
    """The JSON key the codec writes for the court, checked at import.

    This is the one read in this context that matches on a **serialized field
    name** rather than on a stream id, and what is avoidable about that coupling
    is it being *silent*: a renamed field would make every game invisible to
    these queries, which reads as *nobody has ever played* and would leave
    familiarity standing down for ever with a green build.
    """

    if name not in {field.name for field in fields(GamePlanned)}:
        raise RuntimeError(
            f"GamePlanned has no field {name!r}: the game stream reads match on "
            "it and would silently find nobody"
        )
    return name


SEATINGS_KEY = _seatings_key("seatings")


async def streams_seating(
    session: AsyncSession, codec: EventCodec, player_ids: Collection[UUID]
) -> dict[UUID, list[DomainEvent]]:
    """The whole of every game stream any of these people is on the court of.

    Ordered by ``version`` within each stream, which is what a fold needs and the
    only order it may be handed: a replay is a sequence and not a set.
    """

    wanted = sorted(set(player_ids))
    if not wanted:
        return {}

    found = await session.execute(
        select(EventStoreORM.aggregate_id)
        .where(
            EventStoreORM.aggregate_type == GAME_AGGREGATE,
            or_(
                *(
                    EventStoreORM.payload[SEATINGS_KEY].as_string().like(f"%{one}%")
                    for one in wanted
                )
            ),
        )
        .distinct()
    )
    game_ids = list(found.scalars().all())
    if not game_ids:
        return {}

    rows = await session.execute(
        select(EventStoreORM)
        .where(
            EventStoreORM.aggregate_type == GAME_AGGREGATE,
            EventStoreORM.aggregate_id.in_(game_ids),
        )
        .order_by(EventStoreORM.version)
    )
    streams: dict[UUID, list[DomainEvent]] = defaultdict(list)
    for row in rows.scalars().all():
        streams[row.aggregate_id].append(_decode(codec, row))
    return dict(streams)


async def every_stream(
    session: AsyncSession, codec: EventCodec
) -> dict[UUID, list[DomainEvent]]:
    """Every game stream there is, each ordered by ``version``.

    **The one read here that does not start from a player**, because the caller
    it exists for does not have one: the rating context walks confirmed results
    forward and has no idea whose they are until it has folded them
    (``docs/adr/0139``). It is a plain scan of the aggregate type rather than the
    substring match above, so it is the *cheaper* of the two reads per row — and
    the more expensive one per run, because it reads every game rather than one
    person's.

    **Cost.** Bounded by how many games the platform has ever recorded, like
    everything else in this context. The pagination that fixes it belongs with
    the first run that measures it, and it will need the ordering key the caller
    already derives — the moment a result became final — to be somewhere a
    ``WHERE`` can reach.
    """

    rows = await session.execute(
        select(EventStoreORM)
        .where(EventStoreORM.aggregate_type == GAME_AGGREGATE)
        .order_by(EventStoreORM.aggregate_id, EventStoreORM.version)
    )
    streams: dict[UUID, list[DomainEvent]] = defaultdict(list)
    for row in rows.scalars().all():
        streams[row.aggregate_id].append(_decode(codec, row))
    return dict(streams)


def _decode(codec: EventCodec, row: EventStoreORM) -> DomainEvent:
    return codec.decode(
        SerializedEventEnvelope(
            id=row.id,
            event_type=row.event_type,
            schema_version=row.schema_version,
            payload=dict(row.payload),
            occurred_at=row.occurred_at,
            created_at=row.created_at,
        )
    )
