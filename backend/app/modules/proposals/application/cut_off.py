"""**The cut-off: a game plays full or not at all** (#544; the mechanics §12.3,
§16.12, §19; the screens C3).

At each booked game's cut-off — the club's own free-cancellation deadline —
a seat that opened before it and is still open calls the game off: **everybody
still in is refunded in full** (the club bears the card fees: it is its own
rule), the court is the club's to sell again, the Game and its room end, the
club's desk is emailed *A game was called off at the cut-off*, and each player
*Game called off · with the refund*. A game whose seat opened after the cut-off
is not touched: it goes ahead short.

**Correctness depends on it**, as the On request timeout's does: every read says
*called off* from the cut-off on (``BookedGame.called_off_reason``), but only this
gives the money back and frees the court. **One transaction per game, the game
locked first**, over a clock-derived list in one order on every process, so two
processes calling one game off meet at the lock or the stream version, and the
second is counted and stepped over. A run late past a game's hour still gives
the money back: the candidates are every game whose cut-off has come.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.proposals.domain.ports import (
    BookedGameChanges,
    ProposalRepository,
    RefundReason,
    SeatRefunds,
    UndecidedCharges,
)


@final
@dataclass(frozen=True, slots=True)
class CalledOff:
    """What one cut-off run recorded, and how many another process reached
    first."""

    games: int
    conflicts: int


@final
class CallOffShortGames:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        games: BookedGameChanges,
        refunds: SeatRefunds,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._games = games
        self._refunds = refunds
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self) -> CalledOff:
        now = instant(self._clock.now())
        recorded = conflicts = 0
        for booking_id in await self._games.short_at_the_cut_off(now=now):
            try:
                if await self._call_off(booking_id, now=now):
                    await self._uow.commit()
                    recorded += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return CalledOff(games=recorded, conflicts=conflicts)

    async def _call_off(self, booking_id: UUID, *, now: Instant) -> bool:
        # The booking's id is its proposal's, whose row every act on the game
        # locks first.
        await self._proposals.load_for_update(booking_id)
        still_in = await self._games.call_off_at_the_cut_off(booking_id, at=now)
        if still_in is None:
            return False
        await self._refunds.refund(
            booking_id,
            still_in,
            reason=RefundReason.CALLED_OFF_AT_THE_CUT_OFF,
            at=now,
        )
        # A rescue's payment somebody confirmed for a seat here and never took
        # (#545) is let go with the game: nobody pays it.
        await self._undecided.release(booking_id, keeping=(), at=now)
        return True
