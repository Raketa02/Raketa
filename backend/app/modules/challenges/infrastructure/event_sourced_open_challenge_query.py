"""``OpenChallengeQuery`` over the event log itself — no projection, and none
coming.

**Because the standing is derived, the read has to be too.** A projection of
*who has an open challenge with whom* would be a status column with a table
around it: right until a deadline passed, wrong until something swept it, and
believed throughout. What is here instead is a fold of the live streams against
the clock the caller supplies, which is the same answer at every instant.

**It reads the log through the session, not through ``DomainEventStore``.** The
question is *every challenge stream these people are seated in*, which no
aggregate-repository port offers and no keyed read can serve: a challenge's id is
minted rather than derived from the people in it. That is the Blocks context's
exact position, arrived at from the opposite direction — a ``uuid5`` that cannot
be reversed there, an id with nothing to reverse *to* here.

**Two statements, not one.** The first finds the streams by matching the
serialized seats; the second reads those streams whole. They cannot be one,
because a ``SeatAccepted`` row carries no seats and dropping it would fold a
court whose answers had gone missing — the failure would look like an open
challenge that never closes.

**The match is a substring, and that is a decision.** The seats cross the wire as
one code per seat (``seats.py``), so a player is inside an array of strings
rather than in a scalar column of their own — and JSON array containment is
PostgreSQL's ``@>`` and SQLite's ``json_each``, which are not one statement. A
uuid is 36 characters of hex and hyphens with no other meaning in a seat code, so
a substring match on it is exact in the only sense that matters here: nothing
else in a seat code can spell one. What is *not* claimed is that this is
selective — see the cost note below.

**Cost.** Bounded by how many challenges the platform has ever recorded, not by
how many this player is in — a substring match cannot use a B-tree. The index
that fixes it is PostgreSQL's, over a table with no rows on a platform with no
deployed environment, and it belongs with the first query that measures it rather
than with a guess about which; that is `0010_search_telemetry`'s own decision
about its GIN index, and this read is on a **send** path rather than on every
search, which is the one that will want it first.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import fields
from itertools import combinations
from typing import Collection
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.events.envelope import SerializedEventEnvelope
from app.application.ports.events import EventCodec
from app.infrastructure.events.event_store_model import EventStoreORM
from app.kernel import Instant
from app.modules.challenges.domain.challenge import Challenge
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
    this query, which reads as *nobody has an open challenge* and would let the
    one-per-pair rule quietly stop holding. So the spelling is taken from the
    event classes rather than trusted, and a rename stops the process from
    starting.
    """

    for event_cls in _SEATING_EVENTS:
        if name not in {field.name for field in fields(event_cls)}:
            raise RuntimeError(
                f"{event_cls.__name__} has no field {name!r}: the open-challenge "
                "query matches on it and would silently find nobody"
            )
    return name


_SEATS_KEY = _seats_key("seats")


class EventSourcedOpenChallengeQuery:
    """``OpenChallengeQuery`` over ``event_store``, folding each stream it reads."""

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    async def open_pairs_among(
        self, player_ids: Collection[UUID], *, now: Instant
    ) -> frozenset[frozenset[UUID]]:
        """Every pair of these people with an open game already between them.

        Empty in, empty out, and that emptiness is **measured**: one person is
        not a pair, so there is nothing for a challenge to sit between.
        """

        wanted = set(player_ids)
        if len(wanted) < 2:
            return frozenset()

        streams = await self._streams_seating(wanted)
        pairs: set[frozenset[UUID]] = set()
        for events in streams.values():
            challenge = Challenge.from_history(events)
            # The intersection, not the whole line-up: a challenge reaching
            # outside this court is real and is somebody else's business.
            together = sorted(challenge.players_in_it_at(now) & wanted)
            pairs.update(frozenset(pair) for pair in combinations(together, 2))
        return frozenset(pairs)

    async def _streams_seating(
        self, player_ids: set[UUID]
    ) -> dict[UUID, list[DomainEvent]]:
        """The whole of every challenge stream any of these people is seated in."""

        found = await self._session.execute(
            select(EventStoreORM.aggregate_id)
            .where(
                EventStoreORM.aggregate_type == CHALLENGE_AGGREGATE,
                or_(
                    *(
                        EventStoreORM.payload[_SEATS_KEY]
                        .as_string()
                        .like(f"%{player_id}%")
                        for player_id in sorted(player_ids)
                    )
                ),
            )
            .distinct()
        )
        challenge_ids = list(found.scalars().all())
        if not challenge_ids:
            return {}

        rows = await self._session.execute(
            select(EventStoreORM)
            .where(
                EventStoreORM.aggregate_type == CHALLENGE_AGGREGATE,
                EventStoreORM.aggregate_id.in_(challenge_ids),
            )
            .order_by(EventStoreORM.version)
        )
        streams: dict[UUID, list[DomainEvent]] = defaultdict(list)
        for row in rows.scalars().all():
            streams[row.aggregate_id].append(self._decode(row))
        return streams

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
