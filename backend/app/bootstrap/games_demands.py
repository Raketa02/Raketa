"""The register of what ``games`` publishes outward, and who implements it.

**The same shape as ``matcher_demands.py``, and a second file rather than more
rows in that one.** That register holds the ports the *matcher* declares of
contexts it does not write; these are the ports a **provider** publishes for
seven consumers — the card's counted-games block, *Last 5*, the two facts the
Player Score ticket reads per player, the confirmed results the rating context
walks forward (``docs/adr/0139``), the one question a **plan** asks before
it lets anybody write a slot (``docs/adr/0148`` §8), the record sheet's
opponent variety, and the one question a **challenge** asks before a seat on
a court that has been a game may move (``docs/adr/0162`` §4). Rows of both
kinds in one list would make ``MATCHER_DEMANDS``'s exhaustiveness assertion a
claim about two different things, and the first person to add a row would have
to guess which.

**A row carries a builder over a session**, not an instance, so the suite cannot
quietly excuse the implementations with a database behind them — which here is
all of them.

**A port with nothing registered is a red build**, asserted in the suite against
``GAMES_DEMANDS``, because a port added in a hurry would otherwise look
contracted while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.matcher_demands import RegisteredImplementation
from app.bootstrap.composition import (
    build_confirmed_result_ledger,
    build_game_directory,
    build_game_history_query,
    build_opponent_variety_query,
    build_planning_court,
    build_seatable_court,
)
from app.modules.games.domain.ports import (
    ConfirmedResultLedger,
    GameDirectory,
    GameHistoryQuery,
    OpponentVarietyQuery,
    PlanningCourt,
    SeatableCourt,
)

#: What this context owes the rest of the platform, declared as data for the
#: same reason the matcher's list is: *a port with no registered implementation*
#: has to be a question something can ask.
#:
#: **The directory is on this list and the repository is not**, and the line
#: between them is who reads it. A repository is how this module loads its own
#: aggregate and nobody outside will ever hold one. The directory is where
#: *was this counted or a friendly* and *was its result confirmed* are answered
#: about one player — the two facts the rating and Player Score tickets were
#: promised — so it is a demand somebody else will execute, and a demand nobody
#: executes is a demand satisfied by accident.
#:
#: **``PlanningCourt`` is here even though it has one consumer**, and that is the
#: rule rather than an exception: it is the read that decides whether a slot
#: write may land, so *a demand nobody executes* is exactly the thing it must not
#: be. The Plan cannot contract it — a consumer contracting its own provider's
#: port is the consumer marking its own homework — which is why it sits beside
#: the three the rest of the platform already reads.
#:
#: **``SeatableCourt`` is here for the same reason** (``docs/adr/0162`` §4): it
#: is the read that decides whether a departure, a fill or an acceptance may
#: land on a court that has been a game, and its one consumer — ``challenges`` —
#: cannot contract it without marking its own homework.
GAMES_DEMANDS: tuple[type, ...] = (
    GameHistoryQuery,
    GameDirectory,
    ConfirmedResultLedger,
    PlanningCourt,
    OpponentVarietyQuery,
    SeatableCourt,
)


GAME_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=GameHistoryQuery,
        name="EventSourcedGameHistory",
        build=build_game_history_query,
    ),
    RegisteredImplementation(
        port=GameDirectory,
        name="EventSourcedGameDirectory",
        build=build_game_directory,
    ),
    RegisteredImplementation(
        port=ConfirmedResultLedger,
        name="EventSourcedConfirmedResults",
        build=build_confirmed_result_ledger,
    ),
    RegisteredImplementation(
        port=PlanningCourt,
        name="EventSourcedPlanningCourt",
        build=build_planning_court,
    ),
    RegisteredImplementation(
        port=OpponentVarietyQuery,
        name="EventSourcedGameHistory",
        build=build_opponent_variety_query,
    ),
    RegisteredImplementation(
        port=SeatableCourt,
        name="EventSourcedSeatableCourt",
        build=build_seatable_court,
    ),
)


P = TypeVar("P")


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in GAME_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "GAMES_DEMANDS",
    "GAME_IMPLEMENTATIONS",
    "implementations_of",
]
