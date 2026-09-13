"""The register of what ``plans`` demands of contexts it does not write.

**A seventh register rather than more rows in one of the six, and that is the
rule rather than a preference.** ``matcher_demands.py`` holds the ports the
*matcher* declares of contexts it does not write; ``games_demands.py``,
``rating_demands.py`` and ``player_score_demands.py`` each hold what one
*provider* publishes outward; ``challenge_demands.py`` holds what ``challenges``
demands of the matcher, and ``conversation_demands.py`` what a room demands of
the three contexts that tell it. This one holds what a **plan** demands, and each
register's exhaustiveness assertion is about its own kind of claim and would stop
meaning anything with another kind in it.

**There is no ``plans`` provider register, and there never will be.** Nothing on
this side of the wire reads a plan: ``games`` may not import it
(``docs/adr/0145`` §4, enforced in ``.importlinter``), ``conversations`` is
*told* through the outbox and asks this context nothing, and the card ladder that
reads a plan is the **client's** ``domain/``. A context with no consumers
publishes no port.

**Two rows, and the first is the read that decides who may write.**
``PlannableCourts`` — *which courts is this player arranging, and which are
history* — used to be ``games``' question about ``games``' record, published
there and contracted on its register. A plan is the **challenge's** now
(``docs/adr/0164`` §3), so the question is about a court that may or may not
have become a game, neither provider can answer it alone, and it is declared in
the Plan's own words and answered by an adapter that folds the two providers'
records — which is ``conversation_demands.py``'s shape exactly, *one rule read
against two records*. It is contracted here rather than unit-tested only,
because a stub that agreed with the rule would prove nothing about whether
``challenges`` and ``games`` actually fold that way. The second row is the one
fact the Plan asks about a **person**, and it is the fourth spelling of a port
whose provider does not exist: its empty answer is **measured rather than
stubbed**, because nobody can be held while nothing on this platform can hold
anybody.

**A port with nothing registered is a red build**, asserted in the suite against
``PLAN_DEMANDS``, because a port added in a hurry would otherwise look contracted
while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_plan_hold_query,
    build_plannable_courts,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.plans.domain.ports import AccountHoldQuery, PlannableCourts

P = TypeVar("P")

#: What this context asks of the rest of the platform, declared as data for the
#: same reason the other six registers are: *a port with no registered
#: implementation* has to be a question something can ask.
#:
#: **The repository and the directory are not on this list**, and the line
#: between them and this one is who owns the fact. A repository is how this
#: module loads its own aggregate and a directory is how it finds its own rows;
#: nobody outside will ever hold either.
PLAN_DEMANDS: tuple[type, ...] = (PlannableCourts, AccountHoldQuery)


PLAN_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=PlannableCourts,
        name="ChallengesAndGamesPlannableCourts",
        build=build_plannable_courts,
    ),
    RegisteredImplementation(
        port=AccountHoldQuery,
        name="NoHoldsExist",
        build=build_plan_hold_query,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in PLAN_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "PLAN_DEMANDS",
    "PLAN_IMPLEMENTATIONS",
    "implementations_of",
]
