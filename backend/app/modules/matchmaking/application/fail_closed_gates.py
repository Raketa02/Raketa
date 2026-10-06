"""The four gates that fail closed, over one reader and the people shown to them.

``docs/adr/0095`` reaches **every surface that shows one player to another**, and
there is now more than one: a search records an answer and re-verifies it on the
way back out, and a player record is opened about somebody the platform has
already introduced. The search runs all four — a block in either direction, an
account hold, an account state that may not be shown, and the mutual gender
preference. The record runs the three about accounts and no preference (#575):
it opens on a court shared, a group shared or a group run, and binds no index.
The second copy of a safety gate is the defect the whole fail-closed rule exists
to prevent, so the three are ``AccountGates``, a collaborator of their own, and
the four are those three and the preference — never a private step inside
whichever use case needed them first.

**It answers about subjects, and the only thing it can say about the reader is
that it cannot answer at all.** The reader appears in the question because three
of the four gates are *about the pair* — a block is between two people, and the
gender preference is mutual — not because this decides anything about the person
asking. A reader with no profile committed has no preference to weigh, so the
mutual gate cannot be evaluated for anybody and the whole call refuses rather
than withholding everybody one by one; that is the same rule the gates run on,
raised at the only scope it is true at. What is **not** here is *may this person
read anything at all* — a held reader is refused at the entry point of whatever
surface they are on, which is that surface's own rule about its own entry and
reads a different direction of the same port.

**The sport is an argument, and it is the partition's and not the reader's.**
The other half of the gender gate is read off the candidate index, which is
keyed by sport, so the caller has to say which container the row is read from: a
search answers *the sport it ran on*. A subject with no row in the partition
asked about is a gate that **cannot be evaluated**, and a gate that cannot be
evaluated excludes.

**Every read is a set read over the whole list**, never one query per row — the
same shape a search uses, for the same reason — and the index container is bound
**once**, exactly as a search binds it (``docs/adr/0112``).

**What is deliberately not here** is the three soft gates. An open challenge, a
photo and the proposals opt-in do not fail closed, and running them against a
disclosure already made would withhold somebody on a fact the disclosure itself
was willing to be wrong about. The level gate and the radius are not here either:
they are *quality*, and a person who stopped being a good match is still a person
this reader was shown.

**The answer names no gate**, and there is nowhere in it to put one
(``docs/adr/0130``). One withheld subject, four possible causes, and no way to
tell which — a payload naming the gate would deliver a block to the one person it
was meant to be invisible to.
"""

from __future__ import annotations

from typing import Collection, Mapping, final
from uuid import UUID

from app.kernel import Sport
from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.outward_reads import (
    live_block_set,
    read_demand,
)
from app.modules.matchmaking.domain.candidate_index import CandidateRow, Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.errors import PlayerProfileNotCommitted
from app.modules.matchmaking.domain.gates import gender_satisfied
from app.modules.matchmaking.domain.ports import AccountHoldQuery, AccountStatusQuery
from app.modules.player_profile.domain.ports import PlayerProfileRepository


@final
class AccountGates:
    """The three gates about **accounts** — a block in either direction, a
    hold, an account that may not be shown — and nothing that reads a
    partition.

    The three ``FailClosedGates`` asks beside the gender preference, as a
    collaborator of their own, because one surface asks them **without** the
    preference: the player record, which opens on a court shared, a group
    shared or a group run (#575) and binds no candidate index to do it. One
    class, so neither caller holds a second spelling of a gate.
    """

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

        Bounded by ``subject_ids``, for ``withheld_among``'s reason: the block
        read answers with the reader's **whole** exclusion list, and handing it
        back unbounded would make the return value two things at once. Nobody
        to ask about costs no outward read at all.
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


@final
class FailClosedGates:
    """The four, asked about a reader and a set of subjects in one partition:
    the three about accounts, and the mutual gender preference read off the
    candidate index."""

    def __init__(
        self,
        *,
        profiles: PlayerProfileRepository,
        candidates: CandidateSource,
        blocks: BlockQuery,
        holds: AccountHoldQuery,
        account_status: AccountStatusQuery,
    ) -> None:
        self._profiles = profiles
        self._candidates = candidates
        self._accounts = AccountGates(
            blocks=blocks, holds=holds, account_status=account_status
        )

    async def withheld_among(
        self,
        *,
        reader_id: UUID,
        subject_ids: Collection[UUID],
        sport: Sport,
    ) -> frozenset[UUID]:
        """Which of these subjects the live gates no longer admit this reader.

        The answer is a subset of ``subject_ids`` and is bounded by it
        deliberately. The block read answers with the reader's **whole**
        exclusion list, which is a fact about them and not about the question
        asked; handing it back unbounded would make the return value two things
        at once, and a caller that iterated it rather than testing membership
        would be iterating a block list.

        Nobody to ask about costs **no outward read at all** — not an
        optimisation but the honest shape: there is no gate to evaluate over an
        empty set, and a profile loaded to answer about nobody is a refusal
        waiting to happen for a reader who asked nothing.
        """

        subjects = tuple(subject_ids)
        if not subjects:
            return frozenset()
        withheld = await self._accounts.withheld(
            reader_id=reader_id, subject_ids=subjects
        )
        gendered = await self._gender_refuses(
            reader_id=reader_id, subjects=subjects, sport=sport
        )
        return withheld | (gendered & frozenset(subjects))

    async def _gender_refuses(
        self, *, reader_id: UUID, subjects: tuple[UUID, ...], sport: Sport
    ) -> frozenset[UUID]:
        """The mutual gender gate, re-evaluated against both sides as they stand.

        The reader's own half is read **live from their profile**, exactly as a
        search reads it: a preference is the one gate fact its owner can change
        between being shown somebody and asking about them again, and reading it
        from anywhere else would be evaluating a safety setting on a stale copy.

        The other half is the index row, which is where the gate reads it inside
        a search — so the two paths cannot come to different answers about the
        same pair. A subject the index no longer holds has no preference to read,
        which is a gate that cannot be evaluated, and it excludes.
        """

        profile = await self._profiles.load(reader_id)
        if profile is None:
            # The wording is the search read-back's own, kept to the letter: this
            # sentence crosses the wire in a refusal, and an extraction is not
            # the moment to change what a route says.
            raise PlayerProfileNotCommitted(
                "the searcher has no profile to read a preference from"
            )
        indexed = self._indexed(subjects, sport)
        return frozenset(
            subject
            for subject in subjects
            if not gender_satisfied(
                searcher_gender=profile.gender,
                searcher_preference=profile.gender_preference,
                theirs=indexed.get(str(subject)),
            )
        )

    def _indexed(
        self, subjects: Collection[UUID], sport: Sport
    ) -> Mapping[str, CandidateRow]:
        """The index rows for these subjects, in one pass over the partition.

        The container is bound once, exactly as a search binds it — a caller that
        took two snapshots would be one the index could move underneath, which is
        the same rule and not a weaker version of it.

        Resolving twenty ids costs **one pass over the partition**, and that is
        the port's shape rather than an oversight: ``CandidateSource`` answers
        with the container and never with questions about rows
        (``docs/adr/0112``), because a source that answered per-row questions is
        a source a search could call inside its walk.
        """

        wanted = {str(subject) for subject in subjects}
        snapshot = self._candidates.snapshot(Partition.for_sport(sport))
        return {
            row.player_id: row for row in snapshot.rows if row.player_id in wanted
        }
