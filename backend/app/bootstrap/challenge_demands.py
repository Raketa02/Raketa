"""The register of what ``challenges`` demands of the matcher, and who signs it.

**A fourth register rather than more rows in one of the three, and that is the
rule rather than a preference.** ``matcher_demands.py`` holds the ports the
*matcher* declares of contexts it does not write; ``games_demands.py``,
``rating_demands.py`` and ``player_score_demands.py`` each hold what one
*provider* publishes outward. This one holds the demands ``challenges`` makes of
the matcher — a fourth kind of claim, and each register's exhaustiveness
assertion is about its own kind and would stop meaning anything with another kind
in it. **A new provider gets a new register, not a row in somebody else's**, and
the first person to add a row should not have to guess which list it belongs in.

**One row today, and the tuple is what is asserted over.** A register asserts
about the ports it declares rather than about every ``Protocol`` in
``challenges/domain/ports.py``: most of them are this context's own reads, signed
by adapters in its own infrastructure. ``OriginSearchQuery`` is the other outward
demand and the obvious next row here — enrolling it means writing its demands,
which is its own change and not this one.

**A row carries a builder over the two seams a suite supplies for itself**, not
over a bare session. The pairing is recomputed through the whole scoring
pipeline, so what it needs beyond a session is the process's candidate index and
the exposure ledger behind Redis — and **no test in this repository needs Redis
running**. The builder funnels into ``build_court_pairing_query_over``, which is
the same assembly the route's own builder delegates to, so the suite exercises
what ships rather than a second construction of it.

**A port with nothing registered is a red build**, asserted in the suite against
``CHALLENGE_DEMANDS``, because a port added in a hurry would otherwise look
contracted while nothing on earth ran against it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Generic, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

from app.bootstrap.composition import (
    build_clock,
    build_court_pairing_query_over,
    build_domain_event_store,
    build_event_publisher,
    build_unit_of_work,
)
from app.core.config import get_settings
from app.modules.challenges.domain.ports import CourtPairingQuery
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.ledgers import ExposureLedger

P = TypeVar("P")


@dataclass(frozen=True)
class PairingSeams:
    """What a suite hands an implementation of this port, beyond a session.

    Two, and each is a seam the platform itself supplies from somewhere other
    than the request: the candidate index is the **process's**
    (``docs/adr/0112``), and the exposure ledger is Redis, which a suite replaces
    with an in-memory one so that nothing here needs a server.
    """

    session: AsyncSession
    candidates: CandidateSource
    exposure: ExposureLedger


@dataclass(frozen=True)
class RegisteredPairing(Generic[P]):
    """One implementation of one port, and how to build it.

    ``name`` is what the suite reports a failure under, so it is the class's own
    name — a failure that reads ``ChallengeCourtCards`` says which registered
    implementation broke the contract without anybody counting parameters.
    """

    port: type[P]
    name: str
    build: Callable[[PairingSeams], P]


#: What this context asks the matcher for, declared as data for the same reason
#: the other three registers are: *a port with no registered implementation* has
#: to be a question something can ask.
CHALLENGE_DEMANDS: tuple[type, ...] = (CourtPairingQuery,)


CHALLENGE_IMPLEMENTATIONS: tuple[RegisteredPairing, ...] = (
    RegisteredPairing(
        port=CourtPairingQuery,
        name="ChallengeCourtCards",
        build=lambda seams: build_court_pairing_query_over(
            session=seams.session,
            clock=build_clock(),
            unit_of_work=build_unit_of_work(seams.session),
            event_store=build_domain_event_store(seams.session),
            events=build_event_publisher(seams.session),
            settings=get_settings(),
            exposure=seams.exposure,
            candidates=seams.candidates,
        ),
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredPairing[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in CHALLENGE_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "CHALLENGE_DEMANDS",
    "CHALLENGE_IMPLEMENTATIONS",
    "PairingSeams",
    "RegisteredPairing",
    "implementations_of",
]
