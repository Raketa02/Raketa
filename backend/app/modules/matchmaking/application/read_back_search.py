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
re-evaluated at read time, over the rows the record holds.

**They are not evaluated *here*, and that is the point.** They live in
:class:`~app.modules.matchmaking.application.fail_closed_gates.FailClosedGates`,
because a read-back is not the only surface that shows a player somebody the
platform introduced earlier and this use case would otherwise be the only place
the four are spelled. A second spelling of a safety gate is precisely the defect
the fail-closed rule exists to prevent, so what is left here is the one thing the
read-back decides for itself: that the partition to ask in is the sport this
search ran on.

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
the index row rather than in a set the platform can answer in one query. Moving
the four out changed none of that — a collaborator is not a query. The
staleness ladder is **not** applied: it refuses on ranking quality
(``docs/adr/0111``) and a read-back ranks nothing. A candidate the index no longer
holds at all is a gate that cannot be evaluated, and *a gate that cannot be
evaluated excludes*.

**The reader's own hold stays here.** It is a refusal about the person asking
rather than a verdict on anybody shown to them, it raises where the four withhold,
and it is the same rule ``SearchWorkbench.refuse_a_held_searcher`` states at the
entry to a fresh search — an entry rule belongs to the surface whose entry it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.modules.matchmaking.application.fail_closed_gates import FailClosedGates
from app.modules.matchmaking.application.outward_reads import read_demand
from app.modules.matchmaking.domain.errors import SearchNotFound
from app.modules.matchmaking.domain.ports import AccountHoldQuery
from app.modules.matchmaking.domain.search_store import SearchStore
from app.modules.matchmaking.domain.searches import (
    SearchCandidateRecord,
    SearchRecord,
    SortOption,
)
from app.modules.matchmaking.domain.sorting import of_record, sorts_available
from app.shared.domain.errors import AccountHeld


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


def still_shown(
    rows: tuple[ReadBackRow, ...],
) -> tuple[SearchCandidateRecord, ...]:
    """The recorded half of every row the live gates still admit.

    One definition, because two things read it at two different moments: the
    sort list, computed here before the answer exists, and
    :attr:`ReadBackAnswer.shown`, read by the route afterwards. Written twice,
    they would be two answers to *who is this reader actually being shown*.
    """

    return tuple(row.recorded for row in rows if not row.withheld)


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

    @property
    def shown(self) -> tuple[SearchCandidateRecord, ...]:
        """The rows this answer still puts a person on.

        Read by everything that acts on *whom the reader is about to see* — the
        sort list above, and the photo links minted for the response. A withheld
        row carries no person, so signing their photograph would be minting an
        address for somebody this answer has just agreed to stop showing.
        """

        return still_shown(self.rows)


@final
class ReadBackSearch:
    """One stored search, re-verified and rendered again."""

    def __init__(
        self,
        *,
        searches: SearchStore,
        holds: AccountHoldQuery,
        gates: FailClosedGates,
    ) -> None:
        self._searches = searches
        self._holds = holds
        self._gates = gates

    async def execute(self, command: ReadBackSearchCommand) -> ReadBackAnswer:
        record = await self._searches.find(
            search_id=command.search_id, searcher_id=command.reader_id
        )
        if record is None:
            raise SearchNotFound("no search of yours has that id")
        await self._refuse_a_held_reader(command.reader_id)

        rows = record.returned
        # **The sport handed over is the one this search ran on**, which is the
        # partition its rows were drawn from and therefore the only container
        # their index rows can be found in.
        withheld = await self._gates.withheld_among(
            reader_id=record.searcher_id,
            subject_ids=tuple(row.player_id for row in rows),
            sport=record.sport,
        )
        verdicts = tuple(
            ReadBackRow(recorded=row, withheld=row.player_id in withheld)
            for row in rows
        )
        shown = still_shown(verdicts)
        return ReadBackAnswer(
            record=record,
            rows=verdicts,
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
