"""The register of what ``player_score`` publishes outward, and who implements it.

**A fourth register in the shape of the other three**, and a fourth file for the
reason ``games_demands.py`` was a second one: ``MATCHER_DEMANDS`` asserts
exhaustiveness over the ports the *matcher* declares of contexts it does not
write, and ``GAMES_DEMANDS``, ``RATING_DEMANDS`` and this one each assert it over
what **one provider** publishes. Rows of four kinds in one list would make every
assertion a claim about something else, and the first person to add a row would
have to guess which.

**What this one adds that the other two provider registers do not** is a provider
with **nothing behind it** — no aggregate, no repository, no table. Its rows are
arithmetic over two other contexts, which is why its suite arranges the world
through *their* aggregates and why the register is worth having at all: there is
nothing here a reader could mistake for storage that would prove it works.

**One port and one implementation, and the suite is not thereby pointless.** What
it executes is the arithmetic this whole context exists to keep — Player
reliability in points, from the lines two other contexts publish (#659) —
against a real database with real aggregates in front of it, which is the only
place a line can be misread. It is also where
the two provider reads underneath it are proved: they are folds over two other
contexts' streams, and the only honest way to exercise a fold is to arrange the
world through the aggregates that wrote it (``docs/adr/0029``).

**A row carries a builder over a session**, not an instance, because the
implementation genuinely needs one — a suite that could only construct the
implementations needing no I/O would be a suite that quietly excused every real
adapter.

**A port with nothing registered is a red build**, asserted in the suite against
``PLAYER_SCORE_DEMANDS``, because a port added in a hurry would otherwise look
contracted while nothing on earth ran against it.
"""

from __future__ import annotations

from typing import TypeVar

from app.bootstrap.composition import build_published_score_query
from app.bootstrap.matcher_demands import RegisteredImplementation
from app.modules.player_score.domain.ports import PublishedScoreQuery

#: What this context owes the rest of the platform. One port, because there is
#: one question — *what does the record say about this person* — and a second
#: method for the figure alone would be a second place for the figure and its
#: counts to disagree.
PLAYER_SCORE_DEMANDS: tuple[type, ...] = (PublishedScoreQuery,)


PLAYER_SCORE_IMPLEMENTATIONS: tuple[RegisteredImplementation, ...] = (
    RegisteredImplementation(
        port=PublishedScoreQuery,
        name="PointsFromTheRecord",
        build=build_published_score_query,
    ),
)


P = TypeVar("P")


def implementations_of(port: type[P]) -> tuple[RegisteredImplementation[P], ...]:
    """Every registered implementation of one port, in registration order."""

    return tuple(
        implementation
        for implementation in PLAYER_SCORE_IMPLEMENTATIONS
        if implementation.port is port
    )


__all__ = [
    "PLAYER_SCORE_DEMANDS",
    "PLAYER_SCORE_IMPLEMENTATIONS",
    "implementations_of",
]
