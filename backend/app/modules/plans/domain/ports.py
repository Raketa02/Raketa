"""What this context stores behind, and the one safety fact it demands.

**Nothing here is published outward.** A plan is read by the client and by
nobody else on this side of the wire: ``games`` may not import it
(``docs/adr/0145`` §4), ``conversations`` is *told* through the outbox and asks
this context nothing, and the card ladder that reads a plan is the **client's**
``domain/``. So there is no provider register for the Plan and every port below
is either its own store or a demand.

**Two of them are its own and one is somebody else's.** The repository and the
directory are how this module loads and finds its own aggregate; nobody outside
will ever hold either. ``AccountHoldQuery`` is the **fourth** spelling of a port
whose provider does not exist yet, and it is spelled again rather than imported
for the reason the third one was: a context reading a safety fact through
another context is exactly the coupling the split exists to avoid.

**The one fact this context reads about a game is not here, and that is
deliberate.** *Is this player on this game's court, and is that game still open
to planning* is ``games``' question about ``games``' record, so it is
**published** by that context as ``PlanningCourt`` and contracted on its own
provider register (``app/bootstrap/games_demands.py``). Declaring a second
Protocol of that shape here would make the Plan the author of a fact it does not
own — and it is the read that decides who may write, so a second author is the
last thing it should have.
"""

from __future__ import annotations

from typing import Collection, Protocol, runtime_checkable
from uuid import UUID

from app.modules.plans.domain.plan import Plan


@runtime_checkable
class PlanRepository(Protocol):
    """One game's plan, loaded and appended to.

    **``load`` never answers ``None``.** A plan is *born by being used*, so *no
    plan yet* is a plan with nothing in it rather than an absence — and a caller
    that had to spell ``or Plan.unwritten(game_id)`` at each of the three writes
    would be spelling the birth three times. The write path does not care which
    it has; the **read** never meets an unwritten one, because the directory
    below answers off the streams that exist.

    **Nothing here commits.** The transaction boundary is the use case's.
    """

    async def load(self, game_id: UUID) -> Plan: ...

    async def save(self, plan: Plan) -> None: ...


@runtime_checkable
class PlanDirectory(Protocol):
    """*Which of these games have a plan?* The list read's only store question."""

    async def for_games(self, game_ids: Collection[UUID]) -> tuple[Plan, ...]:
        """Every plan among these games. **One set read over the whole answer.**

        Never one per game, which is the shape every set read in this codebase
        takes — and here it costs nothing to promise, because a plan's stream id
        **is** its game's, so this is an ``IN`` over the aggregate id rather than
        the payload match the neighbouring contexts pay.

        **A game with nothing agreed is absent from the answer**, not present
        with three empty slots. *No plan* is what such a game draws, and one
        spelling for it is what stops a client telling an empty plan apart from a
        missing one.

        The order is not part of the demand: the list is ordered like its owner —
        newest arrangement first — and that is a fold over ``games``' own
        ``planned_at``, which belongs to the use case rather than to the store.
        """
        ...


@runtime_checkable
class AccountHoldQuery(Protocol):
    """Whether an account is under a live hold. **Asked on writes only.**

    ``docs/adr/0148`` §9: *a hold stops you writing anywhere another player sees
    it, and never stops you reading.* A slot change writes a system line into a
    room other people are in, so it is reach; but a hold must not erase an
    arrangement other people are already inside, so the read is ungated and all
    three writes are not.

    **The fourth spelling of one empty answer, and the duplication is the
    decision.** The matcher, ``challenges`` and ``conversations`` each declare a
    port of this shape against the same absent provider. On the day ``cases``
    ships, four lines in the composition root change to the same adapter.
    """

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        """Which of these players are under a live hold, right now."""
        ...


__all__ = ["AccountHoldQuery", "PlanDirectory", "PlanRepository"]
