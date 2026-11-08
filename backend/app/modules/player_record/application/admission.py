"""Who may open a record. **The only rule this context enforces itself.**

> A record is read **through a prior disclosure**, never **about** a person.

Admitted on four strands and never otherwise, beside the reader being the
subject: the pair **played together** — were on one court — the pair **share a
group**, the reader **runs a group they are in** (#575), or **the Ranking shows
them to everybody** — listed on General in a sport, *Show me in General* on —
for any reader, with or without a level (``docs/adr/0203`` §9, #773). Without a
rule of that shape, a route taking a player id is a player-enumeration endpoint
— a level, a photograph and an area for anybody in the city reachable by id —
and a UUID being hard to guess is not an authorization model
(``docs/adr/0159``). **General is still a disclosure**: it names its players to
anybody who opens it, and only those it shows.

**A game played does not stop having happened, and a group does.** A game the
pair are both on discloses for as long as they are both on it, played or not; a
group is membership as it stands, because a group's Members lists who is in it
now, and running one is running it now.

**And the gates run live on every open**, because a disclosure made in August is
not a permission to show somebody in December. The disclosure entitles a reader
to *ask*; the gates decide. They are the three about accounts and the reader's
own hold, and **a block made by either of them** (``docs/adr/0203`` §8) — on
every strand, group-mates included — and **no preference**: every strand here
already put the pair in front of each other.

**What this costs, stated rather than discovered.** At most one read per strand,
asked one after another and stopped at the first that answers yes — a group the
pair share is two indexed reads, a court they shared is a fold over the reader's
games, a group the reader runs is the subject's groups and who runs each, and
the Ranking's is the subject's ranking rows and, while one is listed, their
profile — and then one evaluation of the gates. **The Ranking is asked last**: the
first three are the ways a record has always opened, from Members and a game,
and a stranger from the Ranking pays for all four. It is paid on a deliberate
tap on one person, which is the latency budget ``docs/adr/0107`` reserved for
exactly this.
"""

from __future__ import annotations

from typing import Sequence, final
from uuid import UUID

from app.kernel import Instant
from app.modules.player_record.domain.ports import (
    ShownToEverybody,
    PriorDisclosure,
    RecordGates,
)


@final
class RecordAdmission:
    """The strands, then the gates."""

    def __init__(
        self,
        *,
        disclosures: Sequence[PriorDisclosure],
        everybody: ShownToEverybody,
        gates: RecordGates,
    ) -> None:
        self._disclosures = tuple(disclosures)
        self._everybody = everybody
        self._gates = gates

    async def admits(self, *, reader_id: UUID, subject_id: UUID, now: Instant) -> bool:
        """Whether this reader may open this subject's record, right now.

        **A boolean and never a reason.** There is nowhere in this answer to put
        which strand admitted or which gate refused, which is what makes the one
        unnamed refusal a property of the code rather than a discipline every
        raise site has to keep (``domain/errors.py``).
        """

        if reader_id == subject_id:
            # **The only strand with no prior disclosure behind it, and the only
            # one with no gates.** There is no pair to gate: a block is between
            # two people and says nothing about a person reading their own
            # record. A hold does not reach it either — *How others see you* is
            # the one screen a held player has for finding out how they appear.
            return True
        if await self._disclosed(reader_id=reader_id, subject_id=subject_id, now=now):
            return await self._gates.admits(reader_id=reader_id, subject_id=subject_id)
        return False

    async def _disclosed(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> bool:
        for source in self._disclosures:
            # **Read one after another rather than gathered**, because these
            # adapters share the request's session and an ``AsyncSession`` is
            # not safe to use concurrently. The first yes is enough: every
            # strand is admitted under the same gates, so which one answered
            # changes nothing about what is asked next.
            if await source.discloses(reader_id=reader_id, subject_id=subject_id):
                return True
        return await self._everybody.shows(subject_id, now=now)


__all__ = ["RecordAdmission"]
