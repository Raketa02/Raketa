"""One seat, answered. **Yes and no are two use cases, not a flag.**

A boolean argument would make the two acts one act with a parameter, and they are
not: *yes* opens a chat and moves a game towards being on, *no* reopens one seat
and disturbs nothing else. They are also the two halves of a Strand the platform
measures, so a caller that could pass either would be a caller that could pass the
wrong one.

**Each acceptance matters on its own.** There is no ``GameOn`` event and no moment
where the game becomes real: the chat opens on the **first** acceptance and grows
with each one, which is what makes *Line-up incomplete* not a waiting room.

**A decline is not a cancellation.** It reopens exactly the seat it was given and
the people who already agreed are still in — and if the last of them leaves, the
standing settles on its own, because what remains is the organiser alone on an
empty court.

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
from app.kernel import Clock, Instant, instant
from app.modules.challenges.application.commands import AnswerSeatCommand
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import NoChallengeOfYoursHasThatId
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.domain.ports import ChallengeRepository


class _AnswerSeat:
    """What both answers share: load the challenge, or refuse to admit it exists."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._uow = uow
        self._clock = clock

    async def _yours(self, command: AnswerSeatCommand) -> Challenge:
        """That challenge, if this player is on its court.

        **The two ways this refuses are one code**: no such challenge, and a
        challenge that is not yours. Separating them would answer *is this
        challenge id real* about a stranger's evening.
        """

        challenge = await self._challenges.load(command.challenge_id)
        if challenge is None or not any(
            seat.holds(command.player_id) for seat in challenge.seats
        ):
            raise NoChallengeOfYoursHasThatId()
        return challenge

    async def _saved(self, challenge: Challenge, at: Instant) -> StandingChallenge:
        """Write the answer, then read the standing it produced.

        The standing is folded **after** the write and against the same instant
        the answer was recorded at, so an accept that completed a four and the
        ``ON`` it produced are one reading and not two.
        """

        await self._challenges.save(challenge)
        await self._uow.commit()
        return StandingChallenge(
            challenge=challenge, standing=challenge.standing_at(at)
        )


@final
class AcceptSeat(_AnswerSeat):
    """*Yes.* It matters on its own, whatever the other seats do."""

    async def execute(self, command: AnswerSeatCommand) -> StandingChallenge:
        at = instant(self._clock.now())
        challenge = await self._yours(command)
        challenge.accept(command.player_id, occurred_at=at)
        return await self._saved(challenge, at)


@final
class DeclineSeat(_AnswerSeat):
    """*No.* It reopens one seat and retires nothing."""

    async def execute(self, command: AnswerSeatCommand) -> StandingChallenge:
        at = instant(self._clock.now())
        challenge = await self._yours(command)
        challenge.decline(command.player_id, occurred_at=at)
        return await self._saved(challenge, at)
