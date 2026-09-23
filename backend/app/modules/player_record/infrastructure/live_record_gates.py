"""``RecordGates`` over the four that are spelled once on this platform.

The collaborator this delegates to is ``matchmaking``'s
:class:`~app.modules.matchmaking.application.fail_closed_gates.FailClosedGates`,
extracted for exactly this caller (#374): a block in either direction, an account
hold, an account state that may not be shown, and the mutual gender preference,
evaluated over a reader and a set of subjects in one sport's partition. A second
spelling of a safety gate is the defect the whole fail-closed rule exists to
prevent, so what lives here is a **translation and never a copy** — this file
contains no gate.

**The reader's own hold is added here, and it is the one thing this adapter
decides.** The four answer about *subjects*; whether the person asking may be
shown anybody at all is the surface's own entry rule, and it belongs to whichever
surface is being entered — the read-back states the same rule at its own door. A
hold points both ways (``docs/adr/0095``), so a hold that did not reach this
route would be a hold ending at the one route that remembers what a search
already showed. It is asked **first**, because it is the cheaper of the two reads
and the one that can refuse without binding an index.

**Two failures are answers rather than errors**, and both are the fail-closed
rule pointed at this read:

- a reader with **no profile committed** has no preference to weigh, so the
  mutual gate cannot be evaluated for anybody. In a search that is a refusal with
  a sentence on it, because the searcher is being told why their own search
  cannot run; here it is *not admitted*, because this route says one thing to
  everybody it turns away and a reader with no profile has been shown nobody in
  any case.
- a subject with **no row in the partition** is already *not admitted* by the
  collaborator itself, for the same reason.

Everything else that goes wrong underneath — a provider that cannot be reached, a
process with no candidate index — raises through, and the route answers 503. An
outage is not a conclusion about a person, and answering *this record is not
available* to an infrastructure failure would file it under the one refusal that
is supposed to mean something.
"""

from __future__ import annotations

from typing import final
from uuid import UUID

from app.kernel import Sport
from app.modules.matchmaking.application.fail_closed_gates import FailClosedGates
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.errors import PlayerProfileNotCommitted
from app.modules.matchmaking.domain.ports import AccountHoldQuery


@final
class LiveRecordGates:
    """The four gates and the reader's own hold, asked about one pair."""

    def __init__(
        self, *, gates: FailClosedGates, holds: AccountHoldQuery
    ) -> None:
        self._gates = gates
        self._holds = holds

    async def admits(
        self, *, reader_id: UUID, subject_id: UUID, sport: Sport
    ) -> bool:
        """Whether this reader may be shown this person in this partition."""

        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among([reader_id])
        )
        if reader_id in held:
            return False
        try:
            withheld = await self._gates.withheld_among(
                reader_id=reader_id, subject_ids=(subject_id,), sport=sport
            )
        except PlayerProfileNotCommitted:
            return False
        return subject_id not in withheld


__all__ = ["LiveRecordGates"]
