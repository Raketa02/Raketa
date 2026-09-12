"""The moment guard, for the three acts that move a seat on a court that has
been a game (``docs/adr/0162`` §4).

**Written once because three use cases read it** — the departure, the fill and
the acceptance — and it is the same question each time: *may a seat on this
court still be left, or taken?* Three copies would be three chances to answer it
differently, and the one that drifted would be the one that let a newcomer accept
into *Sunday* on Monday.

**In ``application/`` and not beside the port it calls**, on ``completed_line_up.py``'s
argument: the port is a ``Protocol`` and belongs in ``domain/``; this performs I/O
through it, which is a use case's job.

**Asked only on a court that has been a game.** A half-built court that was never
one costs no read; a court that has been one has a game behind it by construction
— the opening runs in the acceptance's own transaction — so a port answering
``None`` there is a broken precondition rather than a state, and it raises rather
than admitting the act. The alternative is a seat moving on a record nobody can
find.
"""

from __future__ import annotations

from app.kernel import Instant, invariant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import (
    TheGameIsHistory,
    TheGameMomentHasPassed,
)
from app.modules.challenges.domain.seatable_game import (
    LineUpChange,
    SeatableGameQuery,
)


async def refuse_a_court_closed_to_seating(
    challenge: Challenge, *, at: Instant, games: SeatableGameQuery
) -> None:
    """Refuse the act if the game this court became no longer admits a seat
    change: **its moment has passed**, or **it has happened or never will**.

    Two refusals and no third: a court that was never a game returns without a
    read, and one that has a game is admitted unless the game says otherwise.
    """

    if not challenge.has_become_a_game_at(at):
        return
    change = invariant(
        await games.line_up_change_on(challenge.id, now=at),
        f"a court that has been a game with no game behind it: {challenge.id}",
    )
    if change is LineUpChange.GAME_IS_HISTORY:
        raise TheGameIsHistory()
    if change is LineUpChange.MOMENT_PASSED:
        raise TheGameMomentHasPassed()


__all__ = ["refuse_a_court_closed_to_seating"]
