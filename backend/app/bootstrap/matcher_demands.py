"""The register — every implementation of every outward port, in one place.

``docs/adr/0098``'s fifth decision is that the contract suite is **parameterised
over every registered implementation of each port, including the null one**, so
that registering a real adapter enrols it automatically. This module is the
register that makes that true: `tests/contracts/` reads it and nothing else, so
enrolling an implementation is adding one row here rather than editing a test.

**It lives in the composition root**, beside the wiring it points at, because
choosing implementations is exactly what a composition root is for — and because
a module may not import ``app.bootstrap``, which is the direction this register
has to look.

Each row carries a **builder over a session** rather than an instance. The null
objects need nothing and take it anyway (see ``composition.build_account_hold_query``);
the real adapter genuinely needs one, and a suite that could only construct the
implementations needing no I/O would be a suite that quietly excused the only
implementation with a database behind it.

**A port with nothing registered is a red build**, asserted in the suite against
``MATCHER_DEMANDS`` — otherwise a port added in a hurry would look contracted
while nothing on earth ran against it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap.composition import (
    build_account_hold_query,
    build_account_status_query,
    build_at_stake_query,
    build_match_history_query,
    build_player_score_query,
)
from app.modules.matchmaking.domain.ports import (
    MATCHER_DEMANDS,
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    MatchHistoryQuery,
    PlayerScoreQuery,
)

P = TypeVar("P")


@dataclass(frozen=True)
class RegisteredImplementation(Generic[P]):
    """One implementation of one port, and how to build it.

    ``name`` is what the contract suite reports a failure under, so it is the
    class's own name — a failure that reads ``NoHoldsExist`` says which of the
    registered implementations broke the contract without anybody counting
    parameters.
    """

    port: type[P]
    name: str
    build: Callable[[AsyncSession], P]


REGISTERED_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=PlayerScoreQuery,
        name="NoPlayerScoresExist",
        build=build_player_score_query,
    ),
    RegisteredImplementation(
        port=MatchHistoryQuery,
        name="NoMatchHistoryExists",
        build=build_match_history_query,
    ),
    RegisteredImplementation(
        port=AtStakeQuery,
        name="NoResultUpdateRuleExists",
        build=build_at_stake_query,
    ),
    RegisteredImplementation(
        port=AccountHoldQuery,
        name="NoHoldsExist",
        build=build_account_hold_query,
    ),
    RegisteredImplementation(
        port=AccountStatusQuery,
        name="UsersAccountStatus",
        build=build_account_status_query,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in REGISTERED_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "MATCHER_DEMANDS",
    "REGISTERED_IMPLEMENTATIONS",
    "RegisteredImplementation",
    "implementations_of",
]
