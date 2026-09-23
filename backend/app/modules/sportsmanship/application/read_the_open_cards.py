"""Which cards are open for one player, and who is on each.

Three reasons a settled game is not on this list, and each of them is spelled
the same way — by not being there:

1. **It has not settled**, so the port never offered it. *Which of my games are
   over* is one question asked in one place, and this use case does not
   re-derive it.
2. **The day after has not come.** The window is this context's own rule and
   lives in ``window.py``.
3. **It has been answered.** Submitting closes the card, whatever was put on it,
   including the card where everybody was left blank.

**One spelling for all three, deliberately.** A payload that said *why* a game is
absent would be a payload naming, for the third case, that this player already
answered — which is a fact about them and harmless, and for the second a
countdown this route has not been asked for. Absence is the answer the client
needs and the only one it needs: it draws the card where the game is on this
list and does not where it is not.

**The clock is read once, here.** The port's *has it settled* and the window's
*may I be asked yet* are folded against the same instant, so a card cannot be
open on one clock and its game unsettled on another.

**Nothing is written and nothing is swept.** An expired card is a fold, not a
row somebody has to delete: *not rating produces no strand, no penalty and no
record of the omission*, so there is nothing here for a job to correct.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Clock
from app.modules.sportsmanship.domain.card import SettledCourt
from app.modules.sportsmanship.domain.ports import SettledCourts, SportsmanshipLedger
from app.modules.sportsmanship.domain.window import card_is_open


@final
class ReadTheOpenCards:
    """The cards waiting for this player's stars, soonest to expire first."""

    def __init__(
        self,
        *,
        clock: Clock,
        courts: SettledCourts,
        ledger: SportsmanshipLedger,
    ) -> None:
        self._clock = clock
        self._courts = courts
        self._ledger = ledger

    async def execute(self, player_id: UUID) -> tuple[SettledCourt, ...]:
        now = self._clock.now()
        open_now = sorted(
            (
                court
                for court in await self._courts.courts_of(player_id, now=now)
                if card_is_open(played_at=court.played_at, now=now)
            ),
            # **Soonest to expire first**, and totally ordered so two processes
            # answering the same player answer in the same order
            # (``docs/adr/0105``). The oldest evening is the one whose card goes
            # first, which is the one worth answering now; the id breaks a tie
            # between two games played at the same instant, which four people
            # playing two courts at a club is not a strange way to spend an
            # evening.
            key=lambda court: (court.played_at, court.game_id.hex),
        )
        if not open_now:
            # No question is asked about an empty list. This is the common case
            # on this route — most players have no card open most of the time.
            return ()

        answered = await self._ledger.answered_among(
            rater_id=player_id,
            game_ids=[court.game_id for court in open_now],
        )
        return tuple(court for court in open_now if court.game_id not in answered)
