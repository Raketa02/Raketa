"""Finding the challenge streams a player is seated in. **One read, two callers.**

Both reads this context has over the log start the same way — *which streams
seat any of these people* — and they differ only in what they fold the answer
into. Written once, because the interesting half is a **coupling to a serialized
field name**, and a coupling like that written twice is one that gets fixed in
one place.

**The match is a substring, and that is a decision.** The seats cross the wire as
one code per seat (``seats.py``), so a player is inside an array of strings rather
than in a scalar column of their own — and JSON array containment is PostgreSQL's
``@>`` and SQLite's ``json_each``, which are not one statement. A uuid is 36
characters of hex and hyphens with no other meaning in a seat code, so a substring
match on it is exact in the only sense that matters here: nothing else in a seat
code can spell one. What is *not* claimed is that this is selective.

**Two statements, not one.** The first finds the streams by matching the
serialized seats; the second reads those streams whole. They cannot be one,
because a ``SeatAccepted`` row carries no seats and dropping it would fold a court
whose answers had gone missing — the failure would look like an open challenge
that never closes.

**Cost.** Bounded by how many challenges the platform has ever recorded, not by
how many this player is in — a substring match cannot use a B-tree. The index that
fixes it is PostgreSQL's, over a table with no rows on a platform with no deployed
environment, and it belongs with the first query that measures it rather than with
a guess about which.
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
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    SeatsInvited,
)
from app.modules.challenges.infrastructure.event_sourced_challenge_repository import (
    CHALLENGE_AGGREGATE,
)
from app.shared.domain import DomainEvent

#: The three events that seat somebody. Every stream opens with one of the first
#: two, so matching these finds every challenge a player is in — and a stream
#: whose membership later changed carries the whole new court on the third.
_SEATING_EVENTS = (ChallengeSent, ChallengeOpenedFromMutualInterest, SeatsInvited)


def _seats_key(name: str) -> str:
    """The JSON key the codec writes for the seats, checked at import.

    This is the one read in this context that matches on a **serialized field
    name** rather than on a stream id, and what is avoidable about that coupling
    is it being *silent*: a renamed field would make every challenge invisible to
    these queries, which reads as *nobody has an open challenge* and would let the
    one-per-pair rule quietly stop holding. So the spelling is taken from the
    event classes rather than trusted, and a rename stops the process from
    starting.
    """

    for event_cls in _SEATING_EVENTS:
        if name not in {field.name for field in fields(event_cls)}:
            raise RuntimeError(
                f"{event_cls.__name__} has no field {name!r}: the challenge "
                "stream reads match on it and would silently find nobody"
            )
    return name


SEATS_KEY = _seats_key("seats")


async def streams_seating(
    session: AsyncSession, codec: EventCodec, player_ids: Collection[UUID]
) -> dict[UUID, list[DomainEvent]]:
    """The whole of every challenge stream any of these people is seated in.

    Ordered by ``version`` within each stream, which is what a fold needs and the
    only order it may be handed: a replay is a sequence and not a set.
    """

    wanted = sorted(set(player_ids))
    if not wanted:
        return {}

    found = await session.execute(
        select(EventStoreORM.aggregate_id)
        .where(
            EventStoreORM.aggregate_type == CHALLENGE_AGGREGATE,
            or_(
                *(
                    EventStoreORM.payload[SEATS_KEY]
                    .as_string()
                    .like(f"%{player_id}%")
                    for player_id in wanted
                )
            ),
        )
        .distinct()
    )
    challenge_ids = list(found.scalars().all())
    if not challenge_ids:
        return {}

    rows = await session.execute(
        select(EventStoreORM)
        .where(
            EventStoreORM.aggregate_type == CHALLENGE_AGGREGATE,
            EventStoreORM.aggregate_id.in_(challenge_ids),
        )
        .order_by(EventStoreORM.version)
    )
    streams: dict[UUID, list[DomainEvent]] = defaultdict(list)
    for row in rows.scalars().all():
        streams[row.aggregate_id].append(_decode(codec, row))
    return dict(streams)


async def stream_of(
    session: AsyncSession, codec: EventCodec, challenge_id: UUID
) -> list[DomainEvent]:
    """One challenge's whole stream, in version order, or nothing at all.

    **The one read here that is not a substring match**, because the one caller
    it has already knows the id: a fill names the challenge it completes
    (``docs/adr/0150`` §2). It is one statement rather than two for the same
    reason — the streams do not have to be *found* — and it uses the B-tree the
    other two cannot.

    It reads the log through the session like its neighbours rather than through
    ``DomainEventStore``, so that *how a challenge stream is addressed* stays
    written once in this module. An empty list is a challenge that does not
    exist, which is a caller's ordinary answer and not a refusal.
    """

    rows = await session.execute(
        select(EventStoreORM)
        .where(
            EventStoreORM.aggregate_type == CHALLENGE_AGGREGATE,
            EventStoreORM.aggregate_id == challenge_id,
        )
        .order_by(EventStoreORM.version)
    )
    return [_decode(codec, row) for row in rows.scalars().all()]


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
