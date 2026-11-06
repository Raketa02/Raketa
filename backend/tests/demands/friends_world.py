"""Friendships and blocks arranged **through their aggregates** for the demand
suites — asked, answered, set aside, blocked — saved by their own
repositories, never an ``INSERT`` (#745)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.bootstrap.composition import (
    build_block_repository,
    build_domain_event_store,
    build_event_publisher,
    build_friendship_repository,
)
from app.kernel import Instant, instant
from app.modules.blocks.domain.block import Block
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.relation import RequestOrigin

ASKED_AT: Instant = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
WHERE = Where(made_from=RequestOrigin.RECORD)


def _friendships(session):
    return build_friendship_repository(
        session,
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )


async def asks(session, requester: UUID, addressee: UUID, *, set_aside=False) -> None:
    friendships = _friendships(session)
    friendship = await friendships.load(requester, addressee)
    friendship.ask(requester=requester, where=WHERE, at=ASKED_AT)
    if set_aside:
        friendship.set_aside(by=addressee, at=ASKED_AT)
    await friendships.save(friendship)
    await session.commit()


async def befriends(session, one: UUID, other: UUID) -> None:
    friendships = _friendships(session)
    friendship = await friendships.load(one, other)
    friendship.ask(requester=one, where=WHERE, at=ASKED_AT)
    friendship.accept(by=other, at=ASKED_AT)
    await friendships.save(friendship)
    await session.commit()


async def blocks(session, blocker: UUID, blocked: UUID) -> None:
    await build_block_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    ).save(
        Block.first_blocked(
            blocker_id=blocker, blocked_id=blocked, occurred_at=ASKED_AT
        )
    )
    await session.commit()
