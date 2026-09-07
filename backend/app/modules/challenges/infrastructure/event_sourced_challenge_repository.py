"""The Challenge repository, over the event store.

The same fifteen lines the other aggregate repositories have — which
aggregate-type string the streams are filed under, that state is rebuilt by
replaying them, and what version the next append expects. ADR-0018 declined a
generic event-sourced base deliberately: event-sourced-versus-persisted-with-
events is an open per-context decision, and a shared base would quietly answer it
for the contexts nobody has built yet.

**Its own aggregate type**, spelled here once and nowhere else — except in a
migration, which is a statement about what the database held on the day it ran
and must not change meaning when a constant does.

**Keyed by the challenge's own id, so every read is a keyed stream read.** This
repository has no lookup by payload and never will: *which challenges is this
player in* is a different question with a different port
(``OpenChallengeQuery``), and answering it here would put half of one question
behind an aggregate repository and half of it not.

**The version is recovered, not taken**, so this must be constructed **per
request** from the session, exactly as the event store dependency is. A challenge
this repository never read has no entry and is appended at version zero.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.challenges.domain.challenge import Challenge

CHALLENGE_AGGREGATE = "challenge"


class EventSourcedChallengeRepository:
    """``ChallengeRepository`` over ``DomainEventStore``."""

    def __init__(
        self,
        *,
        event_store: DomainEventStore,
        events: DomainEventPublisher,
    ) -> None:
        self._event_store = event_store
        self._events = events
        # Aggregate id -> the stream version this request has seen. Read by
        # ``save`` as the expected version.
        self._versions: dict[UUID, int] = {}

    async def load(self, challenge_id: UUID) -> Challenge | None:
        stored = await self._event_store.load_stream(
            aggregate_type=CHALLENGE_AGGREGATE,
            aggregate_id=challenge_id,
        )
        if not stored:
            return None
        challenge = Challenge.from_history(record.event for record in stored)
        self._remember(challenge)
        return challenge

    async def save(self, challenge: Challenge) -> None:
        pending = challenge.pull_events()
        if not pending:
            return

        await self._event_store.append(
            aggregate_type=CHALLENGE_AGGREGATE,
            aggregate_id=challenge.id,
            expected_version=self._versions.get(challenge.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's,
        # for the reason every repository in this codebase leaves it there. A
        # send re-verifies four other facts in the same transaction as this
        # append, and a commit here would break that into two.
        self._remember(challenge)

    def _remember(self, challenge: Challenge) -> None:
        self._versions[challenge.id] = challenge.version
