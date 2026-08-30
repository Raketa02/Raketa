"""Send a challenge: one act, one transaction, everybody asked at once.

**Whole-send, never per-seat.** A partial send that silently dropped one invitee
would hand the organiser an arrangement they did not choose — which is the exact
harm recording the arrangement exists to prevent, arriving through the safety
check instead of through the proposal. A refused send writes nothing, so there is
no half-sent challenge to reconcile.

**One rule is checked here and not in the aggregate: one open challenge per
pair.** It is a statement about every *other* challenge, and an aggregate that
could see them would not be an aggregate. It is asked **across every sport** —
two people are either arranging a game or they are not, and asking for padel
while your tennis challenge sits unanswered is pestering with a sport chip on it.

**Across the whole court, not just from the organiser.** Sharing a line-up makes
a pair: every occupied seat but your own is somebody you have an open game with,
co-invitees and organiser alike. So the check is one bulk read over all six pairs
of a four, not three reads from the organiser outwards.

**The refusal names nobody.** The organiser's own challenges were always theirs
to read, so the client finds out who by reading them — which discloses nothing
and buys no exemption from the rule that no response says who was withheld.

This is the send's first gate and not its last: the four fail-closed
gates — a block either way, a hold, an account status and the mutual gender
preference — are re-verified in this same transaction by the route that owns
them.
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.challenges.application.commands import SendChallengeCommand
from app.modules.challenges.domain.challenge import Challenge
from app.modules.challenges.domain.errors import (
    AnOpenChallengeStandsWithThisPair,
)
from app.modules.challenges.domain.ports import (
    ChallengeRepository,
    OpenChallengeQuery,
)
from app.shared.ids import new_uuid


class SendChallenge:
    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        open_challenges: OpenChallengeQuery,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._challenges = challenges
        self._open_challenges = open_challenges
        self._uow = uow
        self._clock = clock

    async def execute(self, command: SendChallengeCommand) -> UUID:
        """Mint the challenge, or refuse the whole send. Returns its id."""

        at = instant(self._clock.now())
        # The aggregate refuses a court that is not the sport's, an organiser
        # who is not in it and a send with nobody to ask — that is where those
        # rules live. It is built first so that a malformed send is refused
        # before anything is read, and so that the pair check runs over a court
        # the aggregate has already agreed is a court.
        challenge = Challenge.sent(
            challenge_id=new_uuid(),
            sport=command.sport,
            mode=command.mode,
            window=command.window,
            organiser_id=command.organiser_id,
            arrangement=command.arrangement,
            occurred_at=at,
        )

        on_the_court = {
            plan.player_id for plan in command.arrangement if plan.player_id is not None
        }
        if await self._open_challenges.open_pairs_among(on_the_court, now=at):
            raise AnOpenChallengeStandsWithThisPair()

        await self._challenges.save(challenge)
        await self._uow.commit()
        return challenge.id
