"""The Block aggregate: one stream per ordered pair, and the rules on it.

Four claims are load-bearing, and each fails differently.

**The pair is the identity, and it is ordered.** ``A → B`` and ``B → A`` compute
two different stream ids, so they are two independent records — which is what
makes an unblock unambiguous when both parties have blocked, and is the whole
reason ``docs/adr/0095`` rejected one symmetric edge.

**Blocking is idempotent.** A second block of somebody already blocked appends
nothing, in the shape of ``users``' ``disable()``.

**Blocking yourself raises**, rather than opening a stream whose two sides are
one person.

**Unblocking lifts one direction only**, which is the claim the symmetric effect
is built on top of and the one a later "simplification" would break silently.

**No screen is recorded, and a block that named one still folds**
(``docs/adr/0193`` §5): ``blocks.player_blocked`` is v2, with the pair alone, and
a stored v1 row reads its surface and drops it.
"""

from __future__ import annotations

import pytest

from app.application.events import EventCatalog
from app.application.events.envelope import SerializedEventEnvelope
from app.infrastructure.events.json_event_codec import JsonEventCodec
from app.modules.blocks.application.event_subscriptions import register_block_events
from app.modules.blocks.domain.block import Block
from app.modules.blocks.domain.errors import CannotBlockYourself
from app.modules.blocks.domain.events import PlayerBlocked, PlayerUnblocked
from app.modules.blocks.domain.ids import block_id
from app.shared.ids import new_uuid
from tests.unit.fake_event_store import utc

ALICE = new_uuid()
BOB = new_uuid()
BLOCKED_AT = utc(2026, 8, 27)
LATER = utc(2026, 9, 3)


def a_block(**overrides) -> Block:
    arguments = dict(
        blocker_id=ALICE,
        blocked_id=BOB,
        occurred_at=BLOCKED_AT,
    )
    arguments.update(overrides)
    return Block.first_blocked(**arguments)


def test_the_stream_id_is_the_ordered_pair():
    block = a_block()

    assert block.id == block_id(ALICE, BOB)
    assert block_id(ALICE, BOB) != block_id(BOB, ALICE)


def test_blocking_records_the_pair_and_nothing_else():
    block = a_block()

    (event,) = block.pull_events()
    assert isinstance(event, PlayerBlocked)
    assert event.blocker_id == ALICE
    assert event.blocked_id == BOB
    assert event.occurred_at == BLOCKED_AT
    # No reason, no free text and no screen, on either event.
    assert set(vars(event)) == {"blocker_id", "blocked_id", "occurred_at"}


def test_a_standing_block_says_when_it_was_made():
    """What *Blocked players* draws beside each person (``docs/adr/0193`` §3)."""

    block = Block.from_history(a_block().pull_events())

    assert block.blocked_at == BLOCKED_AT


def _codec() -> JsonEventCodec:
    catalog = EventCatalog()
    register_block_events(catalog)
    return JsonEventCodec(catalog)


def test_a_block_is_written_as_version_two():
    (event,) = a_block().pull_events()

    encoded = _codec().encode(event)

    assert (encoded.event_type, encoded.schema_version) == (
        "blocks.player_blocked",
        2,
    )
    assert "surface" not in encoded.payload


def test_a_stored_block_that_named_its_screen_still_folds():
    """``blocks.player_blocked`` v1 carried which of the old loop's four screens
    the block was made from. Rows of it are in the store, and nothing rewrites
    them: the surface is read and dropped."""

    v1 = _codec().decode(
        SerializedEventEnvelope(
            id=new_uuid(),
            event_type="blocks.player_blocked",
            schema_version=1,
            payload={
                "blocker_id": str(ALICE),
                "blocked_id": str(BOB),
                "surface": "SHORTLIST",
                "occurred_at": BLOCKED_AT.isoformat(),
            },
            occurred_at=BLOCKED_AT,
        )
    )

    block = Block.from_history([v1])

    assert (block.blocker_id, block.blocked_id) == (ALICE, BOB)
    assert block.is_standing
    assert block.blocked_at == BLOCKED_AT
    assert block.version == 1
    assert not hasattr(block, "surface")

    block.unblock(occurred_at=LATER)
    block.block(occurred_at=LATER)

    *_, again = block.pull_events()
    assert isinstance(again, PlayerBlocked), "a re-block is written as v2"
    assert block.blocked_at == LATER


def test_blocking_yourself_raises_rather_than_no_ops():
    with pytest.raises(CannotBlockYourself):
        a_block(blocked_id=ALICE)


def test_blocking_somebody_already_blocked_appends_nothing():
    block = Block.from_history(a_block().pull_events())

    block.block(occurred_at=LATER)

    assert block.pull_events() == []
    assert block.version == 1
    assert block.is_standing
    # A repeat is not a new block: the standing one was made when it was made.
    assert block.blocked_at == BLOCKED_AT


def test_unblocking_lifts_it_and_re_blocking_opens_the_next_chapter():
    block = Block.from_history(a_block().pull_events())

    block.unblock(occurred_at=LATER)
    (lifted,) = block.pull_events()
    assert isinstance(lifted, PlayerUnblocked)
    assert not block.is_standing

    block.block(occurred_at=LATER)
    (again,) = block.pull_events()
    assert isinstance(again, PlayerBlocked)
    assert block.is_standing
    # Blocked, unblocked, blocked again — three events on one stream, which is
    # the sequence ADR-0095 keeps event sourcing for.
    assert block.version == 3


def test_unblocking_what_is_not_standing_appends_nothing():
    block = Block.from_history(a_block().pull_events())
    block.unblock(occurred_at=LATER)
    block.pull_events()

    block.unblock(occurred_at=LATER)

    assert block.pull_events() == []
    assert block.version == 2


def test_the_two_directions_are_independent_records():
    alice_blocks_bob = Block.from_history(a_block().pull_events())
    bob_blocks_alice = Block.from_history(
        a_block(blocker_id=BOB, blocked_id=ALICE).pull_events()
    )

    alice_blocks_bob.unblock(occurred_at=LATER)

    assert not alice_blocks_bob.is_standing
    assert bob_blocks_alice.is_standing
    assert alice_blocks_bob.id != bob_blocks_alice.id


def test_replay_is_a_fold_of_the_stream():
    opened = a_block()
    events = opened.pull_events()
    opened.unblock(occurred_at=LATER)
    events += opened.pull_events()

    replayed = Block.from_history(events)

    assert replayed.blocker_id == ALICE
    assert replayed.blocked_id == BOB
    assert not replayed.is_standing
    assert replayed.version == 2
    assert replayed.pull_events() == []


def test_the_counterpart_is_the_other_side_whichever_side_you_are_on():
    """What an exclusion set is built from. A reader that made this conditional
    itself is a reader that eventually gets it the wrong way round and excludes
    the searcher from their own search."""

    block = a_block()

    assert block.counterpart_of(ALICE) == BOB
    assert block.counterpart_of(BOB) == ALICE


def test_somebody_who_is_not_in_the_pair_has_no_counterpart():
    """A caller bug, and returning either side would hide it behind a plausible
    answer."""

    with pytest.raises(ValueError):
        a_block().counterpart_of(new_uuid())
