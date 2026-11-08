"""``RecordGates`` over the gates that are spelled once on this platform.

The collaborators this delegates to are ``matchmaking``'s
:class:`~app.modules.matchmaking.application.fail_closed_gates.AccountGates` —
an account hold, and an account state that may not be shown, evaluated over a
set of subjects — and the Blocks context's ``BlockQuery``. A second spelling of
a safety gate is the defect the whole fail-closed rule exists to prevent, so
what lives here is a **translation and never a copy** — this file contains no
gate.

**A block either way round** (``docs/adr/0203`` §8, #773, superseding
``docs/adr/0193`` §2 for the record). Neither of a blocked pair opens the
other's record, anywhere, group-mates included: asked through
``BlockQuery.blocked_between``, which is symmetric in its arguments, so nothing
here can tell — or tell anybody — which of them made it. The refusal is the
record's one refusal, so the blocked person reads exactly what any closed
record reads.

**No preference** (#575). Every strand a record opens on already put the pair
in front of each other, so the mutual gender preference — which says who a
player is willing to be *matched* with — is not asked and no profile is loaded.

**The reader's own hold is added here, and it is the one thing this adapter
decides.** The two answer about *subjects*; whether the person asking may be
shown anybody at all is the surface's own entry rule. A hold points both ways
(``docs/adr/0095``), so a hold that did not reach this route would end at the
one route that remembers who a player has been shown. It is asked **first**,
because it can refuse on its own.

Everything that goes wrong underneath — a provider that cannot be reached, a
block state that cannot be read (``BlockStateUnavailable``) — raises through,
and the route answers 503. An outage is not a conclusion about a person, and
answering *this record is not available* to an infrastructure failure would
file it under the one refusal that is supposed to mean something.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.fail_closed_gates import AccountGates
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.ports import AccountHoldQuery


@final
class LiveRecordGates:
    """The reader's own hold, the two about accounts and a block either way,
    asked about one pair."""

    def __init__(
        self, *, accounts: AccountGates, holds: AccountHoldQuery, blocks: BlockQuery
    ) -> None:
        self._accounts = accounts
        self._holds = holds
        self._blocks = blocks

    async def admits(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """Whether this reader may be shown this person."""

        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among([reader_id])
        )
        if reader_id in held:
            return False
        withheld = await self._accounts.withheld(subject_ids=(subject_id,))
        if subject_id in withheld:
            return False
        return not await self._blocks.blocked_between(reader_id, subject_id)


__all__ = ["LiveRecordGates"]
