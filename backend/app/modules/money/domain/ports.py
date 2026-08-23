"""The Money context's ports.

Two ports. The first has two halves that are deliberately different shapes.

``load``/``save`` is the **aggregate repository** kind (ADR-0018): it owns the
aggregate-type name, the replay and the optimistic-concurrency bookkeeping, so a
use case reads as domain steps and can be tested against a fake event store
rather than a database.

``all_ledgers`` is the **scan** ADR-0055 names when it refuses to make the
reservation the stream: *"the court view is a query, not a stream … It is a
scan; ADR-0018's projection escape hatch applies if and when it stops being tens
of rows."* The reconciliation is its only caller today, and it is why the port
exists rather than the job reaching for the event store itself.

**The reconciliation is handed this port and no unit of work**, which is how
*it never repairs* is made structural rather than remembered — see
``application/reconcile_ledgers.py``.

``Seats`` is the other kind entirely: not a repository over Money's own storage
but **one question Money asks another context**, in Money's words. ADR-0055
fences the dependency one way — *Money reads Matches; Matches never reads Money*
— so the seat a share is for can be asked about here and the answer can never
travel back into the situation ladder. Stating it as a port rather than reaching
for ``MatchRepository`` is what ``now/domain/ports.py`` gives its reason for: a
use case that took the other context's repository would take its vocabulary with
it, and would have to change every time that context reshaped a read it never
asked for.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

from app.kernel import Instant

from app.modules.money.domain.funding import SeatFunding
from app.modules.money.domain.ledger import Ledger


@runtime_checkable
class LedgerRepository(Protocol):
    """Loads and saves Ledger aggregates, and scans them."""

    async def load(self, player_id: UUID) -> Ledger:
        """This player's ledger, replayed — empty when she has no stream yet.

        Never ``None`` and never an error. A player who has never moved any
        money has no stream, which is the ordinary state of a new account, and a
        caller that had to tell *absent* from *empty* would be writing the same
        branch in every use case.
        """
        ...

    async def save(self, ledger: Ledger) -> None:
        """Append the ledger's pending events and publish them.

        A no-op when nothing is pending, and it does **not** commit: the
        transaction boundary stays the use case's, so a seat payment that writes
        a match, a reservation and a movement can join it
        (``Raketa02/Raketa#70``).
        """
        ...

    async def all_ledgers(self) -> list[Ledger]:
        """Every ledger there is, oldest stream first.

        A scan, and named as one. The reconciliation reads the whole set because
        two of its three invariants are per player and the third is per seat —
        there is no key that narrows it.
        """
        ...


@runtime_checkable
class Seats(Protocol):
    """The seat a share is for, from the context that owns seats.

    **It writes, and the write is the point.** Money hearing that a payment
    landed is the moment the seat becomes hers, so this is not a read followed
    by a separate instruction: *give her the seat this money is for* and *tell
    me what the money is for* are one question, and splitting them would put an
    instant between a paid share and a taken seat.

    **It does not commit.** ADR-0035 fixes that *"a seat payment that earns a
    court, and the court it earns, are one event or they are a bug"*, so the
    transaction carrying the seat, the reservation and both outbox rows is the
    use case's to close (``application/pay_for_a_seat.py``).
    """

    async def pay_for(
        self, *, match_id: UUID, player_id: UUID, at: Instant
    ) -> SeatFunding:
        """Put this player on the seat she is paying for, if it is still hers.

        Answers ``SeatIsHers`` when it is — including when it already was, which
        is the state a process that died between the two transactions leaves
        behind and the state a replayed report finds. Answers ``SeatIsGone``
        when her five minutes ran out while the money was in flight.

        Refuses rather than answering when the money cannot be attributed to a
        seat at all, and when the match has ended — a refund on a match that is
        over has a cause of its own, and this port names none of them.
        """
        ...
