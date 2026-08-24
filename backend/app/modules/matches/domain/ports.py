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

    async def for_player(self, player_id: UUID) -> list[Match]:
        """Every match this player is enrolled in, soonest first.

        **Enrolment is a relationship and not an object** (``seat.py``), so this
        is the query that stands in for the enrolment row Matches deliberately
        does not keep: a seat that names her, *or* a departure that does. Two
        sources and one answer, because ADR-0030's leaver is an audience of the
        same card rather than a different kind of membership — *"the leaver's
        card is the match's card rendered for somebody who used to hold a
        seat"*, and a strip that dropped her would hide the only thing that
        decides her refund.

        Whole matches, like ``get``: the composed screen resolves a situation
        per match and a situation is a function of the whole record.

        Ordered by ``start`` and broken by id, which is what lets the enrolled
        strip be chronological with its order **fixed at composition** — a card
        that moved as the player reached for it would be the one defect a
        chronological region exists to avoid.
        """
        ...

    async def queued_by(self, player_id: UUID) -> list[Match]:
        """Every match this player holds a **standby place** for, soonest first.

        A second method rather than a third arm on ``for_player``, and the
        reason is that the two answers mean different things to their readers.
        ``for_player`` is *enrolment* — a seat or a departure — and eligibility
        reads it twice: ``NotAlreadyMine`` off the identity and
        ``NoScheduleConflict`` off the hours. A standby place is neither. It
        must not make a Thursday evening *hers* for the purposes of a clash,
        because she is not playing; and the shelf rule that keeps a queued match
        off her suggestions is ``NotOnStandby``, which already exists. Widening
        ``for_player`` would have made both of those wrong in silence.

        Ordered by ``start`` and broken by id, the same total order, because the
        enrolled strip merges the two lists and a chronological region's order
        is fixed at composition (ADR-0073).
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
class SeatClaims(Protocol):
    """The one question about claims that no single match can answer.

    **One live claim per player, across every match** (ADR-0081), so nobody
    parks three seats in three matches while deciding. The aggregate can see
    its own claims and cannot see anybody else's, so this is a third port over
    the same tables, in the shape ``MatchSchedule`` already established: that
    one asks *which ids are due*, this one asks *is she already buying
    something*, and neither wants a whole match.

    **It is a query and never a write**, which is what makes the rule survive a
    downed reaper. *Live* is composed — unended **and** not yet expired — so a
    player whose last claim ran out is free the instant it did, without waiting
    for anybody to write the receipt. A unique index would have to spell *live*
    as *unended*, and would then refuse her on the strength of a row nobody had
    got round to closing.

    **The residual race is real and is stated rather than papered over.** Two
    taps in two matches inside the same instant can both see nothing and both
    open a claim, because no version guard spans two matches. What that costs is
    five minutes in which one player holds two queue places; it cannot produce
    two seats, because a seat is taken and paid in one write and one player
    holds at most one seat in a match. The structural limits are the whole
    defence until the player score exists, and ADR-0081 says so.
    """

    async def live_for(self, player_id: UUID, *, at: Instant) -> UUID | None:
        """The match this player is already buying a seat in, or nothing."""
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


@runtime_checkable
class StandbyPlaces(Protocol):
    """The queue: who asked to be told if a seat frees, and the two writes on it.

    A port of its own rather than three more methods on ``MatchRepository``,
    because a standby place is **not part of the aggregate** and the separation
    is what keeps that true. ADR-0034 makes ``matches.version`` the concurrency
    guard for everything the aggregate owns; a join moves no state anybody is
    contending for, and routing it through ``Match`` would bump that version —
    serialising joins against seat payments and invalidating the
    scoring-context cache keyed ``matchId : recordVersion`` every time somebody
    queued.

    **Nothing here announces anything**, which is the one place this context
    departs from ADR-0034's *every change is its own named event*. That
    obligation is about a **match**: the trail exists so a support agent can
    explain what happened to a game somebody paid for. A standby place moves no
    money, confers no place — *priority, not a place* — and has exactly one
    reader, the invitation cascade (``Raketa02/Raketa#82``), which reads the
    list when a seat frees rather than following it. An outbox row nothing
    subscribes to is ADR-0071's field with no reader, written once per tap.

    **Both writes are idempotent and neither reports what it found.** Joining
    twice is joining once and leaving twice is leaving once, which is exactly
    what lets ADR-0087 refuse an idempotency key on the route: *"a repeated
    delete of a standby place a player no longer holds is the state they asked
    for"*. A method answering *and it was there* would be an answer with one
    honest use — telling her she had already left — and ADR-0070 forbids that
    shape: a refusal is not a second shape, and here there is no refusal at all.
    """

    async def join(self, *, match_id: UUID, player_id: UUID, at: Instant) -> None:
        """Queue this player for this match, or leave her queued.

        ``at`` is stored and read by nothing today. Rung 1 of the invitation
        ladder is fit-ordered within itself (ADR-0061), so *when she asked* is a
        fact rather than a place — and it is stored because it is the one thing
        here nothing could derive later.
        """
        ...

    async def leave(self, *, match_id: UUID, player_id: UUID) -> None:
        """Take her off this match's queue, or leave it as it already is."""
        ...

    async def held_by(self, player_id: UUID) -> frozenset[UUID]:
        """Which matches this player is queued for. Empty is the ordinary answer.

        A set rather than a list, on ``RatedSports.for_player``'s rule: nothing
        downstream reads an order out of it, and a list would invite one. The
        thing that *is* ordered is the strip, and its order comes off ``start``
        in ``queued_by`` rather than off the queue.
        """
        ...

    async def queued_for(self, match_id: UUID) -> frozenset[UUID]:
        """Who is queued for this match. **The cascade's read, and rung 1.**

        The other direction of ``held_by``, and the one the table's composite
        key answers off its own left edge — the migration that created it says
        so in as many words, and the index beside it exists for the reverse.
        Two methods rather than one, because the two questions have different
        readers and different costs: the strip asks *what is this player queued
        for* on every compose, and this is asked once when a seat frees.

        A set, for ``held_by``'s reason: rung 1 is **fit-ordered** within itself
        (ADR-0061), so the queue has no order for a list to imply. ``joined_at``
        is stored and still read by nothing.
        """
        ...
