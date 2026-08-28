"""Reading a search back — **the recorded answer, plus live gate state.**

A player opens a shortlist they ran this morning and gets the same answer. The
record is immutable and never expires, because it *is* the answer's identity
(``docs/adr/0104``), and nothing here writes: re-verification changes nothing
stored.

**But the gates that fail closed are live** (``docs/adr/0109``). A stored result
that could resurrect somebody who blocked the searcher in between is a safety
hole dressed as a cache — ``docs/adr/0095`` reaches *every surface that shows one
player to another*, and a stored search read back an hour later is that surface
with a longer memory. So the four fail-closed gates — a block either way, a hold,
an account that may not be shown, and the mutual gender preference — are
re-evaluated here, at read time, over the rows the record holds.

**A row they no longer admit is stated as withheld, never silently dropped.** A
list that quietly gets shorter is the same class of lie as a breakdown that
quietly stops adding up, and worse for being invisible.

**And the statement names no gate.** ``docs/adr/0109`` §1 asked for the coarse
gate spelling beside it; that is narrowed here, because ``docs/adr/0095`` is
explicit that *neither party is ever notified and the other side sees no trace
anywhere in any response* — and *withheld: BLOCKED* is precisely that trace,
delivered to the person the block was meant to be invisible to. The same argument
covers the other three: a hold and an account state are moderation facts about
somebody else, and a gender preference is a safety setting whose owner is the
only person entitled to read it (``docs/adr/0096``). One withheld row, four
possible causes, and no way to tell which — the searcher already knows their own
block list, so a coarser statement costs them nothing they did not already have.

**The three soft gates are not re-evaluated, deliberately.** An open challenge, a
photo and the proposals opt-in do not fail closed, and re-running them here would
withhold rows on facts the search itself was willing to be wrong about. The level
gate and the radius are not re-run either: they are *quality*, and a row that
merely stopped being a good match is still a row this search returned.

**What this use case costs.** ADR-0109 priced the read-back as *a lookup plus a
block-set read*; the mutual gender gate makes it a lookup, three set reads and one
snapshot binding, because gender is the one fail-closed gate whose facts live on
the index row rather than in a set the platform can answer in one query. The
staleness ladder is **not** applied: it refuses on ranking quality
(``docs/adr/0111``) and a read-back ranks nothing. A candidate the index no longer
holds at all is a gate that cannot be evaluated, and *a gate that cannot be
evaluated excludes*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, final
from uuid import UUID

from app.modules.blocks.domain.ports import BlockQuery
from app.modules.matchmaking.application.outward_reads import (
    live_block_set,
    read_demand,
)
from app.modules.matchmaking.domain.candidate_index import CandidateRow, Partition
from app.modules.matchmaking.domain.candidate_snapshot import CandidateSource
from app.modules.matchmaking.domain.errors import (
    AccountHeld,
    PlayerProfileNotCommitted,
    SearchNotFound,
)
from app.modules.matchmaking.domain.gates import gender_satisfied
from app.modules.matchmaking.domain.ports import AccountHoldQuery, AccountStatusQuery
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.domain.searches import (
    SearchCandidateRecord,
    SearchRecord,
    SortOption,
)
from app.modules.matchmaking.domain.sorting import of_record, sorts_available
from app.modules.player_profile.domain.ports import PlayerProfileRepository


@final
@dataclass(frozen=True, slots=True)
class ReadBackSearchCommand:
    """*Show me that shortlist again.* One id, and the person asking."""

    search_id: UUID
    #: **The authorization rule, as an argument.** It reaches the store's own
    #: signature unchanged, so there is no path that could read a search without
    #: naming whose it must be.
    reader_id: UUID


@final
@dataclass(frozen=True, slots=True)
class ReadBackRow:
    """One recorded row, and whether the live gates still admit it.

    The recorded half is kept beside the verdict rather than discarded when the
    verdict is *withheld*, because the two are decided here and rendered
    elsewhere — and the renderer is where the rule that a withheld row carries no
    person is written down and tested.
    """

    recorded: SearchCandidateRecord
    withheld: bool


@final
@dataclass(frozen=True, slots=True)
class ReadBackAnswer:
    """The record, the verdict on each of its rows, and the honest sort list."""

    record: SearchRecord
    rows: tuple[ReadBackRow, ...]
    #: Recomputed over the rows that are **still shown**. A read-back that
    #: withheld half the list must not go on offering a control that would now
    #: reorder nothing — the offerability rule is about the rows in the reader's
    #: hand, and after a withholding those are different rows.
    sorts_available: tuple[SortOption, ...]


@final
class ReadBackSearch:
    """One stored search, re-verified and rendered again."""

    def __init__(
        self,
        *,
        searches: SearchStore,
        profiles: PlayerProfileRepository,
        candidates: CandidateSource,
        blocks: BlockQuery,
        holds: AccountHoldQuery,
        account_status: AccountStatusQuery,
    ) -> None:
        self._searches = searches
        self._profiles = profiles
        self._candidates = candidates
        self._blocks = blocks
        self._holds = holds
        self._account_status = account_status

    async def execute(self, command: ReadBackSearchCommand) -> ReadBackAnswer:
        record = await self._searches.find(
            search_id=command.search_id, searcher_id=command.reader_id
        )
        if record is None:
            raise SearchNotFound("no search of yours has that id")
        await self._refuse_a_held_reader(command.reader_id)

        rows = record.returned
        withheld = await self._withheld(record, rows)
        shown = tuple(row for row in rows if row.player_id not in withheld)
        return ReadBackAnswer(
            record=record,
            rows=tuple(
                ReadBackRow(recorded=row, withheld=row.player_id in withheld)
                for row in rows
            ),
            sorts_available=sorts_available(
                tuple(of_record(row) for row in shown), surface=record.surface
            ),
        )

    async def _refuse_a_held_reader(self, reader_id: UUID) -> None:
        """**The hold points both ways**, and it points at old answers too.

        A held player can still sign in, so refusing them a fresh search while
        handing back this morning's would be the hold ending at the one route
        that remembers.
        """

        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among([reader_id])
        )
        if reader_id in held:
            raise AccountHeld("this account is under a hold")

    async def _withheld(
        self, record: SearchRecord, rows: tuple[SearchCandidateRecord, ...]
    ) -> frozenset[UUID]:
        """Which of these rows the live fail-closed gates no longer admit.

        Every read here is a **set read over the whole list**, never one query
        per row: the same shape the search itself uses, for the same reason.
        """

        if not rows:
            return frozenset()
        player_ids = tuple(row.player_id for row in rows)
        blocked = await live_block_set(self._blocks, record.searcher_id)
        held = await read_demand(
            AccountHoldQuery, lambda: self._holds.held_among(player_ids)
        )
        unshowable = await read_demand(
            AccountStatusQuery,
            lambda: self._account_status.may_not_be_shown(player_ids),
        )
        return frozenset(blocked | held | unshowable) | await self._gender_refuses(
            record, player_ids
        )

    async def _gender_refuses(
        self, record: SearchRecord, player_ids: tuple[UUID, ...]
    ) -> frozenset[UUID]:
        """The mutual gender gate, re-evaluated against both sides as they stand.

        The reader's own half is read **live from their profile**, exactly as the
        search read it: a preference is the one gate fact its owner can change
        between running a search and opening it again, and reading it from
        anywhere else would be evaluating a safety setting on a stale copy.

        The other half is the index row, which is where the gate reads it inside
        a search — so the two paths cannot come to different answers about the
        same pair. A candidate the index no longer holds has no preference to
        read, which is a gate that cannot be evaluated, and it excludes.
        """

        profile = await self._profiles.load(record.searcher_id)
        if profile is None:
            raise PlayerProfileNotCommitted(
                "the searcher has no profile to read a preference from"
            )
        indexed = self._indexed(record, player_ids)
        return frozenset(
            player_id
            for player_id in player_ids
            if not gender_satisfied(
                searcher_gender=profile.gender,
                searcher_preference=profile.gender_preference,
                theirs=indexed.get(str(player_id)),
            )
        )

    def _indexed(
        self, record: SearchRecord, player_ids: Collection[UUID]
    ) -> Mapping[str, CandidateRow]:
        """The index rows for these players, in one pass over the partition.

        The container is bound once, exactly as a search binds it — a read-back
        that took two snapshots would be a read-back the index could move
        underneath, which is the same rule and not a weaker version of it.

        Resolving twenty ids costs **one pass over the partition**, and that is
        the port's shape rather than an oversight: ``CandidateSource`` answers
        with the container and never with questions about rows
        (``docs/adr/0112``), because a source that answered per-row questions is
        a source a search could call inside its walk.
        """

        wanted = {str(player_id) for player_id in player_ids}
        snapshot = self._candidates.snapshot(Partition.for_sport(record.sport))
        return {
            row.player_id: row
            for row in snapshot.rows
            if row.player_id in wanted
        }
