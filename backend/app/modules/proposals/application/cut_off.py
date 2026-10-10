"""**The cut-off: a game plays full or not at all, and its shares are taken**
(#544, #637; the mechanics §12.2, §12.3, §16.12, §19, Q113; the screens C3).

At each booked game's cut-off — the club's own free-cancellation deadline — one
of two things happens to it:

- **A seat that opened before it and is still open calls the game off**: every
  share still held is **let go** — nothing was taken, so nobody pays anything,
  the club included (a share taken already, the fallback of #639, is refunded
  in full) — the court is the club's to sell again, the Game and its room end,
  the club's desk is emailed *A game was called off at the cut-off*, and each
  player *Game called off · nothing was taken*.
- **A full game has every share held for it taken** (#637): captured at the
  provider from the outbox, with the real fee it kept. A game whose seat opened
  after the cut-off is full at it, and goes ahead short: its leaver's share is
  taken with everybody's.

**Correctness depends on it**, as the On request timeout's does: every read says
*called off*, and *paid*, from the cut-off on (``BookedGame.called_off_reason``,
``money_of``), but only this moves the money and frees the court. **One
transaction per game, the game locked first**, over a clock-derived list in one
order on every process, so two processes reaching one game meet at the lock or
the stream version, and the second is counted and stepped over. A run late past
a game's hour still does it: the candidates are every game whose cut-off has
come — the call-offs first, so a game short at its cut-off is never taken.
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
    HeldShares,
    PlayerBookings,
    ProposalRepository,
    RefundReason,
    SeatRefunds,
    UndecidedCharges,
)


@final
@dataclass(frozen=True, slots=True)
class CutOffRun:
    """What one cut-off run recorded, and how many another process reached
    first."""

    #: The games called off, short at their cut-off.
    games: int
    conflicts: int
    #: The games whose held shares were taken (#637).
    taken: int = 0


@final
class TheCutOff:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        bookings: PlayerBookings,
        games: BookedGameChanges,
        refunds: SeatRefunds,
        held: HeldShares,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._bookings = bookings
        self._games = games
        self._refunds = refunds
        self._held = held
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self) -> CutOffRun:
        now = instant(self._clock.now())
        called_off = taken = conflicts = 0
        for booking_id in await self._games.short_at_the_cut_off(now=now):
            try:
                if await self._call_off(booking_id, now=now):
                    await self._uow.commit()
                    called_off += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        for booking_id in await self._held.due(at=now):
            try:
                if await self._take(booking_id, now=now):
                    await self._uow.commit()
                    taken += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return CutOffRun(games=called_off, conflicts=conflicts, taken=taken)

    async def _call_off(self, booking_id: UUID, *, now: Instant) -> bool:
        # The booking's id is its proposal's, whose row every act on the game
        # locks first.
        await self._proposals.load_for_update(booking_id)
        still_in = await self._games.call_off_at_the_cut_off(booking_id, at=now)
        if still_in is None:
            return False
        # Every hold let go — and a share taken already refunded in full.
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

    async def _take(self, booking_id: UUID, *, now: Instant) -> bool:
        await self._proposals.load_for_update(booking_id)
        game = await self._bookings.find(booking_id)
        # A game short at its cut-off is the call-off's, whichever process
        # records it; one the club cancelled let its holds go.
        if game is None or game.called_off_reason(now) is not None:
            return False
        return await self._held.take(booking_id, at=now) > 0
