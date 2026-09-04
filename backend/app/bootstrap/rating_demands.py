"""The register of what ``rating`` publishes outward, and who implements it.

**The third register, and a third file for the reason there is a second.**
``matcher_demands.py`` holds the ports the *matcher* declares of contexts it does
not write; ``games_demands.py`` holds what ``games`` publishes; this holds what
``rating`` does. Each list asserts exhaustiveness over one kind of claim, and rows
of two kinds in one list would make that assertion a claim about two different
things — the first person to add a row would have to guess which.

**One port, and it is here rather than nowhere** (``docs/adr/0139``). The rating
context publishes exactly one thing that is not an aggregate: the Levels the
at-stake block is priced from. A port with one consumer is still a port somebody
can break, and *a demand nobody executes is a demand satisfied by accident*
(``docs/adr/0098``) — the accident here would be quiet, because the consumer fails
soft and a rule that silently stopped finding anybody would draw no block and
raise nothing.

**A row carries a builder over a session**, not an instance, on the same rule the
other two registers state.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_rated_player_query
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.rating.domain.ports import RatedPlayerQuery

#: What this context owes the rest of the platform.
#:
#: **The repositories are not on it**, and the line is the one ``games_demands``
#: draws: a repository is how this module loads its own aggregate and nobody
#: outside will hold one. ``RatedPlayerQuery`` is the opposite — it exists
#: *because* a reader outside must not be able to hold something it could move.
RATING_DEMANDS: tuple[type, ...] = (RatedPlayerQuery,)


RATING_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=RatedPlayerQuery,
        name="EventSourcedRatedPlayers",
        build=build_rated_player_query,
    ),
)


P = TypeVar("P")


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in RATING_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "RATING_DEMANDS",
    "RATING_IMPLEMENTATIONS",
    "implementations_of",
]
