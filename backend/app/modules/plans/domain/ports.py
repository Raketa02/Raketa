"""What this context stores behind, and the two facts it demands.

**Nothing here is published outward.** A plan is read by the client and by
nobody else on this side of the wire: ``games`` may not import it
(``docs/adr/0145`` §4), ``conversations`` is *told* through the outbox and asks
this context nothing, and the card ladder that reads a plan is the **client's**
``domain/``. So there is no provider register for the Plan and every port below
is either its own store or a demand.

**Two of them are its own and two are somebody else's.** The repository and the
directory are how this module loads and finds its own aggregate; nobody outside
will ever hold either. ``AccountHoldQuery`` is the **fourth** spelling of a port
whose provider does not exist yet, and it is spelled again rather than imported
for the reason the third one was: a context reading a safety fact through
another context is exactly the coupling the split exists to avoid.

**``PlannableCourts`` is the one question this context asks about a court, and
it is declared here, in the Plan's own words** (``docs/adr/0164`` §3). It used
to be ``games``' — *is this player on this game's court, and is that game still
open to planning* — published there because it was entirely a question about
that record. A plan is the **challenge's** now, drawn in the room from its
opening with whoever is in, so the question is about a court that has a
challenge and may or may not have a game yet: *every challenge on which the
reader holds an accepted, live seat*, open to planning while the challenge is
arranging or its game is awaiting its entry, history otherwise. Neither provider
can answer that alone and neither may import the other's aggregate, so it is
answered — as ``conversations`` answers *one rule read against two records* —
by an adapter on this side of the arrow that folds the challenge and, for a
court that has become a game, the game, through the two providers' own ports.
It is the read that decides who may write, which is why it is contracted on
this context's demands register rather than trusted.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Collection, Mapping, Protocol, final, runtime_checkable
from uuid import UUID

from app.kernel import Instant
from app.modules.plans.domain.plan import Plan


@runtime_checkable
class PlanRepository(Protocol):
    """One challenge's plan, loaded and appended to.

    **``load`` never answers ``None``.** A plan is *born by being used*, so *no
    plan yet* is a plan with nothing in it rather than an absence — and a caller
    that had to spell ``or Plan.unwritten(challenge_id)`` at each of the four
    writes would be spelling the birth four times. The write path does not care
    which it has, and neither does the read: the directory below answers the
    streams that exist and the list read spells the rest as unwritten.

    **Nothing here commits.** The transaction boundary is the use case's.
    """

    async def load(self, challenge_id: UUID) -> Plan: ...

    async def save(self, plan: Plan) -> None: ...


@runtime_checkable
class PlanDirectory(Protocol):
    """*Which of these courts have a plan written?* The list read's only store
    question."""

    async def for_challenges(
        self, challenge_ids: Collection[UUID]
    ) -> tuple[Plan, ...]:
        """Every written plan among these courts. **One set read over the whole
        answer.**

        Never one per court, which is the shape every set read in this codebase
        takes — and here it costs nothing to promise, because a plan's stream id
        **is** its challenge's, so this is an ``IN`` over the aggregate id rather
        than the payload match the neighbouring contexts pay.

        **A court with nothing agreed is absent from the answer**, because it has
        no stream. That is the store's spelling of *nothing agreed*; the list
        read turns it into an unwritten plan, because ``GET /plans`` lists one
        row for every court the reader may plan, written or not
        (``docs/adr/0164`` §4).

        The order is not part of the demand: the list is ordered like its owner —
        newest arrangement first — and that is a fold over each court's anchor,
        which belongs to the use case rather than to the store.
        """
        ...


@final
@dataclass(frozen=True, slots=True)
class PlannableCourt:
    """One court somebody may still be arranging, as the Plan needs to see it.

    Three fields, and each is one half of a question the Plan cannot answer for
    itself (``docs/adr/0164`` §3–§5).

    ``anchor`` is **what the horizon is measured from**: the instant the
    challenge was sent until the game exists, and the game's ``planned_at``
    after. It is handed over rather than copied — the Plan reads it per write
    and stores it nowhere — and it only ever moves later, so a day chosen under
    the first is still valid under the second.

    ``open_to_planning`` is **whether the slots may still move**: the challenge
    still arranging (``AWAITING_ANSWERS``, ``LINE_UP_INCOMPLETE``) while there
    is no game, and the game still inside its entry window once there is one.
    It is folded against the caller's own instant like every standing in
    ``challenges`` and ``games``, so *are the slots frozen* has the same answer
    at every instant and needs no sweep to become true.

    ``whole`` is **whether every seat is accepted** — the one fact the lock is
    guarded on beside the plan's own count. A court that has never been a game
    is not whole; a game whose seat somebody left is not whole again until the
    next completed line-up re-seats it.

    **A court absent from the answer is one this reader holds no accepted, live
    seat on**, and that is the only shape *you may not write here* takes. A
    stranger, an invitee still deciding and somebody who left are all absent,
    and there is no field saying which, because a field would have to be read
    and a missing row cannot be forgotten.

    **It carries no challenge id**, because the mapping is keyed by one and this
    context's own rule is that nothing is stored where it can be derived — a
    second copy of an identity is the first thing that can disagree with itself.
    """

    anchor: Instant
    open_to_planning: bool
    whole: bool


@runtime_checkable
class PlannableCourts(Protocol):
    """*Which courts is this player arranging, and which are history?*

    **One port asking one question** (``docs/adr/0164`` §3), and the two refusals
    a write can produce are its two answers: absent from the mapping is
    ``plan_not_found``, and ``open_to_planning`` false is ``plan_is_history``.
    The third — ``the_court_is_not_whole`` — reads ``whole`` and reaches only the
    lock.

    **It answers about a player and not about a court**, and that is what makes
    it one method rather than two. The Plan needs the same fact twice — once to
    decide whether one write may land, and once to know which rows a reader's
    list contains — and a port with a per-court arm beside a per-player one
    would be two ways to reach one answer, free to disagree the day a standing
    moved between them.

    **Every court the player holds an accepted seat on is here, open or not**,
    because the list read draws a plan beside a game whatever its standing: a
    game screen reads the plan of a game that was never played, and dropping the
    history would make the plan vanish from the one screen that still shows it.

    **Cost.** Bounded by how many courts this player has ever accepted a seat
    on, which is every read in this context and for the same reason: the fold
    *is* the answer.
    """

    async def plannable_for(
        self, player_id: UUID, *, now: Instant
    ) -> Mapping[UUID, PlannableCourt]:
        """Every court this player holds an accepted, live seat on, keyed by
        challenge id."""
        ...


@runtime_checkable
class AccountHoldQuery(Protocol):
    """Whether an account is under a live hold. **Asked on writes only.**

    ``docs/adr/0148`` §9: *a hold stops you writing anywhere another player sees
    it, and never stops you reading.* A slot change writes a system line into a
    room other people are in, so it is reach; but a hold must not erase an
    arrangement other people are already inside, so the read is ungated and all
    four writes are not.

    **The fourth spelling of one empty answer, and the duplication is the
    decision.** The matcher, ``challenges`` and ``conversations`` each declare a
    port of this shape against the same absent provider. On the day ``cases``
    ships, four lines in the composition root change to the same adapter.
    """

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        """Which of these players are under a live hold, right now."""
        ...


__all__ = [
    "AccountHoldQuery",
    "PlanDirectory",
    "PlanRepository",
    "PlannableCourt",
    "PlannableCourts",
]
