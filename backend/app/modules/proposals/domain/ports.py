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
booked (bookings), and a club's cut-off (clubs) — and,
for the proposer (#540), where a pool may play (groups and clubs), every hour a
club sells (clubs), and each member's Level and week (rating, the Player
profile) — and, for the fill (#541), a court for a full game and its booking
(bookings), and every seat's share, all or nothing (payments) — and, for Home
and the details (#542), a player's booked games (bookings), where each game's
result stands (games), and how far a club is from a player (the Player profile
and clubs) — and, for the club's bookings (#547), what each player is called on
the club's list of them (users) — and, for rescues (#545), a pool's booked games
with a seat open and somebody taking one (bookings), and a refused payment
waiting for its player (payments) — and, for posting (#546), each member's
gender and preference (the Player profile) and the engine's level window around
a poster (the matcher's pair rule).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.scorable import LevelReading
from app.kernel import Instant, Sport, invariant
from app.modules.player_profile.domain.gender import Gender, GenderPreference
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.club_bookings import (
    BookedFrom,
    ClubCancellation,
    CourtToMoveTo,
    Takings,
)
from app.modules.proposals.domain.deck import CardForecast, SellingTerms, Sides
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.home import (
    BookedGame,
    ClubCancelReason,
    GameResult,
    LateRefund,
    OpenSeat,
)
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.post import LevelRange
from app.modules.proposals.domain.proposal import Proposal, TimeTo
from app.modules.proposals.domain.proposer import CourtHourOnSale, PoolClubs

# --------------------------------------------------------------------------- #
# This context's own store
# --------------------------------------------------------------------------- #


@runtime_checkable
class ProposalRepository(Protocol):
    async def load(self, proposal_id: UUID) -> Proposal | None: ...

    async def load_for_update(self, proposal_id: UUID) -> Proposal | None:
        """The same proposal, **locked until the transaction ends** — the read
        before a yes, so the last two yeses on a game fill it once."""
        ...

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

    async def paused_for(self, player_id: UUID, *, now: Instant) -> Sequence[UUID]:
        """Every proposal still filling on which another booking paused this
        player's yes — **soonest first** (#544). Candidates: the aggregate says
        whether it can come back."""
        ...

    async def reopened_for(self, player_id: UUID, *, now: Instant) -> Sequence[UUID]:
        """Every proposal still filling on which this player's yes is gone and
        may come back — withdrawn, or reopened by the last yes — **soonest
        first**. Candidates: the aggregate says whose seat reopened on a payment
        to confirm."""
        ...

    async def past_book_by(self, *, now: Instant) -> Sequence[UUID]:
        """Every proposal whose book-by has passed and whose ending nobody has
        recorded, but a game waiting for its club — or for a payment, whose
        time to pay is what ends it (#625) — **candidates, not conclusions**:
        the aggregate decides."""
        ...

    async def paying_past(self, *, now: Instant) -> Sequence[UUID]:
        """Every game whose ending nobody has recorded with a time to pay up by
        ``now`` — the earliest first (#625). **Candidates**: the aggregate says
        whose time ran out."""
        ...

    async def paying_for(self, player_id: UUID) -> Sequence[UUID]:
        """Every game whose ending nobody has recorded that waits for a
        payment, with this player In — soonest first. Candidates: the
        aggregate says whether the payment awaited is theirs."""
        ...

    async def payment_awaited_of(
        self, player_id: UUID, *, since: Instant | None
    ) -> Sequence[UUID]:
        """Every game this player is In on that waited for a payment as it
        filled, and has not booked — waiting
        still, filling again, or ended before it was full again — **soonest
        first**, from the hour ``since`` (every one, with ``None``). It has no
        booking, so Home reads it from here (#625)."""
        ...

    async def owed_a_new_card_in(
        self, pool_id: UUID, *, now: Instant
    ) -> Sequence[UUID]:
        """Every booked game in this pool its club cancelled (#547), whose
        hour is still ahead, soonest first — **candidates**: the aggregate says
        which still owe their people a new card."""
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

    async def live_posts_of(self, poster_id: UUID, *, now: Instant) -> int:
        """How many of this player's posts are live: still filling — or waiting
        for their club — with the poster still In (#546; the mechanics §9.3)."""
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


#: One club, sport and hour: the key a card's court hour is read under.
CourtHourKey = tuple[UUID, Sport, Instant]


@runtime_checkable
class CourtKinds(Protocol):
    """**A demand of the Club context**: the kind of court a card promises —
    *Indoor* or *Outdoor* when it is certain, and nothing when it is not (the
    mechanics §5.2, Q122; #671). A player sees it and never chooses by it."""

    async def of(self, hours: Collection[CourtHourKey]) -> Mapping[CourtHourKey, bool]:
        """For each club, sport and hour asked, whether the free courts of the
        sport the club still has for Raketa then are **all indoor** (``True``)
        or **all outdoor** (``False``) — read as ``CourtHours.held`` reads
        them, before any deadline, since a card keeps the court hour it was
        made with. **Absent** where the free courts are of mixed kinds, and
        where no court is held: neither is a kind the card can promise."""
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

    async def level_window(
        self, player_id: UUID, *, sport: Sport, kind: SearchMode, at: Instant
    ) -> LevelRange | None:
        """**The engine's own window for the kind around this player's Level**
        — the Levels somebody may hold and pass the level rule beside them,
        narrowed while they are new — rounded inward to the hundredth (#546).
        ``None`` for somebody with no profile or no rating in the sport."""
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
    stand — the forecast a booked game's screen prints too, over the same
    Levels, never a second one."""

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
        with its cut-off. A club that does not sell is absent: its courts reach
        nobody's deck (the mechanics §16.2)."""
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
    #: Their gender and gender preference — read only for whom a post is for
    #: (#546), never said to anybody — ``None`` where it cannot be read.
    gender: Gender | None = None
    preference: GenderPreference | None = None


@runtime_checkable
class PlayersInPlay(Protocol):
    """Each member's Level and week, for the proposer (#540) — **the engine's
    currency**, rating's estimates, as ``PlayerFit`` and the forecasts read —
    and their gender and preference, for whom a post is for (#546)."""

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


# --------------------------------------------------------------------------- #
# The fill's demands (#541)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class BookableCourt:
    """The court a full game would be booked on — the first free one of its
    sport at its hour — its kind, and when the club's free cancellation ends
    for it."""

    court_id: UUID
    name: str
    #: Indoor or outdoor (#671, Q122): what the booked game shows.
    indoor: bool
    cut_off: Instant


@final
@dataclass(frozen=True, slots=True)
class FullGame:
    """A full game, every seat paid: what its booking is born with."""

    proposal_id: UUID
    pool_id: UUID
    club_id: UUID
    sport: Sport
    kind: SearchMode
    start: Instant
    share_grosze: int
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    court: BookableCourt


@runtime_checkable
class GameBookings(Protocol):
    """**A demand of the Bookings context**: a court for a full game, and the
    booking that opens its Game and its chat (the mechanics §11)."""

    async def court_for(
        self, club_id: UUID, *, sport: Sport, start: Instant
    ) -> BookableCourt | None:
        """The first free court of ``sport`` at the club from ``start``, or
        ``None`` when none is left — the card's court hour is gone."""
        ...

    async def book(self, game: FullGame, *, at: Instant) -> UUID:
        """Book it, in the caller's transaction, and answer the Game it
        opened. The booking takes the proposal's id. ``CourtJustTaken`` when
        another game claimed the court a moment before — the transaction is
        spent, and the caller tries again from the start."""
        ...


@runtime_checkable
class BookedGameChanges(Protocol):
    """**A demand of the Bookings context**: what happens to a booked game
    after the fill (#544, #545) — a player leaving it, somebody taking the seat
    they left or having one kept for them (#640), and the cut-off calling off
    one still short (the mechanics §10.1, §12.3, §13)."""

    async def leave(self, booking_id: UUID, player_id: UUID, *, at: Instant) -> None:
        """*Leave the game* (#544): this player's seat on the booked game
        opens — on its Game too, whose room they leave. Whether they may is
        the caller's question. In the caller's transaction."""
        ...

    async def rescue(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> OpenSeat:
        """*I'm in* on an open seat (#545): this player takes **the seat that
        opened first**, on its side — on the Game too, whose room they join.
        Answers whose seat it was. Whether they may, and that they paid, is
        the caller's. In the caller's transaction."""
        ...

    async def say_no_to_the_seat(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        """*Not this time* on a Seat open card (#545): it does not come back to
        their deck. Whether anything was recorded. In the caller's
        transaction."""
        ...

    async def short_at_the_cut_off(self, *, now: Instant) -> Sequence[UUID]:
        """Every booked game whose cut-off has come with a seat open since
        before it — candidates, the earliest cut-off first."""
        ...

    async def call_off_at_the_cut_off(
        self, booking_id: UUID, *, at: Instant
    ) -> tuple[UUID, ...] | None:
        """Short at its cut-off: the game is off, its court the club's again,
        its Game and room ended, the club emailed — and everybody still in
        answered. ``None`` for a game not short at its cut-off, which records
        nothing. In the caller's transaction."""
        ...

    async def card_to_fix(
        self,
        booking_id: UUID,
        player_id: UUID,
        *,
        until: Instant,
        refused: RefusedPayment,
        at: Instant,
    ) -> None:
        """This player's holding was refused (#639): the game stays booked,
        their seat theirs alone until ``until`` — their time to fix the card.
        In the caller's transaction."""
        ...

    async def card_fixed(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        """This player fixed their card in time (#639). Whether anything was
        recorded. In the caller's transaction."""
        ...

    async def card_not_fixed(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        """This player's time to fix the card ran out (#639): their seat opens
        as a leaver's — on the Game too, whose room they leave. Whether
        anything was recorded: nothing while it still runs. In the caller's
        transaction."""
        ...

    async def cards_to_fix_past(self, *, now: Instant) -> Sequence[UUID]:
        """Every booked game with a time to fix the card run out by ``now`` —
        candidates, the earliest first (#639)."""
        ...

    async def cards_to_fix_of(self, player_id: UUID) -> Sequence[UUID]:
        """Every booked game on which this player has a card to fix (#639)."""
        ...

    async def keep_the_seat(
        self,
        booking_id: UUID,
        player_id: UUID,
        *,
        until: Instant,
        refused: RefusedPayment,
        time_to: TimeTo,
        at: Instant,
    ) -> None:
        """This rescuer's share was refused (#640): a seat is kept for them
        alone until ``until`` — their time to fix the card, or to pay. In the
        caller's transaction."""
        ...

    async def kept_seat_ran_out(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> bool:
        """This rescuer's time ran out (#640): the seat kept for them is
        offered again. Whether anything was recorded: nothing while it still
        runs. In the caller's transaction."""
        ...

    async def keeps_past(self, *, now: Instant) -> Sequence[UUID]:
        """Every booked game with a seat kept for a rescuer whose time ran out
        by ``now`` — candidates, the earliest first (#640)."""
        ...

    async def kept_for(self, player_id: UUID) -> Sequence[UUID]:
        """Every booked game on which a seat was kept for this rescuer (#640),
        their time running or up — until they take one, or the game is off."""
        ...


@runtime_checkable
class PlayerNames(Protocol):
    """What each player is called — **the Name, never the nickname**
    (``docs/adr/0171``) — the one thing the club sees of a player on its
    bookings (the mechanics §16.14)."""

    async def names_of(self, player_ids: Collection[UUID]) -> Mapping[UUID, str]:
        """Each of these players' Names; an account that can no longer be named
        is absent."""
        ...


class PaymentRefusal(StrEnum):
    """Why a seat's share could not be held — the payment's own words, spelled
    here in this context's (the mechanics §12.2, §19)."""

    AUTHENTICATION_REQUIRED = "AUTHENTICATION_REQUIRED"
    DECLINED = "DECLINED"
    TERMS_NEEDED = "TERMS_NEEDED"
    NO_METHOD = "NO_METHOD"


@final
@dataclass(frozen=True, slots=True)
class RefusedPayment:
    """A seat whose share could not be held, and the charge that says so."""

    seat_charge_id: UUID
    refusal: PaymentRefusal


@final
@dataclass(frozen=True, slots=True)
class GameToCharge:
    """A full game's seats, as the payments take them."""

    proposal_id: UUID
    club_id: UUID
    sport: Sport
    start: Instant
    share_grosze: int
    court_name: str
    #: The club's cut-off, or ``None`` for a game that filled after it.
    free_to_leave_until: Instant | None
    #: One player taking an open seat on the booked game (#545), rather than
    #: every seat of a game filling.
    rescue: bool = False
    #: **Time to pay** (#625, #626): a share refused now has its seat held for
    #: its player until then, and every other hold kept for it. ``None`` lets
    #: every hold go — a rescue's, and one refused with no time left.
    pay_by: Instant | None = None
    #: The players already given time to pay, and when it ends: refused
    #: again, they keep it.
    paying_until: Mapping[UUID, Instant] = field(default_factory=dict)
    #: The game books on a payment it waited for: its receipt says *booked ·
    #: you paid*, never a second *It's a game!* (Q110) — but to the player
    #: whose payment booked it (``filled_by``), who sees *It's a game!*.
    booked_on_a_payment: bool = False
    filled_by: UUID | None = None


@final
@dataclass(frozen=True, slots=True)
class SeatsCharged:
    """Every seat taken — ``refused`` empty — or nobody paid, and ``refused``
    names whose share could not be held."""

    taken: Mapping[UUID, UUID]
    refused: Mapping[UUID, RefusedPayment]


@runtime_checkable
class SeatCharges(Protocol):
    """**A demand of the Payments context**: every seat's share, **all or
    nothing**, on the club's account — and a refused payment its player has
    since confirmed (the mechanics §12.2)."""

    async def charge(
        self,
        game: GameToCharge,
        players: Sequence[UUID],
        *,
        attempt: int,
        at: Instant,
    ) -> SeatsCharged:
        """Hold every seat, then take them all, or let every hold go — asked of
        the provider now, and recorded in the caller's transaction."""
        ...

    async def confirmed(
        self, seat_charge_id: UUID, *, player_id: UUID, at: Instant
    ) -> UUID:
        """This player says they confirmed this refused payment in the app: the
        provider is asked, the charge is recorded as held if it is, and the game
        it was for is answered. Refused as the payments refuse it otherwise."""
        ...

    async def to_confirm(self, game_id: UUID, *, player_id: UUID) -> UUID | None:
        """This player's refused payment for this game still waiting for them
        to confirm it — ``None`` when there is none (#545)."""
        ...


class RefundReason(StrEnum):
    """Why a share is given back (the mechanics §12.3) — let go while it is
    only held, refunded once taken (#637)."""

    #: The player left before the club's cut-off: their hold let go.
    LEFT_BEFORE_THE_CUT_OFF = "LEFT_BEFORE_THE_CUT_OFF"
    #: The game was called off at the club's cut-off: every hold let go.
    CALLED_OFF_AT_THE_CUT_OFF = "CALLED_OFF_AT_THE_CUT_OFF"
    #: The player left after the cut-off and somebody took their seat (#545):
    #: less exactly the fee kept on their payment (#641).
    SEAT_TAKEN = "SEAT_TAKEN"
    #: The club cancelled the booked game (#547): every hold let go before
    #: the cut-off, in full after it.
    CANCELLED_BY_THE_CLUB = "CANCELLED_BY_THE_CLUB"
    #: The club cancelled a booked game the player had left, their seat still
    #: paid (#623, Q108): in full, in a leaver's words, no new game owed.
    CANCELLED_AFTER_YOU_LEFT = "CANCELLED_AFTER_YOU_LEFT"


@runtime_checkable
class SeatRefunds(Protocol):
    """**A demand of the Payments context**: give a booked game's shares back
    (#544, #545, #637). **A share only held is let go** — nothing was taken, so
    nothing is refunded and no fee arises: a leave before the cut-off, a game
    short at it, the club's cancel before it. **A share taken is refunded** —
    less exactly the fee kept on it to a leaver whose seat somebody takes after
    the cut-off (#641); whole on a game called off at its cut-off or cancelled
    by its club."""

    async def refund(
        self,
        booking_id: UUID,
        players: Collection[UUID],
        *,
        reason: RefundReason,
        at: Instant,
        because: ClubCancelReason | None = None,
    ) -> None:
        """Give back each of these players' share of this game — let go, or
        refunded — emailing each, in the caller's transaction: the money
        follows the commit.
        ``because`` is the club's reason, on a game it cancelled — what the
        email tells the player (#547)."""
        ...

    async def left_after_the_cut_off(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> None:
        """This player left after the club's cut-off: nothing comes back yet,
        and they are emailed what will if somebody takes their seat — the share
        less exactly the fee kept on their payment, or no figure while that fee
        is not yet known (#641) — in the caller's transaction."""
        ...


@runtime_checkable
class HeldShares(Protocol):
    """**A demand of the Payments context**: the shares held for a booked game
    until its club's cut-off, which takes them (#637; ADR-0189's 2026-10-10
    amendment)."""

    async def due(self, *, at: Instant) -> Sequence[UUID]:
        """Every booked game with a share still held whose cut-off has come by
        ``at``, the earliest first."""
        ...

    async def take(self, booking_id: UUID, *, at: Instant) -> int:
        """Take every share held for this game, in the caller's transaction —
        captured at the provider after the commit. Answers how many."""
        ...


@final
@dataclass(frozen=True, slots=True)
class Holding:
    """What a booked game's holding did (#639): whose shares were held again,
    and whose were refused — each with the charge that says so."""

    held: frozenset[UUID]
    refused: Mapping[UUID, RefusedPayment]


@runtime_checkable
class CheckedShares(Protocol):
    """**A demand of the Payments context**: the shares checked at their
    game's fill, held again at their **Holding time**, four days before the
    cut-off (#639; ADR-0189's 2026-10-10 amendment) — and a refused holding
    fixed in time, or let go."""

    async def due(self, *, at: Instant) -> Sequence[UUID]:
        """Every booked game with a share checked whose Holding time has come
        by ``at`` — and one refused there for want of terms or a method, asked
        again once they are fixed — the earliest first."""
        ...

    async def hold(
        self,
        booking_id: UUID,
        *,
        fix_by: Instant,
        fixing_until: Mapping[UUID, Instant],
        at: Instant,
    ) -> Holding:
        """Hold every share of this game due — asked of the provider now, and
        recorded in the caller's transaction — each player refused emailed to
        fix their card by ``fix_by``, or by the time they have already
        (``fixing_until``)."""
        ...


@runtime_checkable
class CardsToFix(Protocol):
    """**A demand of the Payments context**: a holding refused at its Holding
    time, kept once its player fixed the card in time — or let go when that
    time runs out, nothing owed (#639)."""

    async def keep_fixed(self, seat_charge_id: UUID, *, at: Instant) -> bool:
        """A refused holding its player confirmed: kept for the game until the
        cut-off. Whether it was. In the caller's transaction."""
        ...

    async def let_go_unfixed(
        self, booking_id: UUID, player_id: UUID, *, at: Instant
    ) -> None:
        """A refused holding not fixed in time: let go, nothing owed. In the
        caller's transaction."""
        ...


@runtime_checkable
class HoldingTimes(Protocol):
    """**A demand of the Payments context**: when a share only checked at its
    game's fill is held — *held from Sat 19:00* (#639)."""

    async def of(
        self, player_id: UUID, booking_ids: Collection[UUID]
    ) -> Mapping[UUID, Instant]:
        """This player's shares only checked on these games, and each one's
        Holding time."""
        ...


@runtime_checkable
class LateRefunds(Protocol):
    """**A demand of the Payments context**: what leaving after the cut-off
    would give back, said before the player leaves (#641) — **never an
    estimate**: the fee is the provider's own, on that player's payment."""

    async def of(self, booking_id: UUID, player_id: UUID) -> LateRefund | None:
        """This player's share of this game less exactly the fee kept on it —
        ``None`` while that fee is not yet known (a club on its own negotiated
        pricing, or a take not yet captured), and for a share not taken."""
        ...


@runtime_checkable
class UndecidedCharges(Protocol):
    """**A demand of the Payments context**: let go of the charges on a game it
    will not be paid with."""

    async def release(
        self,
        proposal_id: UUID,
        *,
        keeping: Collection[UUID],
        of_player: UUID | None = None,
        at: Instant,
    ) -> None:
        """Release every charge on this game that is not taken and not one of
        ``keeping`` — only ``of_player``'s, when one is named — in the caller's
        transaction."""
        ...


# --------------------------------------------------------------------------- #
# Home and the details' demands (#542)
# --------------------------------------------------------------------------- #


@runtime_checkable
class PlayerBookings(Protocol):
    """**A demand of the Bookings context**: the games a player booked, as
    their booking records them."""

    async def of_player(
        self, player_id: UUID, *, since: Instant | None
    ) -> Sequence[BookedGame]:
        """Every booked game this player has a seat on whose hour starts at or
        after ``since`` — whenever it is, when ``since`` is ``None`` —
        **soonest first**, and by id among games at one hour. Home reads from
        an hour on (#613); a seed reads them all."""
        ...

    async def games_before(
        self, player_id: UUID, *, before: Instant
    ) -> Mapping[UUID, UUID]:
        """Each Game of a booked game this player has a seat on whose hour
        started before ``before``, to its booking — **ids alone, nothing
        folded**: what Home asks the Games context about its older games
        (#613). A booking with no Game is not here."""
        ...

    async def find(self, booking_id: UUID) -> BookedGame | None:
        """The booked game with this id, whoever is on it."""
        ...

    async def rescues_in(
        self, pool_id: UUID, *, sport: Sport, now: Instant
    ) -> Sequence[BookedGame]:
        """Every booked game in this pool and sport with a seat open and its
        hour still ahead at ``now`` — **soonest first** (#545). Candidates:
        whether a seat is there to take is ``domain/rescues.py``'s to say."""
        ...


@runtime_checkable
class GameResults(Protocol):
    """**A demand of the Games context**: where each booked game's ordinary
    Game stands, read by one of its players."""

    async def of(
        self, game_ids: Collection[UUID], *, reader: UUID, now: Instant
    ) -> Mapping[UUID, GameResult]:
        """Each of these games at ``now``, as ``reader`` reads it — one
        question about the set. A game that cannot be read is absent."""
        ...

    async def waiting_among(
        self, game_ids: Collection[UUID], *, now: Instant
    ) -> Collection[UUID]:
        """Those of these games a score may still wait for its answer on at
        ``now`` — **ids, nothing folded**, one question about the set (#613).
        Candidates: whose answer it waits on is ``of``'s to say. A correction
        re-dates its side's score, and may be made again while the other side
        has not answered, so a game long past its hour may still wait on its
        reader — this is how Home finds it."""
        ...


@runtime_checkable
class ClubDistances(Protocol):
    """How far each club is from a player — the WHERE line's *3,1 km*."""

    async def from_player(
        self, player_id: UUID, club_ids: Collection[UUID]
    ) -> Mapping[UUID, float]:
        """Each club's distance from this player's Location area, in
        kilometres as every distance on the platform is printed — one decimal,
        never below a tenth. **Empty for a player with no Location area**; a
        club that does not exist is absent."""
        ...


# --------------------------------------------------------------------------- #
# The club runs its bookings (#547)
# --------------------------------------------------------------------------- #


@runtime_checkable
class ClubBookings(Protocol):
    """**A demand of the Bookings context**: a club's bookings as its desk
    reads and runs them (the mechanics §16.7, §16.9) — a day of them, a court to
    move one to, the move and the cancel. Every act is in the caller's
    transaction, after the caller has locked the game."""

    async def on_day(
        self, club_id: UUID, *, start: Instant, end: Instant
    ) -> Sequence[BookedGame]:
        """Every booking at this club whose game starts from ``start`` until
        ``end``, whatever it came to — soonest first, and by id among games at
        one hour."""
        ...

    async def free_courts(self, booking_id: UUID) -> Sequence[CourtToMoveTo]:
        """Every other court of the game's sport the club still has for Raketa
        at its hour, in the club's order, **of a kind the players would
        accept** — the same kind, or indoor for an outdoor game (#671, Q122) —
        each with its kind."""
        ...

    async def move(
        self, booking_id: UUID, court_id: UUID, *, at: Instant
    ) -> CourtToMoveTo | None:
        """Move the game onto that court — ``None`` when it is not one of the
        free courts, a court of the wrong kind included. ``CourtJustTaken``
        when another game claimed it a moment ago."""
        ...

    async def cancel(
        self, booking_id: UUID, *, because: ClubCancelReason, at: Instant
    ) -> ClubCancellation:
        """Cancel the game, its Game and room with it — and answer whom it
        owes."""
        ...


@runtime_checkable
class BookingTakings(Protocol):
    """**A demand of the Payments context**: what each booking took from its
    players, and gave back (the mechanics §16.7) — one question about the set."""

    async def of(self, booking_ids: Collection[UUID]) -> Mapping[UUID, Takings]:
        """Each booking that took anything; one that took nothing is absent."""
        ...


@runtime_checkable
class PoolOrigins(Protocol):
    """**A demand of the Groups context**: the group each pool is — the *where
    it came from* column of the club's bookings."""

    async def of(self, pool_ids: Collection[UUID]) -> Mapping[UUID, BookedFrom]:
        """Each pool that is a group still there; one that is not is absent."""
        ...
