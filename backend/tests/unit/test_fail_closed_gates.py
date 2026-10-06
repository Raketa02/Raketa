"""The two gates about accounts that fail closed, asked directly.

Since the searches went (#579) the surface they serve is the player record. The
two gates it asks — a hold, an account that may not be shown — are one
collaborator, ``AccountGates``, rather than a private step inside the use case
that needs them, because a second spelling of a safety gate is the defect the
whole fail-closed rule exists to prevent. So they are asserted **at their own
seam** here, and the record's own suite asserts them over HTTP.

**A block is not one of them** (``docs/adr/0193`` §2): it keeps two people off
one court, and the record is not a court. The collaborator takes no block read
at all, which is what keeps one from creeping back in as a third gate.
"""

from __future__ import annotations

import inspect
from dataclasses import dataclass
from typing import Collection
from uuid import UUID, uuid5

import pytest

from app.modules.matchmaking.application.fail_closed_gates import AccountGates
from app.modules.matchmaking.domain.errors import GateDataUnavailable

_PEOPLE = UUID("5d2f0c1e-0000-4000-8000-000000000000")


def player(number: int) -> UUID:
    return uuid5(_PEOPLE, f"subject-{number}")


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
    holds: Holds | None = None,
    statuses: Statuses | None = None,
) -> frozenset[UUID]:
    return await AccountGates(
        holds=holds or Holds(),
        account_status=statuses or Statuses(),
    ).withheld(subject_ids=tuple(player(number) for number in numbers))


async def test_a_clear_set_withholds_nobody():
    assert await ask(1, 2) == frozenset()


async def test_the_two_withhold_on_their_own():
    """A hold and an account that may not be shown are facts about people, so
    each withholds its subject and nobody else."""

    withheld = await ask(
        1,
        2,
        3,
        holds=Holds(held=frozenset({player(1)})),
        statuses=Statuses(hidden=frozenset({player(2)})),
    )

    assert withheld == frozenset({player(1), player(2)})


def test_no_block_read_is_taken():
    """``docs/adr/0193`` §2, as a signature: there is nothing to hand a block
    read to."""

    assert set(inspect.signature(AccountGates).parameters) == {
        "holds",
        "account_status",
    }


@pytest.mark.parametrize(
    "unreadable",
    [
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

    assert await ask(holds=Holds(raises=True), statuses=Statuses(raises=True)) == (
        frozenset()
    )
