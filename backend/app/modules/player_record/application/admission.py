"""Who may open a record. **The only rule this context enforces itself.**

> A record opens for any reader, unless (a) a block stands between the two,
> made by either side, or (b) the subject has turned *Show me to new people*
> off and the reader shares no group, no game and no friendship with them
> (``docs/adr/0204`` §2).

**Rule (b) is ``WithinReach``**, and it is also the rule a friend request is
admitted by: Friends asks it through a port of its own, signed in this
context's ``infrastructure/``, so the record and the ask can never disagree
about who may be reached. It reads **the switch first** — on by default, so for
almost everybody the answer is one profile read — and only for a switched-off
subject the strands: the pair **share a group**, **played together** (were on
one court), the reader **runs a group they are in** (#575; ``docs/adr/0204``
§2's call), they are **friends**, or **the subject asked the reader** to be
friends — a call made by #791, so a switched-off player's request never leads
the person asked to a closed record, nor refuses the *Add friend* that would
cross it. A game played does not stop having
happened, and a group does: a game the pair are both on admits for as long as
they are both on it, played or not; a group is membership as it stands.

**Rule (a) is a gate, with the account gates beside it**, run live on every
open: the subject's hold, an account that may not be shown, the reader's own
hold, and **a block made by either of them** (``docs/adr/0203`` §8) — every
strand, group-mates included — and **no preference**: nothing here matches
anybody with anybody.

**Why a switch and not the whole city.** A route taking a player id is a
player-enumeration endpoint by construction now, and that is the product's
decision (``docs/adr/0204`` Consequences: *this is a social app*). The record
holds nothing the product owner ruled sensitive, and *Show me to new people* is
the way out for whoever wants one.
"""

from __future__ import annotations

from typing import Sequence, final
from uuid import UUID

from app.modules.player_record.domain.ports import (
    OpenToNewPeople,
    PriorDisclosure,
    RecordGates,
)


@final
class WithinReach:
    """Rule (b): the subject is open to new people, or the reader shares a
    group, a game or a friendship with them, or runs a group they are in."""

    def __init__(
        self,
        *,
        new_people: OpenToNewPeople,
        disclosures: Sequence[PriorDisclosure],
    ) -> None:
        self._new_people = new_people
        self._disclosures = tuple(disclosures)

    async def reaches(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """**A boolean and never a reason**, so neither the record nor the ask
        has anywhere to say which half refused."""

        if await self._new_people.open_to_new_people(subject_id):
            return True
        for source in self._disclosures:
            # **Read one after another rather than gathered**, because these
            # adapters share the request's session and an ``AsyncSession`` is
            # not safe to use concurrently. The first yes is enough.
            if await source.discloses(reader_id=reader_id, subject_id=subject_id):
                return True
        return False


@final
class RecordAdmission:
    """Rule (b), then the gates — rule (a) among them."""

    def __init__(self, *, reach: WithinReach, gates: RecordGates) -> None:
        self._reach = reach
        self._gates = gates

    async def admits(self, *, reader_id: UUID, subject_id: UUID) -> bool:
        """Whether this reader may open this subject's record, right now.

        **A boolean and never a reason.** There is nowhere in this answer to put
        which rule refused, which is what makes the one unnamed refusal a
        property of the code rather than a discipline every raise site has to
        keep (``domain/errors.py``).
        """

        if reader_id == subject_id:
            # **The only case with no gates.** A block is between two people
            # and says nothing about a person reading their own record, and a
            # hold does not reach it either — *How others see you* is the one
            # screen a held player has for finding out how they appear.
            return True
        if not await self._reach.reaches(reader_id=reader_id, subject_id=subject_id):
            return False
        return await self._gates.admits(reader_id=reader_id, subject_id=subject_id)


__all__ = ["RecordAdmission", "WithinReach"]
