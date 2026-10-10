"""**Time to pay** — how it ends when the game does not book on it (#625, #626;
the mechanics §12.2, Q109–Q112).

A share refused as a full game fills — or as its On request club says yes —
leaves its player In, the seat theirs alone for thirty minutes, never past the
book-by, and **every other hold kept on its card**, so the payment in time books
the game at once (``fill.py``). When it does not book on it, two things are
owed here:

- **the time runs out** (``run_out``) — the payers' seats reopen, offered to
  others and theirs to take back while free; at the club's yes the booking is
  called off and its desk emailed (*A game didn't go ahead*), the court the
  club's again. It is the job's (``RunOutTheTimeToPay``), and **a payer's own
  act come too late runs it first** — a yes, a confirmation — so the deadline
  reads the same whether or not the job has reached it;
- **what was kept is let go** (``let_go_of_what_was_kept``) — a player who
  leaves a game that waits for a payment takes their hold with them, and once
  no payment is awaited and the game did not book, every hold kept for the
  wait is released: all but the payers' own, a confirmed one waiting for the
  fill as any confirmed payment does, a refused one for its player.

**Nothing here commits but the job**, which is one transaction per game, its
game locked first, a conflict counted and stepped over.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.proposals.domain.ports import (
    ClubRequests,
    ProposalDirectory,
    ProposalRepository,
    UndecidedCharges,
)
from app.modules.proposals.domain.proposal import Ending, Paying, Proposal


async def let_go_of_what_was_kept(
    proposal: Proposal,
    was_paying: Mapping[UUID, Paying],
    *,
    undecided: UndecidedCharges,
    at: Instant,
    leaver: UUID | None = None,
) -> None:
    """After an act on a game that waited for a payment — ``was_paying``, as it
    stood before: the ``leaver``'s hold is let go with their seat, and once no
    payment is awaited and the game did not book, every hold kept for the wait
    is let go but the payers' own — a payment they confirmed, which waits for
    the fill, and one refused that they may still confirm. **No commit.**"""

    if not was_paying:
        return
    if leaver is not None:
        await undecided.release(
            proposal.proposal_id, keeping=(), of_player=leaver, at=at
        )
    if proposal.paying or proposal.ending is Ending.FILLED:
        return
    keeping = frozenset(
        {
            # Paid in time: held for the fill, as a confirmed payment is.
            *proposal.paid_in_time.values(),
            # Out of time: theirs to confirm while the seat is free.
            *(
                paying.seat_charge_id
                for player, paying in was_paying.items()
                if player in proposal.reopened
                and proposal.reopened[player].payment_to_confirm is not None
            ),
        }
    )
    await undecided.release(proposal.proposal_id, keeping=keeping, at=at)


async def run_out(
    proposal: Proposal,
    *,
    proposals: ProposalRepository,
    requests: ClubRequests,
    undecided: UndecidedCharges,
    now: Instant,
) -> tuple[UUID, ...]:
    """Every payer whose time to pay is up at ``now`` — their seats reopen, the
    holds kept for them are let go, and at the club's yes the booking is called
    off, its desk told. Answers whose time ran out. **No commit.**"""

    was_paying = dict(proposal.paying)
    on_the_clubs_yes = proposal.on_the_clubs_yes
    lapsed = proposal.run_out_of_time(at=now)
    if not lapsed:
        return ()
    await proposals.save(proposal)
    if on_the_clubs_yes:
        await requests.payment_not_in_time(
            proposal.proposal_id,
            player_ids=lapsed,
            # Past the book-by it can no longer fill: called off for everybody.
            for_good=now >= proposal.book_by,
            at=now,
        )
    await let_go_of_what_was_kept(proposal, was_paying, undecided=undecided, at=now)
    return lapsed


async def run_out_if_due(
    proposal: Proposal,
    player_id: UUID,
    *,
    proposals: ProposalRepository,
    requests: ClubRequests,
    undecided: UndecidedCharges,
    now: Instant,
) -> None:
    """**A payer's own act come too late** runs their time out first: past it,
    the seat is no longer theirs alone — whether or not the job has recorded
    that — and the act goes on as one on a reopened seat. **No commit.**"""

    paying = proposal.paying.get(player_id)
    if paying is not None and now >= paying.until:
        await run_out(
            proposal,
            proposals=proposals,
            requests=requests,
            undecided=undecided,
            now=now,
        )


@final
@dataclass(frozen=True, slots=True)
class RanOut:
    """What one run recorded, and how many games another process reached
    first."""

    games: int
    conflicts: int

    def __post_init__(self) -> None:
        invariant(self.games >= 0, f"{self.games} games")
        invariant(self.conflicts >= 0, f"{self.conflicts} conflicts")


@final
class RunOutTheTimeToPay:
    """**The deadline of every time to pay** (#625, #626) — the job's.
    **Correctness depends on it**: until it runs, a seat whose time ran out is
    still its payer's alone, and the holds kept for it stay on the others'
    cards. **One transaction per game**, over a clock-derived list in one order
    on every process, so a version conflict is counted and stepped over."""

    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        requests: ClubRequests,
        undecided: UndecidedCharges,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._directory = directory
        self._requests = requests
        self._undecided = undecided
        self._uow = uow
        self._clock = clock

    async def execute(self) -> RanOut:
        now = instant(self._clock.now())
        games = conflicts = 0
        for proposal_id in await self._directory.paying_past(now=now):
            try:
                if await self._run_out(proposal_id, now=now):
                    await self._uow.commit()
                    games += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return RanOut(games=games, conflicts=conflicts)

    async def _run_out(self, proposal_id: UUID, *, now: Instant) -> bool:
        proposal = await self._proposals.load_for_update(proposal_id)
        if proposal is None:
            return False
        return bool(
            await run_out(
                proposal,
                proposals=self._proposals,
                requests=self._requests,
                undecided=self._undecided,
                now=now,
            )
        )
