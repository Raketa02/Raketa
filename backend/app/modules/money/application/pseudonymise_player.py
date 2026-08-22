"""Erasure, as far as an accounting record is allowed to go.

ADR-0055: *"A movement is never deleted, and account deletion pseudonymises the
player party. Accounting records carry a legal-obligation basis that survives an
erasure request."* So this appends one event and removes nothing — and what it
appends is what every later reader of the ledger sees in the player's place.

**The pseudonym is minted, not derived.** A ``uuid5`` of the player id would be
a pseudonym anybody holding the player id could recompute, which is a mapping
table written in a formula. It is generated here, in the use case, where the
composition root's randomness lives — the domain never mints anything.

**Nothing about the movements changes.** The amounts, the causes, the references
and the seats are exactly what they were, and the balance folds to the same
number. That is the whole point: *the ledger refuses to forget*, and a
reconciliation run the day after an account closes still has a position to
assert. What identifies a person lives in Users and is erased there.

**One residual, stated rather than left to be found.** The stream id is derived
from the player id (ADR-0055 fixes that), so a ledger stays *findable* by
someone holding it, and the events written before this one still carry it in
their payload. Rewriting them is the one thing an append-only store cannot do,
and the same ADR forbids it in the sentence that asks for the pseudonym. What is
bought is that no reader of a ledger — the reconciliation, a support view, any
fold — names the player again.
"""

from __future__ import annotations

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant

from app.modules.money.application.commands import PseudonymisePlayerCommand
from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.ports import LedgerRepository
from app.shared.ids import new_uuid


class PseudonymisePlayer:
    """Replace the player behind a ledger; keep every movement on it."""

    def __init__(
        self,
        ledgers: LedgerRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._ledgers = ledgers
        self._uow = uow
        self._clock = clock

    async def execute(self, command: PseudonymisePlayerCommand) -> Ledger:
        ledger = await self._ledgers.load(command.player_id)
        ledger.pseudonymise(pseudonym=new_uuid(), at=instant(self._clock.now()))
        await self._ledgers.save(ledger)
        await self._uow.commit()
        return ledger
