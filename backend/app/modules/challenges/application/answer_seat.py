"""One seat, answered. **Yes and no are two use cases, not a flag.**

A boolean argument would make the two acts one act with a parameter, and they are
not: *yes* opens a chat and moves a game towards being on, *no* reopens one seat
and disturbs nothing else. They are also the two halves of a Strand the platform
measures, so a caller that could pass either would be a caller that could pass the
wrong one.

**Each acceptance matters on its own.** There is still no ``GameOn`` event: the
chat opens on the **first** acceptance and grows with each one, which is what
makes *Line-up incomplete* not a waiting room.

**The acceptance that fills the last seat does one more thing, and it is the only
thing this context asks anybody else to do.** The line-up completing is the one
instant the arrangement is knowable and settled, so it is handed to whoever
records games — **inline, in this transaction**, so the yes and the game it
produced commit together or neither does
(``domain/planned_game.py``, ``docs/adr/0137``). That is not a standing being
announced: the standing is still folded, nothing subscribes to it, and this is a
call rather than an event, exactly as a mutual yes opening a challenge is.

**A decline is not a cancellation.** It reopens exactly the seat it was given and
the people who already agreed are still in — and if the last of them leaves, the
standing settles on its own, because what remains is the organiser alone on an
empty court.

**What both answers share is not here.** Loading a challenge of yours, folding
the standing the write produced and reading the court back is
``challenge_of_yours.py``, because the withdraw does all three too and none of
them is about an answer.

**No hold and no gate is re-checked here, and that is not an oversight.** The five
facts are re-verified when a challenge is *minted*, because that is the act that
puts two people in front of each other. Answering one you were already sent is a
statement about your own evening; refusing it on a gate would leak that something
changed about somebody else on the court, to the one person a refusal is not
allowed to tell.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.challenges.application.challenge_of_yours import AChallengeOfYours
from app.modules.challenges.application.commands import AnswerSeatCommand
from app.modules.challenges.application.completed_line_up import hand_over
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.domain.planned_game import PlannedGameOpening
from app.modules.challenges.domain.ports import ChallengeRepository, PlayerHandles
from app.modules.challenges.domain.standing import Standing


@final
class AcceptSeat(AChallengeOfYours):
    """*Yes.* It matters on its own, whatever the other seats do.

    **The only answer that can complete a line-up**, which is why it is the only
    one holding the game opening. A decline empties a seat; it can never fill the
    last one, so giving both answers the dependency would hand ``DeclineSeat``
    something it could not use and leave a reader wondering when it does.
    """

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        handles: PlayerHandles,
        uow: UnitOfWork,
        clock: Clock,
        planned_games: PlannedGameOpening,
    ) -> None:
        super().__init__(
            challenges=challenges, handles=handles, uow=uow, clock=clock
        )
        self._planned_games = planned_games

    async def execute(self, command: AnswerSeatCommand) -> StandingChallenge:
        at = instant(self._clock.now())
        challenge = await self._yours(command.challenge_id, command.player_id)
        challenge.accept(command.player_id, occurred_at=at)
        standing = await self._written(challenge, at)
        if standing is Standing.ON:
            # **The one thing this context asks anybody else to do**, and it
            # fires at the instant the arrangement is knowable and settled —
            # in this transaction, so the accept and the game it produced
            # commit together or neither does (``domain/planned_game.py``).
            await hand_over(challenge, at=at, games=self._planned_games)
        return await self._committed(challenge, standing, at)


@final
class DeclineSeat(AChallengeOfYours):
    """*No.* It reopens one seat and retires nothing."""

    async def execute(self, command: AnswerSeatCommand) -> StandingChallenge:
        at = instant(self._clock.now())
        challenge = await self._yours(command.challenge_id, command.player_id)
        challenge.decline(command.player_id, occurred_at=at)
        return await self._committed(
            challenge, await self._written(challenge, at), at
        )
