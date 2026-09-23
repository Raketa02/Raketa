"""The register of what ``conversations`` demands of contexts it does not write.

**A sixth register rather than more rows in one of the five, and that is the rule
rather than a preference.** ``matcher_demands.py`` holds the ports the *matcher*
declares of contexts it does not write; ``games_demands.py``,
``rating_demands.py`` and ``player_score_demands.py`` each hold what one
*provider* publishes outward; ``challenge_demands.py`` holds what ``challenges``
demands of the matcher. This one holds what a **conversation** demands of the
three contexts it is told by and reads from — a fifth kind of claim, and each
register's exhaustiveness assertion is about its own kind and would stop meaning
anything with another kind in it.

**There is no ``conversations`` provider register, and there never will be.** A
conversation is *told* and tells nothing (``docs/adr/0146``), so it has no
consumers and publishes no port. Every row here is a demand.

**Four ports, and they are four because the facts have four owners.**
``ArrangingCourt`` is ``challenges``' and ``PlayedCourt`` is ``games``' — the two
records *one rule* is read against, and the reason they are two ports is that
they are two records. ``MemberFaces`` reaches ``users`` and the Player profile
for the one thing a room draws about a person. ``AccountHoldQuery`` is the third
spelling of a port whose provider does not exist, and its empty answer is
**measured rather than stubbed**: nobody can be held because nothing on this
platform can hold anybody.

**A row carries a builder over a session**, not an instance, so the suite cannot
quietly excuse an implementation with a database behind it — which here is three
of the four.

**A port with nothing registered is a red build**, asserted in the suite against
``CONVERSATION_DEMANDS``, because a port added in a hurry would otherwise look
contracted while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import (
    build_arranging_court,
    build_conversation_hold_query,
    build_member_faces,
    build_played_court,
)
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.core.config import get_settings
from app.modules.conversations.domain.ports import (
    AccountHoldQuery,
    ArrangingCourt,
    MemberFaces,
    PlayedCourt,
)

P = TypeVar("P")

#: What this context asks of the rest of the platform, declared as data for the
#: same reason the other four registers are: *a port with no registered
#: implementation* has to be a question something can ask.
#:
#: **The repository and the directory are not on this list**, and the line
#: between them and these is who owns the fact. A repository is how this module
#: loads its own aggregate and a directory is how it finds its own rows; nobody
#: outside will ever hold either. These four are somebody else's facts, and a
#: demand nobody executes is a demand satisfied by accident.
CONVERSATION_DEMANDS: tuple[type, ...] = (
    ArrangingCourt,
    PlayedCourt,
    MemberFaces,
    AccountHoldQuery,
)


CONVERSATION_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=ArrangingCourt,
        name="ChallengesArrangingCourt",
        build=build_arranging_court,
    ),
    RegisteredImplementation(
        port=PlayedCourt,
        name="GamesPlayedCourt",
        build=build_played_court,
    ),
    RegisteredImplementation(
        port=MemberFaces,
        name="ProfileMemberFaces",
        build=lambda session: build_member_faces(session, settings=get_settings()),
    ),
    RegisteredImplementation(
        port=AccountHoldQuery,
        name="NoHoldsExist",
        build=build_conversation_hold_query,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in CONVERSATION_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "CONVERSATION_DEMANDS",
    "CONVERSATION_IMPLEMENTATIONS",
    "implementations_of",
]
