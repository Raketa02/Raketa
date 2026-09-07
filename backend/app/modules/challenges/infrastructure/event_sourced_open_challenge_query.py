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

How the streams are found — the substring match on the serialized seats, the two
statements it takes and what it costs — is in ``challenge_streams.py``, shared
with the directory read behind *your own challenges*.
"""

from __future__ import annotations

from itertools import combinations
from typing import Collection
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import EventCodec
from app.kernel import Instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.infrastructure.challenge_streams import streams_seating


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

        streams = await streams_seating(self._session, self._codec, wanted)
        pairs: set[frozenset[UUID]] = set()
        for events in streams.values():
            challenge = Challenge.from_history(events)
            # The intersection, not the whole line-up: a challenge reaching
            # outside this court is real and is somebody else's business.
            together = sorted(challenge.players_in_it_at(now) & wanted)
            pairs.update(frozenset(pair) for pair in combinations(together, 2))
        return frozenset(pairs)
