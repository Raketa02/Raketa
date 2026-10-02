"""``RecordGates`` over the four that are spelled once on this platform.

The collaborator this delegates to is ``matchmaking``'s
:class:`~app.modules.matchmaking.application.fail_closed_gates.FailClosedGates`,
extracted for exactly this caller (#374): a block in either direction, an account
hold, an account state that may not be shown, and the mutual gender preference,
evaluated over a reader and a set of subjects in one sport's partition. A second
spelling of a safety gate is the defect the whole fail-closed rule exists to
prevent, so what lives here is a **translation and never a copy** — this file
contains no gate.

**The same collaborator answers the fifth strand without the preference.**
Whoever runs a group the subject is in is admitted on the three gates about
accounts, which read no partition (#566, ``docs/adr/0159``'s amendment of
2026-10-02) — ``FailClosedGates.withheld_regardless_of_preference``, which the
four are composed from, so that question is not a copy either.

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
    """The four gates and the reader's own hold, asked about one pair — or the
    three about accounts and the reader's hold, for whoever runs their group."""

    def __init__(
        self, *, gates: FailClosedGates, holds: AccountHoldQuery
    ) -> None:
        self._gates = gates
        self._holds = holds

    async def admits(
        self, *, reader_id: UUID, subject_id: UUID, sport: Sport
    ) -> bool:
        """Whether this reader may be shown this person in this partition."""

        if await self._reader_is_held(reader_id):
            return False
        try:
            withheld = await self._gates.withheld_among(
                reader_id=reader_id, subject_ids=(subject_id,), sport=sport
            )
        except PlayerProfileNotCommitted:
            return False
        return subject_id not in withheld

    async def admits_regardless_of_preference(
        self, *, reader_id: UUID, subject_id: UUID
    ) -> bool:
        """Whether this reader may be shown this person **with the preference
        not asked** — for whoever runs a group the subject is in. The reader's
        own hold first, as above; then the three about accounts, which load no
        profile, so there is no ``PlayerProfileNotCommitted`` to answer."""

        if await self._reader_is_held(reader_id):
            return False
        withheld = await self._gates.withheld_regardless_of_preference(
            reader_id=reader_id, subject_ids=(subject_id,)
        )
        return subject_id not in withheld

    async def _reader_is_held(self, reader_id: UUID) -> bool:
        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among([reader_id])
        )
        return reader_id in held


__all__ = ["LiveRecordGates"]
