"""The one place a movement is born.

ADR-0055: *"A movement is born in one place, fed by two mouths."* Match-caused
movements arrive over the **outbox**, externally-caused ones (a provider
reporting a landing, a club marking a counter share) arrive inbound, and **both
pass through here**. Two entry points would be two places the party rules, the
duplicate check and the transaction boundary are decided, and they would agree
right up until one of them was changed.

**Nothing is written inside a match transaction.** A card charge can fail after
the match record is already correct, and pretending those are one consistency
domain is how a match ends up rolled back because a bank was slow. What this
does share a transaction with is *other movements*: every draft in one command
lands together or none does, which is what an online share on a private court
needs — a `player → Raketa` with no `Raketa → club` beside it is a float that
reads wrong until the second half arrives.

**A compensation is a draft like any other**, so a share and its reversal can be
one write. That is what ``pay_for_a_seat.py`` uses it for: money that arrived for
a seat that had already gone is recorded as ``shareOnline`` and compensated by a
``REV-`` movement with cause ``claimLapsed``, and there is no instant between the
two at which the ledger says Raketa kept 30 zł.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, exhaustive, instant

from app.modules.money.application.commands import (
    Compensation,
    MovementDraft,
    NewMovement,
    RecordMovementsCommand,
)
from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.movement import Movement
from app.modules.money.domain.ports import LedgerRepository
from app.shared.ids import new_uuid


class RecordMovements:
    """Append one or more movements to one player's ledger, in one transaction."""

    def __init__(
        self,
        ledgers: LedgerRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._ledgers = ledgers
        self._uow = uow
        self._clock = clock

    async def execute(self, command: RecordMovementsCommand) -> Ledger:
        ledger = await self._ledgers.load(command.player_id)
        # One clock read for the whole command: two reads inside one write can
        # disagree, and a pass-through share whose two halves are a millisecond
        # apart is two events where there was one.
        at = instant(self._clock.now())

        for draft in command.drafts:
            self._append(ledger, draft, at)

        await self._ledgers.save(ledger)
        await self._uow.commit()
        return ledger

    def _append(self, ledger: Ledger, draft: MovementDraft, at: Instant) -> None:
        match draft:
            case NewMovement():
                ledger.record(
                    Movement(
                        id=new_uuid(),
                        payer=draft.payer,
                        payee=draft.payee,
                        amount=draft.amount,
                        seat=draft.seat,
                        reservation=draft.reservation,
                        reference=draft.reference,
                        cause=draft.cause,
                        occurred_at=at,
                    )
                )
            case Compensation():
                ledger.compensate(
                    original=draft.original,
                    movement_id=new_uuid(),
                    reference=draft.reference,
                    cause=draft.cause,
                    at=at,
                )
            case _:
                exhaustive(draft)
