"""Who may open a record. **The only rule this context enforces itself.**

> A record is read **through a prior disclosure**, never **about** a person.

Admitted on four strands and never otherwise: the reader **is** the subject; a
search of the reader's **returned** them; the pair **share an open challenge, a
game or a group**; or the reader **runs a group they are in**. Without a rule of
that shape, a route taking a player id is a player-enumeration endpoint — a
level, a photograph and an area for anybody in the city reachable by id — and a
UUID being hard to guess is not an authorization model (``docs/adr/0159``).

**Nothing expires.** A search record is kept for ever (``docs/adr/0104``), so any
window shorter than that could only misfire: it would refuse a face the app is
*currently showing*, drawn from a shortlist the reader can still open. So there
is no ``since`` on any read here and no age on any answer. **A group is the one
strand that ends**, and not by age: it is membership as it stands, because a
group's Members lists who is in it now.

**And the four fail-closed gates run live on every open**, because a disclosure
made in August is not a permission to show somebody in December. The disclosure
entitles a reader to *ask*; the gates decide.

**Except the preference, for whoever runs the subject's group** (#566,
``docs/adr/0159``'s amendment of 2026-10-02). An official group's Administrator
is not in it, reads every member's face and Levels on their own page, and lets
them in; a gender preference says who a player is willing to be *matched* with,
and running their group is not that. So that strand is asked **last**, only
once every disclosure has been refused, and is admitted on the gates about
accounts — the block, the holds and an account that may not be shown — which
read no partition. Asked last, it costs the ordinary record nothing: a search,
a challenge, a game or a group the pair share admits first.

**The partition is the disclosure's, and that is the whole reason this reads in
sports.** The mutual gender gate reads the other side's preference off a
candidate index row, and the index is keyed by sport. A subject rated only in
squash has no row in a padel partition — so asked there, the gate cannot be
evaluated, *a gate that cannot be evaluated excludes*, and the route refuses
somebody the reader demonstrably just saw. Asked in the partition the search
actually ran in, the row is there.

**What this costs, stated rather than discovered.** One read per disclosure
source — four, in parallel with nothing, because they are four different
questions of four different stores — and then one gate evaluation per disclosed
partition until one admits. A gate evaluation is a profile load, three set reads
over a single id and one index container binding, and there are at most four
partitions because there are four sports. In the overwhelming case there is one
partition and the loop runs once. Only a record every partition refused pays
one more — *does the reader run a group they are in* — and, where they do, one
evaluation of the three gates about accounts. It is paid on a deliberate tap on
one person, which is the latency budget ``docs/adr/0107`` reserved for exactly
this.
"""

from __future__ import annotations

from typing import Sequence, final
from uuid import UUID

from app.kernel import Instant, Sport
from app.modules.player_record.domain.ports import (
    PriorDisclosure,
    RecordGates,
    RunnerDisclosure,
)


@final
class RecordAdmission:
    """The strands and the four gates, asked in that order — and whoever runs
    the subject's group last, on the three that are about accounts."""

    def __init__(
        self,
        *,
        disclosures: Sequence[PriorDisclosure],
        runners: RunnerDisclosure,
        gates: RecordGates,
    ) -> None:
        self._disclosures = tuple(disclosures)
        self._runners = runners
        self._gates = gates

    async def admits(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> bool:
        """Whether this reader may open this subject's record, right now.

        **A boolean and never a reason.** There is nowhere in this answer to put
        which strand admitted or which gate refused, which is what makes the one
        unnamed refusal a property of the code rather than a discipline four
        raise sites have to keep (``domain/errors.py``).
        """

        if reader_id == subject_id:
            # **The only strand with no prior disclosure behind it, and the only
            # one with no gates.** There is no pair to gate: a block is between
            # two people, the mutual gender preference is mutual, and neither
            # says anything about a person reading their own record. A hold does
            # not reach it either — *How others see you* is the one screen a held
            # player has for finding out how they appear.
            return True

        partitions = await self._disclosed_partitions(
            reader_id=reader_id, subject_id=subject_id, now=now
        )
        for sport in Sport:
            # **The registry's order, never the set's** (``docs/adr/0105``). The
            # answer does not depend on it — any admitting partition admits — but
            # *which* gate reads happen does, and a walk in hash order is a
            # different sequence of database reads on every process.
            if sport not in partitions:
                continue
            if await self._gates.admits(
                reader_id=reader_id, subject_id=subject_id, sport=sport
            ):
                return True
        # **Whoever runs their group, last.** Not a partition, so not in the
        # walk above: the preference is not asked of this strand, and it is the
        # only gate that reads one. Asked only now, so a record any disclosure
        # opened never pays for it.
        if await self._runners.runs_a_group_of(
            reader_id=reader_id, subject_id=subject_id
        ):
            return await self._gates.admits_regardless_of_preference(
                reader_id=reader_id, subject_id=subject_id
            )
        return False

    async def _disclosed_partitions(
        self, *, reader_id: UUID, subject_id: UUID, now: Instant
    ) -> frozenset[Sport]:
        """Every partition any strand says this reader has been shown them in.

        **A union, because each disclosure entitles on its own terms.** A pair
        whose padel index row has gone are still admitted through the tennis game
        they played; stopping at the first strand that answered would make
        admission depend on which one happened to be asked first.

        Read one after another rather than gathered, because these adapters share
        the request's session and an ``AsyncSession`` is not safe to use
        concurrently — the same asymmetry ``PlayerCardIdentities`` writes down
        between its two loops.
        """

        partitions: set[Sport] = set()
        for source in self._disclosures:
            partitions |= await source.partitions_between(
                reader_id=reader_id, subject_id=subject_id, now=now
            )
        return frozenset(partitions)


__all__ = ["RecordAdmission"]
