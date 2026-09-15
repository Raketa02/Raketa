"""What every act on one challenge shares: finding it, and answering with it.

Three steps, and each of them is a rule rather than plumbing.

**Finding it is one refusal for two cases.** No such challenge, and a challenge
that is not yours, answer identically — separating them would tell a caller
whether a stranger's challenge id is real, one probe at a time.

**The standing is folded after the write and against the same instant the act
was recorded at**, so an accept that completed a four and the ``ON`` it produced
are one reading and not two.

**The reply is the redraw** (#327), and the names are read *after* the commit,
because they are the one thing on the answer that is not part of it. **The game
the court became is read before it** (``docs/adr/0172`` §4): it is asked of the
store the act just wrote to, in the act's own transaction, so an outage there
has already rolled the act back — and a redraw that could not say whether the
court has been a game would draw the wrong sheet.

Answering a seat and withdrawing a challenge are different acts on different
subjects — one is about your own seat and the other ends everybody's — and they
share this because what they share is neither of those things: it is *reading one
challenge of yours back*. It is a base class rather than three functions because
the four collaborators are the same four, and a caller assembling them per act is
a caller that can assemble one of them differently.
"""

from __future__ import annotations

import logging
from typing import Mapping
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant
from app.modules.challenges.application.read_challenges import (
    StandingChallenge,
    been_a_game,
    game_of,
)
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import NoChallengeOfYoursHasThatId
from app.modules.challenges.domain.game_of_court import GameOfCourtQuery
from app.modules.challenges.domain.ports import ChallengeRepository, PlayerNames
from app.modules.challenges.domain.standing import Standing

logger = logging.getLogger(__name__)


class AChallengeOfYours:
    """One challenge, loaded for somebody who holds a seat in it, and read back."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        names: PlayerNames,
        court_games: GameOfCourtQuery,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._names = names
        self._court_games = court_games
        self._uow = uow
        self._clock = clock

    async def _yours(self, challenge_id: UUID, player_id: UUID) -> Challenge:
        """That challenge, if this player is on its court.

        **The two ways this refuses are one code**: no such challenge, and a
        challenge that is not yours. Separating them would answer *is this
        challenge id real* about a stranger's evening.

        **Holding a seat is what this asks, and it is not the whole permission
        for every act.** It is the whole of it for an answer, because the seat
        being yours is the act; a withdraw asks one thing more, and asks it in
        the aggregate where the organiser is.
        """

        challenge = await self._challenges.load(challenge_id)
        if challenge is None or not any(
            seat.holds(player_id) for seat in challenge.seats
        ):
            raise NoChallengeOfYoursHasThatId()
        return challenge

    async def _written(self, challenge: Challenge, at: Instant) -> Standing:
        """Append what just happened and read the standing it produced.

        The standing is folded **after** the write and against the same instant
        the act was recorded at. **It does not commit** — an accept has one more
        thing to do first.
        """

        await self._challenges.save(challenge)
        return challenge.standing_at(at)

    async def _committed(
        self, challenge: Challenge, standing: Standing, at: Instant
    ) -> StandingChallenge:
        """The court as it now stands — **the reply is the redraw** (#327).

        The names are read **after** the commit, because they are the one thing
        on the answer that is not part of it: a name that could not be looked up
        must not roll back somebody's yes.

        **And it must not lose it either**, which is why the read cannot raise
        from here. The act is already committed at this line, so an exception
        would hand the player a failure for something that succeeded — and *the
        reply is the redraw* means they would do it again, into a seat that has
        already been answered or a challenge that has already ended. A name
        nobody could look up is the same absence as an account ``users`` no
        longer has: ``null`` on the wire, the seat intact, and the screen naming
        a side instead.

        **The game is read before the commit, and only where the fold says
        there is one.** It is the same store the act wrote to — the hand-over
        appends to it in this transaction, and the rows are flushed — so an
        outage there is one that has already refused the act; and a court the
        fold says has been a game with no game behind it is a broken store,
        refused rather than drawn as *never a game*.
        """

        games = await self._court_games.games_of(been_a_game([challenge]))
        game_id = game_of(challenge, games)
        await self._uow.commit()
        names: Mapping[UUID, str] = {}
        try:
            names = await self._names.names_of(
                sorted(
                    seat.player_id
                    for seat in challenge.seats
                    if seat.player_id is not None
                )
            )
        except Exception:
            logger.warning(
                "the court's names could not be read after an act on it",
                exc_info=True,
            )
        return StandingChallenge(
            challenge=challenge,
            standing=standing,
            read_at=at,
            names=names,
            game_id=game_id,
        )
