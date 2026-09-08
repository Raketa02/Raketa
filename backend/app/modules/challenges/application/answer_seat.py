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

**No hold and no gate is re-checked here, and that is not an oversight.** The five
facts are re-verified when a challenge is *minted*, because that is the act that
puts two people in front of each other. Answering one you were already sent is a
statement about your own evening; refusing it on a gate would leak that something
changed about somebody else on the court, to the one person a refusal is not
allowed to tell.
"""

from __future__ import annotations

import logging
from typing import Mapping, final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.challenges.application.completed_line_up import hand_over
from app.modules.challenges.application.commands import AnswerSeatCommand
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import NoChallengeOfYoursHasThatId
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.domain.planned_game import PlannedGameOpening
from app.modules.challenges.domain.ports import ChallengeRepository, PlayerHandles
from app.modules.challenges.domain.standing import Standing

logger = logging.getLogger(__name__)


class _AnswerSeat:
    """What both answers share: load the challenge, or refuse to admit it exists."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        handles: PlayerHandles,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._handles = handles
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

    async def _written(self, challenge: Challenge, at: Instant) -> Standing:
        """Append the answer and read the standing it produced.

        The standing is folded **after** the write and against the same instant
        the answer was recorded at, so an accept that completed a four and the
        ``ON`` it produced are one reading and not two. **It does not commit** —
        an accept has one more thing to do first.
        """

        await self._challenges.save(challenge)
        return challenge.standing_at(at)

    async def _committed(
        self, challenge: Challenge, standing: Standing, at: Instant
    ) -> StandingChallenge:
        """The court as it now stands — **the reply is the redraw** (#327).

        The handles are read **after** the commit, because they are the one thing
        on the answer that is not part of it: a name that could not be looked up
        must not roll back somebody's yes.

        **And it must not lose it either**, which is why the read cannot raise
        from here. The answer is already committed at this line, so an exception
        would hand the player a failure for an act that succeeded — and *the
        reply is the redraw* means they would answer again, into a seat that has
        already been answered. A handle nobody could look up is the same absence
        as an account ``users`` no longer has: ``null`` on the wire, the seat
        intact, and the screen naming a side instead.
        """

        await self._uow.commit()
        handles: Mapping[UUID, str] = {}
        try:
            handles = await self._handles.handles_of(
                sorted(
                    seat.player_id
                    for seat in challenge.seats
                    if seat.player_id is not None
                )
            )
        except Exception:
            logger.warning(
                "the court's handles could not be read after an answer",
                exc_info=True,
            )
        return StandingChallenge(
            challenge=challenge, standing=standing, read_at=at, handles=handles
        )


@final
class AcceptSeat(_AnswerSeat):
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
        challenge = await self._yours(command)
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
class DeclineSeat(_AnswerSeat):
    """*No.* It reopens one seat and retires nothing."""

    async def execute(self, command: AnswerSeatCommand) -> StandingChallenge:
        at = instant(self._clock.now())
        challenge = await self._yours(command)
        challenge.decline(command.player_id, occurred_at=at)
        return await self._committed(
            challenge, await self._written(challenge, at), at
        )
