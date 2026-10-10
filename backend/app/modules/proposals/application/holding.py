"""**The holding: a game that filled far ahead has its checked shares held four
days before the cut-off** (#639; the mechanics §12.2, Q113; ADR-0189's
2026-10-10 amendment).

A card hold made without its player lasts days, not until the game, so the
fill **checks** a seat whose hold would not reach the cut-off — held for a
moment and let go — and its share is held again at its **Holding time**, four
days before the cut-off, to stay until it. This is that moment, per game:

- **held** — the share stays on the card until the cut-off takes it, or, a hold
  that still would not reach it, until its last safe moment (the fallback);
- **refused** — the card was declined, the bank wants its player present, or
  the terms must be accepted again: **the game stays booked**, and the player
  has their **time to fix the card** — thirty minutes, never past the cut-off,
  their seat theirs alone. Fixed in time (``ConfirmPayment``) the share is
  held; run out (the time-to-pay job), their seat opens to Fill in as a
  leaver's before the cut-off, and they owe nothing.

**Correctness depends on it**: until it runs, a checked share is held nowhere,
and the cut-off has nothing of that player's to take. **One transaction per
game, the game locked first**, over a clock-derived list in one order on every
process, so two processes reaching one game meet at the lock or the stream
version, and the second is counted and stepped over. **Only while the cut-off
is ahead**: a game the job reaches only after its cut-off — days of outage — is
an operator's question, not answered here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.proposals.application.time_to_pay import run_out_the_cards_to_fix
from app.modules.proposals.domain.home import BookingStage
from app.modules.proposals.domain.limits import TIME_TO_PAY
from app.modules.proposals.domain.ports import (
    BookedGameChanges,
    CardsToFix,
    CheckedShares,
    PlayerBookings,
    ProposalRepository,
)


@final
@dataclass(frozen=True, slots=True)
class HoldingRun:
    """What one holding run did, and how many games another process reached
    first."""

    #: The shares held again.
    held: int
    #: The shares refused, whose players have their time to fix the card.
    refused: int
    conflicts: int

    def __post_init__(self) -> None:
        invariant(
            min(self.held, self.refused, self.conflicts) >= 0, f"{self!r} counts less"
        )


@final
class TheHolding:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        bookings: PlayerBookings,
        games: BookedGameChanges,
        checked: CheckedShares,
        cards: CardsToFix,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._bookings = bookings
        self._games = games
        self._checked = checked
        self._cards = cards
        self._uow = uow
        self._clock = clock

    async def execute(self) -> HoldingRun:
        now = instant(self._clock.now())
        held = refused = conflicts = 0
        for booking_id in await self._checked.due(at=now):
            try:
                done = await self._hold(booking_id, now=now)
                if done is None:
                    await self._uow.rollback()
                    continue
                await self._uow.commit()
                held += done.held
                refused += done.refused
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return HoldingRun(held=held, refused=refused, conflicts=conflicts)

    async def _hold(self, booking_id: UUID, *, now: Instant) -> HoldingRun | None:
        """This game's shares due, held — and each player refused given their
        time to fix the card, or keeping the time they have. Answers how many
        of each, or ``None`` when nothing was recorded."""

        # The booking's id is its proposal's, whose row every act on the game
        # locks first.
        await self._proposals.load_for_update(booking_id)
        game = await self._bookings.find(booking_id)
        if (
            game is None
            or game.stage not in (BookingStage.BOOKED, BookingStage.SEAT_OPEN)
            or game.called_off_reason(now) is not None
            or now >= game.cut_off
        ):
            return None
        # A time to fix already up is run out first: what its player fixed
        # since came too late, and their seat is no longer theirs alone.
        ran_out = await run_out_the_cards_to_fix(
            booking_id,
            bookings=self._bookings,
            games=self._games,
            cards=self._cards,
            now=now,
        )
        if ran_out:
            game = invariant(
                await self._bookings.find(booking_id), f"{booking_id} is gone"
            )
        # Never past the cut-off: leaving is free until it, and so is fixing.
        fix_by = instant(min(now + TIME_TO_PAY, game.cut_off))
        # A player refused again — their terms fixed, their bank declining —
        # keeps the time they had (Q109).
        fixing_until = {
            player: refused.until for player, refused in game.cards_to_fix.items()
        }
        holding = await self._checked.hold(
            booking_id, fix_by=fix_by, fixing_until=fixing_until, at=now
        )
        for player, refusal in sorted(
            holding.refused.items(), key=lambda one: str(one[0])
        ):
            if game.has_a_seat_for(player):
                await self._games.card_to_fix(
                    booking_id,
                    player,
                    until=fixing_until.get(player, fix_by),
                    refused=refusal,
                    at=now,
                )
        for player in sorted(holding.held, key=str):
            # Held on the terms its player accepted meanwhile: fixed.
            if player in game.cards_to_fix:
                await self._games.card_fixed(booking_id, player, at=now)
        if not (holding.held or holding.refused or ran_out):
            return None
        return HoldingRun(
            held=len(holding.held), refused=len(holding.refused), conflicts=0
        )
