"""The Money context's ports.

One port, and it has two halves that are deliberately different shapes.

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
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable
from uuid import UUID

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
