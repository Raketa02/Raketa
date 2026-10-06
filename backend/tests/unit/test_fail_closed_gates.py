"""The three gates about accounts that fail closed, asked directly.

``docs/adr/0095`` reaches **every surface that shows one player to another**,
and since the searches went (#579) that is the player record. The three gates it
asks — a block in either direction, a hold, an account that may not be shown —
are one collaborator, ``AccountGates``, rather than a private step inside the use
case that needs them, because a second spelling of a safety gate is the defect
the whole fail-closed rule exists to prevent. So they are asserted **at their own
seam** here, and the record's own suite asserts them over HTTP.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection
from uuid import UUID, uuid5

import pytest

from app.modules.blocks.domain.errors import BlockStateUnavailable
from app.modules.matchmaking.application.fail_closed_gates import AccountGates
from app.modules.matchmaking.domain.errors import GateDataUnavailable

_PEOPLE = UUID("5d2f0c1e-0000-4000-8000-000000000000")
READER = uuid5(_PEOPLE, "the-reader")


def player(number: int) -> UUID:
    return uuid5(_PEOPLE, f"subject-{number}")


@dataclass
class Blocks:
    exclusions: frozenset[UUID] = frozenset()
    raises: bool = False

    async def exclusions_for(self, player_id: UUID) -> frozenset[UUID]:
        if self.raises:
            raise BlockStateUnavailable("the block store is unreachable")
        return self.exclusions

    async def blocked_between(self, first: UUID, second: UUID) -> bool:
        return False

    async def blocked_pairs_among(
        self, player_ids: Collection[UUID]
    ) -> frozenset[frozenset[UUID]]:
        """The pairwise mask, which these three gates never ask for.

        Spelled out rather than left off: the stub stands in for the whole
        ``BlockQuery`` protocol, and a stub missing a method is a stub that would
        keep passing on the day the collaborator started calling it.
        """

        return frozenset()


@dataclass
class Holds:
    held: frozenset[UUID] = frozenset()
    raises: bool = False

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        if self.raises:
            raise RuntimeError("the case store is unreachable")
        return frozenset(self.held) & frozenset(player_ids)


@dataclass
class Statuses:
    hidden: frozenset[UUID] = frozenset()
    raises: bool = False

    async def may_not_be_shown(
        self, candidate_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        if self.raises:
            raise RuntimeError("the users store is unreachable")
        return frozenset(self.hidden) & frozenset(candidate_ids)


async def ask(
    *numbers: int,
    blocks: Blocks | None = None,
    holds: Holds | None = None,
    statuses: Statuses | None = None,
) -> frozenset[UUID]:
    return await AccountGates(
        blocks=blocks or Blocks(),
        holds=holds or Holds(),
        account_status=statuses or Statuses(),
    ).withheld(
        reader_id=READER, subject_ids=tuple(player(number) for number in numbers)
    )


async def test_a_clear_reader_withholds_nobody():
    assert await ask(1, 2) == frozenset()


async def test_the_three_withhold_on_their_own():
    """A block either way, a hold and an account that may not be shown are
    facts about people, so each withholds its subject and nobody else."""

    withheld = await ask(
        1,
        2,
        3,
        4,
        blocks=Blocks(exclusions=frozenset({player(1)})),
        holds=Holds(held=frozenset({player(2)})),
        statuses=Statuses(hidden=frozenset({player(3)})),
    )

    assert withheld == frozenset({player(1), player(2), player(3)})


async def test_a_block_against_somebody_not_asked_about_is_not_in_the_answer():
    """The block read answers with the reader's **whole** exclusion list; the
    answer is bounded by the question, so it never carries a block list."""

    withheld = await ask(1, blocks=Blocks(exclusions=frozenset({player(9)})))

    assert withheld == frozenset()


@pytest.mark.parametrize(
    "unreadable",
    [
        pytest.param({"blocks": Blocks(raises=True)}, id="blocks"),
        pytest.param({"holds": Holds(raises=True)}, id="holds"),
        pytest.param({"statuses": Statuses(raises=True)}, id="account-state"),
    ],
)
async def test_an_unreadable_gate_refuses_rather_than_admitting(unreadable):
    with pytest.raises(GateDataUnavailable):
        await ask(1, 2, **unreadable)


async def test_nobody_to_ask_about_reads_nothing_at_all():
    """No gate to evaluate over an empty set, so no outward read is made — an
    unreachable store is never touched."""

    assert await ask(blocks=Blocks(raises=True), holds=Holds(raises=True)) == (
        frozenset()
    )
