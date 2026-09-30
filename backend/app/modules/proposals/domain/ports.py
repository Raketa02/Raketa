"""What the Proposals context needs from the outside world, in its own words.

**Two ports are this context's own store**: the aggregate repository, whose
``save`` writes the pools, proposals and proposal-people projections in the
caller's transaction, and the directory that reads them back. **The pools are a
third**: which pools there are, and who is in each.

**The other four are demands on contexts it does not write**, each answered by
an adapter in ``infrastructure/`` over that provider's own published port, never
its table: who is in a group (groups), what a club sells at an hour and what
it is called (clubs), whether two people fit (blocks, the Player profile and
rating, judged by the matcher's pair rule), and whether a player has a method
their share could be charged to (payments).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.proposal import Proposal

# --------------------------------------------------------------------------- #
# This context's own store
# --------------------------------------------------------------------------- #


@runtime_checkable
class ProposalRepository(Protocol):
    async def load(self, proposal_id: UUID) -> Proposal | None: ...

    async def save(self, proposal: Proposal) -> None:
        """Append what the aggregate recorded and write both projections, in the
        caller's transaction."""
        ...


@final
@dataclass(frozen=True, slots=True)
class LiveYes:
    """One of a player's yeses on a game that has not filled, as the
    projections hold it."""

    proposal_id: UUID
    pool_id: UUID
    sport: Sport
    kind: SearchMode
    club_id: UUID
    start: Instant
    share_grosze: int
    book_by: Instant


@runtime_checkable
class ProposalDirectory(Protocol):
    """The two projections, read. Written only by ``ProposalRepository.save``,
    so a read straight after an act already sees it.

    **Live is read against ``now``**: a proposal past its book-by is over at
    every instant, whether or not the sweep has recorded it yet, so no read
    here trusts the recorded ending alone."""

    async def live_yeses_of(
        self, player_id: UUID, *, now: Instant
    ) -> Sequence[LiveYes]:
        """Every yes of this player on a game still filling, across pools —
        **soonest game first**, and by proposal id among games at one hour."""
        ...

    async def live_yes_count(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> int:
        """How many of those are in ``sport`` — what the cap counts."""
        ...

    async def past_book_by(self, *, now: Instant) -> Sequence[UUID]:
        """Every proposal whose book-by has passed and whose ending nobody has
        recorded — **candidates, not conclusions**: the aggregate decides."""
        ...

    async def filling_in(self, pool_id: UUID, *, now: Instant) -> Sequence[UUID]:
        """Every proposal in this pool still filling, soonest first."""
        ...


@runtime_checkable
class Pools(Protocol):
    """The pools, and who is in each."""

    async def find(self, pool_id: UUID) -> Pool | None:
        """The pool with this id — a group's for a group's id, whether or not a
        proposal has been made in it yet. ``None`` for an id that is neither."""
        ...

    async def members_among(
        self, pool: Pool, player_ids: Collection[UUID]
    ) -> frozenset[UUID]:
        """Which of these players are in the pool now."""
        ...


# --------------------------------------------------------------------------- #
# Demands on contexts this one does not write
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class OfferedCourtHour:
    """A court hour a club sells through Raketa: at least one court of the
    sport is free then, at this share, until this book-by."""

    club_id: UUID
    sport: Sport
    start: Instant
    share_grosze: int
    book_by: Instant


@runtime_checkable
class CourtHours(Protocol):
    """What a club sells, in this context's words — never a court, which is
    given at booking (the mechanics §5.2)."""

    async def offered(
        self, club_id: UUID, *, sport: Sport, start: Instant, now: Instant
    ) -> OfferedCourtHour | None:
        """The hour from ``start`` at this club, if a court of ``sport`` is for
        sale then **and the club is taking new cards** — ``None`` for a club
        that is not live or is paused, and for an hour it does not sell or
        whose book-by has passed at ``now``."""
        ...


@runtime_checkable
class ClubNames(Protocol):
    async def names_of(self, club_ids: Collection[UUID]) -> Mapping[UUID, str]:
        """Each club's name. A club that does not exist is absent."""
        ...


@runtime_checkable
class PlayerFit(Protocol):
    """**Whether two people may be on one game**, as today's engine requires of
    every pair on a court (``docs/adr/0116``): neither blocked the other, each
    passes the other's gender preference, and their Levels in the sport are
    within the kind's window — narrower while either is new.

    It answers the pairs that **do not** fit and names nobody's reason: which
    rule refused a pair is not something a card may say (``docs/adr/0130``).
    **Fails closed**: a pair whose facts are missing — no profile, no rating in
    the sport — does not fit, and a block state that cannot be read raises
    rather than answering, since *unfit* would take a card away for good."""

    async def unfit_pairs(
        self,
        player_ids: Collection[UUID],
        *,
        sport: Sport,
        kind: SearchMode,
        at: Instant,
    ) -> frozenset[frozenset[UUID]]:
        """Every pair among these players that may not share a court."""
        ...


@runtime_checkable
class SavedMethods(Protocol):
    """Whether a player has a payment method their share could be charged to —
    the one fact a yes needs from payments (the mechanics §6.1)."""

    async def saved_for(self, player_id: UUID) -> bool: ...
