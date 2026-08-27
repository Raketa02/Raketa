"""The Play intent declaration repository, over the event store.

The same fifteen lines the other three aggregate repositories have — which
aggregate-type string the streams are filed under, that state is rebuilt by
replaying them, and what version the next append expects. ADR-0018 declined a
generic event-sourced base deliberately: event-sourced-versus-persisted-with-
events is an open per-context decision, and a shared base would quietly answer it
for the contexts nobody has built yet. A fourth concrete adapter that reads
straight through is the cheaper mistake.

**Its own aggregate type, beside the profile's.** Two streams in one context, and
the column that separates them is this string — so it is spelled here once and
nowhere else, exactly as ``PLAYER_PROFILE_AGGREGATE`` is.

**There is no lookup by payload here.** The stream id is a pure function of
``(player, sport)`` (``player_profile/domain/ids.py``), so every question this
port answers is a direct stream read: nothing scans opening events and nothing
depends on a serialized field name staying spelled the way the codec writes it.
That is what the deterministic id buys, and it is why *has this player declared
in this sport* costs one read rather than a scan of their sports.

**The version is recovered, not taken**, so this must be constructed **per
request** from the session, exactly as the event store dependency is. A
declaration this repository never read has no entry and is appended at version
zero — which is also what makes two concurrent first declarations for one pair
collide on version 1 of one stream rather than quietly opening a second.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventPublisher, DomainEventStore
from app.kernel import Sport
from app.modules.player_profile.domain.ids import play_intent_declaration_id
from app.modules.player_profile.domain.play_intent_declaration import (
    PlayIntentDeclaration,
)

PLAY_INTENT_AGGREGATE = "play_intent_declaration"


class EventSourcedPlayIntentDeclarationRepository:
    """``PlayIntentDeclarationRepository`` over ``DomainEventStore``."""

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

    async def load(
        self, *, player_id: UUID, sport: Sport
    ) -> PlayIntentDeclaration | None:
        stored = await self._event_store.load_stream(
            aggregate_type=PLAY_INTENT_AGGREGATE,
            aggregate_id=play_intent_declaration_id(player_id, sport),
        )
        if not stored:
            return None
        declaration = PlayIntentDeclaration.from_history(
            record.event for record in stored
        )
        self._remember(declaration)
        return declaration

    async def save(self, declaration: PlayIntentDeclaration) -> None:
        pending = declaration.pull_events()
        if not pending:
            return

        await self._event_store.append(
            aggregate_type=PLAY_INTENT_AGGREGATE,
            aggregate_id=declaration.id,
            expected_version=self._versions.get(declaration.id, 0),
            events=pending,
        )
        await self._events.publish_many(pending)
        # Deliberately no commit: the transaction boundary is the use case's,
        # for the reason every repository in this codebase leaves it there. A
        # declaration made at a rating run's tail will be one write in a
        # transaction that has others.
        self._remember(declaration)

    def _remember(self, declaration: PlayIntentDeclaration) -> None:
        self._versions[declaration.id] = declaration.version
