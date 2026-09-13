"""*End it.* The one act on a challenge that is nobody's seat.

**The exit exists exactly where nothing else ends it** (``docs/adr/0142``).
``AWAITING_ANSWERS`` ends itself when the clocks run out. ``ON`` has become a
game. ``LINE_UP_INCOMPLETE`` — two or more in, a seat open, nobody deciding —
never ends on its own. This is the act that ends it. (An acceptor can now take
their yes back, ``docs/adr/0165`` §1, and a court left with one person on it
ends by itself; what the withdraw *is* once that is so is ``0165`` §4's, built
by #426.)

**And on a court that has been a game, it is the exit that reaches the game**
(``docs/adr/0163``). A reopened court is ``LINE_UP_INCOMPLETE`` again once
somebody left it, and the withdraw is admitted there too — by the organiser, or
by any remaining player once the organiser's own seat is open. The game it
became is **called off** in this transaction, on the port the departure already
uses: the ``WITHDRAWN`` on the challenge and the end on the game commit together
or neither does, for the reason the opening and the departure run inline — the
player who taps is told by a screen that cannot yet show it otherwise.

**Whole-challenge, irreversible, and whose act it is decided in the
aggregate.** Every one of those is the aggregate's to enforce and none of them
is re-derived here: this use case knows what every act in this context knows —
load a challenge of yours, write, fold the standing it produced, hand over where
there is a game to tell, commit, and answer with the court as it now stands.

**The one port here is the hand-over, and it is asked only where there is a
game.** A court that never became a game costs no read and hands over nothing —
there is nothing downstream of an arrangement that never became one. The
conversation this challenge opened is destroyed by the context that owns
conversations, which subscribes to ``challenges.withdrawn`` rather than being
called from this line; it does so whether or not the room already holds its
game. **No moment guard**, deliberately (``docs/adr/0163`` §6): that guard stops a
no-show vacating a seat to block a result, and on a court with a seat open there
is no result to block. A court whose game has already ended by its clock is
withdrawn all the same, and the other side leaves the ghost standing.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.challenges.application.challenge_of_yours import AChallengeOfYours
from app.modules.challenges.application.commands import WithdrawChallengeCommand
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.domain.planned_game import PlannedGameHandover
from app.modules.challenges.domain.ports import ChallengeRepository, PlayerHandles


@final
class WithdrawChallenge(AChallengeOfYours):
    """Somebody who holds the exit ends a half-built line-up, for everybody on
    it — and the game it became, if it became one."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        handles: PlayerHandles,
        uow: UnitOfWork,
        clock: Clock,
        planned_games: PlannedGameHandover,
    ) -> None:
        super().__init__(challenges=challenges, handles=handles, uow=uow, clock=clock)
        self._planned_games = planned_games

    async def execute(self, command: WithdrawChallengeCommand) -> StandingChallenge:
        """Withdraw it, and answer with the challenge as it now stands.

        **The reader is loaded as somebody holding a seat and refused as somebody
        who may not end it**, and the two refusals are different on purpose: a
        stranger is told no challenge of theirs has that id, and an invitee is
        told the act is not theirs. The invitee can already see the challenge,
        so hiding it from them would be pretending it is not there while their
        own seat is drawn on it.
        """

        at = instant(self._clock.now())
        challenge = await self._yours(command.challenge_id, command.player_id)
        challenge.withdraw(command.player_id, occurred_at=at)
        standing = await self._written(challenge, at)
        if challenge.has_become_a_game():
            # **The game is told in this transaction**, so the ``WITHDRAWN`` on
            # the challenge and the end on the game commit together or neither
            # does. A court that never became a game hands over nothing.
            await self._planned_games.call_off(
                challenge_id=challenge.id, by=command.player_id, occurred_at=at
            )
        return await self._committed(challenge, standing, at)
