"""The register of what ``games`` demands of other contexts, and who signs it.

**A tenth register rather than a row in one of the nine, and that is the rule
rather than a preference.** ``games_demands.py`` holds what this context
*publishes*; this holds what it *demands* of contexts it does not write — the
matcher's answer about a game's court (``docs/adr/0161``), and the Plan's answer
about a game's agreed moment (``docs/adr/0162``). A provider's list and a
consumer's list are two kinds of claim, and each register's exhaustiveness
assertion is about its own kind: **a new provider or a new consumer gets a new
register, not a row in somebody else's**, and the first person to add a row
should not have to guess which list it belongs in.

**Three rows, and the tuple is what is asserted over** — the third since #547:
who the club's desk checked in to a booked game (``ClubCheckIns``), the
booking's fact, which a report of not turning up asks first and whose adapter
the Bookings context signs, as the Plan signs the moment. A register asserts about
the ports it declares rather than about every ``Protocol`` in
``games/domain/ports.py``: most of them are this context's own reads or what it
publishes, contracted on the register beside this one. ``PlayerNames`` is the
other port this context consumes and is deliberately not here: one field wide,
over ``users``, it is what the games list already exercises on every read and
was never an outward demand on a context with rules of its own.

**The second row is what makes the Plan a provider without a provider
register.** ``games`` may not import the Plan (ADR-0145 §4), so it demands the
moment in its own words — keyed by the challenge the game was opened from, which
is the plan's own id (``docs/adr/0164`` §1) — and the Plan's adapter signs it:
the consumer contracts its own demand, which is the rule ``SeatableCourt``
states from the other side.

**A row carries a builder over the two seams a suite supplies for itself**, on
``challenge_demands.py``'s shape and for its reason: the pairing is recomputed
through the whole scoring pipeline, so what it needs beyond a session is the
process's candidate index and the exposure ledger behind Redis — and **no test
in this repository needs Redis running**. The builder funnels into
``build_game_court_pairing_over``, which is the same assembly the route's own
builder delegates to, so the suite exercises what ships rather than a second
construction of it.

**A port with nothing registered is a red build**, asserted in the suite against
``GAME_DEMANDS``, because a port added in a hurry would otherwise look contracted
while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.challenge_demands import PairingSeams, RegisteredPairing
from app.bootstrap.composition import (
    build_agreed_moment,
    build_club_check_ins,
    build_clock,
    build_court_pairing_workbench,
    build_domain_event_store,
    build_event_publisher,
    build_game_court_pairing_over,
    build_unit_of_work,
)
from app.core.config import get_settings
from app.modules.games.domain.ports import AgreedMoment, ClubCheckIns, CourtPairing

P = TypeVar("P")

#: What this context asks other contexts for, declared as data for the same
#: reason every other register is: *a port with no registered implementation* has to
#: be a question something can ask.
GAME_DEMANDS: tuple[type, ...] = (CourtPairing, AgreedMoment, ClubCheckIns)


GAME_IMPLEMENTATIONS: tuple[RegisteredPairing, ...] = (
    RegisteredPairing(
        port=CourtPairing,
        name="GamesCourtPairing",
        build=lambda seams: build_game_court_pairing_over(
            session=seams.session,
            workbench=build_court_pairing_workbench(
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
    ),
    RegisteredPairing(
        port=AgreedMoment,
        name="PlansAgreedMoment",
        # Over the session alone; the two seams the pairing needs are not
        # this port's, and the builder ignores them rather than the row taking a
        # second shape.
        build=lambda seams: build_agreed_moment(seams.session),
    ),
    RegisteredPairing(
        port=ClubCheckIns,
        name="BookingCheckIns",
        build=lambda seams: build_club_check_ins(seams.session),
    ),
)


def implementations_of(port: type[P]) -> tuple[RegisteredPairing[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in GAME_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "GAME_DEMANDS",
    "GAME_IMPLEMENTATIONS",
    "PairingSeams",
    "implementations_of",
]
