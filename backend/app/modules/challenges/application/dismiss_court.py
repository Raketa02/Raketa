"""*Remove this row.* The reader's own act on a called-off court, met from the
Chats row — and recorded on the game, for everybody the court asked
(``docs/adr/0175`` §5).

**Why a door on the challenge.** The dismissal ``docs/adr/0172`` §5 built is
the game's: admitted for a player on its court and answered as a stranger is
answered for anybody else, so the game's id is not confirmed to people it was
never for. That rule is right for the card and wrong for the row: the Chats
row is drawn for **everybody the court asked**, and an invitee who was still
deciding when the hour or the last departure called it off has a row and no
card — the game never held a seat for them. This route asks the question the
row can answer — *were you asked*, which is holding any seat on the challenge,
answered or not — and hands the act to ``games`` on the hand-over, where the
same ``GameDismissed`` the trash writes is recorded. One set, read by both
lists (``docs/adr/0173``); one act, met from either.

**What it asks and in what order.** A stranger is told no challenge of theirs
has that id, as every act here says it. Then the standing: ``CALLED_OFF`` and
nothing else, refused with the row's own code. Then the game is told, in this
transaction, and it commits — the act is the whole request, as the trash is.
Answers nothing: the thing a redraw would draw is the thing that was removed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import (
    NoChallengeOfYoursHasThatId,
    TheCourtIsNotCalledOff,
)
from app.modules.challenges.domain.planned_game import PlannedGameHandover
from app.modules.challenges.domain.ports import ChallengeRepository
from app.modules.challenges.domain.standing import Standing


@final
@dataclass(frozen=True, slots=True)
class DismissCourtCommand:
    """*Remove this row.* One court, and the person clearing it from their
    own lists."""

    challenge_id: UUID
    player_id: UUID


@final
class DismissCourt:
    """*Remove this row* → the game this court became records that this reader
    has cleared it."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        planned_games: PlannedGameHandover,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._planned_games = planned_games
        self._uow = uow
        self._clock = clock

    async def execute(self, command: DismissCourtCommand) -> None:
        at = instant(self._clock.now())
        challenge = await self._asked(command.challenge_id, command.player_id)
        if challenge.standing_at(at) is not Standing.CALLED_OFF:
            raise TheCourtIsNotCalledOff()
        await self._planned_games.dismiss(
            challenge_id=challenge.id, by=command.player_id, occurred_at=at
        )
        await self._uow.commit()

    async def _asked(self, challenge_id: UUID, player_id: UUID) -> Challenge:
        """That challenge, if this player holds any seat on it — asked,
        whatever they answered. ``AChallengeOfYours._yours`` is the same
        question; it is spelled here because this act reads nothing back and
        borrows none of that base's readers."""

        challenge = await self._challenges.load(challenge_id)
        if challenge is None or not any(
            seat.holds(player_id) for seat in challenge.seats
        ):
            raise NoChallengeOfYoursHasThatId()
        return challenge


__all__ = ["DismissCourt", "DismissCourtCommand"]
