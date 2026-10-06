"""Blocking and unblocking, through the repository the routes use.

The event store is faked and the repository is real, for the reason every
use-case test in this suite works that way: a repository fake would leave the
aggregate-type string, the version arithmetic and the identity map exercised by
nothing, and those are what the repository introduced.

Four claims, and each is one ADR-0095 sentence made checkable:

**Blocking is idempotent** — a second block appends nothing and publishes
nothing, so a double tap costs one row and not two.

**Blocking yourself raises before the store is asked anything.**

**The two directions are two streams**, so A unblocking B leaves B's block of A
standing — the whole reason the record is directed.

**Nothing is notified**: what a block releases is exactly the two block events,
and there is no path from here to the other player.
"""

from __future__ import annotations

import pytest

from app.modules.blocks.application.block_player import BlockPlayer
from app.modules.blocks.application.commands import (
    BlockPlayerCommand,
    UnblockPlayerCommand,
)
from app.modules.blocks.application.unblock_player import UnblockPlayer
from app.modules.blocks.domain.errors import CannotBlockYourself
from app.modules.blocks.domain.events import PlayerBlocked, PlayerUnblocked
from app.modules.blocks.infrastructure.event_sourced_block_repository import (
    BLOCK_AGGREGATE,
    EventSourcedBlockRepository,
)
from app.modules.blocks.domain.ids import block_id
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import (
    CountingUnitOfWork,
    FrozenClock,
    InMemoryEventStore,
    RecordingPublisher,
)

ALICE = new_uuid()
BOB = new_uuid()


class Harness:
    """One event store, one publisher, and use cases built the way a request is.

    A fresh repository per call, exactly as a request gets one: the repository
    remembers the stream versions *it* read, and a harness that reused one would
    be testing a long-lived object the application never has.
    """

    def __init__(self) -> None:
        self.store = InMemoryEventStore()
        self.events = RecordingPublisher()
        self.uow = CountingUnitOfWork()
        self.clock = FrozenClock()

    def _repository(self) -> EventSourcedBlockRepository:
        return EventSourcedBlockRepository(
            event_store=self.store, events=self.events
        )

    async def block(self, blocker=ALICE, blocked=BOB):
        await BlockPlayer(
            blocks=self._repository(), uow=self.uow, clock=self.clock
        ).execute(BlockPlayerCommand(blocker_id=blocker, blocked_id=blocked))

    async def unblock(self, blocker=ALICE, blocked=BOB):
        await UnblockPlayer(
            blocks=self._repository(), uow=self.uow, clock=self.clock
        ).execute(UnblockPlayerCommand(blocker_id=blocker, blocked_id=blocked))

    async def stream(self, blocker=ALICE, blocked=BOB):
        return await self.store.load_stream(
            aggregate_type=BLOCK_AGGREGATE,
            aggregate_id=block_id(blocker, blocked),
        )


@pytest.fixture
def harness() -> Harness:
    return Harness()


async def test_blocking_opens_the_stream_for_the_ordered_pair(harness):
    await harness.block()

    (record,) = await harness.stream()
    assert isinstance(record.event, PlayerBlocked)
    assert record.event.blocker_id == ALICE
    assert record.event.blocked_id == BOB
    assert record.event.occurred_at == harness.clock.at
    assert harness.uow.commits == 1


async def test_blocking_again_appends_nothing_and_publishes_nothing(harness):
    await harness.block()
    published_after_first = len(harness.events.published)

    await harness.block()

    assert len(await harness.stream()) == 1
    assert len(harness.events.published) == published_after_first


async def test_blocking_yourself_is_refused_before_the_store_is_asked(harness):
    with pytest.raises(CannotBlockYourself):
        await harness.block(blocker=ALICE, blocked=ALICE)

    assert harness.store.appends == 0
    assert harness.uow.commits == 0


async def test_unblocking_lifts_only_the_callers_own_direction(harness):
    await harness.block(blocker=ALICE, blocked=BOB)
    await harness.block(blocker=BOB, blocked=ALICE)

    await harness.unblock(blocker=ALICE, blocked=BOB)

    alice_side = await harness.stream(ALICE, BOB)
    bob_side = await harness.stream(BOB, ALICE)
    assert isinstance(alice_side[-1].event, PlayerUnblocked)
    assert len(bob_side) == 1
    assert isinstance(bob_side[-1].event, PlayerBlocked)


async def test_unblocking_what_was_never_blocked_records_nothing_at_all(harness):
    await harness.unblock()

    assert await harness.stream() == []
    assert harness.store.appends == 0
    assert harness.uow.commits == 0
    assert harness.events.published == []


async def test_unblocking_twice_records_one_lift(harness):
    await harness.block()
    await harness.unblock()

    await harness.unblock()

    assert len(await harness.stream()) == 2


async def test_re_blocking_after_a_lift_opens_the_next_chapter_of_one_stream(harness):
    await harness.block()
    await harness.unblock()

    await harness.block()

    kinds = [type(record.event) for record in await harness.stream()]
    assert kinds == [PlayerBlocked, PlayerUnblocked, PlayerBlocked]


async def test_nothing_but_the_two_block_events_is_ever_released(harness):
    """Neither party is notified, in either direction (`docs/adr/0193` §3), and
    the outbox is the only place a notification could be introduced. What a
    block publishes is the fact itself and nothing beside it."""

    await harness.block()
    await harness.unblock()

    assert [type(event) for event in harness.events.published] == [
        PlayerBlocked,
        PlayerUnblocked,
    ]


async def test_no_cap_and_no_cooldown(harness):
    """Not a limit test — a test that there is no limit to find. Twenty-five
    blocks in one frozen instant all land, because friction on the one control a
    person has is a tax ADR-0095 §3 refuses to pay."""

    victims = [new_uuid() for _ in range(25)]
    for victim in victims:
        await harness.block(blocked=victim)

    for victim in victims:
        assert len(await harness.stream(ALICE, victim)) == 1
