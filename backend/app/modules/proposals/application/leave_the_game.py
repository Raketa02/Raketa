"""**Leave the game** (#544; the mechanics §12.3, §13; the screens A4.1).

Leaving is free until the club's cut-off, and what it costs is said before the
player confirms (the details' ``leave_terms``). One act, three outcomes:

- **before the cut-off** — nothing is taken: the leaver's hold is let go, nobody
  is refunded and no fee arises (#637), and their seat is offered to others; it
  is on their record only if the game is then called off because of it;
- **after the cut-off** — the seat stays paid and is offered to others until
  the start; the leaver is refunded, less exactly the fee kept on their
  payment, when somebody takes it (#545, #641) — and is emailed that figure as
  they leave, or none while the fee is not yet known — and it is on their
  record if nobody does;
- **while a payment is awaited** (#625) — nobody has paid, so leaving
  withdraws the yes, exactly as *Withdraw* does: the leaver's hold is let go,
  and the payer's time runs on — and so it does on a full game gone back to
  filling (Q106), whose details offer *Withdraw* instead: a screen opened while
  the payment was still awaited may press it.

**A friends game is left too** (#752; the friends mechanics §11), its own
row locked since no proposal stands for it. **Before the cut-off** a friend
leaves free — their hold let go, their seat empty, the sender told — and the
sender's own leave is *Leave · the others play on*: with *Split* his share and
every cover are let go and the game turns ordinary, every empty seat a rescue
at once; with *Whole court* he still pays, nothing let go, his seat a rescue
whose taker pays him back. **After the cut-off** anybody's leave is a late
leave, the sender's too: his own share comes back if somebody takes his seat.
*Call it off* is the sender's other choice, ``CallOffAFriendsGame``'s.

After the start there is no button, and the route refuses it
(``game_has_started``); a game already called off has nothing to leave
(``booking_is_called_off``).

**The game is locked first** — its proposal's row, the booking's own id — as
every act on a game is, so a leaving, a rescue and the cut-off arriving
together are one after another. One transaction: the seat, the Game's line-up,
and the refund's decision stand or fall together; the money follows the commit.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant
from app.modules.proposals.application.answers import withdraw_a_yes
from app.modules.proposals.application.home import the_game
from app.modules.proposals.application.commands import LeaveTheGameCommand
from app.modules.proposals.domain.errors import (
    BookingIsCalledOff,
    BookingNotFound,
    GameHasStarted,
)
from app.modules.proposals.domain.home import (
    BookingStage,
    Leaving,
    PayMode,
    leaving_of,
)
from app.modules.proposals.domain.ports import (
    BookedGameChanges,
    FriendsGameBookings,
    PlayerBookings,
    ProposalRepository,
    RefundReason,
    SeatRefunds,
    UndecidedCharges,
)
from app.modules.proposals.domain.proposal import Proposal


@final
class LeaveTheGame:
    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        bookings: PlayerBookings,
        friends_games: FriendsGameBookings,
        games: BookedGameChanges,
        refunds: SeatRefunds,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._friends_games = friends_games
        self._proposals = proposals
        self._bookings = bookings
        self._games = games
        self._refunds = refunds
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self, command: LeaveTheGameCommand) -> Leaving:
        now = instant(self._clock.now())
        player = command.player_id
        proposal = await self._proposals.load_for_update(command.booking_id)
        if proposal is None:
            return await self._a_friends_game(command.booking_id, player, now=now)
        game = await the_game(
            command.booking_id,
            bookings=self._bookings,
            proposals=self._proposals,
            now=now,
        )
        if proposal is None or game is None or not game.has_a_seat_for(player):
            raise BookingNotFound()
        if game.stage is BookingStage.WAITING_FOR_A_PAYMENT:
            return await self._withdraw(proposal, player, now=now)
        if game.called_off_reason(now) is not None:
            raise BookingIsCalledOff()
        if game.filling_again:
            return await self._withdraw(proposal, player, now=now)
        if now >= game.start:
            raise GameHasStarted()
        await self._games.leave(game.booking_id, player, at=now)
        left = leaving_of(game, now=now)
        if left is Leaving.BEFORE_THE_CUT_OFF:
            await self._refunds.refund(
                game.booking_id,
                [player],
                reason=RefundReason.LEFT_BEFORE_THE_CUT_OFF,
                at=now,
            )
        else:
            # Nothing comes back yet: they are told what will, if somebody
            # takes the seat (#641).
            await self._refunds.left_after_the_cut_off(game.booking_id, player, at=now)
        await self._uow.commit()
        return left

    async def _a_friends_game(
        self, booking_id: UUID, player: UUID, *, now: Instant
    ) -> Leaving:
        """A friends game left (#752): its own row locked first."""

        game = await self._friends_games.locked(booking_id)
        if game is None or not game.is_friends_game or not game.has_a_seat_for(player):
            raise BookingNotFound()
        if game.called_off_reason(now) is not None:
            raise BookingIsCalledOff()
        if now >= game.start:
            raise GameHasStarted()
        await self._games.leave(game.booking_id, player, at=now)
        left = leaving_of(game, now=now)
        if left is Leaving.AFTER_THE_CUT_OFF:
            await self._refunds.left_after_the_cut_off(game.booking_id, player, at=now)
        elif player != game.sender or game.pay_mode is PayMode.SPLIT_THE_COST:
            # A friend's own hold — or, the *Split* sender's leave, his share
            # and every cover: his card stops covering the game.
            await self._refunds.refund(
                game.booking_id,
                [player],
                reason=RefundReason.LEFT_BEFORE_THE_CUT_OFF,
                at=now,
            )
        # With *Whole court* the sender still pays the court: nothing is let go.
        await self._uow.commit()
        return left

    async def _withdraw(
        self, proposal: Proposal, player: UUID, *, now: Instant
    ) -> Leaving:
        """Nobody has paid: leaving withdraws the yes."""

        await withdraw_a_yes(
            proposal,
            player,
            proposals=self._proposals,
            undecided=self._undecided,
            at=now,
        )
        await self._uow.commit()
        return Leaving.WHILE_WAITING_FOR_A_PAYMENT
