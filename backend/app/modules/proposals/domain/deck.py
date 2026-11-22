"""The group deck as one reader is dealt it — the rules that need no I/O (the
mechanics §6.6, §7, §8; the screens A2).

A deck is **a projection, never an aggregate** (``docs/adr/0189`` §5): every card
is a proposal read for one person at one instant. Five rules shape it.

**My card is my version** (§7): everybody In — on any version, since yeses are
the game's — then me, then the rest of my version's names for the seats still
open, **in the order they were dealt**, so the names a no left behind come
before the next best fits dealt for its seat. Somebody who took their yes back
is still named and simply not In; somebody who said no is gone. **Two people who
may not share a court are never on one card** (§4.1): a card with somebody In I
do not fit is withheld — my yes would be refused (``no_longer_fits``) — and a
name that does not fit me, somebody In or a name already on the card, who has
left the pool, or whose Play intent no longer wants the card's kind and who has
given no yes on it (Q127, ``left_the_kind``), is left off for the next one. A
name whose intent wants the kind again is on it again. A pair *In* that
stopped fitting is not mine to hide: it is the fill's to read, which lets the
later yes go (``application/fill.py``). A card that would show nobody
but me is not dealt: there is no game on it.

**A mixed pairs post keeps two of each** (#546): a card is withheld from a
reader who would be a third of their gender among the people In, a name that
would be is left off, and the sides stand a man and a woman each.

**A withdrawn yes is dealt again.** A no is final (§5.3); a yes taken back is no
verdict on the card and may be said again while it fills, and the deck is where
a card is answered — so a card I withdrew from comes back to me.

**The sides are the evenest arrangement, with me on my own** (§8.1, Q70): each
way the people on my card can stand is forecast by the engine, and the highest
forecast is drawn — a tie keeps the arrangement named first, so the answer is
the same on every process. An empty seat is one of the positions.

**A card says its kind's own number** (``docs/adr/0207`` §5, #830): a
competitive card how even its game is forecast — the forecast of my version —
and a For-fun card its table's **Social vibe** (``domain/vibe.py``), never a
forecast. The forecast still arranged a friendly's sides; it is only not said.

**The competitive order is §8.2's four keys**: seats still open after my yes,
fewest first; then a seat open, a challenge, a pick; then the soonest deadline;
then the best fit for me — **read as the forecast of my own version**, the
engine's number for how good this game is with me in it, highest first and a
card with none last. **The For-fun order opens on the best company**
(``docs/adr/0207`` §4): a rescue first, the rescues by their vibe; then every
other card by **the vibe it shows** — the rounded number, so two cards that look
alike tie — highest first and a card with none last; then the fewest seats open
after my yes, a challenge before a pick, and the soonest deadline. In either,
the cards owed to me come before everything, and then the same people are dealt
**only at their best hour** (§5.3): the first card in that order a set of people
is on is the one they are on.

**A week at the player's cap deals nothing** (§6.6, Q73), counted Monday to
Sunday on the club's clock; and neither does an hour they already have a game at
(§5.3).

**Two borrows, both pure**: the club's clock — ``CLUB_ZONE``, ``local_day`` and
``hour_start`` from ``clubs/domain/court_hours.py``, where every court hour is
read — and the grid's first hour from ``player_profile/domain/weekly_hours.py``.
A card's week and its hour are the club's, so a second spelling of either is how
a card and the hour it sells would come to disagree.
"""

from __future__ import annotations

from collections.abc import Callable, Collection, Iterable, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, timedelta
from enum import StrEnum
from typing import Final, final
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, exhaustive, hours, invariant, shifted
from app.modules.clubs.domain.court_hours import CLUB_ZONE, hour_start, local_day
from app.modules.player_profile.domain.gender import Gender
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.player_profile.domain.weekly_hours import FIRST_HOUR, WeeklyHours
from app.modules.proposals.domain.overlap import Overlap, overlap_of
from app.modules.proposals.domain.post import Who, stand_together
from app.modules.proposals.domain.proposal import Origin, Proposal, Standing
from app.modules.proposals.domain.vibe import social_vibe_of

#: How far ahead the engine deals, and so how far ahead a deck can hold a card
#: (the mechanics §4.3).
DECK_HORIZON: Final = timedelta(days=14)
#: Every game is one hour, for every sport (the mechanics §2).
GAME_LENGTH: Final = timedelta(hours=1)
_A_WEEK: Final = timedelta(days=7)


class CardType(StrEnum):
    """The three cards a deck deals (the mechanics §8.1)."""

    #: A rescue: a booked game that lost a player, dealt to its best fits (#545).
    SEAT_OPEN = "SEAT_OPEN"
    #: A member's post, dealt to a best fit.
    CHALLENGE = "CHALLENGE"
    #: A game the engine built.
    PICKED_FOR_YOU = "PICKED_FOR_YOU"


#: At the same momentum: a rescue is a real booked court losing its game, a
#: challenge is a person's own ask, a pick is the engine's suggestion (§8.2).
_TYPE_RANK: Final = {
    CardType.SEAT_OPEN: 0,
    CardType.CHALLENGE: 1,
    CardType.PICKED_FOR_YOU: 2,
}


class CourtState(StrEnum):
    """What a yes on the card does (the screens A2.3)."""

    #: A free vote: the game does not fill.
    COURT_AVAILABLE = "COURT_AVAILABLE"
    #: The yes fills the game, and books it.
    BOOK_IT_NOW = "BOOK_IT_NOW"
    #: A rescue: the court is booked, and the yes takes a seat on it and pays
    #: at once (#545).
    BOOKED = "BOOKED"


def card_type(proposal: Proposal) -> CardType:
    match proposal.origin:
        case Origin.POST:
            return CardType.CHALLENGE
        case Origin.PICK:
            return CardType.PICKED_FOR_YOU
        case _:
            exhaustive(proposal.origin)


# --------------------------------------------------------------------------- #
# Who is on my card
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class ReadersView:
    """A proposal as one reader is dealt it: who is In, the reader, and the rest
    of their version shown beside them."""

    reader: UUID
    #: Everybody In, in the order they said yes.
    in_: tuple[UUID, ...]
    #: The rest of the reader's version on the card, in the order dealt.
    others: tuple[UUID, ...]

    @property
    def people(self) -> tuple[UUID, ...]:
        return (*self.in_, self.reader, *self.others)


def anybody(people: Sequence[UUID]) -> bool:
    """Every set of people may stand on a game for anybody."""

    return True


def may_stand_on(
    proposal: Proposal, genders: Mapping[UUID, Gender | None]
) -> Callable[[Sequence[UUID]], bool]:
    """Whether a set of people may all be on this game — two of each on a
    *Mixed pairs* post, anybody on any other."""

    return lambda people: stand_together(
        proposal.who, genders, people, seats=proposal.seats
    )


def view_of(
    proposal: Proposal,
    reader: UUID,
    *,
    unfit: Collection[frozenset[UUID]],
    in_the_pool: Collection[UUID],
    now: Instant,
    may_stand: Callable[[Sequence[UUID]], bool] = anybody,
    wants: Mapping[UUID, Collection[SearchMode]] | None = None,
) -> ReadersView | None:
    """The reader's card — ``None`` for a proposal that is not in their deck:
    never dealt to them, answered by them, no longer filling or full, withheld
    for somebody In they do not fit, or showing nobody but them. ``unfit`` is
    every pair on it that may not share a court; ``may_stand`` whether a set
    of people may all be on the game — two of each on *Mixed pairs*; and
    ``wants`` the names' Play intents in the sport, where they are asked — a
    name whose intent left the card's kind holds no seat on it (Q127)."""

    version = proposal.version_of(reader)
    if (
        version is None
        or reader in proposal.yeses
        or reader in proposal.declined
        or proposal.standing_at(now) is not Standing.FILLING
        or proposal.open_seats == 0
    ):
        return None
    if any(frozenset((reader, player)) in unfit for player in proposal.yeses):
        return None
    if not may_stand((*proposal.yeses, reader)):
        return None
    seats_beside = proposal.seats - len(proposal.yeses) - 1
    on_the_card = [reader, *proposal.yeses]
    others: list[UUID] = []
    for player in version.players:
        if len(others) == seats_beside:
            break
        if (
            player in on_the_card
            or player in proposal.declined
            or player not in in_the_pool
            or (
                wants is not None
                and player in wants
                and left_the_kind(proposal, player, wants=wants[player])
            )
            or any(frozenset((player, there)) in unfit for there in on_the_card)
            or not may_stand((*on_the_card, player))
        ):
            continue
        others.append(player)
        on_the_card.append(player)
    if not proposal.yeses and not others:
        return None
    return ReadersView(reader=reader, in_=proposal.yeses, others=tuple(others))


def named_on(proposal: Proposal) -> tuple[UUID, ...]:
    """Everybody any version of the proposal names, in dealt order."""

    return tuple(player for version in proposal.versions for player in version.players)


def left_the_kind(
    proposal: Proposal, player: UUID, *, wants: Collection[SearchMode]
) -> bool:
    """Whether this name holds no seat on the game because their Play intent —
    ``wants``, empty while undeclared — no longer wants its kind (Q127;
    ``docs/adr/0201`` §3). **Never a yes already given**: somebody In, or whose
    yes a full week paused, holds their seat whatever their intent now says.
    **Only a changed intent leaves a kind**: every declared intent wants one,
    and nothing deals a card to somebody who has declared none (*may play*),
    so a name with no intent — a card made through the dealer for them — is
    never asked. **Nor is a post's poster**: Post a game is a one-off of
    whatever kind they chose (``docs/adr/0201`` §2), their yes said again
    after a withdrawal included. Read live and recorded nowhere — it is not a
    no, so a name whose intent wants the kind again is a name on the card
    again."""

    return (
        bool(wants)
        and player not in proposal.yeses
        and player not in proposal.paused
        and player != proposal.poster_id
        and proposal.kind not in wants
    )


def challenger_of(proposal: Proposal) -> UUID | None:
    """Who a challenge names — *Kuba challenged you* — and ``None`` on a pick and
    once the poster withdrew: *the group challenged you* (§8.1)."""

    if proposal.origin is Origin.POST and not proposal.poster_withdrew:
        return proposal.poster_id
    return None


# --------------------------------------------------------------------------- #
# The sides
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class Sides:
    """Which way round the people on a card stand: the reader's side, and the
    other. A side may be short of a seat."""

    yours: tuple[UUID, ...]
    theirs: tuple[UUID, ...]


@final
@dataclass(frozen=True, slots=True)
class SellingTerms:
    """What a card needs of the club it is at, while the club sells: when its
    free cancellation ends."""

    cut_off_hours: int


@final
@dataclass(frozen=True, slots=True)
class CardForecast:
    """How even the engine forecasts a card's game, as a whole percent, and
    whether a seat was assumed to match its partner to say so."""

    pct: int
    provisional: bool


def arrangements(
    reader: UUID, others: Sequence[UUID], *, seats_per_side: int
) -> tuple[Sides, ...]:
    """Every way the people on a card can stand, the reader on their own side:
    each of the others as their partner, in the card's order, and — while a seat
    is empty — the reader beside the empty one. Never a side of nobody unless
    there is nobody else at all."""

    invariant(seats_per_side >= 1, f"{seats_per_side} a side")
    if seats_per_side == 1:
        return (Sides(yours=(reader,), theirs=tuple(others)),)
    partners: list[UUID | None] = list(others)
    if len(others) < 2 * seats_per_side - 1:
        partners.append(None)
    options = tuple(
        Sides(
            yours=(reader,) if partner is None else (reader, partner),
            theirs=tuple(player for player in others if player != partner),
        )
        for partner in partners
    )
    fitting = tuple(
        option for option in options if 1 <= len(option.theirs) <= seats_per_side
    )
    return fitting or (Sides(yours=(reader,), theirs=tuple(others)),)


def standing_for(
    options: Sequence[Sides], *, who: Who | None, genders: Mapping[UUID, Gender | None]
) -> tuple[Sides, ...]:
    """The arrangements a game for ``who`` may stand in: on *Mixed pairs*, a
    man and a woman a side — never more than one of either on one — and every
    arrangement otherwise, or when none could stand so."""

    if who is not Who.MIXED_PAIRS:
        return tuple(options)
    kept = tuple(
        option
        for option in options
        if stand_together(who, genders, option.yours, seats=2)
        and stand_together(who, genders, option.theirs, seats=2)
    )
    return kept or tuple(options)


def evenest(
    options: Sequence[Sides], forecasts: Sequence[CardForecast | None]
) -> tuple[Sides, CardForecast | None]:
    """The arrangement with the highest forecast, the first among equals; the
    first arrangement and no forecast when none could be read."""

    invariant(len(options) == len(forecasts) > 0, "a forecast per arrangement")
    best: tuple[Sides, CardForecast | None] = (options[0], None)
    for option, forecast in zip(options, forecasts, strict=True):
        if forecast is not None and (best[1] is None or forecast.pct > best[1].pct):
            best = (option, forecast)
    return best


# --------------------------------------------------------------------------- #
# A card, and the order
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class DeckCard:
    """One card as its reader is dealt it."""

    proposal_id: UUID
    type: CardType
    kind: SearchMode
    #: Who a challenge names; ``None`` on a pick and once the poster withdrew.
    challenger_id: UUID | None
    club_id: UUID
    start: Instant
    share_grosze: int
    #: When the card leaves: the book-by.
    deadline: Instant
    #: Everybody In on the game, across every version.
    in_: tuple[UUID, ...]
    sides: Sides
    #: How even the game is forecast — on a competitive card; ``None`` on a
    #: For-fun one, whose sides it still arranged (``docs/adr/0207`` §5).
    forecast: CardForecast | None
    overlap: Overlap
    open_seats_after_your_yes: int
    #: How many versions the game was dealt in — more than one, and the card
    #: says how many are In on the whole game.
    version_count: int
    no_free_cancellation: bool
    #: What the club calls the court — once booked: a rescue's (#545).
    court_name: str | None = None
    #: The kind of court the card promises (the mechanics §5.2, Q122; #671):
    #: ``True`` *Indoor*, ``False`` *Outdoor* — a rescue's booked court, or
    #: every free court the card could be booked on being of one kind — and
    #: ``None`` when they are of mixed kinds, which is nothing to promise.
    indoor: bool | None = None
    #: Everybody on a rescue's booked game — each *paid* (#545); nobody on a
    #: game still filling, whose people are In.
    paid: tuple[UUID, ...] = ()
    #: The owed card for its reader (#673; the mechanics §8.2, Q123): first in
    #: their deck, until they answer it or it is gone. **Never said** — it
    #: carries no mark, for anybody.
    owed_to_you: bool = False
    #: The table's Social vibe, as the whole percent the card shows — on a
    #: For-fun card, worked out from everybody's tags now; ``None`` on a
    #: competitive one, and where the table has nothing to measure
    #: (``docs/adr/0207`` §2, §5).
    vibe: int | None = None

    @property
    def court(self) -> CourtState:
        if self.type is CardType.SEAT_OPEN:
            return CourtState.BOOKED
        if self.open_seats_after_your_yes == 0:
            return CourtState.BOOK_IT_NOW
        return CourtState.COURT_AVAILABLE

    @property
    def people(self) -> frozenset[UUID]:
        return frozenset((*self.sides.yours, *self.sides.theirs))


def headline_of(
    kind: SearchMode,
    *,
    table: Iterable[UUID],
    forecast: CardForecast | None,
    tags: Mapping[UUID, Collection[SocialTag]],
) -> tuple[CardForecast | None, int | None]:
    """What a card of this kind says about its game — its forecast and its
    vibe, one of them ``None`` (``docs/adr/0207`` §5). **Competitive** says how
    even the game is forecast; **For fun** says how much the people at the
    ``table`` share, from ``tags``, and never a forecast."""

    match kind:
        case SearchMode.COMPETITIVE:
            return forecast, None
        case SearchMode.FOR_FUN:
            return None, social_vibe_of(table, tags)
        case _:
            exhaustive(kind)


def card_of(
    proposal: Proposal,
    view: ReadersView,
    *,
    sides: Sides,
    forecast: CardForecast | None,
    weeks: Sequence[WeeklyHours],
    terms: SellingTerms,
    now: Instant,
    tags: Mapping[UUID, Collection[SocialTag]],
    indoor: bool | None = None,
) -> DeckCard:
    """The card ``view`` is of, standing as ``sides`` — ``weeks`` being the
    weeks of the people on it, whose overlap it draws on the club's clock,
    ``tags`` their Social tags now, which a For-fun card's vibe is read from
    (the table is everybody on the version), and ``indoor`` the kind of court
    it promises, when that is certain (Q122). It is owed to its reader when the
    reader is one of those it was dealt to first after a club's cancel
    (#673)."""

    shown, vibe = headline_of(
        proposal.kind, table=view.people, forecast=forecast, tags=tags
    )
    return DeckCard(
        proposal_id=proposal.proposal_id,
        type=card_type(proposal),
        kind=proposal.kind,
        challenger_id=challenger_of(proposal),
        club_id=proposal.club_id,
        start=proposal.start,
        share_grosze=proposal.share_grosze,
        deadline=proposal.book_by,
        in_=view.in_,
        sides=sides,
        forecast=shown,
        vibe=vibe,
        overlap=overlap_of(weeks, start=proposal.start, zone=CLUB_ZONE),
        open_seats_after_your_yes=proposal.open_seats - 1,
        version_count=len(proposal.versions),
        no_free_cancellation=cut_off_passed(
            proposal.start, cut_off_hours=terms.cut_off_hours, now=now
        ),
        indoor=indoor,
        owed_to_you=view.reader in proposal.owed_card_for,
    )


def _competitive_key(card: DeckCard) -> tuple[int, int, Instant, int, str]:
    """§8.2: momentum, then seat open › challenge › pick, then the deadline,
    then the best forecast."""

    # A card with no forecast after every card with one: a pct is at most 100.
    fit = -card.forecast.pct if card.forecast is not None else 1
    return (
        card.open_seats_after_your_yes,
        _TYPE_RANK[card.type],
        card.deadline,
        fit,
        str(card.proposal_id),
    )


def _for_fun_key(card: DeckCard) -> tuple[int, int, int, int, Instant, str]:
    """``docs/adr/0207`` §4: a rescue, then the vibe the card shows, then
    momentum, then challenge › pick, then the deadline. **Only a seat open on
    a booked game is a rescue** — a full game gone back to filling is dealt as
    the pick or challenge it was, and waits for its vibe."""

    rescue = 0 if card.type is CardType.SEAT_OPEN else 1
    # A card with no vibe after every card with one: a vibe is at least 0.
    company = -card.vibe if card.vibe is not None else 1
    return (
        rescue,
        company,
        card.open_seats_after_your_yes,
        _TYPE_RANK[card.type],
        card.deadline,
        str(card.proposal_id),
    )


def dealt_in_order(cards: Iterable[DeckCard]) -> tuple[DeckCard, ...]:
    """One segment's cards in its kind's order — §8.2's for Competitive, the
    best company first for For fun (``docs/adr/0207`` §4) — the same people
    only at their best hour. **One batch is one kind**, so call it per kind.
    **The cards owed to the reader come first** (#673; Q123), soonest first,
    ahead of the usual order — and so are the ones kept of the same people at
    two hours."""

    every = list(cards)
    kinds = {card.kind for card in every}
    invariant(len(kinds) <= 1, f"one segment of cards of {len(kinds)} kinds")
    order: Callable[[DeckCard], tuple[object, ...]] = (
        _for_fun_key if kinds == {SearchMode.FOR_FUN} else _competitive_key
    )
    owed = sorted(
        (card for card in every if card.owed_to_you),
        key=lambda card: (card.start, order(card)),
    )
    usual = sorted((card for card in every if not card.owed_to_you), key=order)
    seen: set[frozenset[UUID]] = set()
    dealt: list[DeckCard] = []
    for card in (*owed, *usual):
        if card.people in seen:
            continue
        seen.add(card.people)
        dealt.append(card)
    return tuple(dealt)


# --------------------------------------------------------------------------- #
# Weeks, the cut-off, and an hour already taken
# --------------------------------------------------------------------------- #


@final
@dataclass(frozen=True, slots=True)
class CappedWeek:
    """A week in which the player has as many games booked as they allow."""

    #: Its Monday, on the club's clock.
    starts_on: date
    booked: int


def week_of(at: Instant) -> date:
    """The Monday of the week ``at`` falls in, on the club's clock."""

    day = local_day(at)
    return day - timedelta(days=day.weekday())


def weeks_ahead(now: Instant) -> tuple[date, ...]:
    """Every week a card dealt now could be in: this one to the one the
    horizon ends in."""

    first, last = week_of(now), week_of(now + DECK_HORIZON)
    return tuple(
        first + _A_WEEK * index for index in range((last - first).days // 7 + 1)
    )


def week_window(weeks: Sequence[date]) -> tuple[Instant, Instant]:
    """From the first of these weeks' first court hour to the one after the
    last — every game in them, since no court hour opens before the grid does."""

    invariant(bool(weeks), "the window of no weeks")
    return hour_start(weeks[0], FIRST_HOUR), hour_start(weeks[-1] + _A_WEEK, FIRST_HOUR)


def capped_weeks(
    weeks: Sequence[date], booked: Iterable[Instant], *, games_per_week: int
) -> tuple[CappedWeek, ...]:
    counts = {week: 0 for week in weeks}
    for start in booked:
        week = week_of(start)
        if week in counts:
            counts[week] += 1
    return tuple(
        CappedWeek(starts_on=week, booked=count)
        for week, count in counts.items()
        if count >= games_per_week
    )


def hour_taken(start: Instant, booked: Iterable[Instant]) -> bool:
    """Whether the hour from ``start`` overlaps a game the player already has."""

    return any(abs(start - game) < GAME_LENGTH for game in booked)


def cut_off_of(start: Instant, *, cut_off_hours: int) -> Instant:
    """When the club's free cancellation ends for a game at ``start``:
    ``cut_off_hours`` elapsed hours before it."""

    return shifted(start, hours(-cut_off_hours))


def cut_off_passed(start: Instant, *, cut_off_hours: int, now: Instant) -> bool:
    """Whether the club's free cancellation has already ended for a game at
    ``start`` — *no free cancellation* on the card (§5.4). Elapsed hours."""

    return now >= cut_off_of(start, cut_off_hours=cut_off_hours)
