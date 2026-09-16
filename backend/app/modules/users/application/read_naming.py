"""What this player is called, read off their own stream.

Served on ``GET /api/v1/users/me`` as ``name`` and ``nickname``, both null until
the naming — and ``name`` is the entry gate's **first** destination
(``docs/adr/0171`` §3): a player with no name is sent to the naming step before
anything else. The gate reads this immediately after the commit that named
them, which is exactly when a read model that had not caught up would send a
player back to a step they just finished; so it is answered from the stream,
the way ``HasPlayerProfile`` answers the gate's fourth destination
(``docs/adr/0089``), and never from the projection.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventStore
from app.modules.users.application.user_stream import replay_user
from app.modules.users.domain.ports import Naming


class ReadNaming:
    def __init__(self, *, event_store: DomainEventStore) -> None:
        self._event_store = event_store

    async def execute(self, user_id: UUID) -> Naming | None:
        user = await replay_user(self._event_store, user_id)
        if user is None or user.name is None or user.nickname is None:
            return None
        return Naming(name=user.name.value, nickname=user.nickname.value)
