"""The Player profile repository, over the event store.

The same shape the rating context's two adapters have, and near-identical to them
in about fifteen lines: which aggregate-type string the streams are filed under,
that state is rebuilt by replaying them, and what version the next append
expects. That repetition is deliberate — ADR-0018 declined a generic
event-sourced base, because event-sourced-versus-persisted-with-events is an open
per-context decision and a shared base would quietly answer it for the contexts
nobody has built yet.

**There is no lookup by payload here**, which is the one way this adapter is
simpler than the rating ones. A profile's stream id *is* the player id
(``domain/ids.py``), so every question this port answers is a direct stream
read — nothing scans opening events, and nothing depends on a serialized field
name staying spelled the way the codec writes it.

**The version is recovered, not taken**, so this must be constructed **per
request** from the session, exactly as the event store dependency is. A profile
this repository never read has no entry and is appended at version zero — "this
stream does not exist yet" follows from never having read it, which is also what
makes a second commit for the same player collide on version 1 of one stream
rather than quietly opening a second profile.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.modules.player_profile.domain.profile import PlayerProfile

PLAYER_PROFILE_AGGREGATE = "player_profile"


class EventSourcedPlayerProfileRepository:
    """``PlayerProfileRepository`` over ``DomainEventStore``."""

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

    async def load(self, player_id: UUID) -> PlayerProfile | None:
        stored = await self._event_store.load_stream(
            aggregate_type=PLAYER_PROFILE_AGGREGATE,
            aggregate_id=player_id,
        )
        if not stored:
            return None
        profile = PlayerProfile.from_history(record.event for record in stored)
        self._remember(profile)
        return profile

    async def save(self, profile: PlayerProfile) -> None:
        pending = profile.pull_events()
        if not pending:
            return

        await self._event_store.append(
            aggregate_type=PLAYER_PROFILE_AGGREGATE,
            aggregate_id=profile.id,
            expected_version=self._versions.get(profile.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's,
        # for the reason the rating context's repositories leave it there.
        self._remember(profile)

    async def exists_for(self, *, player_id: UUID) -> bool:
        # One stream read and nothing replayed. Nothing is remembered either — a
        # caller that only asked a question must not be able to save an
        # aggregate it never read.
        stored = await self._event_store.load_stream(
            aggregate_type=PLAYER_PROFILE_AGGREGATE,
            aggregate_id=player_id,
        )
        return bool(stored)

    def _remember(self, profile: PlayerProfile) -> None:
        self._versions[profile.id] = profile.version
