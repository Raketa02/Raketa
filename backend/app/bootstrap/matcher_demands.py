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
the real adapters genuinely need one, and a suite that could only construct the
implementations needing no I/O would be a suite that quietly excused the only
implementations with a database behind it.

**Four of the six rows named a null object once and one still does.**
``NoHoldsExist`` remains, because nothing on this platform can open a case;
``NoMatchHistoryExists``, ``NoResultUpdateRuleExists`` and ``NoPlayerScoresExist``
are gone, each on the day the fact its own name asserted stopped being true
(``docs/adr/0137``, ``docs/adr/0139``, ``docs/adr/0140``). Swapping a row is the
whole integration, which is what the register was for — and the one row left is a
**gate** rather than a term, which is ``docs/adr/0098``'s rule showing through:
a gate may be honestly empty, and a term may never be honestly neutral.

**A row names one implementation and not one provider**, which is what lets
``GamesPlayedAndChallengesAnswered`` sit here as ``MatchHistoryQuery``'s single
registered implementation while composing two shipped contexts. ADR-0098's *one
provider signs one contract* is bent there and the bend is recorded in the ADR's
amendment banner, not smuggled in as a second row — and the composition is what
kept the bend to one row when the second provider arrived (``docs/adr/0137``).

**It is not the only register.** ``games_demands.py`` holds the ports a
*provider* publishes outward, in the same shape and for the same reason; they are
separate files because ``MATCHER_DEMANDS`` asserts exhaustiveness over one kind
of claim and would stop meaning anything with the other kind in it.

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
    build_half_built_court_query,
    build_match_history_query,
    build_player_score_query,
)
from app.modules.matchmaking.domain.ports import (
    MATCHER_DEMANDS,
    AccountHoldQuery,
    AccountStatusQuery,
    AtStakeQuery,
    HalfBuiltCourtQuery,
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
        name="PublishedPlayerScores",
        build=build_player_score_query,
    ),
    RegisteredImplementation(
        port=MatchHistoryQuery,
        name="GamesPlayedAndChallengesAnswered",
        build=build_match_history_query,
    ),
    RegisteredImplementation(
        port=AtStakeQuery,
        name="RatingResultUpdateRule",
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
    RegisteredImplementation(
        port=HalfBuiltCourtQuery,
        name="ChallengesHalfBuiltCourts",
        build=build_half_built_court_query,
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
