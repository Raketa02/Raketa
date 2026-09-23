"""The ``User`` as its own stream tells it.

``users`` is event-sourced with a projection beside it (``docs/adr/0002``): the
``users`` table answers lookups — by id, by email, by nickname — and the stream
is the record. Two reads here want the record rather than the row. The naming
appends to the stream and needs the version it expects; and ``/me``'s ``name``
is what onboarding's entry gate routes on, read the instant after the commit
that wrote it, so it comes from the source that is correct at that instant by
construction (``docs/adr/0171`` §3, on ``docs/adr/0089``'s argument for the
profile flag) rather than from a model that could, one day, be behind.

A function and not a repository, on the rating context's precedent for a
replay with one caller shape: what an ``EventSourcedUserRepository`` would add
is a version memo, and the one writer here reads and appends in one method.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import DomainEventStore
from app.modules.users.domain.user import User

#: The aggregate-type string every ``User`` stream is filed under.
USER_AGGREGATE = "user"


async def replay_user(event_store: DomainEventStore, user_id: UUID) -> User | None:
    """This account as its stream tells it, or ``None`` for a stream that does
    not exist. ``User.version`` after this is the version an append expects."""

    stored = await event_store.load_stream(
        aggregate_type=USER_AGGREGATE, aggregate_id=user_id
    )
    if not stored:
        return None
    return User.from_history(record.event for record in stored)
