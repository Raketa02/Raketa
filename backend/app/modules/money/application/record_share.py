"""A share arriving, in the three shapes ADR-0056 says it can arrive in.

**This use case has no repository, no unit of work and no clock.** It turns one
share into the movements that share *is* and hands them to ``RecordMovements``,
which is the entry point ADR-0055 requires. That is not tidiness: a second
place that loads a ledger and appends to it is a second place the party rules,
the duplicate check and the transaction boundary are decided, and structurally
refusing to be one is cheaper than remembering not to.

**Custody follows what was sold, and the two regimes are why this exists.** The
same 30 zł buys a held seat on one path and a passed-through share on the other,
and the difference is invisible on the screen:

* **Open match** — nothing is booked yet, so the money is genuinely Raketa's to
  hold until the match commits. One movement, `player → Raketa`. This is the
  money ``cancelledIncomplete`` returns whole, and without it the open path has
  no refund to give.
* **Private split court** — the court is already bought, so the share is paid
  through on arrival. **Two** movements in one write, `player → Raketa` then
  `Raketa → club`, because ADR-0056 requires the pair: with only the second,
  ``held`` and the float are not derivable and a refund has no movement to
  compensate. Raketa's position on that seat is zero from the same instant.
* **Cash at a counter** — the one movement that is `player → club`, with Raketa
  as neither party (ADR-0059). It is on the ledger even though we never touched
  the money, because without it the seat reads unpaid for ever and the nightly
  assertion that a seat's chain closes never passes on any court with a cash
  payer.

**Which door the payer came through is not recorded here.** It lives on the
*match record*, because it decides who is refunded when the sold format goes
unmet — and that is an input to a rule the kernel evaluates from the record and
the clock alone (ADR-0044, ADR-0056). The ledger references a seat; it does not
define one.
"""

from __future__ import annotations

from app.kernel import exhaustive

from app.modules.money.application.commands import (
    HeldByRaketa,
    NewMovement,
    PaidAtTheCounter,
    PassedToTheClub,
    RecordMovementsCommand,
    RecordShareCommand,
)
from app.modules.money.application.record_movements import RecordMovements
from app.modules.money.domain.causes import MovementCause
from app.modules.money.domain.ledger import Ledger
from app.modules.money.domain.parties import ClubParty, PlayerParty, RaketaParty


class RecordShare:
    """One share, one write, one to three movements."""

    def __init__(self, movements: RecordMovements) -> None:
        self._movements = movements

    async def execute(self, command: RecordShareCommand) -> Ledger:
        return await self._movements.execute(
            RecordMovementsCommand(
                player_id=command.player_id,
                drafts=_drafts(command),
            )
        )


def _drafts(command: RecordShareCommand) -> tuple[NewMovement, ...]:
    player = PlayerParty(command.player_id)

    match command.arrival:
        case HeldByRaketa():
            return (
                NewMovement(
                    payer=player,
                    payee=RaketaParty(),
                    amount=command.amount,
                    cause=MovementCause.SHARE_ONLINE,
                    reference=command.reference,
                    seat=command.seat,
                    reservation=command.reservation,
                ),
            )
        case PassedToTheClub(club_id, settlement):
            return (
                NewMovement(
                    payer=player,
                    payee=RaketaParty(),
                    amount=command.amount,
                    cause=MovementCause.SHARE_ONLINE,
                    reference=command.reference,
                    seat=command.seat,
                    reservation=command.reservation,
                ),
                NewMovement(
                    payer=RaketaParty(),
                    payee=ClubParty(club_id),
                    amount=command.amount,
                    cause=MovementCause.SHARE_ONLINE,
                    reference=settlement,
                    seat=command.seat,
                    reservation=command.reservation,
                ),
            )
        case PaidAtTheCounter(club_id):
            return (
                NewMovement(
                    payer=player,
                    payee=ClubParty(club_id),
                    amount=command.amount,
                    cause=MovementCause.SHARE_AT_COUNTER,
                    reference=command.reference,
                    seat=command.seat,
                    reservation=command.reservation,
                ),
            )
        case _:
            exhaustive(command.arrival)
