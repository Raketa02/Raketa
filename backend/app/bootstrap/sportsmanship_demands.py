"""The register of what ``sportsmanship`` publishes outward, and who answers it.

**A sixth register, and the fourth of the *provider* kind.** ``matcher_demands``
and ``player_record_demands`` hold what a **consumer** declares of contexts it
does not write; ``games_demands``, ``rating_demands``, ``player_score_demands``
and this one each hold what **one provider** publishes. Rows of two kinds in one
list would make every exhaustiveness assertion a claim about something else, and
the first person to add a row would have to guess which — which is the rule
``backend/CLAUDE.md`` states for the next arrival, and this is the next arrival.

**One port and two questions, and the suite is not thereby ceremonial.** What it
executes is the pair of rules this context's whole design rests on and that no
type could hold: the window is fifty **people** rather than fifty ratings, and
the answer given to the *subject* carries no figure and no count. Both are
properties of rows in a table, and the only honest way to exercise a fold over a
table is against one — arranged, as everywhere else here, through this context's
own aggregate rather than an ``INSERT`` (``docs/adr/0029``).

**What is deliberately not on this list** is ``SportsmanshipLedger`` and
``SettledCourts``. The first is this context's own store and the second is a
demand it makes of ``games``; neither is something this context publishes, and a
register mixing what a context *keeps* with what it *says* would assert
exhaustiveness over nothing in particular.

**A port with nothing registered is a red build**, asserted in the suite against
``SPORTSMANSHIP_DEMANDS``, because a port added in a hurry would otherwise look
contracted while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_published_sportsmanship
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.sportsmanship.domain.ports import PublishedSportsmanshipQuery

#: What this context owes the rest of the platform. **One port**, because there
#: is one window — and the two methods on it are two *resolutions* of one record
#: rather than two questions, which is exactly why they must not be two ports:
#: a second port would be a second fold, free to disagree with the first about
#: the number it coarsens.
SPORTSMANSHIP_DEMANDS: tuple[type, ...] = (PublishedSportsmanshipQuery,)


SPORTSMANSHIP_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=PublishedSportsmanshipQuery,
        name="StandingAnswersAboutThem",
        build=build_published_sportsmanship,
    ),
)


P = TypeVar("P")


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in SPORTSMANSHIP_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "SPORTSMANSHIP_DEMANDS",
    "SPORTSMANSHIP_IMPLEMENTATIONS",
    "implementations_of",
]
