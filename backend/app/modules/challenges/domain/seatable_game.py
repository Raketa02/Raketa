"""The third seam this context has onto a **game**: may its seats still change?

``planned_game.py`` hands an arrangement and a departure over; ``settled_game.py``
asks whether anything more will happen to the game that came of it; this asks
the question every act that moves a seat on a court that has been a game must
ask first (``docs/adr/0162`` §4): **is the game still awaiting its entry, and is
its agreed moment ahead?** The second half is a fact about a *plan*, which this
context knows even less about than a game — so it is asked of ``games``, which
demands it of the Plan in turn, and what crosses here is one of three words.

**Three readers, one answer.** The departure, the fill and the acceptance are
gated on the same two facts, so a port answering all three is what keeps the
leaving and the filling from disagreeing about one instant.
"""

from __future__ import annotations

from enum import Enum
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant


@final
class LineUpChange(str, Enum):
    """Whether a seat may still change on the game this court became.

    A second spelling of ``games``' ``SeatChange``, equal by name on purpose —
    the mapping at the adapter is identity rather than a table — and this
    context's own, because an application layer here importing a games type
    would be the reuse the split exists to refuse.
    """

    ADMITTED = "ADMITTED"
    MOMENT_PASSED = "MOMENT_PASSED"
    GAME_IS_HISTORY = "GAME_IS_HISTORY"


@runtime_checkable
class SeatableGameQuery(Protocol):
    """*May a seat on this court still be left, or taken?* — of the game it became.

    Signed by an adapter that reads the ``games`` context, wired in the
    composition root with every other choice of implementation.
    """

    async def line_up_change_on(
        self, challenge_id: UUID, *, now: Instant
    ) -> LineUpChange | None:
        """The answer for this challenge's game, or ``None`` because it has
        none — which a caller on an ``ON`` court treats as a broken precondition
        rather than as permission.
        """
        ...


__all__ = ["LineUpChange", "SeatableGameQuery"]
