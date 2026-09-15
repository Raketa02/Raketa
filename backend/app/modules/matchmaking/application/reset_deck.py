"""*Show them again* — one tap, and the deck is whole again for one sport.

**It writes one moment and clears nothing itself.** The three things a reset
lifts — every pass suppression, the day's dealt memory and the cool-off
(``docs/adr/0169`` §5) — are each read at the next deal off a durable record
the deal already holds, against this moment: a pass made before it no longer
hides, the memory reaches back no further than it, and a court behind the pair
before it no longer counts (``domain/deck.py``). Nothing is deleted: the pass
record stays, so a re-shown card is still a re-show; the search record stays;
the game stays. *Already asked* is not among the three — the people the viewer
has a live yes on are still theirs to wait on.

**No cache is touched, and that is the point of it being a moment.** The Redis
suppression keys are left to lapse on their own and the deal subtracts what the
record says was cleared. A reset that had to reach the cache would be a reset
that could fail soft, and a ``204`` that was a lie: the player would press it,
be told it worked, and open the same empty deck.

**Two refusals, and they are the deal's own words** (``refusals.py``) — a held
account and a sport the player holds no rating in. The deal owes a third about
*you*, a profile not committed, and this does not: a reset reads no radius, no
grid and no area, and a rated player with no profile has nothing to deal and
nothing the reset could harm. The hold is asked of the same port the deal asks,
failing closed like every gate.

**Idempotent, and a second press is still a second row.** Pressing twice in a
row leaves the deck as one press leaves it; what the second row records is that
it happened, which the ``PASS_SUPPRESS`` falsifier needs in order to exclude the
re-shows a reset caused (``deck_reset.py``).

**Answers nothing.** There is no shape a reset crosses the wire in, and the
route says ``204`` because of what exists rather than by discipline.
"""

from __future__ import annotations

from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.matchmaking.application.commands import ResetDeckCommand
from app.modules.matchmaking.application.refusals import (
    rated_in,
    refuse_a_held_player,
)
from app.modules.matchmaking.domain.deck_reset import DeckReset, DeckResetLedger
from app.modules.matchmaking.domain.ports import AccountHoldQuery
from app.modules.rating.domain.ports import SkillRatingRepository


@final
class ResetDeck:
    """One reset: a moment on the record, and nothing else."""

    def __init__(
        self,
        *,
        clock: Clock,
        ratings: SkillRatingRepository,
        holds: AccountHoldQuery,
        resets: DeckResetLedger,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._ratings = ratings
        self._holds = holds
        self._resets = resets
        self._uow = unit_of_work

    async def execute(self, command: ResetDeckCommand) -> None:
        """Refuse what the deal would refuse, then record the moment and commit."""

        now = self._clock.now()
        await rated_in(self._ratings, player_id=command.player_id, sport=command.sport)
        await refuse_a_held_player(self._holds, command.player_id)

        await self._resets.record(
            DeckReset(player_id=command.player_id, sport=command.sport, at=now)
        )
        await self._uow.commit()
