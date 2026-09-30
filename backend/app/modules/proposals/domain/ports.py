"""What the Proposals context needs from the outside world, in its own words.

**Three ports are this context's own store**: the Proposal repository, whose
``save`` writes the pools, proposals and proposal-people projections in the
caller's transaction, the directory that reads them back, and a player's Games
& money. **The pools are a fourth**: which pools there are, and who is in each.

**The rest are demands on contexts it does not write**, each answered by an
adapter in ``infrastructure/`` over that provider's own published port, never
its table: who is in a group (groups), what a club sells at an hour, what it is
called and when its free cancellation ends (clubs), whether two people fit
(blocks, the Player profile and rating, judged by the matcher's pair rule),
whether a player has a method their share could be charged to (payments) — and,
for the deck (#539), what a card draws of a person (users, the Player profile,
rating), how even a card's game is forecast (the matcher's engine over rating),
which kinds of game a player wants (their Play intent), which games they have
booked (bookings, #541), and a club's cut-off and way of working (clubs) — and,
for the proposer (#540), where a pool may play (groups and clubs), every hour a
club sells (clubs), and each member's Level and week (rating, the Player
profile).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.scorable import LevelReading
from app.kernel import Instant, Sport, invariant
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.deck import CardForecast, SellingTerms, Sides
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.proposal import Proposal
from app.modules.proposals.domain.proposer import CourtHourOnSale, PoolClubs

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

    async def dealt_to(
        self, player_id: UUID, *, pool_id: UUID, sport: Sport, now: Instant
    ) -> Sequence[UUID]:
        """Every proposal in this pool and sport still filling that was dealt to
        this player and that they have not answered — or took their yes back
        from — **soonest first**, and by id among games at one hour. Candidates
        for their deck: the aggregate says which are cards."""
        ...


@runtime_checkable
class GamesAndMoneyRepository(Protocol):
    """A player's Games & money, one stream per player under their own id."""

    async def load(self, player_id: UUID) -> GamesAndMoney:
        """**The defaults for a player who never chose** — never ``None``."""
        ...

    async def save(self, settings: GamesAndMoney) -> None: ...


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

    async def every(self) -> Sequence[Pool]:
        """Every pool there is — a group's for every group, whether or not a
        game was proposed in it — **oldest first**. What the proposer walks."""
        ...

    async def members_of(self, pool: Pool) -> tuple[UUID, ...]:
        """Everybody in the pool now, **in the order they joined** — the order
        a tie between two equally even games is broken in."""
        ...

    async def of_player(self, player_id: UUID) -> Sequence[Pool]:
        """Every pool this player is in now."""
        ...


@runtime_checkable
class WherePoolsPlay(Protocol):
    """Where a pool may play (the mechanics §4.3) — a group's home club, and
    the clubs its games may also use."""

    async def of(self, pool: Pool, *, now: Instant) -> PoolClubs | None:
        """The clubs the pool plays at, at ``now``: a player group's home club
        and the clubs within ten kilometres of it, nearest first; an official
        group's own club, and — while the club offers its groups other clubs'
        courts — the clubs within the distance it set. ``None`` for a pool that
        no longer exists."""
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

    async def on_sale(
        self,
        club_ids: Collection[UUID],
        *,
        start: Instant,
        end: Instant,
        now: Instant,
    ) -> Sequence[CourtHourOnSale]:
        """Every hour these clubs sell from ``start`` until ``end``, one per
        club, sport and hour, with **how many courts** of the sport are free
        then — a paused club's too, marked as taking no new cards, since its
        cards keep their court. A club that is not live sells nothing, and an
        hour past its book-by at ``now`` is not for sale. In no particular
        order."""
        ...

    async def held(
        self, club_ids: Collection[UUID], *, start: Instant, end: Instant
    ) -> Collection[tuple[UUID, Sport, Instant]]:
        """Every club, sport and hour from ``start`` until ``end`` at which these
        clubs still have a court for Raketa — **whatever deadline their settings
        now give it**, since a card keeps the book-by it was made with. What a
        card loses its court hour by: an hour booked, closed or no longer
        offered is absent, and so is every hour of a club that is not live; a
        paused club's hours are held."""
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


# --------------------------------------------------------------------------- #
# The deck's demands (#539)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class DeckPerson:
    """What a card draws of one person: a **Name** and never the nickname
    (``docs/adr/0171``), a photograph, their **published** Level in the card's
    sport, and their week — which the card summarises with everybody else's and
    never shows.

    ``name`` is ``None`` for an account ``users`` can no longer name, and the
    tile is kept. ``photo_id`` and ``photo_url`` are present **exactly
    together**; neither means the client draws a poster. ``level`` is ``None``
    for somebody not rated in the sport."""

    name: str | None
    photo_id: UUID | None
    photo_url: str | None
    level: float | None
    #: Blank for somebody with no Player profile: free for nothing.
    week: WeeklyHours

    def __post_init__(self) -> None:
        invariant(
            (self.photo_id is None) == (self.photo_url is None),
            f"a photograph with only half an address: {self!r}",
        )


@runtime_checkable
class DeckPeople(Protocol):
    async def people(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, DeckPerson]:
        """Each of these players, in **one question about the union** of every
        card in a deck — never one per tile. Everybody asked about is answered."""
        ...


@runtime_checkable
class BalanceForecasts(Protocol):
    """**How even the engine forecasts a game**, for each way its people could
    stand — the Match Fit forecast a line-up and a game screen print, over the
    same Levels, never a second one."""

    async def forecasts(
        self, options: Sequence[Sides], *, sport: Sport
    ) -> Sequence[CardForecast | None]:
        """One forecast per arrangement, in their order. ``None`` where somebody
        on it holds no rating in the sport, or where a side is empty."""
        ...


@runtime_checkable
class ClubTerms(Protocol):
    """Whether each club sells, and on what terms a card at it is drawn."""

    async def of(
        self, club_ids: Collection[UUID], *, now: Instant
    ) -> Mapping[UUID, SellingTerms]:
        """Each of these clubs **selling through Raketa at ``now``** — live, and
        answered while paused, since a paused club's cards keep their court —
        with its cut-off and whether it confirms each game. A club that does not
        sell is absent: its courts reach nobody's deck (the mechanics §16.2)."""
        ...


@runtime_checkable
class BookedGames(Protocol):
    """The games a player has booked — what *games per week* and *one game per
    hour* are counted from (the mechanics §5.3, §6.6)."""

    async def starts_of(
        self, player_id: UUID, *, start: Instant, end: Instant
    ) -> Sequence[Instant]:
        """When each of this player's booked games starts, from ``start`` until
        ``end``, in no particular order."""
        ...


@final
@dataclass(frozen=True, slots=True)
class InPlay:
    """What the proposer reads of one member for one sport: their Level and
    Uncertainty — ``None`` while unrated there — and their week."""

    level: LevelReading | None
    #: Blank for somebody with no Player profile: free for nothing.
    week: WeeklyHours


@runtime_checkable
class PlayersInPlay(Protocol):
    """Each member's Level and week, for the proposer (#540) — **the engine's
    currency**, rating's estimates, as ``PlayerFit`` and the forecasts read."""

    async def of(
        self, player_ids: Collection[UUID], *, sport: Sport
    ) -> Mapping[UUID, InPlay]:
        """Each of these players, in one read per provider. Everybody asked
        about is answered."""
        ...


@runtime_checkable
class WantedKinds(Protocol):
    """Which kinds of game a player wants in a sport — their Play intent, in the
    deck's words: *competitive*, *for fun*, or both for *either*."""

    async def of(
        self, player_id: UUID, *, sport: Sport
    ) -> frozenset[SearchMode] | None:
        """``None`` while they have declared nothing for the sport — the one
        question the deck asks before it deals (the mechanics §4.1)."""
        ...
