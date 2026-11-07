"""Friendships and blocks arranged **through their aggregates** for the demand
suites — asked, answered, set aside, blocked, and asked for a level (#764) —
saved by their own repositories, never an ``INSERT`` (#745)."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from app.bootstrap.composition import (
    build_block_repository,
    build_domain_event_store,
    build_event_publisher,
    build_friendship_repository,
)
from app.kernel import Instant, Sport, instant
from app.modules.blocks.domain.block import Block
from app.modules.friends.domain.friendship import Where
from app.modules.friends.domain.relation import RequestOrigin

ASKED_AT: Instant = instant(datetime(2026, 10, 5, 6, tzinfo=timezone.utc))
WHERE = Where(made_from=RequestOrigin.RECORD)
#: The group an ask for a level is made from — nothing here reads it.
GROUP: UUID = UUID("00000000-0000-4000-8000-000000000764")


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


async def asks_for_a_level(
    session,
    asker: UUID,
    friend: UUID,
    *,
    sport: Sport = Sport.PADEL,
    at: Instant = ASKED_AT,
    set_aside: bool = False,
    answered: bool = False,
) -> None:
    """A friend asks for a level — friends already — and the friend sets it
    aside, or gets the level, when told to."""

    friendships = _friendships(session)
    friendship = await friendships.load(asker, friend)
    friendship.ask_for_a_level(asker=asker, sport=sport, group_id=GROUP, at=at)
    if set_aside:
        friendship.set_aside_the_ask(by=friend, sport=sport, at=at)
    if answered:
        friendship.answer_the_ask(friend=friend, sport=sport, at=at)
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
