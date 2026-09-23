"""*Remove the challenge.* The one route on a challenge that is nobody's seat —
and since ``docs/adr/0175`` §1 one act again: the organiser's, on a court that
was never a game.

**Admitted exactly while nobody besides the organiser holds an accepted seat**
(``docs/adr/0165`` §4) — before anybody has answered, and again once everybody
who joined has left — whatever seats are still deciding. A court somebody has
joined is nobody's to end for the others: the organiser leaves it like anybody
else (``leave_game.py``), and it is over by itself when nobody is on it, or one
player is and nobody is still deciding (``0165`` §3, ``0175`` §2).
``docs/adr/0142`` §2 refused the pre-answer case so that a withdraw-and-resend
could not hand somebody a fresh clock; ``0165`` §4 overrules that on the
simplicity rule and names the falsifier.

**A court that has been a game is refused with its own code** —
``court_has_been_a_game``. *Call it off* lived on this route for a season
(``docs/adr/0163``, ``docs/adr/0172`` §1) and is gone: a game with a seat open
ends by its seats or by its hour (``call_off_unfilled_courts.py``), never by
one person's decision over the others. Nothing here reaches the game any more,
so the hand-over left this use case with the act.

**Whole-challenge, irreversible, and whose act it is decided in the
aggregate.** Every one of those is the aggregate's to enforce and none of them
is re-derived here: this use case knows what every act in this context knows —
load a challenge of yours, write, fold the standing it produced, commit, and
answer with the court as it now stands. The conversation this challenge opened,
where one exists — there is none before anybody has answered, and there may be
one the organiser is alone in again — is destroyed by the context that owns
conversations, which subscribes to ``challenges.withdrawn`` rather than being
called from this line.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.challenges.application.challenge_of_yours import AChallengeOfYours
from app.modules.challenges.application.commands import WithdrawChallengeCommand
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.domain.game_of_court import GameOfCourtQuery
from app.modules.challenges.domain.ports import ChallengeRepository, PlayerNames


@final
class WithdrawChallenge(AChallengeOfYours):
    """The organiser removes a challenge nobody has joined."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        names: PlayerNames,
        court_games: GameOfCourtQuery,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        super().__init__(
            challenges=challenges,
            names=names,
            court_games=court_games,
            uow=uow,
            clock=clock,
        )

    async def execute(self, command: WithdrawChallengeCommand) -> StandingChallenge:
        """Withdraw it, and answer with the challenge as it now stands.

        **The reader is loaded as somebody holding a seat and refused as somebody
        who may not end it**, and the two refusals are different on purpose: a
        stranger is told no challenge of theirs has that id, and somebody with
        a seat who may not end it — an invitee — is told the act is not theirs.
        They can already see the challenge, so hiding it from them would be
        pretending it is not there while their own seat is drawn on it.
        """

        at = instant(self._clock.now())
        challenge = await self._yours(command.challenge_id, command.player_id)
        challenge.withdraw(command.player_id, occurred_at=at)
        standing = await self._written(challenge, at)
        return await self._committed(challenge, standing, at)
