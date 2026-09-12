"""Handing a completed line-up to whoever records games.

**Written once because there are two places a line-up can complete**, and they
are not obviously two: the acceptance that fills the last seat, and the mint of a
challenge born of two *Let's play* yeses, whose seats are accepted from birth and
which is therefore already complete in a **singles** sport. Two copies of this
would be two places for *what counts as a game* to be decided, and the second copy
is the one nobody would think to change.

**In `application/` and not beside the port it calls.** The port is a
``Protocol`` and belongs in ``domain/``; this performs I/O through it, which is a
use case's job — the same split ``matchmaking`` keeps between
``domain/mutual_challenge.py`` and the caller that drives it.
"""

from __future__ import annotations

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.planned_game import PlannedGameHandover


async def hand_over(
    challenge: Challenge, *, at: Instant, games: PlannedGameHandover
) -> None:
    """This challenge's completed court, in the port's vocabulary.

    **A friendly must be chosen.** A send carries the mode its search ran under;
    the deck and a mutual yes carry none, because neither surface asks. The
    absence resolves to **counted** — *a friendly is a thing people choose*, so
    nobody may end up with one by accident, and the reverse default would leave
    the games ledger empty on the surface most games come from.

    Empty seats cannot reach here — a complete line-up has none — and they are
    filtered rather than asserted about, because this function's job is to
    translate rather than to re-check the caller's standing.
    """

    await games.open_planned_game(
        challenge_id=challenge.id,
        sport=challenge.sport,
        counted=challenge.mode is not SearchMode.FOR_FUN,
        window=None if challenge.window is None else challenge.window.value,
        line_up=tuple(
            (seat.side.value, seat.player_id)
            for seat in challenge.seats
            if seat.player_id is not None
        ),
        occurred_at=at,
    )
