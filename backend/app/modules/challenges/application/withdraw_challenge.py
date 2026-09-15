"""*End it.* The one act on a challenge that is nobody's seat — two acts, in
fact, told apart by whether the court has been a game (``docs/adr/0165``
§4–§5), and one event.

**On a court that was never a game it is *Remove the challenge*.** The
organiser's, and admitted exactly while nobody besides the organiser holds an
accepted seat — before anybody has answered, and again once everybody who
joined has left — whatever seats are still deciding. A court somebody has
joined is nobody's to end for the others: the organiser leaves it like anybody
else (``leave_game.py``), and it is over by itself when at most one player is
on it and nobody is still deciding (``0165`` §3). ``docs/adr/0142`` §2 refused
the pre-answer case so that a withdraw-and-resend could not hand somebody a
fresh clock; ``0165`` §4 overrules that on the simplicity rule and names the
falsifier.

**On a court that has been a game it is *Call it off*, and it is the exit that
reaches the game** (``docs/adr/0163``). A reopened court is
``LINE_UP_INCOMPLETE`` again once somebody left it, and the withdraw is
admitted there for **any player on the court** — the organiser's seat buys
nothing, and there is no fallback to wait for. The game it became is **called
off** in this transaction, on the port the departure already uses: the
``WITHDRAWN`` on the challenge and the end on the game commit together or
neither does, for the reason the opening and the departure run inline — the
player who taps is told by a screen that cannot yet show it otherwise.

**Whole-challenge, irreversible, and whose act it is decided in the
aggregate.** Every one of those is the aggregate's to enforce and none of them
is re-derived here: this use case knows what every act in this context knows —
load a challenge of yours, write, fold the standing it produced, hand over where
there is a game to tell, commit, and answer with the court as it now stands.

**The one port here is the hand-over, and it is asked only where there is a
game.** A court that never became a game costs no read and hands over nothing —
there is nothing downstream of an arrangement that never became one. The
conversation this challenge opened, where one exists — there is none before
anybody has answered, and there may be one the organiser is alone in again —
is destroyed by the context that owns conversations, which subscribes to
``challenges.withdrawn`` rather than being called from this line; it does so
whether or not the room already holds its game. **No moment guard**,
deliberately (``docs/adr/0163`` §6): that guard stops a no-show vacating a seat
to block a result, and on a court with a seat open there is no result to block.
A court whose game has already ended by its clock is withdrawn all the same,
and the other side leaves the ghost standing.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.challenges.application.challenge_of_yours import AChallengeOfYours
from app.modules.challenges.application.commands import WithdrawChallengeCommand
from app.modules.challenges.application.read_challenges import StandingChallenge
from app.modules.challenges.domain.planned_game import PlannedGameHandover
from app.modules.challenges.domain.ports import ChallengeRepository, PlayerNames


@final
class WithdrawChallenge(AChallengeOfYours):
    """The organiser removes a challenge nobody has joined — or a player on a
    court that has been a game calls that game off, for everybody on it."""

    def __init__(
        self,
        *,
        challenges: ChallengeRepository,
        names: PlayerNames,
        uow: UnitOfWork,
        clock: Clock,
        planned_games: PlannedGameHandover,
    ) -> None:
        super().__init__(challenges=challenges, names=names, uow=uow, clock=clock)
        self._planned_games = planned_games

    async def execute(self, command: WithdrawChallengeCommand) -> StandingChallenge:
        """Withdraw it, and answer with the challenge as it now stands.

        **The reader is loaded as somebody holding a seat and refused as somebody
        who may not end it**, and the two refusals are different on purpose: a
        stranger is told no challenge of theirs has that id, and somebody with
        a seat who may not end it — an invitee on a court that was never a game,
        somebody off the court of one that has been — is told the act is not
        theirs. They can already see the challenge, so hiding it from them would
        be pretending it is not there while their own seat is drawn on it.
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
