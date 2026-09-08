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

**One row, and the port it names is not the obvious one.** The fact this context
reads about a *game* — *is this player on this game's court, and is that game
still open to planning* — is ``games``' question about ``games``' record, so it is
published by that context and contracted on **its** register. What is left here
is the one fact the Plan asks about a **person**, and it is the fourth spelling
of a port whose provider does not exist: its empty answer is **measured rather
than stubbed**, because nobody can be held while nothing on this platform can
hold anybody.

**A port with nothing registered is a red build**, asserted in the suite against
``PLAN_DEMANDS``, because a port added in a hurry would otherwise look contracted
while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_plan_hold_query
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.plans.domain.ports import AccountHoldQuery

P = TypeVar("P")

#: What this context asks of the rest of the platform, declared as data for the
#: same reason the other six registers are: *a port with no registered
#: implementation* has to be a question something can ask.
#:
#: **The repository and the directory are not on this list**, and the line
#: between them and this one is who owns the fact. A repository is how this
#: module loads its own aggregate and a directory is how it finds its own rows;
#: nobody outside will ever hold either.
PLAN_DEMANDS: tuple[type, ...] = (AccountHoldQuery,)


PLAN_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
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
