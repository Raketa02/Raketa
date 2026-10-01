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
booked (bookings), and a club's cut-off and way of working (clubs) — and,
for the proposer (#540), where a pool may play (groups and clubs), every hour a
club sells (clubs), and each member's Level and week (rating, the Player
profile) — and, for the fill (#541), a court for a full game and its booking
(bookings), and every seat's share, all or nothing (payments) — and, for Home
and the details (#542), a player's booked games and each seat's check-in code
(bookings), where each game's result stands (games), and how far a club is from
a player (the Player profile and clubs) — and, for an On request club (#543), the
request a full game is put to it as, and its answer (bookings), and what each
player is called on the club's list of them (users) — and, for rescues (#545), a
pool's booked games with a seat open and somebody taking one (bookings), and a
refused payment waiting for its player (payments).
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, final, runtime_checkable
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.engines.matchfit.scorable import LevelReading
from app.kernel import SPORT_SPECS, Instant, Minutes, Sport, invariant
from app.modules.player_profile.domain.weekly_hours import WeeklyHours
from app.modules.proposals.domain.deck import CardForecast, SellingTerms, Sides
from app.modules.proposals.domain.games_and_money import GamesAndMoney
from app.modules.proposals.domain.home import (
    BookedGame,
    CheckIn,
    GameResult,
    OpenSeat,
)
from app.modules.proposals.domain.pool import Pool
from app.modules.proposals.domain.proposal import ClubAnswer, Proposal
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

    async def live_yes_count(
        self, player_id: UUID, *, sport: Sport, now: Instant
    ) -> int:
        """How many of those are in ``sport`` — what the cap counts."""
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
        recorded, but a game waiting for its club — **candidates, not
        conclusions**: the aggregate decides."""
        ...

    async def turned_down_in(self, pool_id: UUID, *, now: Instant) -> Sequence[UUID]:
        """Every game in this pool its club turned down whose hour is still
        ahead, soonest first — **candidates**: the aggregate says which still
        owe their people a new card (#543)."""
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


# --------------------------------------------------------------------------- #
# The fill's demands (#541)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class BookableCourt:
    """The court a full game would be booked on — the first free one of its
    sport at its hour — when the club's free cancellation ends for it, and how
    long an On request club has to answer for it."""

    court_id: UUID
    name: str
    cut_off: Instant
    time_to_confirm: Minutes


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
    they left, and the cut-off calling off one still short (the mechanics
    §10.1, §12.3, §13)."""

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


# --------------------------------------------------------------------------- #
# On request (#543)
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class GameToAsk:
    """A full game at an On request club, nobody paid: what its request to the
    club holds — the court held for the answer, and the sides already drawn."""

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
    answer_by: Instant


@final
@dataclass(frozen=True, slots=True)
class ClubRequest:
    """A full game put to its On request club, as its booking records it."""

    booking_id: UUID
    club_id: UUID
    sport: Sport
    kind: SearchMode
    start: Instant
    share_grosze: int
    #: The court reserved for the answer — given to the players with the club's
    #: yes.
    court_name: str
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    cut_off: Instant
    answer_by: Instant
    #: Still waiting for the club's answer.
    waiting: bool

    @property
    def players(self) -> tuple[UUID, ...]:
        return (*self.first_side, *self.second_side)

    @property
    def price_grosze(self) -> int:
        """The court's price for the hour: every seat's share."""

        return self.share_grosze * SPORT_SPECS[self.sport].players


@runtime_checkable
class ClubRequests(Protocol):
    """**A demand of the Bookings context**: a full game put to its On request
    club, and the club's answer (the mechanics §16.3, §16.8). Every act is in
    the caller's transaction."""

    async def ask(self, game: GameToAsk, *, at: Instant) -> None:
        """Put the game to its club, holding its court — or put it again, once
        a withdrawn request's game is full again — and tell the club's desk.
        ``CourtJustTaken`` when another game claimed the court a moment
        before: the transaction is spent, and the caller tries again."""
        ...

    async def find(self, booking_id: UUID) -> ClubRequest | None:
        """The request for this game, waiting or answered — ``None`` for a
        game never put to a club."""
        ...

    async def waiting_at(self, club_id: UUID) -> Sequence[ClubRequest]:
        """Every request at this club still waiting for its answer, the one due
        first, first."""
        ...

    async def unanswered(self, *, now: Instant) -> Sequence[UUID]:
        """Every request whose answer was due by ``now`` and never came —
        candidates, the longest overdue first."""
        ...

    async def accept(self, booking_id: UUID, *, at: Instant) -> UUID:
        """The club's yes, every seat paid: the Game opens on the held court
        and the booking is booked. Answers the Game."""
        ...

    async def turn_down(
        self,
        booking_id: UUID,
        *,
        answer: ClubAnswer,
        reason: str | None,
        at: Instant,
    ) -> None:
        """Called off: refused, with the club's note, or never answered."""
        ...

    async def withdraw(
        self, booking_id: UUID, *, player_ids: tuple[UUID, ...], at: Instant
    ) -> bool:
        """These players' seats opened while the game waited: the request is
        off, and nobody keeps a seat on it. Whether one was waiting to
        withdraw."""
        ...


@runtime_checkable
class PlayerNames(Protocol):
    """What each player is called — **the Name, never the nickname**
    (``docs/adr/0171``) — the one thing the club sees of a player on a request
    (the mechanics §16.14)."""

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
    """Why a paid share is given back (the mechanics §12.3)."""

    #: The player left before the club's cut-off: less the card fee.
    LEFT_BEFORE_THE_CUT_OFF = "LEFT_BEFORE_THE_CUT_OFF"
    #: The game was called off at the club's cut-off: in full.
    CALLED_OFF_AT_THE_CUT_OFF = "CALLED_OFF_AT_THE_CUT_OFF"
    #: The player left after the cut-off and somebody took their seat (#545):
    #: less the card fee.
    SEAT_TAKEN = "SEAT_TAKEN"


@runtime_checkable
class SeatRefunds(Protocol):
    """**A demand of the Payments context**: give a booked game's paid shares
    back (#544, #545) — less the card fee to a leaver before the cut-off, and
    to one after it when somebody takes their seat; whole on a game called off
    at its cut-off."""

    async def refund(
        self,
        booking_id: UUID,
        players: Collection[UUID],
        *,
        reason: RefundReason,
        at: Instant,
    ) -> None:
        """Give back what each of these players paid for this game, emailing
        each, in the caller's transaction — the money follows the commit."""
        ...


@runtime_checkable
class CardFees(Protocol):
    """**A demand of the Payments context**: what the card fee on a share
    comes to — the estimate the *Leave the game* sheet quotes, since a leaver
    before the cut-off is refunded their share less it (#544)."""

    def card_fee_on(self, share_grosze: int) -> int: ...


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
    their booking records them, and each seat's check-in code."""

    async def of_player(self, player_id: UUID) -> Sequence[BookedGame]:
        """Every booked game this player has a seat on, whenever it is —
        **soonest first**, and by id among games at one hour."""
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

    def check_in(self, booking_id: UUID, player_id: UUID) -> CheckIn:
        """This player's code for this booking — the same on every read."""
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
