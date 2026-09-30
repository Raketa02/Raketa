"""The book-by sweep — **it buys the record, not correctness**.

A proposal past its book-by reads as expired at every instant, swept or not:
``Proposal.standing_at`` compares the book-by with the caller's clock, so a yes
on it is already refused, it is already off every live list and no yes on it
counts against a cap. Nothing here changes any of that (the mechanics §5.4: *at
book-by an unfilled card simply disappears … and nobody is told*).

What it buys is a ``ProposalExpired`` on the stream, which is what a poster's
*your post didn't fill* will be told from (#546), and a projection whose
``ended`` column lets the live reads stay narrow as the table grows.

**One transaction per proposal**, on the challenge lapse loop's argument
(``challenges/application/lapse_expired_seats.py``): every process walks the
same clock-derived list in the same order, so a version conflict is counted and
stepped over rather than ending the run on the first collision, and nothing
holds a cursor.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.proposals.domain.ports import ProposalDirectory, ProposalRepository


@final
@dataclass(frozen=True, slots=True)
class Expired:
    """What one sweep recorded, and how many proposals another process reached
    first — *the sweep does nothing* and *the sweep loses every race* have one
    symptom, and only one of them is somebody's problem."""

    proposals: int
    conflicts: int

    def __post_init__(self) -> None:
        invariant(self.proposals >= 0, f"{self.proposals} expired")
        invariant(self.conflicts >= 0, f"{self.conflicts} conflicts")


@final
class ExpireProposals:
    def __init__(
        self,
        *,
        clock: Clock,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        unit_of_work: UnitOfWork,
    ) -> None:
        self._clock = clock
        self._proposals = proposals
        self._directory = directory
        self._uow = unit_of_work

    async def execute(self) -> Expired:
        """Record every passed book-by. The clock is read **once**, so which
        proposals this sweep calls expired is one instant's answer."""

        now = instant(self._clock.now())
        expired = conflicts = 0
        for proposal_id in await self._directory.past_book_by(now=now):
            recorded = await self._expire(proposal_id, now=now)
            if recorded is None:
                conflicts += 1
            elif recorded:
                expired += 1
        return Expired(proposals=expired, conflicts=conflicts)

    async def _expire(self, proposal_id: UUID, *, now: Instant) -> bool | None:
        """Whether this one was recorded, or ``None`` if somebody got there
        first."""

        proposal = await self._proposals.load(proposal_id)
        if proposal is None or not proposal.expire(now=now):
            return False
        try:
            await self._proposals.save(proposal)
            await self._uow.commit()
        except EventStreamVersionConflict:
            await self._uow.rollback()
            return None
        return True
