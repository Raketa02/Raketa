"""The Matches context's port.

One repository, and it is the **record** kind — rows in, rows out, with the
optimistic-concurrency guard a version column rather than a stream version.
ADR-0034 is why this side of it, and it is the third context to land here after
Clubs and Courts: three record repositories and three event-sourced ones, which
is what ADR-0002's *per-context choice* looks like once four contexts have made
it.

**``save`` publishes.** The match keeps no history, so its announcements are the
only trail there will be, and they have to be written in the transaction that
wrote the row — an outbox row without its match is a support agent reading a
change that never happened, and a match without its outbox row is one nobody can
explain. That is ADR-0003's ordinary guarantee, and here it is load-bearing in a
way it is nowhere else in the tree.

**``save`` does not commit.** The transaction boundary stays a use-case
dependency, and it matters more here than in most contexts: ADR-0035 fixes that
*"a seat payment that earns a court, and the court it earns, are one event or
they are a bug"*, and ``Raketa02/Raketa#70`` writes that across three of them. A
repository that committed would make joining that write impossible from outside.
"""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable
from uuid import UUID

from app.kernel import Boundary, Instant, Minutes

from app.modules.matches.domain.match import Match
from app.modules.matches.domain.wake import MatchWake


@runtime_checkable
class MatchRepository(Protocol):
    async def get(self, match_id: UUID) -> Match | None:
        """One match, whole — every seat and every vacancy — or nothing.

        Whole, because the situation is a function of the whole record and a
        narrower read would be a second answer to *what is this match doing*.
        One row-set is also all it costs: ADR-0034's *"the busiest object in the
        product is the cheapest to read"* is this method's whole justification.
        """
        ...

    async def for_club(self, club_id: UUID) -> list[Match]:
        """Every match at one club, soonest first.

        Ordered by ``start`` and broken by id, which is total: a match has no
        *open row* to be last by construction, so the tie-break is only ever
        about determinism. The two ordering defects `Raketa02/Raketa#64` and
        `#65` measured were both semantic; this one has no semantics to get
        wrong, and it still may not be ambiguous.
        """
        ...

    async def starting_between(
        self, *, club_ids: Sequence[UUID], window_from: Instant, window_to: Instant
    ) -> list[Match]:
        """Every match at any of those clubs starting inside the window.

        The narrow read a composed screen wants, and the reason it takes clubs
        and a window rather than a player: `Now`'s shelves are *the city's*
        matches scored for a viewer (`Raketa02/Raketa#75`), so the fetch is by
        place and time and the ranking is a pure function above it.
        """
        ...

    async def add(self, match: Match) -> Match:
        """Insert a match that does not exist yet, with its seats.

        Publishes whatever it announced, in this transaction.
        """
        ...

    async def save(self, match: Match) -> Match:
        """Persist the delta and the announcements, refusing on a stale version.

        Raises ``ConcurrentMatchModification`` when the stored version has moved
        since the match was loaded — never a silent merge, because two writers
        interleaving on a seat would produce an occupancy nobody authored.
        """
        ...


@runtime_checkable
class CourtHolds(Protocol):
    """Somewhere to keep a court aside for a match, and to give it back.

    **Stated in Matches' words, not Courts'.** A ladder reaching into
    ``ReservationRepository`` would put a reservation, a holder and two intervals
    into its constructor, and the ladder would then have to change every time
    Courts reshaped a read it never asked for. What the ladder knows is that a
    match wants a court of its category for its hour, and that a match it has
    given up on wants one no longer — which is ADR-0035's *"it asks for a court
    of this category, for this window, and is given a reservation or refused. It
    never learns how courts are organised"* seen from the asking side. The
    adapter beside it is the one file that knows whose question it really is.
    """

    async def keep_aside(
        self,
        *,
        match_id: UUID,
        club_id: UUID,
        category_id: UUID,
        start: Instant,
        duration: Minutes,
    ) -> bool:
        """Keep a court for this match, and say whether one was there to keep.

        ``False`` is *nothing was free* and never *somebody beat us to it*: a
        refused claim is re-asked with that court removed, so losing a race
        never reaches this far (ADR-0035). It is therefore a fact about the
        club's inventory, and the ladder's answer to it is a fact about the
        match.

        Idempotent: a match already keeping a court is kept, not doubled.
        """
        ...

    async def give_back(self, *, match_id: UUID, at: Instant) -> None:
        """Put this match's court back on sale. Does nothing if it holds none.

        A **release** and never a delete, because a court's booking history is a
        query over reservations — which is Courts' rule and the reason this is a
        method here rather than an obligation on the ladder to remember.
        """
        ...


@runtime_checkable
class MatchSchedule(Protocol):
    """The timekeeper's two operations over the schedule columns.

    Separate from ``MatchRepository`` on purpose. That port speaks in whole
    matches — every seat and every vacancy, because a situation is a function of
    the whole record — and the timekeeper's tick wants neither: it wants *which
    ids are due* and, at the end, *put this one's moment back*. Loading the
    aggregate to answer the first would be a scan reading three tables to
    discover it has nothing to do.

    **Neither method writes a fact about the match**, which is why neither
    announces anything and why ``re_arm`` does not bump the version. The schedule
    is derived — ``kernel.next_wake`` computes it from the row it sits on — so
    moving it is not a change a support agent would ever need explained
    (ADR-0034's obligation), and versioning it would make every scheduled look a
    write that a player's own tap could lose a race to.
    """

    async def due(self, *, now: Instant, limit: int) -> list[MatchWake]:
        """The matches whose moment has arrived, soonest first.

        Late is not a special case: ``next_wake_at <= now`` stays true through a
        restart, a crash and a redeploy, so a missed wake is simply taken later.
        ADR-0076's *"a restart loses nothing"* is this comparison and nothing
        else.
        """
        ...

    async def re_arm(
        self, *, match_id: UUID, version: int, wake: Boundary | None
    ) -> bool:
        """Point the schedule at the next moment, on the version it was read at.

        **Needed because a look that finds nothing writes nothing.** The hold
        ladder is deliberately silent when it has no move to make — saving anyway
        would bump the version on every wake — and a row left naming a moment
        that has passed is one the tick picks up again a second later, for ever.
        So the schedule is re-armed even when the record did not move.

        Guarded on the version and **not bumping it**: if a real writer moved the
        match in between, it recomputed the schedule from the record it wrote and
        its answer is the right one. Losing here is therefore not an error and
        not a retry — it is somebody else having already done it. Answers whether
        the row was ours to arm.
        """
        ...
