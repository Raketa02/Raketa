"""The two gates about accounts that fail closed, over the people a reader
would be shown.

Since the searches went (#579) the surface they serve is the player record,
opened about somebody the platform has already introduced — on a court shared, a
group shared or a group run (#575). It runs two gates: an account hold, and an
account state that may not be shown. **A block is not one of them any more**
(``docs/adr/0193`` §2): it keeps two people off one court, and the record is not
a court. The second copy of a safety gate is the defect the whole fail-closed
rule exists to prevent, so the two are ``AccountGates``, a collaborator of their
own, and never a private step inside whichever use case needed them first.

**Every read is a set read over the whole list**, never one query per subject.

**The answer names no gate**, and there is nowhere in it to put one
(``docs/adr/0130``). One withheld subject, two possible causes, and no way to
tell which.
"""

from __future__ import annotations

from typing import Collection, final
from uuid import UUID

from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.ports import AccountHoldQuery, AccountStatusQuery


@final
class AccountGates:
    """The two gates about **accounts** — a hold, and an account that may not
    be shown."""

    def __init__(
        self,
        *,
        holds: AccountHoldQuery,
        account_status: AccountStatusQuery,
    ) -> None:
        self._holds = holds
        self._account_status = account_status

    async def withheld(self, *, subject_ids: Collection[UUID]) -> frozenset[UUID]:
        """Which of these subjects the two withhold — a subset of
        ``subject_ids``. Nobody to ask about costs no outward read at all.

        **Nothing here is about the reader** since the block left
        (``docs/adr/0193`` §2): both gates are facts about a subject's account.
        The reader's own hold is the surface's entry rule
        (``player_record``'s ``LiveRecordGates``).
        """

        subjects = tuple(subject_ids)
        if not subjects:
            return frozenset()
        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among(subjects)
        )
        unshowable = await read_demand(
            AccountStatusQuery,
            lambda: self._account_status.may_not_be_shown(subjects),
        )
        return frozenset(held | unshowable) & frozenset(subjects)
