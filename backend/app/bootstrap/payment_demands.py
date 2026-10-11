"""The register of what ``payments`` demands of other contexts, and who signs
each demand (#548).

**A register of its own**, on the rule every register here states: a new
consumer gets a new register, not a row in somebody else's — and
``payments_demands.py`` is a different kind of claim, the two adapters of the
provider. **One row**: which games are over for good, so their money is the
club's to be paid out (``GamesOver``) — answered by ``proposals`` off the
bookings as it reads them, and signed in ``proposals/infrastructure/``, so the
arrow runs ``proposals → payments``. The payments' older demands — a seller, a
payer, a player's commitments — were contracted over HTTP only and are owed
rows here.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_games_over
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.payments.domain.ports import GamesOver

P = TypeVar("P")

#: What the Payments context asks of the rest of the platform, declared as data
#: so that *a port with no registered implementation* is a question something
#: can ask.
PAYMENT_DEMANDS: tuple[type, ...] = (GamesOver,)


PAYMENT_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=GamesOver,
        name="BookedGamesOver",
        build=build_games_over,
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in PAYMENT_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "PAYMENT_DEMANDS",
    "PAYMENT_IMPLEMENTATIONS",
    "implementations_of",
]
