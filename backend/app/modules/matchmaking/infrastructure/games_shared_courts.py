"""``SharedCourtQuery``, answered by the ``games`` context and translated here.

**The deck's cool-off reads this and nothing else does** (``docs/adr/0169`` §6).
*Somebody you are already with is not in your deck, and stays out for thirty
days after* — and what *after* is dated from is the moment ``docs/adr/0168`` lets
a member leave the chat: the entry that said *we played*, the call-off, or the
entry window closing on silence. Those are three readings of one aggregate, and
the aggregate is where they are made.

**It reads through ``GameDirectory`` and the game's own methods**, on the
argument ``conversations/infrastructure/games_played_court.py`` already makes
for the same arrow: the aggregate is where the standing is, and a second
published read declaring *when did this court go behind them* would be a second
place for that to be true. ``Game.became_history_at`` is that fold — the one
moment ``GAME_IS_HISTORY`` is dated from — and this class reads it and adds
nothing to it.

**Not a reading of ``played_counterparts``**, and the reason is written on the
port. That read dates a ghost from its plan and files a call-off nowhere — both
by decisions of their own about *what happened between you* (``docs/adr/0163``
§3) — and the cool-off asks a different question, *when did this court stop being
ahead of you*, which a row answering the first cannot be bent to without one of
the two decisions quietly reversing.

**A seat the searcher left is no court of theirs.** ``playing`` answers the games
somebody is on the court of **now**, so a departure ends the pair here the moment
it opens the seat — a game that is ahead is a game they are no longer in, and one
that is behind is one they were not on the court for. It follows that a departure
which calls the game off (``docs/adr/0165`` §3 — the leaver was the second-last
player on it) cools **nobody** off: the leaver is off the court, and for the person
left behind the leaver's seat is open, so ``counterparts_of`` names nobody. That
is the pair rule ``games`` already keeps for its own history — a vacated seat is
nobody's counterpart — and the cool-off's reason points the same way: a rematch
is arranged in the chat the two already have, and that room was destroyed by the
call-off.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Clock, Instant, instant
from app.modules.games.domain.ports import GameDirectory
from app.modules.matchmaking.domain.ports import (
    PAIRWISE_COUNTERPART_BOUND,
    SharedCourt,
)


@final
class GamesSharedCourts:
    """*Who am I on a court with, and which of those courts is behind us?*"""

    def __init__(self, games: GameDirectory, clock: Clock) -> None:
        self._games = games
        self._clock = clock

    async def shared_courts(self, searcher_id: UUID) -> tuple[SharedCourt, ...]:
        """One row per person, an ahead court first, then newest behind first.

        The clock is read here rather than demanded of the caller because the
        port takes none: *ahead* is a fact about this instant, and a caller that
        could supply the instant could supply a stale one.
        """

        now = instant(self._clock.now())
        courts: dict[UUID, Instant | None] = {}
        for game in await self._games.playing(searcher_id):
            behind_since = game.became_history_at(now)
            for other in game.line_up.counterparts_of(searcher_id):
                courts[other] = (
                    _the_more_binding(courts[other], behind_since)
                    if other in courts
                    else behind_since
                )

        rows = [
            SharedCourt(counterpart_id=other, behind_since=behind_since)
            for other, behind_since in courts.items()
        ]
        # **Ahead first, then newest first, then the bound** — in that order,
        # because a bound applied to an unordered list would drop an arbitrary
        # half rather than the oldest one, and the order is what makes a person
        # cut off by the bound one with five hundred more recent courts ahead
        # of them.
        rows.sort(key=lambda row: (not row.ahead, _newest(row), row.counterpart_id))
        return tuple(rows[:PAIRWISE_COUNTERPART_BOUND])


def _the_more_binding(so_far: Instant | None, this: Instant | None) -> Instant | None:
    """Of two courts between one pair, the one the cool-off reads.

    A court ahead beats any court behind, because the two are *with* each other
    for as long as it stands; between two behind them, the later moment is the
    one the window runs from.
    """

    if so_far is None or this is None:
        return None
    return max(so_far, this)


def _newest(row: SharedCourt) -> float:
    """Sort key: later behind-moments first, ahead rows equal among themselves."""

    return 0.0 if row.behind_since is None else -row.behind_since.timestamp()


__all__ = ["GamesSharedCourts"]
