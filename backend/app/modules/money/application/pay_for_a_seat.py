"""A seat payment landing: the seat, the court it earns, and the money.

The join between Matches, Courts and Money, and ``Raketa02/Raketa#70`` is the
ticket. It is the place a partial write would leave a player holding a paid seat
in a match with no court and no record of why.

**Two transactions, in this order, and the order is the whole design.**

1. **The seat, the reservation (or the inventory loss) and both outbox rows.**
   ADR-0035: *"a seat payment that earns a court, and the court it earns, are one
   event or they are a bug."* The ``Seats`` port writes and does not commit; this
   use case closes the transaction, so a failure anywhere inside it leaves none
   of the four rows behind.
2. **The movement, or the movement and its reversal.** ADR-0055 is blunt that
   this is *not* the same transaction: *"no movement is ever written inside a
   match transaction — a card charge can fail after the match record is already
   correct, and pretending those are one consistency domain is how a match ends
   up rolled back because a bank was slow."*

**Matches first, because the movement names what that write produced.** A
``Movement`` carries the reservation behind it *"when there is one"*, and the
reservation this share earns does not exist until the ladder has claimed it —
so a money-first order could never name it, on the one payment that most
obviously funded a court. It also means the seat write's refusals decide which
chain is recorded, rather than being discovered after the money is already down.

**The seam between the two is safe in one direction and is stated rather than
hidden.** A process that dies between them leaves a paid seat with no movement:
the player has what she paid for and the ledger is short a row. A replayed
report heals it — ``SeatIsHers`` is answered for a seat that is *already* paid,
so the second run writes no seat and records the share it owes. The other order
would leave money recorded against a seat she never got, which is the failure
that costs somebody a Saturday game.

**Two things this does not do**, both named rather than left to be found.

* It does not **settle an open match's held shares to the club at commit**.
  ADR-0056 puts that at commit rather than on arrival, and it is a movement per
  paid seat across as many ledgers, on an event nothing subscribes to yet. Filed
  as ``Raketa02/Raketa#103`` rather than half-built.
* It does not detect a **second** payment under a different reference for a seat
  she already holds paid. A reference arriving twice is refused at the door —
  the only one of ADR-0057's three ways money gets recorded wrongly that is
  detectable there — but two references for one seat are two payments as far as
  the ledger can tell, and it records both. That is the same class of thing the
  reconciliation exists to find, and inventing a *one share per seat* rule here
  would be wrong on the paths where a seat is legitimately funded twice (a
  leaver settling, an owner reimbursed).
"""

from __future__ import annotations

from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, exhaustive, instant

from app.modules.money.application.commands import (
    AcrossTheCounter,
    Compensation,
    HeldByRaketa,
    NewMovement,
    Online,
    PaidAtTheCounter,
    PassedToTheClub,
    PayForASeatCommand,
    PaymentChannel,
    RecordMovementsCommand,
    RecordShareCommand,
    ShareArrival,
)
from app.modules.money.application.record_movements import RecordMovements
from app.modules.money.application.record_share import RecordShare
from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.errors import CounterShareNotOwed
from app.modules.money.domain.funding import Custody, SeatIsGone, SeatIsHers
from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.parties import PlayerParty, RaketaParty
from app.modules.money.domain.ports import Seats
from app.modules.money.domain.reference import Reference, ReferenceKind


class PayForASeat:
    """The money landed: give her the seat, and write down what happened."""

    def __init__(
        self,
        seats: Seats,
        shares: RecordShare,
        movements: RecordMovements,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._seats = seats
        self._shares = shares
        self._movements = movements
        self._uow = uow
        self._clock = clock

    async def execute(self, command: PayForASeatCommand) -> Ledger:
        # One read for the seat write. The movement takes its own, from
        # `RecordMovements`, and that is right rather than sloppy: these are two
        # transactions at two instants, and dating the second one from the first
        # would say the money was recorded before it was.
        at = instant(self._clock.now())

        funding = await self._seats.pay_for(
            match_id=command.match_id, player_id=command.player_id, at=at
        )
        # The transaction ADR-0035 names: the seat, the reservation **or** the
        # inventory loss, and the outbox rows for both. `pay_for` writes nothing
        # at all on the two paths that have nothing to write, and a commit of
        # nothing costs nothing.
        await self._uow.commit()

        match funding:
            case SeatIsHers():
                return await self._shares.execute(
                    RecordShareCommand(
                        player_id=command.player_id,
                        seat=funding.seat,
                        amount=command.amount,
                        reference=command.reference,
                        arrival=_arrival(
                            command.channel, funding.club_id, funding.custody
                        ),
                        reservation=funding.reservation,
                    )
                )
            case SeatIsGone():
                return await self._give_it_back(command, funding)
            case _:  # pragma: no cover - `exhaustive` never returns
                exhaustive(funding)

    async def _give_it_back(
        self, command: PayForASeatCommand, funding: SeatIsGone
    ) -> Ledger:
        """The share and its reversal, in one write.

        There is no instant at which the stored ledger says Raketa kept 38 zł:
        both movements land in one append, so a support agent reading the stream
        never sees a payment standing alone that was refunded a millisecond
        later (ADR-0057).

        The reversal's reference is **derived** from the payment's — same token,
        ``REV-`` prefix — because it corrects exactly that movement and nothing
        else. That cannot collide with a real payment: a reference is a kind and
        a token, and no payment is ever filed under ``REV-``.
        """

        if isinstance(command.channel, AcrossTheCounter):
            # Cash the club is holding. We cannot give back money we never took,
            # and reversing it would debit the club (ADR-0045).
            raise CounterShareNotOwed()

        return await self._movements.execute(
            RecordMovementsCommand(
                player_id=command.player_id,
                drafts=(
                    NewMovement(
                        payer=PlayerParty(command.player_id),
                        payee=RaketaParty(),
                        amount=command.amount,
                        cause=MovementCause.SHARE_ONLINE,
                        reference=command.reference,
                        seat=funding.seat,
                    ),
                    Compensation(
                        original=command.reference,
                        reference=Reference(
                            ReferenceKind.REVERSAL, command.reference.token
                        ),
                        cause=MovementCause.CLAIM_LAPSED,
                    ),
                ),
            )
        )


def _arrival(channel: PaymentChannel, club_id: UUID, custody: Custody) -> ShareArrival:
    """The channel and the custody, put together — the one place they meet.

    A caller states the channel because it is the only one that knows it; the
    match states the custody because it is the only thing that may. Neither
    alone answers *what movements does this write*.
    """

    match channel:
        case AcrossTheCounter():
            # Neither custody applies: Raketa is not a party to it at all.
            return PaidAtTheCounter(club_id=club_id)
        case Online():
            match custody:
                case Custody.HELD:
                    return HeldByRaketa()
                case Custody.PASSED_THROUGH:
                    return PassedToTheClub(
                        club_id=club_id, settlement=channel.settlement
                    )
                case _:  # pragma: no cover - `exhaustive` never returns
                    exhaustive(custody)
        case _:  # pragma: no cover - `exhaustive` never returns
            exhaustive(channel)
