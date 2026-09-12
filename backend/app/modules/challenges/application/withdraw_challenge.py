"""*End it.* The one act on a challenge that is nobody's seat.

**The exit exists exactly where nothing else ends it** (``docs/adr/0142``).
``AWAITING_ANSWERS`` ends itself when the clocks run out. ``ON`` has become a
game. ``LINE_UP_INCOMPLETE`` — somebody in, a seat open, nobody deciding — never
ends on its own, and nobody holds an exit: the acceptor is refused by the
already-answered rule and the organiser has had no act at all. This is that act.

**Except on a court that has been a game** (``docs/adr/0162`` §2), which is
``LINE_UP_INCOMPLETE`` again once somebody left it and is refused here all the
same: its exit is calling the game off, which reaches the game's record and is
#417's. The aggregate holds the refusal.

**Whole-challenge, organiser only, irreversible.** Every one of those is the
aggregate's to enforce and none of them is re-derived here: this use case knows
what every act in this context knows — load a challenge of yours, write, fold the
standing it produced, commit, and answer with the court as it now stands.

**Nothing is asked of anybody else.** The accept has one call outward, because a
completed line-up is a game somebody has to open; a withdraw ends an arrangement
that never became one, so there is nothing downstream of it and no port here.
The conversation this challenge opened is destroyed by the context that owns
conversations, and that context does not exist yet — when it does, it subscribes
to ``challenges.withdrawn`` rather than being called from this line.
"""

from __future__ import annotations

from typing import final

from app.kernel import instant
from app.modules.challenges.application.challenge_of_yours import AChallengeOfYours
from app.modules.challenges.application.commands import WithdrawChallengeCommand
from app.modules.challenges.application.read_challenges import StandingChallenge


@final
class WithdrawChallenge(AChallengeOfYours):
    """The organiser ends a half-built line-up, for everybody on it."""

    async def execute(self, command: WithdrawChallengeCommand) -> StandingChallenge:
        """Withdraw it, and answer with the challenge as it now stands.

        **The reader is loaded as somebody holding a seat and refused as somebody
        who is not the organiser**, and the two refusals are different on
        purpose: a stranger is told no challenge of theirs has that id, and an
        invitee is told the withdraw is the organiser's. The invitee can already
        see the challenge, so hiding it from them would be pretending it is not
        there while their own seat is drawn on it.
        """

        at = instant(self._clock.now())
        challenge = await self._yours(command.challenge_id, command.player_id)
        challenge.withdraw(command.player_id, occurred_at=at)
        return await self._committed(
            challenge, await self._written(challenge, at), at
        )
