"""The three gates about accounts that fail closed, over one reader and the
people shown to them.

``docs/adr/0095`` reaches **every surface that shows one player to another**.
Since the searches went (#579) that is the player record, opened about somebody
the platform has already introduced — on a court shared, a group shared or a
group run (#575). It runs three gates: a block in either direction, an account
hold, and an account state that may not be shown. The second copy of a safety
gate is the defect the whole fail-closed rule exists to prevent, so the three
are ``AccountGates``, a collaborator of their own, and never a private step
inside whichever use case needed them first.

**Every read is a set read over the whole list**, never one query per subject.

**The answer names no gate**, and there is nowhere in it to put one
(``docs/adr/0130``). One withheld subject, three possible causes, and no way to
tell which — a payload naming the gate would deliver a block to the one person it
was meant to be invisible to.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.outward_reads import (
    live_block_set,
    read_demand,
)
from app.modules.matchmaking.domain.ports import AccountHoldQuery, AccountStatusQuery


@final
class AccountGates:
    """The three gates about **accounts** — a block in either direction, a
    hold, an account that may not be shown."""

    def __init__(
        self,
        *,
        blocks: BlockQuery,
        holds: AccountHoldQuery,
        account_status: AccountStatusQuery,
    ) -> None:
        self._blocks = blocks
        self._holds = holds
        self._account_status = account_status

    async def withheld(
        self, *, reader_id: UUID, subject_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these subjects the three withhold from this reader.

        The answer is a subset of ``subject_ids`` and is bounded by it
        deliberately: the block read answers with the reader's **whole**
        exclusion list, which is a fact about them and not about the question
        asked, and handing it back unbounded would make the return value two
        things at once. Nobody to ask about costs no outward read at all.
        """

        subjects = tuple(subject_ids)
        if not subjects:
            return frozenset()
        blocked = await live_block_set(self._blocks, reader_id)
        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among(subjects)
        )
        unshowable = await read_demand(
            AccountStatusQuery,
            lambda: self._account_status.may_not_be_shown(subjects),
        )
        return frozenset(blocked | held | unshowable) & frozenset(subjects)
