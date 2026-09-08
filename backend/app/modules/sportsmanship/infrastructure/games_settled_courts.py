"""``SettledCourts`` over ``games``' directory. **The translation lives here.**

The adapter is in the *consumer's* infrastructure, which is the shape ``games``
itself takes for ``PlayerHandles``: a provider publishes what it knows about its
own subject and the context that wants it narrower does the narrowing, so a
question about sportsmanship does not become a method on somebody else's port.

**It asks *which games are mine* and never *which game is this*.** The directory
answers about one player, so a game the caller did not play in is not findable
through this read at all — *you may only rate a court you were on* is the shape of
the query rather than a check somebody remembered to write. The cost is the same
cost every read in ``games`` has, which is bounded by how many games the platform
has recorded; the index that fixes it belongs with the first query that measures
it.

**``RATEABLE`` is ``games``' two words intersected, and the intersection is the
whole rule.** *Settled* over there includes a plan nobody ever claimed — a ghost —
and there is nobody to rate for an evening that did not happen; *played* includes
a game whose score is still being argued over, and asking how somebody was while
they are still disagreeing with you about the score is asking at the worst
possible moment. What is left is a game that happened and is over: confirmed, or
unscored because two sides could not agree and both windows closed. **An unscored
game is in on purpose** — two people who cannot agree what the score was were
still on a court together for two hours, and how that went is exactly the thing
this context exists to collect.
"""

from __future__ import annotations

from typing import Final, final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.ports import GameDirectory
from app.modules.games.domain.standing import PLAYED, SETTLED
from app.modules.sportsmanship.domain.card import SettledCourt

#: The standings a card may be drawn for: **played, and over.** Derived from
#: ``games``' own two sets rather than spelled as a literal pair, so a fourth
#: ending added over there arrives here as a question rather than as a silent
#: omission.
RATEABLE: Final = SETTLED & PLAYED


@final
class GamesSettledCourts:
    """``games``' aggregates, narrowed to *a court of mine that is over*."""

    def __init__(self, games: GameDirectory) -> None:
        self._games = games

    async def court_of(
        self, game_id: UUID, *, player_id: UUID, now: Instant
    ) -> SettledCourt | None:
        """This player's settled court for that game, or ``None`` for all three
        absences — unknown, not theirs, not over."""

        for game in await self._games.playing(player_id):
            if game.id != game_id:
                continue
            if game.standing_at(now) not in RATEABLE:
                return None
            return SettledCourt(
                game_id=game.id,
                rater_id=player_id,
                # The line-up's own order, which is what makes a walk over a
                # court the same walk on every process (``docs/adr/0105``).
                # ``counterparts_of`` is a set, so the order is taken from the
                # seatings rather than from it.
                others=tuple(
                    seating.player_id
                    for seating in game.line_up.seatings
                    if seating.player_id != player_id
                ),
            )
        return None
