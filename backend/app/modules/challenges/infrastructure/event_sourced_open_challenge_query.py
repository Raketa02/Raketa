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

**Two questions, one search, and they are not two readings of one fold.** The
pair rule folds every stream these people share and asks who is still arranging;
the mutual mint's idempotence key keeps only the streams a mutual between exactly
these two opened, in one sport, that reached ``ON``. They read the same log
because that is where both answers are, and they answer about different things —
which is the distinction ``docs/adr/0152`` §1 exists to hold apart.
"""

from __future__ import annotations

from itertools import combinations
from typing import Collection
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import EventCodec
from app.kernel import Instant, Sport
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
)
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

    async def mutual_born_challenges_that_became_games(
        self,
        one_player: UUID,
        other_player: UUID,
        *,
        sport: Sport,
        now: Instant,
    ) -> frozenset[UUID]:
        """The mutual-born challenges between these two that reached ``ON``.

        **The same two statements, folded on a different question.** It reads the
        streams both of them are seated in and keeps the ones that are a mutual
        between *exactly* these two, in this sport, and that reached ``ON``.

        **Mutual-born is read off the opening event, not off the aggregate.** A
        stream that opens with ``ChallengeOpenedFromMutualInterest`` is one two
        yeses minted and no other stream is, so the fact is already in the log
        and needs no field on the challenge to carry it — which also keeps the
        pair it was minted between readable after a doubles court has since been
        invited into. A later invitee sharing a mutual-born court with one of
        these two is **not** a mutual between them, and holding the mint on that
        would be this guard reaching back outside its own key.
        """

        pair = frozenset({one_player, other_player})
        if len(pair) < 2:
            return frozenset()

        streams = await streams_seating(self._session, self._codec, pair)
        minted: set[UUID] = set()
        for challenge_id, events in streams.items():
            opening = events[0]
            if not isinstance(opening, ChallengeOpenedFromMutualInterest):
                continue
            if frozenset({opening.organiser_id, opening.other_player_id}) != pair:
                continue
            challenge = Challenge.from_history(events)
            if challenge.sport is not sport:
                continue
            if challenge.has_become_a_game_at(now):
                minted.add(challenge_id)
        return frozenset(minted)
