"""Every one of the thirty-six names is produced by some record, named on failure.

The prototype shipped one key no rung could produce and two more reachable only
from a fact combination nothing writes (``docs/specs/now/research/state-table.md``
§3). Nothing failed, because a name nobody produces has no test to fail — it
simply sits in the enumeration until somebody builds against it.

So the walk runs the whole grid — club × occupancy × clock × court × custody ×
kind × outcome, crossed with every relationship a viewer can have to a match —
and then **one test per member**, so a name that stops being produced fails by
its own name rather than as a count that went down by one.
"""

from __future__ import annotations

from collections import Counter

import pytest

from app.kernel import SITUATION_COUNT, InvariantViolated, Situation, situation
from tests.unit.match_records import VIEWERS, grid

#: The ladder, in order, as the wire spells it. Written out rather than derived
#: from the enumeration, because **the order of the ladder is the specification**
#: (``docs/adr/0040-one-ladder-resolves-a-situation.md``): reordering the members
#: reorders the rungs, so the order is a thing to diff and not a thing to trust.
#: Written as the wire values for the same reason the rest of this suite asserts
#: names — these thirty-six strings are what a generated client union will hold.
THE_LADDER_IN_ORDER = (
    "inventoryLost",
    "cancelledClub",
    "cancelledIncomplete",
    "cancelledCheckpoint",
    "playedNoShow",
    "playedShort",
    "completed",
    "playedNoScore",
    "confirmResult",
    "needsResult",
    "seatOffered",
    "seatOpened",
    "waitlisted",
    "privateOpen",
    "privateFull",
    "privatePartial",
    "privateReserved",
    "replacementTransfer",
    "rescueLate",
    "rescue",
    "replacement",
    "protectedBack",
    "formingBack",
    "ready",
    "confirmedOnFill",
    "confirmed",
    "full",
    "formingLateHeld",
    "clubHeld",
    "heldSoft",
    "heldReleased",
    "formingHeld",
    "formingLate",
    "forming",
    "heldStale",
    "heldExtended",
)

#: The three names only a viewer can be in
#: (``docs/adr/0040-...``, ``docs/adr/0072-...``).
VIEWER_ONLY = (
    Situation.SEAT_OFFERED,
    Situation.SEAT_OPENED,
    Situation.WAITLISTED,
)


def _walk() -> tuple[Counter[Situation], Counter[Situation], int]:
    """The whole grid, once, resolved with every viewer and with none.

    Returns what each pass produced and how many resolutions were made, so a
    walk that quietly stopped walking cannot pass by finding nothing.
    """

    everything: Counter[Situation] = Counter()
    absolute: Counter[Situation] = Counter()
    resolutions = 0
    for record, now in grid():
        for viewer in VIEWERS:
            resolutions += 1
            answer = situation(record, viewer, now)
            everything[answer] += 1
            if viewer is None:
                absolute[answer] += 1
    return everything, absolute, resolutions


PRODUCED, PRODUCED_WITHOUT_A_VIEWER, RESOLUTIONS = _walk()


@pytest.mark.parametrize("name", list(Situation), ids=lambda member: member.value)
def test_the_ladder_produces_this_name(name: Situation) -> None:
    """A member produced zero times fails here, by its own name."""

    assert PRODUCED[name] > 0


def test_the_grid_is_large_enough_to_be_making_a_claim() -> None:
    """A walk over an empty generator passes every assertion above it.

    The lesson the seed runner's structural walk paid for: assert the size, or
    the suite goes green the day the grid stops producing records.
    """

    assert RESOLUTIONS > 100_000
    assert len(set(PRODUCED)) == SITUATION_COUNT


def test_no_input_in_the_grid_reaches_a_refused_fact_combination() -> None:
    """The grid models only what a writer can produce.

    ``_custody`` refuses to pair commitment with a match that is neither complete
    nor short a vacated seat, so the walk above never has to catch an
    ``InvariantViolated``. If it did, the generator — not the ladder — would be
    the thing making the claim.
    """

    for record, now in grid():
        try:
            situation(record, None, now)
        except InvariantViolated as broken:  # pragma: no cover - a red suite
            pytest.fail(f"the grid produced a record the ladder refuses: {broken}")
        break


def test_without_a_viewer_the_kernel_cannot_say_any_of_the_three() -> None:
    """The absolute form of the resolver, over the whole grid.

    ``waitlisted`` is the one ADR-0040 names; ADR-0072 added the two offer
    sentences on the same terms. All three are claims about *one reader*, and a
    resolver that could produce them with the parameter absent would be a second
    derivation wearing the same signature.
    """

    for name in VIEWER_ONLY:
        assert PRODUCED_WITHOUT_A_VIEWER[name] == 0
        assert PRODUCED[name] > 0


def test_the_enumeration_is_the_ladder_in_order() -> None:
    assert tuple(member.value for member in Situation) == THE_LADDER_IN_ORDER


def test_the_count_is_pinned_rather_than_counted() -> None:
    assert len(Situation) == SITUATION_COUNT == 36
