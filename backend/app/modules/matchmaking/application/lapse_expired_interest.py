"""The expiry loop — **a yes lapses; it never quietly decays.**

``docs/adr/0127``: ``INTEREST_TTL`` is flat and then absent. There is no final
week in which the lift tapers, and there is no ``expired`` state a row moves
into: past ``expires_at`` the row is simply gone, and the product never has to
say *no* because it said *until when* at the start.

**Correctness does not depend on this loop running.** Every read of the ledger is
bounded by ``now``, so a yes stops lifting, stops being outstanding and stops
being listed the moment it expires, whether or not anything has swept it. What the
loop buys is that the table stays the size of what is live, and — the part that
could not be bought later — the one figure a lapsed row could ever be asked for.

**Idempotent and safe beside itself with no lock** (``docs/adr/0092``): deleting a
row twice deletes it once, and two processes racing over the same batch leave what
one leaves. With N API processes it runs N times per interval, at unrelated
moments, which for a delete keyed on a date is exactly nothing.

**It counts the falsifier on the way out.** *Yeses that expired having never
lifted anybody* is ``INTEREST_TTL``'s one day-one falsifier — the one that runs
without ``matches`` (``the-five-numbers.md`` §8) — and if most yeses expire unfired
then 21 days is answering the wrong question and the pool is too quiet. A lapsed
row leaves no trace by design, so the count is taken in the same breath as the
delete or it is never taken at all.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.application.ports import UnitOfWork
from app.kernel import Clock
from app.modules.matchmaking.domain.interest import InterestLedger, Lapsed


@final
@dataclass(frozen=True, slots=True)
class LapseReport:
    """What one tick removed, for the log line that carries the falsifier."""

    removed: int
    never_lifted: int


@final
class LapseExpiredInterest:
    """One sweep of the interest ledger. **The whole of expiry.**"""

    def __init__(
        self,
        *,
        clock: Clock,
        interest: InterestLedger,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._interest = interest
        self._uow = unit_of_work

    async def execute(self) -> LapseReport:
        lapsed: Lapsed = await self._interest.lapse(now=self._clock.now())
        await self._uow.commit()
        return LapseReport(
            removed=lapsed.removed, never_lifted=lapsed.never_lifted
        )
