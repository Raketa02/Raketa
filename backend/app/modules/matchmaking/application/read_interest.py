"""*What have I got out, and who said yes back?* — **outgoing and mutuals only.**

``docs/adr/0109``: an **inbox is refused.** Incoming-and-not-mutual never crosses
in any shape, because a one-sided yes was banked under a promise of silence and
re-reading it onto a screen is treating that promise as consent to a screen
nobody agreed to. It is not a filter applied here — the ledger has no method that
could answer *who has said yes to me*, so there is nothing on this side to
forget.

**The cap is shown before it bites** (``docs/adr/0127`` §4). Every sport carries
its outstanding count and the cap in force, on every read, because a cap the
player cannot see is a refusal they cannot predict. The count is the **ledger's**
definition — sent, unexpired and not yet mutual — and never one recomputed here,
so the number on the screen and the number the write checks are one query.

**A block reaches this surface too.** ``docs/adr/0095`` says a block reaches
every surface that shows one player to another, and a mutual row names a person.
So the block set is read live and fails **closed**: a read that cannot evaluate
it refuses rather than listing somebody the product has agreed to stop showing.
The rows are not deleted by it — a block is forward-looking, and lifting one
brings back a yes that was still standing all along.

**Nothing here writes.** A lapsed yes is not swept on read; it is invisible
because every ledger query is bounded by ``now``, and the loop removes it in its
own time.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import final
from uuid import UUID

from app.engines.matchfit.ruleset import Ruleset
from app.kernel import Clock, Sport
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.commands import ReadInterestCommand
from app.modules.matchmaking.application.outward_reads import live_block_set
from app.modules.matchmaking.domain.interest import (
    Interest,
    InterestLedger,
    OutstandingCount,
)


@final
@dataclass(frozen=True, slots=True)
class InterestSummary:
    """Everything the *Let's play* screen may know.

    ``outgoing`` excludes the mutuals rather than containing them, so a client
    renders two lists without deriving either — the same reason ``sorts_available``
    is server-driven one route over. A yes that came back is a different thing to
    a player from a yes still in flight, and asking a client to compute which is
    which is asking it to hold this ledger's rules.
    """

    outgoing: tuple[Interest, ...]
    mutual: tuple[Interest, ...]
    outstanding: tuple[OutstandingCount, ...]


@final
class ReadInterest:
    """The one read of the interest ledger a player may make: their own."""

    def __init__(
        self,
        *,
        clock: Clock,
        ruleset: Ruleset,
        interest: InterestLedger,
        blocks: BlockQuery,
    ) -> None:
        self._clock = clock
        self._ruleset = ruleset
        self._interest = interest
        self._blocks = blocks

    async def execute(self, command: ReadInterestCommand) -> InterestSummary:
        now = self._clock.now()
        blocked = await live_block_set(self._blocks, command.player_id)
        sent = await self._interest.outgoing(player_id=command.player_id, now=now)
        answered = await self._interest.mutual(
            player_id=command.player_id, now=now
        )
        mutual_keys = {(row.to_player_id, row.sport) for row in answered}
        return InterestSummary(
            outgoing=tuple(
                row
                for row in sent
                if row.to_player_id not in blocked
                and (row.to_player_id, row.sport) not in mutual_keys
            ),
            mutual=tuple(
                row for row in answered if row.to_player_id not in blocked
            ),
            outstanding=await self._outstanding(command.player_id, now),
        )

    async def _outstanding(
        self, player_id: UUID, now: datetime
    ) -> tuple[OutstandingCount, ...]:
        """The count and the cap for **every** sport, whether or not it is used.

        Every sport rather than only the ones with rows, because the screen that
        needs this is the one the player is about to say yes on: a cap they can
        only see once they are close to it is a cap that arrives as a surprise,
        which is the failure §4 of ``docs/adr/0127`` exists to prevent. The cap
        itself is per sport and the same integer today; it is sent per sport
        anyway, so a ruleset that differentiates them is a data change rather
        than a contract one.

        One read of the ledger and then the roster, rather than a query per
        sport: the sports the player has nothing out in are exactly the ones the
        ledger has nothing to say about, and asking it four times to be told
        *nothing* three times is the query-per-row shape this module refuses
        everywhere else.
        """

        cap = self._ruleset.interest.outstanding_cap_per_sport
        counts = await self._interest.outstanding(player_id=player_id, now=now)
        return tuple(
            OutstandingCount(
                sport=sport, outstanding=counts.get(sport, 0), cap=cap
            )
            for sport in Sport
        )
