"""``ChallengeDirectory`` over the log — *what have I been asked, and what have I
asked for*.

The same fold ``OpenChallengeQuery`` performs, stopping one step earlier: it
answers with the **challenges** rather than with the pairs inside them, because
this read has a screen behind it and that one has a rule behind it.

**Newest first, ordered on ``opened_at``.** The order is part of the demand — a
list whose order depended on how the streams happened to come back would reorder
itself between two identical requests — and it is the *opening* moment rather than
``updated_at``: a challenge does not move to the top of somebody's list because a
fourth person accepted a seat in it.

**No standing is stored and none is read.** Each challenge is folded and the
caller derives its standing against a clock, so the list is right for the whole
gap between a deadline passing and a sweep noticing.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.application.ports.events import EventCodec
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.infrastructure.challenge_streams import streams_seating


@final
class EventSourcedChallengeDirectory:
    """Every challenge one player holds a seat in, folded from its stream."""

    def __init__(self, session: AsyncSession, codec: EventCodec) -> None:
        self._session = session
        self._codec = codec

    async def seating(self, player_id: UUID) -> tuple[Challenge, ...]:
        """Their challenges, newest first.

        A stream matched by the substring read but whose current court no longer
        holds this player is dropped here: a seat that was re-offered to somebody
        else is that person's challenge now, and it was never this reader's to
        keep watching. The **answer** they gave is still theirs and is what the
        aggregate remembers; the challenge is not.
        """

        streams = await streams_seating(self._session, self._codec, [player_id])
        found = [
            challenge
            for challenge in (
                Challenge.from_history(events) for events in streams.values()
            )
            if any(seat.holds(player_id) for seat in challenge.seats)
        ]
        return tuple(sorted(found, key=lambda one: one.opened_at, reverse=True))
