"""``RecordGates`` over the three that are spelled once on this platform.

The collaborator this delegates to is ``matchmaking``'s
:class:`~app.modules.matchmaking.application.fail_closed_gates.AccountGates`: a
block in either direction, an account hold, and an account state that may not be
shown, evaluated over a reader and a set of subjects. A second spelling of a
safety gate is the defect the whole fail-closed rule exists to prevent, so what
lives here is a **translation and never a copy** — this file contains no gate.

**No preference and no partition** (#575). Every strand a record opens on is a
court or a group that already put the pair in front of each other, so the
mutual gender preference — which says who a player is willing to be *matched*
with — is not asked, no profile is loaded and no candidate index is bound.

**The reader's own hold is added here, and it is the one thing this adapter
decides.** The three answer about *subjects*; whether the person asking may be
shown anybody at all is the surface's own entry rule. A hold points both ways
(``docs/adr/0095``), so a hold that did not reach this route would end at the
one route that remembers who a player has been shown. It is asked **first**,
because it can refuse on its own.

Everything that goes wrong underneath — a provider that cannot be reached —
raises through, and the route answers 503. An outage is not a conclusion about
a person, and answering *this record is not available* to an infrastructure
failure would file it under the one refusal that is supposed to mean something.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.modules.matchmaking.application.fail_closed_gates import AccountGates
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.ports import AccountHoldQuery


@final
class LiveRecordGates:
    """The three about accounts and the reader's own hold, asked about one
    pair."""

    def __init__(self, *, accounts: AccountGates, holds: AccountHoldQuery) -> None:
        self._accounts = accounts
        self._holds = holds

    async def admits(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """Whether this reader may be shown this person."""

        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among([reader_id])
        )
        if reader_id in held:
            return False
        withheld = await self._accounts.withheld(
            reader_id=reader_id, subject_ids=(subject_id,)
        )
        return subject_id not in withheld


__all__ = ["LiveRecordGates"]
