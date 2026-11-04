"""The register of what the Player profile demands of other contexts, and who
signs each demand (#726).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register, not a row in somebody else's. **One row**: where a
club is (``ClubPoints``), for a Location area picked as a club in place of a
reading (``docs/adr/0200`` §10) — answered by ``clubs`` over its own published
directory and signed in ``clubs/infrastructure/``, so the arrow keeps running
``clubs → player_profile``. The profile's other ports — photo storage, the
transcoder, the photo check — are the outside world's, and are not demands on a
context.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_club_points
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.player_profile.domain.ports import ClubPoints

P = TypeVar("P")

#: What the Player profile asks of the rest of the platform, declared as data
#: so that *a port with no registered implementation* is a question something
#: can ask.
PLAYER_PROFILE_DEMANDS: tuple[type, ...] = (ClubPoints,)


PLAYER_PROFILE_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=ClubPoints,
        name="DirectoryClubPoints",
        build=build_club_points,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in PLAYER_PROFILE_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "PLAYER_PROFILE_DEMANDS",
    "PLAYER_PROFILE_IMPLEMENTATIONS",
    "implementations_of",
]
