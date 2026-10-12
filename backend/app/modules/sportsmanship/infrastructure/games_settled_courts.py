"""``SettledCourts`` over ``games``' directory. **The translation lives here.**

The adapter is in the *consumer's* infrastructure, which is the shape ``games``
itself takes for ``PlayerNames``: a provider publishes what it knows about its
own subject and the context that wants it narrower does the narrowing, so a
question about sportsmanship does not become a method on somebody else's port.

**It asks *which games are mine* and never *which game is this*.** The directory
answers about one player, so a game the caller did not play in is not findable
through this read at all — *you may only rate a court you were on* is the shape of
the query rather than a check somebody remembered to write. That is why the two
arities cost the same thing here: the singular is the plural with one id kept,
because there was never a cheaper way to ask. The cost is the same cost every read
in ``games`` has, which is bounded by how many games the platform has recorded;
the index that fixes it belongs with the first query that measures it.

**``RATEABLE`` is ``games``' two words intersected, and the intersection is the
whole rule.** *Settled* over there includes a game called off or started short,
and there is nobody to rate for an evening that did not happen; *played* includes
a game whose score is still being argued over, and asking how somebody was while
they are still disagreeing with you about the score is asking at the worst
possible moment. What is left is a game that happened and is over: confirmed,
disputed because two sides named different winners, or **played with no score**
because a full court nobody recorded had its window close (#655). **A game with
no agreed score is in on purpose** — two people who cannot agree what the score
was, or four who never said, were still on a court together, and how that went
is exactly the thing this context exists to collect.
"""

from __future__ import annotations

from typing import Final, final
from uuid import UUID

from app.kernel import Instant
from app.modules.games.domain.game import Game
from app.modules.games.domain.ports import GameDirectory
from app.modules.games.domain.standing import PLAYED, SETTLED, GameStanding
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

    async def courts_of(
        self, player_id: UUID, *, now: Instant
    ) -> tuple[SettledCourt, ...]:
        """Every court of theirs that is over, in the directory's own order.

        **The card's week is not applied here.** What is over is ``games``'
        answer; when somebody may be asked about it is this context's, and it
        lives in ``window.py`` where the two clocks are.
        """

        return tuple(
            court
            for game in await self._games.playing(player_id)
            if (court := self._court(game, player_id=player_id, now=now)) is not None
        )

    async def court_of(
        self, game_id: UUID, *, player_id: UUID, now: Instant
    ) -> SettledCourt | None:
        """This player's settled court for that game, or ``None`` for all three
        absences — unknown, not theirs, not over."""

        for game in await self._games.playing(player_id):
            if game.id == game_id:
                return self._court(game, player_id=player_id, now=now)
        return None

    def _court(
        self, game: Game, *, player_id: UUID, now: Instant
    ) -> SettledCourt | None:
        """One game as a court, or ``None`` where there is nobody to ask about.

        **Both arities narrow in one place**, so *which endings may be rated*
        cannot come to two answers depending on which route asked.
        """

        standing = game.standing_at(now)
        if standing not in RATEABLE:
            return None
        played_at = game.played_at
        if played_at is None and standing is GameStanding.PLAYED_NO_SCORE:
            # **A full court nobody recorded was played at its hour** (#655):
            # nobody said when, and the booked hour is the evening's own
            # moment — the only one there is.
            played_at = game.starts_at
        if played_at is None:
            # A game nobody said they played: ``UNSCORED`` is reached only by a
            # booked game every report of not coming to was disputed (#547) —
            # two scores end confirmed or disputed since #654. A game with no
            # evening behind it is a game with nobody to rate, which is exactly
            # the answer every other absence here gets.
            return None
        return SettledCourt(
            game_id=game.id,
            rater_id=player_id,
            # The line-up's own order, which is what makes a walk over a
            # court the same walk on every process (``docs/adr/0105``).
            # ``counterparts_of`` is a set, so the order is taken from the
            # seatings rather than from it.
            # A played game has every seat filled — a score is refused on a
            # court with one open (``docs/adr/0162``) — so the ``None`` arm
            # is the type's and drops nobody.
            others=tuple(
                seating.player_id
                for seating in game.line_up.seatings
                if seating.player_id is not None and seating.player_id != player_id
            ),
            played_at=played_at,
        )
