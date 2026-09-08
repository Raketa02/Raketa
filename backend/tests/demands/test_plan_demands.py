"""What ``plans`` demands of the rest of the platform, run against every
registered implementation.

**A demand nobody executes is a demand satisfied by accident** (``docs/adr/0098``).
Every implementation registered in ``app/bootstrap/plan_demands.py`` is enrolled
here automatically, so a second one either satisfies the demand or turns the
build red. There is no skipped test to go stale.

**One port, and it is the fourth spelling of an empty answer.** The fact this
context reads about a *game* is ``games``' and is contracted on its own register;
what is left is the one fact it reads about a *person*, whose provider does not
exist. The demand made of it is therefore about the shape of an honest empty
answer rather than about a hold — because nobody can be held while nothing on
this platform can hold anybody, and a test that pretended otherwise would be
testing a stub.

**The held arm of the three slot writes is unreachable by ``make seed`` and that
is stated rather than discovered** — here, and in the null object itself. It is
an honest, named exception rather than an oversight.
"""

from __future__ import annotations

import pytest
import pytest_asyncio

from app.bootstrap.plan_demands import (
    PLAN_DEMANDS,
    PLAN_IMPLEMENTATIONS,
    implementations_of,
)
from app.modules.plans.domain.ports import AccountHoldQuery
from app.shared.ids import new_uuid


@pytest_asyncio.fixture
async def session(session_factory):
    async with session_factory() as open_session:
        yield open_session


def registered(port):
    """Every registered implementation of one port, as pytest parameters."""

    return [
        pytest.param(implementation, id=implementation.name)
        for implementation in implementations_of(port)
    ]


# ---------------------------------------------------------------------------
# The register itself
# ---------------------------------------------------------------------------


def test_every_declared_demand_has_at_least_one_implementation():
    """**A port with nothing registered is a red build**, because one added in a
    hurry would otherwise look contracted while nothing ran against it."""

    unregistered = [
        port.__name__ for port in PLAN_DEMANDS if not implementations_of(port)
    ]

    assert unregistered == []


def test_every_registered_implementation_answers_a_declared_demand():
    """The other direction: a row for a port this context does not declare is a
    row in the wrong register."""

    declared = set(PLAN_DEMANDS)

    assert all(one.port in declared for one in PLAN_IMPLEMENTATIONS)


def test_the_plan_publishes_nothing_and_therefore_has_no_provider_register():
    """``docs/adr/0145`` §4 — nothing on this side of the wire reads a plan.

    ``games`` may not import it, ``conversations`` is told through the outbox and
    asks this context nothing, and the ladder that reads a plan is the client's.
    A context with no consumers publishes no port, so there is no
    ``plan_provider_demands.py`` to add a row to and there never will be.
    """

    with pytest.raises(ModuleNotFoundError):
        __import__("app.bootstrap.plan_provider_demands")


# ---------------------------------------------------------------------------
# AccountHoldQuery — an empty answer that is measured rather than stubbed
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("implementation", registered(AccountHoldQuery))
async def test_nobody_is_held_because_nothing_can_hold_anybody(
    implementation, session
):
    """Not a stub standing in for a provider — the correct answer.

    There is no case, no route and no record anywhere that can put an account
    under a hold, so *nobody* is what this measures. On the day ``cases`` ships,
    this row changes to the same adapter the other three spellings change to.
    """

    port: AccountHoldQuery = implementation.build(session)
    somebody, somebody_else = new_uuid(), new_uuid()

    assert await port.held_among((somebody, somebody_else)) == frozenset()


@pytest.mark.parametrize("implementation", registered(AccountHoldQuery))
async def test_asking_about_nobody_answers_about_nobody(implementation, session):
    """The empty ask, which the write path never makes and a caller may.

    It is here because the answer to *which of these* over an empty list is the
    empty set and never an error — the shape every set read in this codebase
    promises.
    """

    port: AccountHoldQuery = implementation.build(session)

    assert await port.held_among(()) == frozenset()
