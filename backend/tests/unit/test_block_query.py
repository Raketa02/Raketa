"""``BlockQuery`` over the log: both directions, live, and failing closed.

Run against the real adapter and a real (SQLite) session rather than a double,
because what is being asserted is exactly what a double would have to invent: the
payload disjunction that finds *every stream this player appears in, on either
side*, and the fold that decides whether each one is standing.

Four claims:

**The exclusion set is symmetric.** Whom I blocked and who blocked me arrive as
one flat set, because nothing downstream may branch on which side a block came
from.

**Your own blocks are directed, and only yours** (``docs/adr/0193`` §3). The one
read that knows which way round answers with the blocks a player *made*, and
never one made of them.

**It is live.** An unblock disappears from the set on the next read; there is no
projection to lag, by decision (``docs/adr/0095`` §4).

**It fails closed.** A read that cannot complete raises rather than answering
*nobody is blocked* — the sentence that stops somebody later "fixing" a flaky
query by defaulting it to empty.
"""

from __future__ import annotations

import pytest

from app.bootstrap.composition import (
    build_block_query,
    build_block_repository,
    build_domain_event_store,
    build_event_publisher,
)
from app.modules.blocks.domain.block import Block
from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.blocks.domain.ports import OwnBlock
from app.modules.blocks.infrastructure.event_sourced_block_query import _payload_key
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import utc

ALICE = new_uuid()
BOB = new_uuid()
CAROL = new_uuid()
AT = utc(2026, 8, 27)
LATER = utc(2026, 9, 3)


async def _record(session, *, blocker, blocked, lifted=False, at=AT):
    """Write a block — and optionally its lift — the way a request would."""

    repository = build_block_repository(
        event_store=build_domain_event_store(session),
        events=build_event_publisher(session),
    )
    block = Block.first_blocked(blocker_id=blocker, blocked_id=blocked, occurred_at=at)
    await repository.save(block)
    if lifted:
        block.unblock(occurred_at=LATER)
        await repository.save(block)
    await session.commit()


async def test_the_exclusion_set_holds_both_directions(session_factory):
    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB)
        await _record(session, blocker=CAROL, blocked=ALICE)

        excluded = await build_block_query(session).exclusions_for(ALICE)

        assert excluded == frozenset({BOB, CAROL})


async def test_a_lifted_block_leaves_the_set_immediately(session_factory):
    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB, lifted=True)

        assert await build_block_query(session).exclusions_for(ALICE) == frozenset()
        assert await build_block_query(session).exclusions_for(BOB) == frozenset()


async def test_one_unblock_does_not_lift_the_other_direction(session_factory):
    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB, lifted=True)
        await _record(session, blocker=BOB, blocked=ALICE)

        query = build_block_query(session)

        assert await query.exclusions_for(ALICE) == frozenset({BOB})
        assert await query.exclusions_for(BOB) == frozenset({ALICE})


async def test_a_player_nobody_has_blocked_is_excluded_from_nobody(session_factory):
    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB)

        assert await build_block_query(session).exclusions_for(CAROL) == frozenset()


async def test_the_pairwise_question_is_symmetric_in_its_arguments(session_factory):
    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB)

        query = build_block_query(session)

        assert await query.blocked_between(ALICE, BOB)
        assert await query.blocked_between(BOB, ALICE)
        assert not await query.blocked_between(ALICE, CAROL)


async def test_the_pairwise_question_sees_a_lift(session_factory):
    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB, lifted=True)

        assert not await build_block_query(session).blocked_between(ALICE, BOB)


async def test_nobody_is_blocked_from_themselves(session_factory):
    async with session_factory() as session:
        assert not await build_block_query(session).blocked_between(ALICE, ALICE)


async def test_the_bulk_read_names_every_pair_between_these_people(session_factory):
    """``docs/adr/0116``'s own read: **one query over the ``K`` ids, not ``K²``.**

    A four contains six pairs and the searcher is in three of them, so a line-up
    has to know whether `a` blocked `b` — a question no shortlist ever asked. It
    comes back as unordered pairs, because nothing downstream may learn which way
    round a block was taken.
    """

    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB)

        pairs = await build_block_query(session).blocked_pairs_among(
            [ALICE, BOB, CAROL]
        )

        assert pairs == frozenset({frozenset({ALICE, BOB})})


async def test_the_bulk_read_ignores_a_block_reaching_outside_the_line_up(
    session_factory,
):
    """Both ends have to be on the court. A block between one of these people and
    somebody who is not being seated is somebody else's business, and a mask that
    counted it would refuse a four for a reason that is not on it."""

    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB)

        pairs = await build_block_query(session).blocked_pairs_among([ALICE, CAROL])

        assert pairs == frozenset()


async def test_the_bulk_read_sees_a_lift(session_factory):
    """A lifted block is not a block, here as in the other two reads."""

    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB, lifted=True)

        assert await build_block_query(session).blocked_pairs_among(
            [ALICE, BOB]
        ) == frozenset()


async def test_a_line_up_of_one_has_no_pair_for_a_block_to_sit_between(
    session_factory,
):
    """The one emptiness here that is **measured** rather than a refusal: fewer
    than two people is no pair at all, and the read is not taken."""

    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB)
        query = build_block_query(session)

        assert await query.blocked_pairs_among([ALICE]) == frozenset()
        assert await query.blocked_pairs_among([]) == frozenset()


async def test_your_own_blocks_are_the_ones_you_made_and_never_one_made_of_you(
    session_factory,
):
    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB)
        await _record(session, blocker=CAROL, blocked=ALICE)

        query = build_block_query(session)

        assert await query.blocks_made_by(ALICE) == (
            OwnBlock(blocked_id=BOB, blocked_at=AT),
        )
        assert await query.blocks_made_by(BOB) == ()
        assert await query.blocks_made_by(CAROL) == (
            OwnBlock(blocked_id=ALICE, blocked_at=AT),
        )


async def test_your_own_blocks_come_newest_first_and_a_lifted_one_is_gone(
    session_factory,
):
    dee = new_uuid()
    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB, at=AT)
        await _record(session, blocker=ALICE, blocked=CAROL, at=LATER)
        await _record(session, blocker=ALICE, blocked=dee, lifted=True)

        assert await build_block_query(session).blocks_made_by(ALICE) == (
            OwnBlock(blocked_id=CAROL, blocked_at=LATER),
            OwnBlock(blocked_id=BOB, blocked_at=AT),
        )


async def test_both_having_blocked_each_sees_only_their_own(session_factory):
    """The record is directed, so this is per person (``docs/adr/0193`` §3)."""

    async with session_factory() as session:
        await _record(session, blocker=ALICE, blocked=BOB)
        await _record(session, blocker=BOB, blocked=ALICE, at=LATER)
        query = build_block_query(session)

        assert await query.blocks_made_by(ALICE) == (
            OwnBlock(blocked_id=BOB, blocked_at=AT),
        )
        assert await query.blocks_made_by(BOB) == (
            OwnBlock(blocked_id=ALICE, blocked_at=LATER),
        )


class BrokenSession:
    """A session whose reads fail, which is the only interesting failure here."""

    async def execute(self, *args, **kwargs):
        raise RuntimeError("the database went away")


async def test_a_read_that_cannot_complete_refuses_rather_than_answering_empty():
    """**The fail-closed rule.** An empty exclusion set means *nobody is
    blocked*, and a ``False`` means *these two are verified fine*; neither may
    ever be the answer to *we could not tell*. This is the test that stops the
    next person defaulting a flaky query to empty."""

    query = build_block_query(BrokenSession())

    with pytest.raises(BlockStateUnavailable):
        await query.exclusions_for(ALICE)
    with pytest.raises(BlockStateUnavailable):
        await query.blocked_between(ALICE, BOB)
    with pytest.raises(BlockStateUnavailable):
        await query.blocked_pairs_among([ALICE, BOB])
    with pytest.raises(BlockStateUnavailable):
        await query.blocks_made_by(ALICE)


def test_the_payload_keys_are_taken_from_the_events_and_not_trusted():
    """The exclusion read matches on a *serialized field name*, which is the one
    coupling the deterministic stream id does not remove. A rename would make the
    set come back empty — *nobody is blocked* — so the spelling is checked
    against the event classes at import rather than hoped over."""

    assert _payload_key("blocker_id") == "blocker_id"
    with pytest.raises(RuntimeError):
        _payload_key("reason")
