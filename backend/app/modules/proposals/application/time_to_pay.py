"""**Time to pay** — how it ends when the game does not book on it (#625, #626;
the mechanics §12.2, Q109–Q112).

A share refused as a full game fills leaves its player In, the seat theirs
alone for thirty minutes, never past the book-by, and **every other hold kept
on its card**, so the payment in time books the game at once (``fill.py``).
When it does not book on it, two things are owed here:

- **the time runs out** (``run_out``) — the payers' seats reopen, offered to
  others and theirs to take back while free. It is the job's
  (``RunOutTheTimeToPay``), and **a payer's own act come too late runs it
  first** — a yes, a confirmation — so the deadline reads the same whether or
  not the job has reached it;
- **what was kept is let go** (``let_go_of_what_was_kept``) — a player who
  leaves a game that waits for a payment takes their hold with them, and once
  no payment is awaited and the game did not book, every hold kept for the
  wait is released: all but the payers' own, a confirmed one waiting for the
  fill as any confirmed payment does, a refused one for its player.

**And on a booked game, a refused holding's time to fix the card** (#639):
run out, the player's seat opens to Fill in — on the record a leave before the
cut-off — and their refused holding is let go; they owe nothing
(``run_out_the_cards_to_fix``). **And a refused rescuer's kept seat** (#640):
run out, it is offered again — every read says so off the clock already — and
their refused payment stays theirs to confirm while the seat is free
(``run_out_the_keeps``).

**Nothing here commits but the job**, which is one transaction per game, its
game locked first, a conflict counted and stepped over.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.events import EventStreamVersionConflict
from app.application.ports import UnitOfWork
from app.kernel import Clock, Instant, instant, invariant
from app.modules.proposals.domain.ports import (
    BookedGameChanges,
    CardsToFix,
    PlayerBookings,
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
    undecided: UndecidedCharges,
    now: Instant,
) -> tuple[UUID, ...]:
    """Every payer whose time to pay is up at ``now`` — their seats reopen, and
    the holds kept for them are let go. Answers whose time ran out. **No
    commit.**"""

    was_paying = dict(proposal.paying)
    lapsed = proposal.run_out_of_time(at=now)
    if not lapsed:
        return ()
    await proposals.save(proposal)
    await let_go_of_what_was_kept(proposal, was_paying, undecided=undecided, at=now)
    return lapsed


async def run_out_if_due(
    proposal: Proposal,
    player_id: UUID,
    *,
    proposals: ProposalRepository,
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
            undecided=undecided,
            now=now,
        )


async def run_out_the_cards_to_fix(
    booking_id: UUID,
    *,
    bookings: PlayerBookings,
    games: BookedGameChanges,
    cards: CardsToFix,
    now: Instant,
) -> tuple[UUID, ...]:
    """**A booked game's time to fix the card run out** (#639): each player
    whose holding was refused and whose time is up at ``now`` lets their seat
    go — it opens to Fill in, as a leaver's before the cut-off — and their
    refused holding is let go: they owe nothing. Answers whose ran out. **No
    commit.**"""

    game = await bookings.find(booking_id)
    if game is None:
        return ()
    ran_out: list[UUID] = []
    for player, to_fix in sorted(
        game.cards_to_fix.items(), key=lambda one: str(one[0])
    ):
        if now >= to_fix.until and await games.card_not_fixed(
            booking_id, player, at=now
        ):
            await cards.let_go_unfixed(booking_id, player, at=now)
            ran_out.append(player)
    return tuple(ran_out)


async def run_out_the_keeps(
    booking_id: UUID,
    *,
    games: BookedGameChanges,
    bookings: PlayerBookings,
    now: Instant,
) -> tuple[UUID, ...]:
    """**A refused rescuer's time run out** (#640): each seat kept for a
    rescuer whose time is up at ``now`` is offered again — never kept for them
    again here. Answers whose ran out. **No commit.**"""

    game = await bookings.find(booking_id)
    if game is None:
        return ()
    ran_out: list[UUID] = []
    for player, kept in sorted(game.kept.items(), key=lambda one: str(one[0])):
        if now >= kept.until and await games.kept_seat_ran_out(
            booking_id, player, at=now
        ):
            ran_out.append(player)
    return tuple(ran_out)


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
    cards. A seat kept for a refused rescuer (#640) is read off the clock, so
    for it the job only records the run-out and tells the rescuer. **One
    transaction per game**, over a clock-derived list in one order on every
    process, so a version conflict is counted and stepped over."""

    def __init__(
        self,
        *,
        proposals: ProposalRepository,
        directory: ProposalDirectory,
        undecided: UndecidedCharges,
        bookings: PlayerBookings,
        games: BookedGameChanges,
        cards: CardsToFix,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._proposals = proposals
        self._directory = directory
        self._undecided = undecided
        self._bookings = bookings
        self._games = games
        self._cards = cards
        self._uow = uow
        self._clock = clock

    async def execute(self) -> RanOut:
        now = instant(self._clock.now())
        games, conflicts = await self._each(
            await self._directory.paying_past(now=now), self._run_out, now=now
        )
        # A booked game's time to fix the card, at its holding (#639).
        booked, booked_conflicts = await self._each(
            await self._games.cards_to_fix_past(now=now),
            self._run_out_the_cards,
            now=now,
        )
        # A seat kept for a refused rescuer (#640).
        kept, kept_conflicts = await self._each(
            await self._games.keeps_past(now=now), self._run_out_the_keeps, now=now
        )
        return RanOut(
            games=games + booked + kept,
            conflicts=conflicts + booked_conflicts + kept_conflicts,
        )

    async def _each(
        self,
        game_ids: Sequence[UUID],
        act: Callable[..., Awaitable[bool]],
        *,
        now: Instant,
    ) -> tuple[int, int]:
        """``act`` on each game in its own transaction: how many it recorded,
        and how many another process reached first."""

        recorded = conflicts = 0
        for game_id in game_ids:
            try:
                if await act(game_id, now=now):
                    await self._uow.commit()
                    recorded += 1
                else:
                    await self._uow.rollback()
            except EventStreamVersionConflict:
                await self._uow.rollback()
                conflicts += 1
        return recorded, conflicts

    async def _run_out_the_cards(self, booking_id: UUID, *, now: Instant) -> bool:
        # The booking's id is its proposal's, whose row every act on the game
        # locks first.
        await self._proposals.load_for_update(booking_id)
        return bool(
            await run_out_the_cards_to_fix(
                booking_id,
                bookings=self._bookings,
                games=self._games,
                cards=self._cards,
                now=now,
            )
        )

    async def _run_out_the_keeps(self, booking_id: UUID, *, now: Instant) -> bool:
        await self._proposals.load_for_update(booking_id)
        return bool(
            await run_out_the_keeps(
                booking_id, games=self._games, bookings=self._bookings, now=now
            )
        )

    async def _run_out(self, proposal_id: UUID, *, now: Instant) -> bool:
        proposal = await self._proposals.load_for_update(proposal_id)
        if proposal is None:
            return False
        return bool(
            await run_out(
                proposal,
                proposals=self._proposals,
                undecided=self._undecided,
                now=now,
            )
        )
