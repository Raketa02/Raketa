"""The player surface's shapes for proposals (#538, #539), and Home and the
two details a game has — booked, or still filling (#542).

**Money crosses as integer grosze**, as every price on this platform does, and
the client renders it (``docs/value-formatting.md``). A yes answers only the
seats still open, and the live-yeses list is the reader's own: **the one shape
that draws other people is the deck's card** — each by their whole nickname,
never a familiar form of it (``docs/adr/0199`` §1), their photograph and published
Level, and whether they are In. Nothing on it says who is still deciding, and
the overlap grid says how many are free together, never who.

**Codes, never sentences** (``docs/adr/0022``): *Kuba challenged you*, *Book it
now*, *no free cancellation* and *Slim overlap* are the client's words over the
codes and values here.
"""

from __future__ import annotations

from collections.abc import Collection, Mapping, Sequence
from datetime import date, datetime
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, Field

from app.engines.matchfit.core import ReliabilityBand, SearchMode
from app.kernel import Instant, Sport, instant, invariant
from app.modules.player_profile.domain.social_tags import SocialTag
from app.modules.proposals.application.answers import YesAnswer
from app.modules.proposals.application.booking_details import BookingDetails
from app.modules.proposals.application.friends_card import (
    FriendsCard,
    FriendsCourts,
    FriendsLineUpRead,
)
from app.modules.proposals.application.group_deck import DeckCounts, GroupDeck
from app.modules.friends.domain.relation import FriendRelation
from app.modules.proposals.application.friends_games import (
    FriendsGameAnswer,
    FriendsGameSent,
)
from app.modules.proposals.application.home import Home, HomeGame, HomeInvitation
from app.modules.proposals.application.live_yeses import LiveYeses, NamedLiveYes
from app.modules.proposals.application.payments_to_confirm import PaymentToConfirm
from app.modules.proposals.application.proposal_details import ProposalDetails
from app.modules.proposals.application.posting import (
    Posted,
    PostingSlot,
    PostingWeek,
    SlotFit,
)
from app.modules.proposals.application.rescues import FillIn
from app.modules.proposals.domain.deck import (
    GAME_LENGTH,
    CardForecast,
    CardType,
    CourtState,
    DeckCard,
    Sides,
)
from app.modules.proposals.domain.details import ProposalStatus, ReaderAction
from app.modules.proposals.domain.vibe import TableVibe
from app.modules.proposals.domain.friends_card import CourtForFriends
from app.modules.proposals.domain.games_and_money import (
    GAMES_PER_WEEK,
    MOST_ILL_PAY_CHOICES_GROSZE,
    GamesAndMoney,
)
from app.modules.proposals.domain.needs_your_answer import WhatIsNew
from app.modules.proposals.domain.overlap import (
    DayRange,
    Overlap,
    OverlapGrade,
    OverlapShade,
)
from app.modules.proposals.domain.home import (
    BookedGame,
    BookedMoney,
    CalledOffReason,
    ClubCancelReason,
    HomeStatus,
    LeaveTerms,
    Leaving,
    PayMode,
    SeatState,
    ShareState,
    UncountedReason,
)
from app.modules.proposals.domain.ports import (
    DeckPerson,
    HomeFriendRequest,
    HomeLevelAsk,
    HomeRanking,
    PaymentRefusal,
    Stakes,
)
from app.modules.proposals.domain.proposal import TimeTo
from app.modules.proposals.domain.post import LevelRange, Who
from app.modules.proposals.domain.posting_grid import GridCell


class BookedSchema(BaseModel):
    """The game a yes booked — *It's a game!*"""

    booking_id: UUID = Field(
        description="The booking — the same id the game had while it filled."
    )
    game_id: UUID = Field(description="The ordinary Game it opened.")


class YourPaymentSchema(BaseModel):
    """This player's share could not be held when the game filled: nobody paid,
    and their seat is open again until they confirm it or somebody takes it."""

    seat_charge_id: UUID = Field(
        description=(
            "The refused payment: `GET /seat-charges/{id}` for what the phone "
            "confirms it with, then `POST /seat-charges/{id}/confirmation`."
        )
    )
    refusal: PaymentRefusal = Field(
        description=(
            "`AUTHENTICATION_REQUIRED` — the bank wants the player to confirm; "
            "`DECLINED` — confirm with another card; `TERMS_NEEDED` — accept the "
            "terms again, then say yes; `NO_METHOD` — save a method, then say yes."
        )
    )
    confirm_by: datetime | None = Field(
        default=None,
        description=(
            "**Their time to pay** (#625, #626; Q109) — before the club's "
            "cut-off, their time to fix the card (`time_to`, #638): the seat is "
            "theirs alone until then — *Confirm your payment by 14:40 to keep "
            "your seat*, or *Fix your card by 14:40* — every other hold kept, so "
            "paying in time books the game at once. Thirty minutes from the "
            "refusal, never past the book-by (nor, to fix, the cut-off). `null` "
            "once it ran out: the seat is open to others too, and still theirs "
            "to take back while it is free. **On a rescue** (#640) the seat is "
            "kept for them alone until then — *Fix your card by 14:40 to take "
            "the seat*, or after the cut-off *Confirm your payment by 14:40* — "
            "never past the game's start; `null` when none was kept, as for a "
            "rescuer whose kept seat ran out once already."
        ),
    )
    time_to: TimeTo | None = Field(
        default=None,
        description=(
            "What the time to `confirm_by` is for (#638; Q113). `FIX_THE_CARD` "
            "— refused **before the club's cut-off**, where nothing is taken, "
            "only held: *Fix your card by 14:40 to keep your seat* — nothing is "
            "paid now, the same hold runs again once it is fixed, and the time "
            "never runs past the cut-off. `PAY` — refused from the cut-off on, "
            "where the money is taken at once: *Confirm your payment by 14:40*. "
            "`null` with `confirm_by`."
        ),
    )


class YesAnswerResponse(BaseModel):
    """What a yes left on the game — and, when it was the last, what the fill
    did."""

    proposal_id: UUID
    open_seats: int = Field(
        description=(
            "Seats nobody is In on yet, this player's yes counted. Nought on a "
            "game that booked, and on a full game waiting for one payment, whose "
            "seat is its payer's alone for their time to pay (#625)."
        )
    )
    booked: BookedSchema | None = Field(
        default=None,
        description=(
            "Present when this yes booked the game: every seat's share was held "
            "until the club's cut-off, or taken after it (#637), and the booking "
            "and its Game are open. `null` otherwise."
        ),
    )
    your_payment: YourPaymentSchema | None = Field(
        default=None,
        description=(
            "Present when **this player's** share could not be held: nobody paid "
            "and the game did not book, and their time to pay runs to "
            "`confirm_by`. `null` otherwise — including when somebody else's "
            "could not (`payment_awaited_until`)."
        ),
    )
    payment_awaited_until: datetime | None = Field(
        default=None,
        description=(
            "**This yes filled the game and a share was refused** (#625; "
            "Q110): the game waits for that payment until then — *It's a game!* "
            "with *Waiting for one payment · until 14:40 · Nobody pays until "
            "it's in*. Somebody else's, or this player's own (`your_payment`). "
            "`null` on every other answer — a rescue's refused payment too, "
            "whose seat is kept for its player alone and no game waits on it "
            "(`your_payment.confirm_by`, #640)."
        ),
    )
    money: BookedMoneySchema | None = Field(
        default=None,
        description=(
            "**The seat this answer took on a booked game** — a rescue's join, "
            "or its payment confirmed (#640; Q113): the joiner's money line, "
            "as Home reads it. `HELD` — *27 zł held until Fri 17:00*, taken at "
            "the club's cut-off (`free_to_leave_until`), and free to leave "
            "until then like everybody else; `CHECKED` — far ahead of the "
            "cut-off the card was only checked, and the share is held from "
            "`held_from`; `TAKEN` — after the cut-off, *you paid 27 zł* now. "
            "`null` on every other answer, and when the share was refused."
        ),
    )

    @classmethod
    def from_answer(cls, answer: YesAnswer) -> "YesAnswerResponse":
        booked = answer.booked
        mine = answer.your_payment
        return cls(
            proposal_id=answer.proposal_id,
            open_seats=answer.open_seats,
            booked=(
                None
                if booked is None
                else BookedSchema(booking_id=booked.booking_id, game_id=booked.game_id)
            ),
            your_payment=(
                None
                if mine is None
                else YourPaymentSchema(
                    seat_charge_id=mine.seat_charge_id,
                    refusal=mine.refusal,
                    confirm_by=(
                        answer.kept_until
                        if answer.kept_until is not None
                        else answer.paying_until
                    ),
                    time_to=answer.time_to,
                )
            ),
            payment_awaited_until=answer.paying_until,
            money=None if answer.money is None else _money(answer.money),
        )


class LiveYesClubSchema(BaseModel):
    id: UUID
    name: str | None = Field(
        description="The club's name; `null` for a club that no longer exists."
    )


class LiveYesSchema(BaseModel):
    """One yes on a game that has not filled."""

    proposal_id: UUID
    pool_id: UUID = Field(description="The pool the game was dealt in — a group's id.")
    sport: Sport
    kind: SearchMode = Field(description="Competitive, or for fun (a friendly).")
    starts_at: datetime = Field(
        description="The court hour's start. Every game is one hour."
    )
    club: LiveYesClubSchema
    share_grosze: int = Field(
        description="What this player is charged if the game fills, in grosze."
    )
    book_by: datetime = Field(
        description="The latest moment the game can fill; past it the yes lapses."
    )
    indoor: bool | None = Field(
        description=(
            "The kind of court the game promises — `true` *Indoor*, `false` "
            "*Outdoor* — when every free court it could be booked on is of "
            "that kind; `null` when they are mixed, which promises neither "
            "(Q122). The same rule as the deck card's `indoor`. Shown, never "
            "chosen by."
        )
    )

    @classmethod
    def from_named(cls, named: NamedLiveYes) -> "LiveYesSchema":
        yes = named.yes
        return cls(
            proposal_id=yes.proposal_id,
            pool_id=yes.pool_id,
            sport=yes.sport,
            kind=yes.kind,
            starts_at=yes.start,
            club=LiveYesClubSchema(id=yes.club_id, name=named.club_name),
            share_grosze=yes.share_grosze,
            book_by=yes.book_by,
            indoor=named.indoor,
        )


class LiveYesesResponse(BaseModel):
    """You › Payments' **LIVE YESES**: every yes of the reader's on a game that
    has not filled, across groups, soonest game first."""

    yeses: list[LiveYesSchema]

    @classmethod
    def from_live(cls, live: LiveYeses) -> "LiveYesesResponse":
        return cls(yeses=[LiveYesSchema.from_named(named) for named in live.yeses])


# --------------------------------------------------------------------------- #
# Games & money (#539)
# --------------------------------------------------------------------------- #


class GamesPerWeekRangeSchema(BaseModel):
    least: int
    most: int


class GamesAndMoneyRequest(BaseModel):
    """Both values, as the screen saves them on every tap. **Types only**: a
    value the form does not offer is refused by the domain, with a code naming
    what it offers."""

    games_per_week: int = Field(
        description="Games a week, Monday to Sunday, from 1 to 7."
    )
    most_ill_pay_grosze: int | None = Field(
        description=(
            "The most one game's share may cost, in grosze — one of "
            "`most_ill_pay_choices_grosze` — or `null` for *off*."
        )
    )


class GamesAndMoneyResponse(BaseModel):
    """You › Account › **Games & money**: the player's two limits, and what the
    form offers so the client holds neither range."""

    games_per_week: int = Field(
        description=(
            "Once this many games are booked in a week (Monday to Sunday), the "
            "deck deals nothing more for it."
        )
    )
    most_ill_pay_grosze: int | None = Field(
        description=(
            "Cards whose share is above this, in grosze, are never dealt; `null` "
            "is *off* — every card is shown."
        )
    )
    games_per_week_range: GamesPerWeekRangeSchema
    most_ill_pay_choices_grosze: list[int] = Field(
        description="The ceilings offered beside *Off*, in grosze."
    )

    @classmethod
    def from_settings(cls, settings: GamesAndMoney) -> "GamesAndMoneyResponse":
        least, most = GAMES_PER_WEEK
        return cls(
            games_per_week=settings.games_per_week,
            most_ill_pay_grosze=settings.most_ill_pay_grosze,
            games_per_week_range=GamesPerWeekRangeSchema(least=least, most=most),
            most_ill_pay_choices_grosze=list(MOST_ILL_PAY_CHOICES_GROSZE),
        )


# --------------------------------------------------------------------------- #
# The group deck (#539)
# --------------------------------------------------------------------------- #


class DeckTileSchema(BaseModel):
    """One person on a card."""

    player_id: UUID
    is_you: bool = Field(description="The reader's own tile.")
    nickname: str | None = Field(
        description=(
            "Their nickname, whole and never with an @ — the tile may cut it "
            "short, never invent a familiar form (`docs/adr/0199` §1). `null` "
            "for an account that can no longer be named."
        )
    )
    photo_id: UUID | None
    photo_url: str | None = Field(
        description=(
            "A short-lived link to their first photograph; `null` with `photo_id` "
            "draws a poster."
        )
    )
    level: float | None = Field(
        description="Their published Level in the card's sport; `null` if unrated."
    )
    is_in: bool = Field(
        description=(
            "They said yes: the **IN** tag. Nobody else carries a tag — a player "
            "still deciding is a plain tile."
        )
    )
    paid: bool = Field(
        description=(
            "On a `SEAT_OPEN` card, a player on the booked game — *2,75 · paid* "
            "(#545). `false` on a game still filling, and on the reader's own "
            "tile, which is the open seat."
        )
    )
    friend: bool = Field(
        description=(
            "**Your** friend — the *FRIEND* tag (`docs/adr/0202` §2). Only your "
            "own friends ever carry it: nothing here says who else is friends "
            "with whom. `false` on your own tile."
        )
    )


class DeckSidesSchema(BaseModel):
    """The rows are the sides (Q70): the reader's, and the other. A side may be
    short of a seat, which the client draws empty."""

    yours: list[DeckTileSchema]
    theirs: list[DeckTileSchema]


class DeckForecastSchema(BaseModel):
    """How even the game on **this** card is forecast to be, with these sides."""

    pct: int
    provisional: bool = Field(
        description="A seat is empty and was read as matching its partner."
    )


class DeckVibeSchema(BaseModel):
    """How much the people on **this** For-fun card share (`docs/adr/0207` §2):
    on average, each Social tag at the table is carried by `pct` percent of the
    other players. Worked out from everybody's tags now, on every read."""

    pct: int = Field(
        description=(
            "A whole percent, 0–100, rounded half up. The bar fills to it; the "
            "app words it in its own bands."
        )
    )


class OverlapCellSchema(BaseModel):
    day: int = Field(description="ISO weekday, Monday 1.")
    range: DayRange = Field(
        description="Morning 07–12, Afternoon 12–17, Evening 17–23."
    )
    shade: OverlapShade = Field(
        description=(
            "`BRIGHT` — everybody on the card is free together for a whole hour "
            "of it; `DIM` — all but one (never on a two-person card); `DARK` — "
            "fewer."
        )
    )


class OverlapGameCellSchema(BaseModel):
    """The game's own cell, ringed."""

    day: int
    range: DayRange


class DeckOverlapSchema(BaseModel):
    grade: OverlapGrade = Field(
        description=(
            "*High / Good / Slim overlap*: the hours everybody on the card "
            "shares, over the week of whoever has least to give."
        )
    )
    cells: list[OverlapCellSchema] = Field(
        description="Twenty-one: day by day from Monday, morning first."
    )
    game: OverlapGameCellSchema


class DeckClubSchema(BaseModel):
    id: UUID
    name: str | None = Field(
        description="The club's name; `null` for a club that no longer exists."
    )


class DeckChallengerSchema(BaseModel):
    """Who a challenge names — *kuba challenged you*."""

    player_id: UUID
    nickname: str | None


class DeckCardSchema(BaseModel):
    """One card, as the reader is dealt it: **their own version** of the game."""

    proposal_id: UUID = Field(
        description=(
            "The game. On a `SEAT_OPEN` card it is the **booking's** id — the same "
            "id the game had while it filled: `POST /bookings/{id}/seats` takes "
            "the seat, `POST /bookings/{id}/no` is *not this time*, and "
            "`GET /bookings/{id}` its details."
        )
    )
    type: CardType = Field(
        description=(
            "`PICKED_FOR_YOU`, `CHALLENGE` (a member's post) or `SEAT_OPEN` (a "
            "rescue: a booked game that lost a player, dealt to its best fits — "
            "#545)."
        )
    )
    kind: SearchMode
    challenger: DeckChallengerSchema | None = Field(
        description=(
            "The poster of a challenge; `null` on a pick, and on a challenge once "
            "its poster withdrew — *the group challenged you*."
        )
    )
    starts_at: datetime = Field(description="The court hour's start; games are 1 h.")
    club: DeckClubSchema
    share_grosze: int = Field(
        description=(
            "What this player pays if it fills — at once, on a `SEAT_OPEN` card."
        )
    )
    deadline: datetime = Field(
        description=(
            "When the card leaves unfilled — its book-by; on a `SEAT_OPEN` card "
            "the club's cut-off, then the start. The client counts down only "
            "under 24 h."
        )
    )
    in_count: int = Field(
        description=(
            "People In on the whole game, every version counted — nought on a "
            "`SEAT_OPEN` card, whose players have paid (`paid` on their tiles)."
        )
    )
    version_count: int = Field(
        description=(
            "Versions the game was dealt in; above one, the card says how many "
            "people are In on the whole game."
        )
    )
    open_seats_after_your_yes: int = Field(
        description="Nought is *You complete it*."
    )
    court: CourtState = Field(
        description=(
            "`COURT_AVAILABLE` — a yes is a free vote; `BOOK_IT_NOW` — a yes "
            "fills the game and books it; `BOOKED` — a rescue: the court is "
            "booked, and a yes takes the seat and pays at once."
        )
    )
    court_name: str | None = Field(
        description=(
            "What the club calls the court — *Court 6* — on a `SEAT_OPEN` card; "
            "`null` on a game still filling, which is given one at booking."
        )
    )
    indoor: bool | None = Field(
        description=(
            "The kind of court the card promises — `true` *Indoor*, `false` "
            "*Outdoor* — when every free court it could be booked on is of "
            "that kind; `null` when they are mixed, which promises neither "
            "(Q122). Shown, never chosen by. On a `SEAT_OPEN` card: the booked "
            "court's kind."
        )
    )
    no_free_cancellation: bool = Field(
        description="The club's cut-off has already passed for this game."
    )
    sides: DeckSidesSchema
    forecast: DeckForecastSchema | None = Field(
        description=(
            "How even a **competitive** card's game is forecast. **Always `null` "
            "on a `FOR_FUN` card**, which says its `vibe` instead "
            "(`docs/adr/0207` §5) — its sides are still the evenest. Also "
            "`null` where it cannot be read: somebody on the card holds no "
            "rating in the sport, or nobody faces the reader yet."
        )
    )
    vibe: DeckVibeSchema | None = Field(
        description=(
            "A **`FOR_FUN`** card's Social vibe, its table everybody named on "
            "the reader's version — the people In, the reader and the names "
            "dealt, never an empty seat — and on a `SEAT_OPEN` card the reader "
            "with the players on the game. **Always `null` on a `COMPETITIVE` "
            "card**, and where nobody at the table holds a tag (#830)."
        )
    )
    overlap: DeckOverlapSchema

    @classmethod
    def from_card(
        cls,
        card: DeckCard,
        *,
        reader: UUID,
        people: Mapping[UUID, DeckPerson],
        club_names: Mapping[UUID, str],
    ) -> "DeckCardSchema":
        return cls(
            proposal_id=card.proposal_id,
            type=card.type,
            kind=card.kind,
            challenger=_challenger(card.challenger_id, people),
            starts_at=card.start,
            club=DeckClubSchema(id=card.club_id, name=club_names.get(card.club_id)),
            share_grosze=card.share_grosze,
            deadline=card.deadline,
            in_count=len(card.in_),
            version_count=card.version_count,
            open_seats_after_your_yes=card.open_seats_after_your_yes,
            court=card.court,
            court_name=card.court_name,
            indoor=card.indoor,
            no_free_cancellation=card.no_free_cancellation,
            sides=_deck_sides(
                card.sides, reader=reader, people=people, in_=card.in_, paid=card.paid
            ),
            forecast=_forecast(card.forecast),
            vibe=_vibe(card.vibe),
            overlap=_overlap(card.overlap),
        )


def _deck_sides(
    sides: Sides,
    *,
    reader: UUID,
    people: Mapping[UUID, DeckPerson],
    in_: Collection[UUID],
    paid: Collection[UUID] = (),
) -> DeckSidesSchema:
    """A card's two rows of tiles — the deck's and a proposal's details'."""

    def tile(player_id: UUID) -> DeckTileSchema:
        person = people.get(player_id)
        return DeckTileSchema(
            player_id=player_id,
            is_you=player_id == reader,
            nickname=None if person is None else person.nickname,
            photo_id=None if person is None else person.photo_id,
            photo_url=None if person is None else person.photo_url,
            level=None if person is None else person.level,
            is_in=player_id in in_,
            paid=player_id in paid,
            friend=person is not None and person.friend,
        )

    return DeckSidesSchema(
        yours=[tile(player) for player in sides.yours],
        theirs=[tile(player) for player in sides.theirs],
    )


def _challenger(
    player_id: UUID | None, people: Mapping[UUID, DeckPerson]
) -> DeckChallengerSchema | None:
    if player_id is None:
        return None
    person = people.get(player_id)
    return DeckChallengerSchema(
        player_id=player_id, nickname=None if person is None else person.nickname
    )


def _forecast(forecast: CardForecast | None) -> DeckForecastSchema | None:
    if forecast is None:
        return None
    return DeckForecastSchema(pct=forecast.pct, provisional=forecast.provisional)


def _vibe(pct: int | None) -> DeckVibeSchema | None:
    return None if pct is None else DeckVibeSchema(pct=pct)


def _overlap(overlap: Overlap) -> DeckOverlapSchema:
    return DeckOverlapSchema(
        grade=overlap.grade,
        cells=[
            OverlapCellSchema(day=cell.day, range=cell.range, shade=cell.shade)
            for cell in overlap.cells
        ],
        game=OverlapGameCellSchema(day=overlap.game.day, range=overlap.game.range),
    )


class DeckSegmentSchema(BaseModel):
    """One side of the *Competitive · N / For fun · N* switch."""

    kind: SearchMode
    count: int = Field(description="Cards of this kind the reader is dealt here.")


class DeckCountsResponse(BaseModel):
    """How many cards each kind deals the reader now in one sport, across every
    group they are in (#739) — You › *What kind of game*'s *Your 7 competitive
    cards in your groups go*."""

    sport: Sport
    competitive: int = Field(
        description=(
            "Competitive cards, summed over the reader's groups — each group's "
            "number exactly the one its switch shows, Seat open cards included. "
            "Nought when their Play intent does not show competitive games."
        )
    )
    for_fun: int = Field(
        description=(
            "For-fun cards, summed the same way. Nought when their Play intent "
            "does not show for-fun games."
        )
    )

    @classmethod
    def from_counts(cls, counts: DeckCounts) -> "DeckCountsResponse":
        return cls(
            sport=counts.sport,
            competitive=counts.competitive,
            for_fun=counts.for_fun,
        )


class CappedWeekSchema(BaseModel):
    """A week the player has as many games booked in as they allow: nothing is
    dealt for it."""

    starts_on: date = Field(description="Its Monday, on the club's clock.")
    booked: int


class GroupDeckResponse(BaseModel):
    """A group's **Games** tab for one sport and segment."""

    pool_id: UUID
    sport: Sport
    kind: SearchMode
    segments: list[DeckSegmentSchema] = Field(
        description=(
            "The segments the reader's Play intent shows, Competitive first — "
            "**empty while they have declared no intent for the sport**, which is "
            "the one question that replaces the deck."
        )
    )
    games_badge: int = Field(
        description=(
            "The tab's badge: cards where somebody is already In with the reader, "
            "across the segments."
        )
    )
    games_per_week: int
    capped_weeks: list[CappedWeekSchema] = Field(
        description=(
            "Weeks within the deck's fortnight at the reader's games per week — "
            "*your 2 games this week are booked*. None of their games is dealt."
        )
    )
    cards: list[DeckCardSchema] = Field(
        description=(
            "This segment's cards in the order dealt. **A card owed to the "
            "reader comes first** — the new game a club's cancel owed them, "
            "soonest first among two, with no mark (#673). **Competitive**: then "
            "seats open after the reader's yes (fewest first), then seat open › "
            "challenge › pick, then the soonest deadline, then the best "
            "forecast. **For fun** (`docs/adr/0207` §4): then the `SEAT_OPEN` "
            "cards by vibe, then every other card by the vibe it shows (highest "
            "first), then seats open after the reader's yes, then challenge › "
            "pick, then the soonest deadline. In both, the same people only at "
            "their best hour."
        )
    )

    @classmethod
    def from_deck(cls, deck: GroupDeck, *, reader: UUID) -> "GroupDeckResponse":
        return cls(
            pool_id=deck.pool_id,
            sport=deck.sport,
            kind=deck.kind,
            segments=[
                DeckSegmentSchema(kind=segment.kind, count=segment.count)
                for segment in deck.segments
            ],
            games_badge=deck.games_badge,
            games_per_week=deck.games_per_week,
            capped_weeks=[
                CappedWeekSchema(starts_on=week.starts_on, booked=week.booked)
                for week in deck.capped_weeks
            ],
            cards=[
                DeckCardSchema.from_card(
                    card,
                    reader=reader,
                    people=deck.people,
                    club_names=deck.club_names,
                )
                for card in deck.cards
            ],
        )


class PaymentToConfirmSchema(BaseModel):
    """A game still filling whose last yes could not hold this player's share:
    their seat is open until they confirm the payment, or somebody takes it."""

    seat_charge_id: UUID = Field(
        description=(
            "The payment to confirm: `GET /seat-charges/{id}` for what the phone "
            "confirms it with, then `POST /seat-charges/{id}/confirmation`."
        )
    )
    refusal: PaymentRefusal = Field(
        description=(
            "`AUTHENTICATION_REQUIRED` — the bank wants the player to confirm; "
            "`DECLINED` — confirm with another card."
        )
    )
    proposal_id: UUID
    pool_id: UUID
    sport: Sport
    kind: SearchMode
    starts_at: datetime
    club: LiveYesClubSchema
    share_grosze: int
    book_by: datetime = Field(
        description="The latest moment the game can fill; past it the seat is gone."
    )
    confirm_by: datetime | None = Field(
        description=(
            "**Their time to pay** (#625, #626; Q109) — before the club's "
            "cut-off, their time to fix the card (`time_to`, #638): the seat is "
            "theirs alone until then — *Confirm your payment by 14:40*, or *Fix "
            "your card by 14:40* — and the others' holds wait for it. `null` "
            "once it ran out: the row stays, without a time, while the seat is "
            "still free to take back."
        )
    )
    time_to: TimeTo | None = Field(
        description=(
            "What the time to `confirm_by` is for (#638; Q113): `FIX_THE_CARD` "
            "before the club's cut-off — *Fix your card by 14:40*, with a line "
            "that nothing is paid now; `PAY` after it — *Confirm your payment "
            "by 14:40*. `null` with `confirm_by`."
        )
    )


class PaymentsToConfirmResponse(BaseModel):
    """*Confirm your payment to keep your seat*, every one the reader owes,
    soonest game first."""

    payments: list[PaymentToConfirmSchema]

    @classmethod
    def from_owed(
        cls, owed: Sequence[PaymentToConfirm]
    ) -> "PaymentsToConfirmResponse":
        return cls(
            payments=[
                PaymentToConfirmSchema(
                    seat_charge_id=one.seat_charge_id,
                    refusal=PaymentRefusal(one.reason.value),
                    proposal_id=one.proposal.proposal_id,
                    pool_id=one.proposal.pool.id,
                    sport=one.proposal.sport,
                    kind=one.proposal.kind,
                    starts_at=one.proposal.start,
                    club=LiveYesClubSchema(
                        id=one.proposal.club_id, name=one.club_name
                    ),
                    share_grosze=one.proposal.share_grosze,
                    book_by=one.proposal.book_by,
                    confirm_by=one.confirm_by,
                    time_to=one.time_to,
                )
                for one in owed
            ]
        )


# --------------------------------------------------------------------------- #
# Home and a booked game's details (#542)
# --------------------------------------------------------------------------- #

_HOME_STATUS = (
    "`BOOKED` — full and booked, its hour still ahead. `NEEDS_RESULT` — its hour "
    "has come and nobody has said it happened. `CONFIRM_THE_RESULT` — a score is "
    "on the table. `COUNTED` — a score is agreed. `UNCOUNTED` — they played and "
    "no score is agreed: two scores named different winners (no "
    "`uncounted_reason`), or one of the reasons `uncounted_reason` names. "
    "`PLAYED_NO_SCORE` — full at its hour, and nobody recorded it before the "
    "entry window closed: played for everybody on it, and no Level moves. "
    "`CALLED_OFF` — it will not be played; `called_off_reason` says why. "
    "`SEAT_OPEN` — somebody left and the seat is offered (`open_seats`); before "
    "the cut-off (`money.free_to_leave_until`) *fills by then or the game is off "
    "and everyone is refunded*, after it *the game goes ahead*. A game whose "
    "hour comes with a seat still open is `UNCOUNTED` with `uncounted_reason` "
    "`SEAT_EMPTY`. **`WAITING_FOR_A_PAYMENT`** (#625; Q111) — full, and one "
    "player's share was refused when it filled: *Waiting for one payment · until "
    "`payment_due_by` · Nobody pays until it's in*. Nobody paid, there is no "
    "Game and no court given, and it asks nothing of the reader (`needs_you` is "
    "`false`); to the payer it reads *Confirm your payment by "
    "`your_payment_due_by`* — *Fix your card by …* before the cut-off "
    "(`time_to`, #638) — beside their *To confirm* row. Paid in time it is "
    "`BOOKED`; out of time it is `SEAT_OPEN` with `filling_again` — and so is a "
    "game one of the others left meanwhile. **`SEAT_OPEN` with `filling_again`** "
    "(Q106) — a full game that went back to filling before it was booked: a "
    "payment it waited for did not come in time, or a seat opened while it "
    "waited — a player left, their week filled, or two players stopped fitting. "
    "Nobody paid, there is no Game and no court, and it asks nothing of the "
    "reader (`needs_you` is `false`): *1 seat open · books when it's full · "
    "nobody paid*. It is in the reader's live yeses too, where *Withdraw* "
    "(`DELETE /proposals/{id}/yes`, the same id) takes it off their Home. Full "
    "again, it reads `BOOKED`; `CALLED_OFF` if its book-by passes first. No club "
    "confirms a game: nothing on Home waits for a club's answer (#669)."
)

_PAYMENT_DUE_BY = (
    "When the payment the game waits for is due — *Waiting for one payment · "
    "until 14:40 · Nobody pays until it's in* (#625; Q111): a share was "
    "refused, and its player's seat is theirs alone until then. Never names "
    "whose payment it is. `null` unless `WAITING_FOR_A_PAYMENT`. Like "
    "`free_to_leave_until`, the line switches by itself at this instant."
)

_TIME_TO = (
    "What the time to `payment_due_by` and `your_payment_due_by` is for (#638; "
    "Q113). `FIX_THE_CARD` — the hold was refused **before the club's "
    "cut-off**, where nothing is taken, only held: the payer reads *Fix your "
    "card by 14:40 to keep your seat* — nothing is paid now — and the time "
    "never runs past the cut-off. `PAY` — refused from the cut-off on, where "
    "the money is taken at once: *Confirm your payment by 14:40*. The others "
    "read *Waiting for one payment* either way. `null` while neither is set."
)

_YOUR_PAYMENT_DUE_BY = (
    "**The reader's own** refused share and their time to pay — *Confirm your "
    "payment by 14:40*, or before the cut-off *Fix your card by 14:40* "
    "(`time_to`, #638) — while it runs, on a game waiting for it or one gone "
    "back to filling meanwhile (#625). The payment is their *To confirm* "
    "row's (`GET /players/me/payments-to-confirm`). **A rescuer whose share "
    "was refused** reads, from outside, the seat kept for them alone until "
    "then (#640) — *Fix your card by 14:40 to take the seat*, or after the "
    "cut-off *Confirm your payment by 14:40* — offered to nobody else "
    "meanwhile. `null` for everybody else, and from the moment it runs out."
)

_CALLED_OFF_REASON = (
    "Why a `CALLED_OFF` game will not be played — `null` on every other status. "
    "`BOOK_BY_PASSED` — a game that went back to filling reached its book-by "
    "before it was full again: nobody paid. `COURT_HOUR_LOST` — a game that "
    "went back to filling lost its court to another game before it was full "
    "again — or before the payment it waited for came in: nobody paid, and its "
    "players are dealt a new card first. `PAYMENT_NOT_IN_TIME` — a payment the "
    "game waited for did not come in time and it could no longer fill: the "
    "book-by had come (#625). Nobody paid. "
    "`SHORT_AT_THE_CUT_OFF` — a seat "
    "that opened before the club's cut-off was still empty at it: everybody "
    "still in is refunded in full (`money.refunded_grosze`); read off the clock "
    "from the cut-off on. `CANCELLED_BY_THE_CLUB` — the club cancelled it, "
    "with its reason (`club_cancel_reason`): everybody still in is refunded in "
    "full (`money.refunded_grosze`), it is on nobody's record, and they are "
    "dealt a new card first (#547)."
)

_CLUB_CANCEL_REASON = (
    "Why the club cancelled a `CANCELLED_BY_THE_CLUB` game — `WEATHER`, "
    "`REPAIR`, `DOUBLE_BOOKING` or `OTHER` (no reason given). `null` on every "
    "other game."
)

_UNCOUNTED_REASON = (
    "Why an `UNCOUNTED` game is uncounted with nobody disagreeing about a score "
    "— `null` otherwise. `SEAT_EMPTY` — its hour came with a seat open: "
    "somebody left after the cut-off and nobody took the seat. No Level moved, "
    "and nothing is on the record of those who stayed. `DIDNT_COME` — somebody "
    "was tapped *isn't here yet* at the court and never arrived (#657; "
    "`GET /games` — `attendance`): the game takes no score and never counts. "
    "For a day it is provisional — their *I was there*, confirmed by somebody "
    "else on the court, makes them Came late and the game carries on."
)

_OPEN_SEATS = (
    "Seats a leaver left open — the dashed tiles; nought unless `SEAT_OPEN`. "
    "The sides list the seats still held. On a game `filling_again`, the seats "
    "nobody is In on, the sides listing everybody In now."
)

_FILLING_AGAIN = (
    "A full game that went back to filling before it was booked (#625, Q106) "
    "— `SEAT_OPEN` while it fills, nobody paid; `CALLED_OFF` once its book-by "
    "passes, or its court goes, before it is full again. `false` on every "
    "booked game."
)


class BookedTileSchema(BaseModel):
    """One seat on a booked game."""

    player_id: UUID
    is_you: bool
    nickname: str | None = Field(
        description=(
            "Their nickname, whole and never with an @ — the tile may cut it "
            "short, never invent a familiar form (`docs/adr/0199` §1). `null` "
            "for an account that can no longer be named."
        )
    )
    photo_id: UUID | None
    photo_url: str | None = Field(
        description=(
            "A short-lived link to their first photograph; `null` with `photo_id` "
            "draws a poster."
        )
    )
    level: float | None = Field(
        description="Their published Level in the game's sport; `null` if unrated."
    )
    paid: bool = Field(
        description=(
            "Their share was taken — the *paid* tag. `false` while the game "
            "waits for a payment, on a game that was never booked, and on the "
            "reader's own tile when they are not on the game but offered its "
            "open seat — the dashed *You?* (#545)."
        )
    )
    friend: bool = Field(
        description=(
            "**Your** friend — the *FRIEND* tag (`docs/adr/0202` §2). Only your "
            "own friends ever carry it: nothing here says who else is friends "
            "with whom. `false` on your own tile."
        )
    )


class BookedSidesSchema(BaseModel):
    """The sides the game was booked with, **the reader's first, with them first
    on it** — *You + Piotr vs Inés + Bartek*."""

    yours: list[BookedTileSchema]
    theirs: list[BookedTileSchema]


class BookedMoneySchema(BaseModel):
    """The money line: *30 zł · free to leave until Fri 17:00* while the share
    is held, *Paid · 30 zł* once it is taken (#637; the mechanics §14.1,
    Q113)."""

    share_grosze: int = Field(description="Every seat's share, in grosze.")
    paid: bool = Field(
        description=(
            "Every seat's share was **taken** — at the club's cut-off, or at "
            "once for a game booked after it. `false` while the shares are only "
            "held (`share_state` `HELD`), and for a reader not on the game, who "
            "has paid nothing (#545)."
        )
    )
    share_state: ShareState | None = Field(
        description=(
            "`HELD` — every share is held on its card and taken at `taken_at`, "
            "the club's cut-off; leaving before it takes nothing. `CHECKED` — "
            "**the reader's** card was only checked when the game filled far "
            "ahead, and their share is held from `held_from`: *40 zł held from "
            "Sat 19:00 · taken Wed 19:00* (#639) — free to leave until the "
            "cut-off all the same. `TAKEN` — taken (`paid`). `null` while "
            "nobody's money is on the game: waiting for a payment, called off, "
            "and for a reader not on the game. Switches by "
            "itself at `held_from` and at `taken_at`."
        )
    )
    held_from: datetime | None = Field(
        description=(
            "When the reader's share is held — its Holding time, four days "
            "before the cut-off — while it is only checked and that is ahead "
            "at `read_at` (`share_state` `CHECKED`, #639). `null` on every "
            "other line."
        )
    )
    taken_at: datetime | None = Field(
        description=(
            "When the shares are taken — the club's cut-off — or were: the "
            "cut-off, or when a game booked after it was booked. Present "
            "exactly when `share_state` is."
        )
    )
    free_to_leave_until: datetime | None = Field(
        description=(
            "The club's cut-off while it is still ahead at `read_at`: leaving "
            "before it takes nothing — the hold on the card is let go — so the "
            "line says *free to leave until Fri 17:00* (Q113). `null` from the "
            "cut-off on, for a game that filled after it, for a game still "
            "waiting for its club, and for a reader not on the game. The line "
            "switches by itself at this instant."
        )
    )
    refunded_grosze: int | None = Field(
        description=(
            "What everybody still in is given back — the whole share, on a game "
            "its club cancelled after the cut-off had taken it (*refunded 30 "
            "zł*). `null` where nothing is: a game short at its cut-off, or "
            "cancelled before it, took nothing (#637)."
        )
    )


class BookedClubSchema(BaseModel):
    id: UUID
    name: str | None = Field(
        description="The club's name; `null` for a club that no longer exists."
    )


def _tile(
    player_id: UUID,
    *,
    reader: UUID,
    sport_people: Mapping[UUID, DeckPerson],
    paid: bool,
) -> BookedTileSchema:
    person = sport_people.get(player_id)
    return BookedTileSchema(
        player_id=player_id,
        is_you=player_id == reader,
        nickname=None if person is None else person.nickname,
        photo_id=None if person is None else person.photo_id,
        photo_url=None if person is None else person.photo_url,
        level=None if person is None else person.level,
        paid=paid,
        friend=person is not None and person.friend,
    )


def _booked_sides(
    sides: Sides,
    *,
    game: BookedGame,
    reader: UUID,
    people: Mapping[tuple[Sport, UUID], DeckPerson],
    paid: bool,
) -> BookedSidesSchema:
    sport_people = {
        player: person
        for (sport, player), person in people.items()
        if sport is game.sport
    }
    on_it = frozenset(game.players)
    return BookedSidesSchema(
        yours=[
            _tile(
                player,
                reader=reader,
                sport_people=sport_people,
                paid=paid and player in on_it,
            )
            for player in sides.yours
        ],
        theirs=[
            _tile(
                player,
                reader=reader,
                sport_people=sport_people,
                paid=paid and player in on_it,
            )
            for player in sides.theirs
        ],
    )


def _money(money: BookedMoney) -> BookedMoneySchema:
    return BookedMoneySchema(
        share_grosze=money.share_grosze,
        paid=money.paid,
        share_state=money.share_state,
        held_from=money.held_from,
        taken_at=money.taken_at,
        free_to_leave_until=money.free_to_leave_until,
        refunded_grosze=money.refunded_grosze,
    )


class SeatInvitationSchema(BaseModel):
    """A friend invited into an empty seat, still to answer (#752)."""

    player_id: UUID
    nickname: str | None = Field(
        description="*Piotr invited* — `null` for an account no longer named."
    )
    until: datetime = Field(
        description="When their 24 hours end, never past the cut-off or the start."
    )
    invited_by_you: bool


class FriendsSeatSchema(BaseModel):
    """One seat of a friends game, as everybody on it reads it (#751; the words
    §29.8): *In*, *waiting · 3 h left*, *can't make it*, *didn't answer*,
    *empty*, *Seat open* — and what the reader may do with it (#752)."""

    player_id: UUID = Field(
        description=(
            "Whose face it draws — the player In, the friend it is held for, or "
            "on a seat nobody holds whose it was: the friend who said no, didn't "
            "answer or left, or the sender. The reader's own, on a seat they are "
            "invited into. Their face is among `sides`."
        )
    )
    state: SeatState = Field(
        description=(
            "`IN` — somebody holds it: the sender, a friend who accepted, a "
            "rescuer. `WAITING` — held for its friend until `waiting_until`. "
            "`CANT_MAKE_IT` — they said *Not this time*. `DIDNT_ANSWER` — their "
            "24 hours ended, read off the clock whether or not the job has "
            "recorded it. `EMPTY` — the friend who accepted it left (#752). "
            "`SEAT_OPEN` — open to the group: a rescue anybody who fits may take "
            "(#752). The last four are **empty seats**, `seat_of` named."
        )
    )
    waiting_until: datetime | None = Field(
        description=(
            "With `WAITING`: when the friend's time to answer ends — 24 hours "
            "from the invitation, never past the cut-off. Count it down from "
            "`read_at`."
        )
    )
    seat_of: UUID | None = Field(
        default=None,
        description=(
            "On an empty seat: its name — `POST /bookings/{id}/seats/{seat_of}/"
            "invitations` invites a friend into it, `…/opening` opens it to the "
            "group. `null` on a seat somebody holds or is still held for."
        ),
    )
    invitations: list[SeatInvitationSchema] = Field(
        default_factory=list,
        description=(
            "Every friend invited into this empty seat and still to answer — "
            "*Piotr invited · 20 h left*. The first to accept, or the first "
            "rescue, takes the seat (#752)."
        ),
    )
    can_invite: bool = Field(
        default=False,
        description=(
            "*Invite a friend* on this seat is the reader's: In, the seat empty "
            "or open, the game still to be played — before or after the cut-off."
        ),
    )
    can_open: bool = Field(
        default=False,
        description=(
            "*Open to {group}* on this seat is the reader's: the sender, In, "
            "before the cut-off, on an empty seat not yet open — behind a "
            "confirmation that a stranger can then take it."
        ),
    )


class FriendsGameSchema(BaseModel):
    """**A friends game**'s own facts (#751; ``docs/adr/0202`` §5–§6): who sent
    it, how its court is paid, and where each seat stands."""

    sender_id: UUID = Field(description="The friend who sent it and booked the court.")
    sender_nickname: str | None = Field(
        description=(
            "Their nickname — *Tomek's game*, *Tomek paid the court*. `null` for "
            "an account that can no longer be named."
        )
    )
    you_are_the_sender: bool
    pay_mode: PayMode = Field(
        description=(
            "`SPLIT_THE_COST` — each friend pays their own share on accepting, "
            "and the sender's card covers every seat still without its own "
            "payment at the cut-off (*Split*). `WHOLE_COURT` — the sender pays "
            "every seat; friends accept free (*Tomek paid the court*)."
        )
    )
    seats: list[FriendsSeatSchema] = Field(
        description="Every seat: the sender's first, then each friend's in the "
        "card's order."
    )
    friends_in: int = Field(
        description="The friends In beside the sender — *2 of 3 friends in*."
    )
    friends_seated: int = Field(
        description="The friends the sport seats beside the sender: 3 in doubles, "
        "1 in singles."
    )
    your_invitation_until: datetime | None = Field(
        description=(
            "**The reader's own invitation**, while it waits on them: when it "
            "ends. `POST /bookings/{id}/invitation/acceptance` accepts it, "
            "`…/invitation/decline` is *Not this time*. `null` for the sender, "
            "for a friend In, and once it was answered or ran out."
        )
    )
    can_call_off: bool = Field(
        description=(
            "*Call it off* is the reader's — the sender, before the club's "
            "cut-off and the hour: `POST /bookings/{id}/call-off`."
        )
    )

    @classmethod
    def of(
        cls,
        game: BookedGame,
        *,
        reader: UUID,
        people: Mapping[tuple[Sport, UUID], DeckPerson],
        read_at: datetime,
    ) -> "FriendsGameSchema | None":
        if game.sender is None or game.pay_mode is None:
            return None
        now = instant(read_at)
        seats = game.seat_states(now=now, reader=reader)
        invited = game.invited_now(reader, now=now)
        sender = people.get((game.sport, game.sender))
        may_invite = game.may_invite(reader, now=now)

        def named(player: UUID) -> str | None:
            person = people.get((game.sport, player))
            return None if person is None else person.nickname

        return cls(
            sender_id=game.sender,
            sender_nickname=None if sender is None else sender.nickname,
            you_are_the_sender=game.sender == reader,
            pay_mode=game.pay_mode,
            seats=[
                FriendsSeatSchema(
                    player_id=seat.player_id,
                    state=seat.state,
                    waiting_until=seat.until,
                    seat_of=seat.seat_of,
                    invitations=[
                        SeatInvitationSchema(
                            player_id=one.player_id,
                            nickname=named(one.player_id),
                            until=one.until,
                            invited_by_you=one.invited_by == reader,
                        )
                        for one in seat.invitations
                    ],
                    can_invite=may_invite and seat.seat_of is not None,
                    can_open=game.may_open(reader, seat, now=now),
                )
                for seat in seats
            ],
            friends_in=sum(
                1
                for seat in seats
                if seat.state is SeatState.IN and seat.player_id != game.sender
            ),
            friends_seated=len(seats) - 1,
            your_invitation_until=None if invited is None else invited.until,
            can_call_off=game.may_be_called_off_by(reader, now=now),
        )


class HomeFriendsGameSchema(BaseModel):
    """One card in **FRIENDS GAME · n** (#751; mock 12): *Tomek's game*, the
    clock, the four faces — ✓ on those In — *Saturday 10:00 · Ogrody 33 ·
    Court 3 · Padel · Competitive*, and **Not this time** / **Accept and pay 25
    zł** (*Whole court*: **Accept**, *Tomek paid the court*)."""

    booking_id: UUID = Field(
        description="The friends game. `GET /bookings/{id}` for its details."
    )
    pool_id: UUID = Field(description="The group it belongs to — a group's id.")
    sport: Sport
    kind: SearchMode = Field(description="The sender's choice for this game.")
    starts_at: datetime
    club: BookedClubSchema
    court_name: str
    indoor: bool
    share_grosze: int = Field(
        description="Each seat's share — *Accept and pay 25 zł* with *Split*."
    )
    sides: BookedSidesSchema = Field(
        description=(
            "Every seat the card drew, the reader's side first and the reader "
            "first on it. `friends_game.seats` says who is In."
        )
    )
    friends_game: FriendsGameSchema

    @classmethod
    def from_invitation(
        cls,
        invitation: HomeInvitation,
        *,
        reader: UUID,
        people: Mapping[tuple[Sport, UUID], DeckPerson],
        read_at: datetime,
    ) -> "HomeFriendsGameSchema":
        game = invitation.game
        friends_game = FriendsGameSchema.of(
            game, reader=reader, people=people, read_at=read_at
        )
        assert friends_game is not None
        return cls(
            booking_id=game.booking_id,
            pool_id=game.pool_id,
            sport=game.sport,
            kind=game.kind,
            starts_at=game.start,
            club=BookedClubSchema(id=game.club_id, name=invitation.club_name),
            court_name=game.court_name,
            indoor=game.indoor,
            share_grosze=game.share_grosze,
            sides=_booked_sides(
                # A friend invited into an empty seat is drawn in it (#752).
                game.seen_by(reader, now=instant(read_at)),
                game=game,
                reader=reader,
                people=people,
                paid=False,
            ),
            friends_game=friends_game,
        )


class HomeGameSchema(BaseModel):
    """One card on Home: a game the reader booked."""

    booking_id: UUID = Field(
        description=(
            "The booking — the same id the game had while it filled. "
            "`GET /bookings/{id}` for its details."
        )
    )
    game_id: UUID | None = Field(
        description=(
            "The ordinary Game it opened: the result is told and agreed on "
            "`/games/{id}/result`, and its room in `GET /conversations` carries "
            "this id. `null` on a game that waited for a payment and was never "
            "booked — there is no Game, and no room."
        )
    )
    pool_id: UUID = Field(description="The pool it filled in — a group's id.")
    sport: Sport
    kind: SearchMode = Field(description="Competitive, or for fun (a friendly).")
    status: HomeStatus = Field(description=_HOME_STATUS)
    called_off_reason: CalledOffReason | None = Field(description=_CALLED_OFF_REASON)
    club_cancel_reason: ClubCancelReason | None = Field(
        description=_CLUB_CANCEL_REASON
    )
    uncounted_reason: UncountedReason | None = Field(description=_UNCOUNTED_REASON)
    open_seats: int = Field(description=_OPEN_SEATS)
    needs_you: bool = Field(
        description=(
            "One of the games that need the reader: a result to enter, the other "
            "side's score waiting on their agreement, or a seat open in their "
            "booked game — never a game `filling_again`, which asks nothing of "
            "them."
        )
    )
    filling_again: bool = Field(description=_FILLING_AGAIN)
    starts_at: datetime = Field(description="The court hour's start; games are 1 h.")
    club: BookedClubSchema
    court_name: str | None = Field(
        description=(
            "What the club calls the court — *Court 2*. `null` on a game that "
            "was never booked, which no court was given."
        )
    )
    indoor: bool | None = Field(
        description=(
            "The court's kind — *Court 2 · indoor* — which follows a move "
            "(Q122). `null` with `court_name`."
        )
    )
    sides: BookedSidesSchema
    money: BookedMoneySchema
    payment_due_by: datetime | None = Field(description=_PAYMENT_DUE_BY)
    your_payment_due_by: datetime | None = Field(description=_YOUR_PAYMENT_DUE_BY)
    time_to: TimeTo | None = Field(description=_TIME_TO)
    friends_game: FriendsGameSchema | None = Field(
        description=(
            "A friends game's own facts (#751) — the sender's game in Your "
            "games, *2 of 3 friends in · waiting for Ania*, and a friend's once "
            "they accepted. `null` on a game a fill booked."
        )
    )

    @classmethod
    def from_card(
        cls,
        card: HomeGame,
        *,
        reader: UUID,
        people: Mapping[tuple[Sport, UUID], DeckPerson],
        read_at: datetime,
    ) -> "HomeGameSchema":
        game = card.game
        yours = _yours_due_by(game, reader, read_at=read_at)
        return cls(
            booking_id=game.booking_id,
            game_id=game.game_id,
            pool_id=game.pool_id,
            sport=game.sport,
            kind=game.kind,
            status=card.state.status,
            called_off_reason=card.state.called_off,
            club_cancel_reason=card.state.cancel_reason,
            uncounted_reason=card.state.uncounted,
            open_seats=game.open_seats,
            needs_you=card.state.needs_you,
            filling_again=game.filling_again,
            starts_at=game.start,
            club=BookedClubSchema(id=game.club_id, name=card.club_name),
            court_name=game.court_name if game.court_given else None,
            indoor=game.indoor if game.court_given else None,
            sides=_booked_sides(
                game.seen_by(reader),
                game=game,
                reader=reader,
                people=people,
                paid=card.state.money.paid,
            ),
            money=_money(card.state.money),
            payment_due_by=card.state.pay_by,
            your_payment_due_by=yours,
            time_to=_time_to(
                game, card.state.pay_by, yours, reader=reader, read_at=read_at
            ),
            friends_game=FriendsGameSchema.of(
                game, reader=reader, people=people, read_at=read_at
            ),
        )


def _yours_due_by(
    game: BookedGame, reader: UUID, *, read_at: datetime
) -> datetime | None:
    """The reader's own time to pay, while it runs — or, a rescuer whose share
    was refused, the seat kept for them (#640)."""

    kept = game.kept_for(reader, now=instant(read_at))
    if kept is not None:
        return kept.until
    until = game.paying.get(reader)
    return until if until is not None and read_at < until else None


def _time_to(
    game: BookedGame, *due: datetime | None, reader: UUID, read_at: datetime
) -> TimeTo | None:
    """What a payment due on the game is for — with either of its moments,
    never without (#638); the reader's own, a seat kept for them (#640)."""

    if not any(one is not None for one in due):
        return None
    kept = game.kept_for(reader, now=instant(read_at))
    return kept.time_to if kept is not None else game.time_to


class HomeFriendRequestGroupSchema(BaseModel):
    id: UUID
    name: str


class HomeFriendRequestLevelSchema(BaseModel):
    """One sport on a request's sport-levels line — *● Padel 3,40*."""

    sport: Sport
    level: float = Field(
        description="Their published Level in it, as RacketSkill published it."
    )


class HomeFriendRequestSchema(BaseModel):
    """One card in *FRIEND REQUESTS* — *Inés wants to be your friend · With you
    in Kazimierz crew · Padel 3,40 · ✦ 98*, **Not now** and **Accept**."""

    player_id: UUID = Field(
        description=(
            "Who asked. `POST /friends/requests/{player_id}/acceptance` accepts, "
            "`…/set-aside` is **Not now**."
        )
    )
    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    photo_id: UUID | None
    photo_url: str | None = Field(
        description="A short-lived link to their first photograph; `null` with "
        "`photo_id` draws initials."
    )
    asked_at: datetime
    by_link: bool = Field(
        description=(
            "Made by their Friend link: draw *Invited you to Raketa* in place of "
            "the group line."
        )
    )
    from_ranking: bool = Field(
        description=(
            "Made from your record on the Rankings page: draw *Found you in the "
            "padel ranking* — `sport`'s ranking — in place of the group line, "
            "whether or not you share a group (#773)."
        )
    )
    from_new_players: bool = Field(
        description=(
            "Made from Home's *New in Raketa* row, or a record opened from it: "
            "draw *Found you among new players* in place of the group line "
            "(#793)."
        )
    )
    from_same_level: bool = Field(
        description=(
            "Made from Home's *Same competitive level players* row, or a record "
            "opened from it, in `sport` (#794): draw *Your level in padel · 91% "
            "even* — `percent_even` — in place of the group line, or *Found you "
            "at your padel level* when `percent_even` is `null`."
        )
    )
    from_same_vibe: bool = Field(
        description=(
            "Made from Home's *Same vibe players* row, or a record opened from "
            "it (#795): draw *6 things in common* — `in_common`; *1 thing in "
            "common* for one — in place of the group line, or *Found you through "
            "your tags* when `in_common` is `0`."
        )
    )
    group: HomeFriendRequestGroupSchema | None = Field(
        description=(
            "The group they asked from — *With you in Kazimierz crew* — **while "
            "you are both in it**. `null` for a link's request, for one asked "
            "from a screen that showed no group, and once either of you left."
        )
    )
    sport: Sport | None = Field(
        description="The sport of the screen they asked from, if it showed one."
    )
    level: float | None = Field(
        description=(
            "Their published Level in `sport` — *Padel 3,40*. `null` with no "
            "sport, or when they hold no Level in it."
        )
    )
    player_score: int = Field(
        ge=0,
        le=100,
        description="Their Player reliability in points — the chip's *✦ 98*.",
    )
    reliability_band: ReliabilityBand = Field(
        description="The band of that figure, the code their record serves."
    )
    percent_even: int | None = Field(
        ge=0,
        le=100,
        description=(
            "With `from_same_level`: **today's** % even between you two in "
            "`sport` — the app's Forecast with one player a side, worked out on "
            "this read. `null` once either of you holds no level there, and on "
            "every other card."
        ),
    )
    in_common: int | None = Field(
        ge=0,
        description=(
            "With `from_same_vibe`: how many Social tags you two hold **today**, "
            "counted on this read — `0` once you share none. `null` on every "
            "other card."
        ),
    )
    levels: list[HomeFriendRequestLevelSchema] = Field(
        description=(
            "**Every sport they hold a published Level in**, in the app's sport "
            "order, each with that Level — the tile's sport-levels line, *● Padel "
            "3,40 · ● Tennis 2,90* (docs/adr/0205 §2). **Empty** when they hold "
            "none, and the line is left out. `level` is the entry for `sport`."
        )
    )

    @classmethod
    def of(cls, request: HomeFriendRequest) -> "HomeFriendRequestSchema":
        return cls(
            player_id=request.requester_id,
            nickname=request.nickname,
            photo_id=request.photo_id,
            photo_url=request.photo_url,
            asked_at=request.asked_at,
            by_link=request.by_link,
            from_ranking=request.from_ranking,
            from_new_players=request.from_new_players,
            from_same_level=request.from_same_level,
            from_same_vibe=request.from_same_vibe,
            group=None
            if request.group_id is None or request.group_name is None
            else HomeFriendRequestGroupSchema(
                id=request.group_id, name=request.group_name
            ),
            sport=request.sport,
            level=request.level,
            player_score=request.reliability_points,
            reliability_band=request.reliability_band,
            percent_even=request.percent_even,
            in_common=request.in_common,
            levels=[
                HomeFriendRequestLevelSchema(sport=one.sport, level=one.level)
                for one in request.levels
            ],
        )


class HomeLevelAskerSchema(BaseModel):
    """One friend on an *ASKED FOR A LEVEL* card — a face that opens their
    record."""

    player_id: UUID
    nickname: str = Field(description="Whole, never with an @ (docs/adr/0199 §1).")
    photo_id: UUID | None
    photo_url: str | None = Field(
        description="A short-lived link to their first photograph; `null` with "
        "`photo_id` draws initials."
    )


class HomeLevelAskSchema(BaseModel):
    """One card in *ASKED FOR A LEVEL* — *kuba.w and tomek.k want to play padel
    with you* / *A few questions, and they can add you to a game.*, **Get your
    padel level** and **Not now** (#764; `docs/adr/0202` §4's 2026-11-07
    amendment). It names no group."""

    sport: Sport = Field(
        description=(
            "The sport they asked you to get a level in — one you hold none in. "
            "**Get your {sport} level** starts its questionnaire; "
            "`POST /friends/level-asks/{sport}/set-aside` is **Not now**."
        )
    )
    askers: list[HomeLevelAskerSchema] = Field(
        description=(
            "Every friend whose ask in this sport waits on you, **newest "
            "first** — never empty. Name two and count the rest; draw up to "
            "three faces."
        )
    )

    @classmethod
    def of(cls, ask: HomeLevelAsk) -> "HomeLevelAskSchema":
        return cls(
            sport=ask.sport,
            askers=[
                HomeLevelAskerSchema(
                    player_id=asker.player_id,
                    nickname=asker.nickname,
                    photo_id=asker.photo_id,
                    photo_url=asker.photo_url,
                )
                for asker in ask.askers
            ],
        )


class HomeRankingSchema(BaseModel):
    """Home's trophy, **🏆 #7**, just left of the bell (#768, #771;
    `docs/adr/0203` §5). A tap opens Rankings on `sport`, in the view you last
    looked at."""

    sport: Sport = Field(
        description=(
            "The sport of your latest confirmed competitive result, in any "
            "sport — after a tennis win, tennis."
        )
    )
    general_place: int | None = Field(
        ge=1,
        description=(
            "Your place on General in `sport` — `null` when you aren't listed "
            "there (fewer than 5 results, or none in the last 90 days), and the "
            "trophy draws no number."
        ),
    )
    friends_place: int | None = Field(
        ge=1,
        description=(
            "Your place among your friends in `sport` — `null` when you aren't "
            "listed there (no result in the last 90 days), and when no friend "
            "of yours is (*Just you so far*), and the trophy draws no number. "
            "The trophy shows the place of the view you last looked at on "
            "Rankings, General the first time."
        ),
    )

    @classmethod
    def of(cls, ranking: HomeRanking) -> "HomeRankingSchema":
        return cls(
            sport=ranking.sport,
            general_place=ranking.general_place,
            friends_place=ranking.friends_place,
        )


class HomeNeedsYourAnswerSchema(BaseModel):
    """**The envelope's badge** (#815; `docs/adr/0205` §3): what is new in
    *Needs your answer* since you last closed it, kept on the server so every
    phone agrees — and the watermark to send back when you close it."""

    new_count: int = Field(
        description=(
            "How many of the items waiting on you **arrived since you last "
            "closed Needs your answer** (`POST /players/me/needs-your-answer/"
            "visit`), on any phone — every one of them before your first close. "
            "Counted over the four sections: each payment to confirm "
            "(`payments_to_confirm`) by when it came to need confirming, each "
            "friends game invitation by when your seat was "
            "invited into, each friend request by when it was asked, and **each "
            "friend on an ask for a level by their own ask** — so a second "
            "friend asking on a card already there is new. **A change of state "
            "is never new**: a payment going from *Fix your card* to *Confirm* "
            "counts as it did. An answered item leaves the count with its "
            "section. Draw *99+* above 99. Never `needing_you`, never the bell's "
            "number."
        )
    )
    watermark: datetime | None = Field(
        description=(
            "**This read's watermark**: the newest arrival among everything "
            "counted above, seen or not, to the millisecond. Send it back as the "
            "visit's `watermark` when the sheet drawn from this read closes — "
            "draw all four sections from this read (`payments_to_confirm` "
            "included), or a row read elsewhere may be covered without being "
            "shown. `null` while nothing waits."
        )
    )

    @classmethod
    def of(cls, new: WhatIsNew) -> "HomeNeedsYourAnswerSchema":
        return cls(new_count=new.count, watermark=new.watermark)


class NeedsYourAnswerVisitRequest(BaseModel):
    """Closing *Needs your answer* (#815): the watermark of the read the sheet
    showed."""

    watermark: AwareDatetime | None = Field(
        description=(
            "`GET /home`'s `needs_your_answer.watermark` from the read the sheet "
            "was last drawn from, as it was served — never the phone's clock, "
            "never the moment of the close. Compared to the millisecond, so a "
            "date that kept only milliseconds is the same watermark. `null`, a "
            "read with nothing waiting, records nothing."
        )
    )


class HomeResponse(BaseModel):
    """**Home**: the reader's games from the moment they fill, and the friend
    requests, friends game invitations and asks for a level waiting on them."""

    read_at: datetime = Field(
        description=(
            "The instant every status and money line here was folded against. "
            "Switch a card's line at `free_to_leave_until` from this clock."
        )
    )
    needing_you: int = Field(
        description=(
            "Home's badge — the games that need the reader: the cards with "
            "`needs_you`, and every payment they have to confirm "
            "(`GET /players/me/payments-to-confirm`), a game still filling whose "
            "seat is theirs until somebody else takes it."
        )
    )
    games: list[HomeGameSchema] = Field(
        description=(
            "The reader's booked games — and their full games waiting for one "
            "payment, or gone back to filling — **soonest first**, and only what "
            "Home draws: **every live game** (waiting for a payment, booked, with "
            "a seat open, waiting on its result or on an answer to a score), "
            "**every game that ended less than a day after its hour's end**, and "
            "**any game that needs the reader** (`needs_you`). "
            "Nothing older is sent; its details (`GET /bookings/{id}`) still read "
            "it. A game a Classic play challenge opened is not here."
        )
    )
    friend_requests: list[HomeFriendRequestSchema] = Field(
        description=(
            "*FRIEND REQUESTS · n* — the requests waiting on you, **newest "
            "first** (`docs/adr/0202` §1). A card leaves once you accept it, say "
            "**Not now**, or they cancel; the row and its title are gone when "
            "this is empty. They are not counted in `needing_you`."
        )
    )
    friends_games: list[HomeFriendsGameSchema] = Field(
        description=(
            "*FRIENDS GAME · n*, at the very top of Home (#751; "
            "`docs/adr/0202` §5): every friends game whose invitation waits on "
            "you, **the soonest to end first**. A card leaves once you accept — "
            "the game is then among `games` — say **Not this time**, or your 24 "
            "hours end; the row and its title are gone when this is empty. Not "
            "counted in `needing_you`."
        )
    )
    level_asks: list[HomeLevelAskSchema] = Field(
        description=(
            "*ASKED FOR A LEVEL · n*, between `friend_requests` and `games` "
            "(#764; `docs/adr/0202` §4's 2026-11-07 amendment): **one card per "
            "sport**, the sport with the newest ask first — every friend's ask "
            "for a level still waiting on you. A card leaves once you hold any "
            "level in its sport, by any route, or say **Not now**, and an asker "
            "leaves it once no longer your friend or blocked by you; a new "
            "friend's ask in the sport brings it back, naming only the askers "
            "you have not set aside. It never expires. The row and its title are "
            "gone when this is empty. Not counted in `needing_you`."
        )
    )
    ranking: HomeRankingSchema | None = Field(
        default=None,
        description=(
            "The trophy left of the bell (#768): the sport of your latest "
            "result and your General place in it. **`null` when you have no "
            "result in any sport** — the trophy still shows, with no number, "
            "and still opens Rankings."
        ),
    )
    payments_to_confirm: list[PaymentToConfirmSchema] = Field(
        description=(
            "*TO CONFIRM · n*, first in *Needs your answer* (#815; "
            "`docs/adr/0205` §1, §3): every payment you have to confirm, soonest "
            "game first — **the same rows as `GET /players/me/payments-to-"
            "confirm`**, read at this read's instant. They are the payments "
            "`needing_you` counts and `needs_your_answer` covers, so a sheet "
            "drawn from this read alone shows exactly what its watermark says "
            "it showed."
        )
    )
    needs_your_answer: HomeNeedsYourAnswerSchema = Field(
        description=(
            "The envelope's badge, left of the bell (#815; `docs/adr/0205` §2, "
            "§3): what is new in *Needs your answer*, and the watermark of this "
            "read."
        )
    )

    @classmethod
    def from_home(cls, home: Home, *, reader: UUID) -> "HomeResponse":
        return cls(
            read_at=home.read_at,
            needing_you=home.needing_you,
            payments_to_confirm=PaymentsToConfirmResponse.from_owed(
                home.payments_to_confirm
            ).payments,
            needs_your_answer=HomeNeedsYourAnswerSchema.of(home.needs_your_answer),
            friend_requests=[
                HomeFriendRequestSchema.of(request) for request in home.friend_requests
            ],
            friends_games=[
                HomeFriendsGameSchema.from_invitation(
                    invitation,
                    reader=reader,
                    people=home.people,
                    read_at=home.read_at,
                )
                for invitation in home.friends_games
            ],
            level_asks=[HomeLevelAskSchema.of(ask) for ask in home.level_asks],
            ranking=(
                None if home.ranking is None else HomeRankingSchema.of(home.ranking)
            ),
            games=[
                HomeGameSchema.from_card(
                    card, reader=reader, people=home.people, read_at=home.read_at
                )
                for card in home.games
            ],
        )


class WhereSchema(BaseModel):
    """WHERE: the club, and how far it is from the reader."""

    id: UUID
    name: str | None = Field(
        description="The club's name; `null` for a club that no longer exists."
    )
    distance_km: float | None = Field(
        description=(
            "From the reader's Location area to the club, one decimal, never below "
            "a tenth — *3,1 km*. `null` for a reader with no Location area."
        )
    )


class LeavingSchema(BaseModel):
    """What *Leave the game* would cost now (the mechanics §13)."""

    kind: Leaving = Field(
        description=(
            "`BEFORE_THE_CUT_OFF` — *Nothing is taken: the hold on your card is "
            "let go. Your seat is offered to others. On your record only if the "
            "game is then called off.* (Q113) `AFTER_THE_CUT_OFF` — *Your seat "
            "is offered to others. If someone takes it, you get 38,24 zł back "
            "(40 zł less the 1,76 zł kept on your payment); if nobody does, you "
            "won't. On your record if nobody takes it.* — with no figure and no "
            "clause while the fee kept is not yet known (#641). "
            "`WHILE_WAITING_FOR_A_PAYMENT` — the game waits for one payment "
            "(#625): *Nobody has paid yet. Leaving withdraws your yes.* The same "
            "words the departure answers with."
        )
    )
    refund_grosze: int | None = Field(
        description=(
            "After the cut-off, what comes back if somebody takes the seat — "
            "the share less **exactly the fee kept on the reader's own "
            "payment**, to the grosz (#641); nought when nobody paid. `null` "
            "before the cut-off, when nothing is taken and nothing comes back "
            "(#637), and **while that fee is not yet known** — a club on its "
            "own negotiated pricing is told it after the share is taken: no "
            "figure and no clause, never an estimate."
        )
    )
    card_fee_grosze: int | None = Field(
        description=(
            "After the cut-off, exactly what was kept on the reader's payment "
            "— *1,76 zł* on a 40 zł share paid by a business card — the "
            "provider's own figure, as the refund's receipt will say it. `null` "
            "wherever `refund_grosze` is."
        )
    )

    @classmethod
    def from_terms(cls, terms: LeaveTerms) -> "LeavingSchema":
        return cls(
            kind=terms.kind,
            refund_grosze=terms.refund_grosze,
            card_fee_grosze=terms.card_fee_grosze,
        )


class DepartureResponse(BaseModel):
    """*Leave the game*, done."""

    left: Leaving = Field(
        description=(
            "`BEFORE_THE_CUT_OFF` — nothing was taken: the hold on the card is "
            "let go, nobody is refunded (#637); the seat is offered to others. "
            "`AFTER_THE_CUT_OFF` — the seat stays paid and is offered to others "
            "until the start; refunded, less exactly the fee kept on the payment, "
            "when somebody takes it — emailed that figure now, or none while the "
            "fee is not yet known (#641). "
            "`WHILE_WAITING_FOR_A_PAYMENT` — on a game `WAITING_FOR_A_PAYMENT` "
            "(#625): nobody had paid, the yes is withdrawn, the leaver's hold is "
            "let go, and the payer's time runs on — the game is `SEAT_OPEN` with "
            "`filling_again` on the others' Home. So it is on a game already "
            "`filling_again`: the yes is withdrawn."
        )
    )


class RescueOfferSchema(BaseModel):
    """The open seat, offered to a reader not on the game (#545)."""

    deadline: datetime = Field(
        description=(
            "When the seat leaves the board — the club's cut-off while it is "
            "ahead, then the start."
        )
    )
    fills_by_the_cut_off: bool = Field(
        description=(
            "*fills by Fri 16:00* — before the cut-off, the game is off unless "
            "its seats are taken by `deadline`; `false` is *offered until the "
            "start*. Switches by itself at the cut-off."
        )
    )


class PlayedWithSchema(BaseModel):
    """One person on the game with **your** relation to them."""

    player_id: UUID
    relation: FriendRelation


class BookingDetailsResponse(BaseModel):
    """A booked game's details, for a player in it — or for a member its open
    seat is offered to (#545)."""

    booking_id: UUID
    game_id: UUID | None = Field(
        description=(
            "The ordinary Game it opened: its result acts, its balance forecast "
            "(`GET /games/{id}/pairing`) and its room in `GET /conversations` are "
            "all reached by this id. `null` on a game that waited for a payment "
            "and was never booked."
        )
    )
    pool_id: UUID
    sport: Sport
    kind: SearchMode
    read_at: datetime = Field(
        description="The instant the status and money line were folded against."
    )
    status: HomeStatus = Field(description=_HOME_STATUS)
    called_off_reason: CalledOffReason | None = Field(description=_CALLED_OFF_REASON)
    club_cancel_reason: ClubCancelReason | None = Field(
        description=_CLUB_CANCEL_REASON
    )
    uncounted_reason: UncountedReason | None = Field(description=_UNCOUNTED_REASON)
    open_seats: int = Field(description=_OPEN_SEATS)
    needs_you: bool
    filling_again: bool = Field(description=_FILLING_AGAIN)
    starts_at: datetime
    ends_at: datetime = Field(description="An hour after `starts_at`: TIME's *until*.")
    where: WhereSchema
    court_name: str | None = Field(
        description=(
            "The court the game was given — *Court 2*. `null` on a game that "
            "was never booked, which no court was given."
        )
    )
    indoor: bool | None = Field(
        description=(
            "The court's kind — *Court 2 · indoor* — which follows a move "
            "(Q122). `null` with `court_name`."
        )
    )
    sides: BookedSidesSchema
    money: BookedMoneySchema
    payment_due_by: datetime | None = Field(description=_PAYMENT_DUE_BY)
    your_payment_due_by: datetime | None = Field(description=_YOUR_PAYMENT_DUE_BY)
    time_to: TimeTo | None = Field(description=_TIME_TO)
    shows_forecast: bool = Field(
        description=(
            "Draw the balance forecast — `GET /games/{game_id}/pairing`, the card "
            "today's game screen draws — while the full game awaits its entry. "
            "`false` while a seat is open and once a result is told."
        )
    )
    leaving: LeavingSchema | None = Field(
        description=(
            "What *Leave the game* would cost now — the line under the button and "
            "its sheet (`POST /bookings/{id}/departure`). `null` where there is "
            "no button: once the hour has come, on a game that is over, for a "
            "reader not on the game, and on a game `filling_again`, whose way "
            "out is a game still filling's — *Withdraw*, "
            "`DELETE /proposals/{id}/yes`."
        )
    )
    rescue: RescueOfferSchema | None = Field(
        default=None,
        description=(
            "Present for a reader **not on the game** whom its open seat is "
            "offered to — a Seat open card, a Seats to fill row (#545): they "
            "stand in the seat that opened first, unpaid (*You?*), and "
            "**I'm in · `money.share_grosze`** is `POST /bookings/{id}/seats`. "
            "No Chat and no Leave. `null` for a player in it."
        ),
    )
    played_with: list[PlayedWithSchema] = Field(
        description=(
            "*PLAYED WITH* on the result screen (`docs/adr/0202` §1): everybody "
            "else on the game with **your** relation to them — Members' pills, "
            "**+ Add**, *request sent*, **Accept**, *friend*. Hide the card when "
            "every one is `FRIEND`. Empty for a reader not on the game. Only "
            "your own relations: nothing says who else is friends with whom."
        )
    )
    friends_game: FriendsGameSchema | None = Field(
        description=(
            "A friends game's own facts (#751): the sender, the pay mode — "
            "*Split* or *Tomek paid the court* under the price — whether the "
            "reader sent it and may call it off, each seat's state, and the "
            "reader's own invitation while it waits. A friend invited and not "
            "In reads the game too, every seat drawn. `null` on a game a fill "
            "booked."
        )
    )

    @classmethod
    def from_details(
        cls, details: BookingDetails, *, reader: UUID
    ) -> "BookingDetailsResponse":
        game = details.game
        yours = _yours_due_by(game, reader, read_at=details.read_at)
        return cls(
            booking_id=game.booking_id,
            game_id=game.game_id,
            pool_id=game.pool_id,
            sport=game.sport,
            kind=game.kind,
            read_at=details.read_at,
            status=details.state.status,
            called_off_reason=details.state.called_off,
            club_cancel_reason=details.state.cancel_reason,
            uncounted_reason=details.state.uncounted,
            open_seats=game.open_seats,
            needs_you=details.state.needs_you,
            filling_again=game.filling_again,
            starts_at=game.start,
            ends_at=_an_hour_after(game.start),
            where=WhereSchema(
                id=game.club_id,
                name=details.club_name,
                distance_km=details.distance_km,
            ),
            court_name=game.court_name if game.court_given else None,
            indoor=game.indoor if game.court_given else None,
            sides=_booked_sides(
                details.sides,
                game=game,
                reader=reader,
                people=details.people,
                # A rescue's players have paid once the cut-off took their
                # shares, whatever the reader outside has (#545, #637).
                paid=details.state.money.paid
                or (
                    details.rescue is not None
                    and not details.rescue.fills_by_the_cut_off
                ),
            ),
            money=_money(details.state.money),
            payment_due_by=details.state.pay_by,
            your_payment_due_by=yours,
            time_to=_time_to(
                game,
                details.state.pay_by,
                yours,
                reader=reader,
                read_at=details.read_at,
            ),
            shows_forecast=details.shows_forecast,
            leaving=(
                None
                if details.leaving is None
                else LeavingSchema.from_terms(details.leaving)
            ),
            rescue=(
                None
                if details.rescue is None
                else RescueOfferSchema(
                    deadline=details.rescue.deadline,
                    fills_by_the_cut_off=details.rescue.fills_by_the_cut_off,
                )
            ),
            played_with=[
                PlayedWithSchema(player_id=player, relation=relation)
                for player in game.players
                if (relation := details.played_with.get(player)) is not None
            ],
            friends_game=FriendsGameSchema.of(
                game, reader=reader, people=details.people, read_at=details.read_at
            ),
        )


def _an_hour_after(start: Instant) -> datetime:
    return start + GAME_LENGTH


# --------------------------------------------------------------------------- #
# A game still filling, opened (#542)
# --------------------------------------------------------------------------- #


def _your_payment(details: ProposalDetails) -> YourPaymentSchema | None:
    """The reader's own refused payment: within their time to pay, the one the
    game waits for, and until when (#625); after it, or refused before it was
    full, the one their reopened seat waits on."""

    paying = details.paying
    if paying is not None:
        running = details.read_at < paying.until
        return YourPaymentSchema(
            seat_charge_id=paying.seat_charge_id,
            refusal=PaymentRefusal(paying.reason.value),
            confirm_by=paying.until if running else None,
            time_to=paying.time_to if running else None,
        )
    reopened = details.reopened
    if reopened is None or ReaderAction.CONFIRM_PAYMENT not in details.actions:
        return None
    to_confirm = reopened.payment_to_confirm
    if to_confirm is None:
        return None
    return YourPaymentSchema(
        seat_charge_id=to_confirm, refusal=PaymentRefusal(reopened.reason.value)
    )


class DetailsForecastSchema(DeckForecastSchema):
    """How even the game drawn is forecast, **with the two side strengths it
    was read from** — a competitive game's full forecast (`docs/adr/0207` §6):
    each side's level, the gap and the bar's % — the figures a booked game's
    pairing prints as `forecast` and `split`, for the same people standing the
    same way. **One computation**: while a seat is empty the % is `provisional`,
    read as if the missing player matched their partner, and so are the side
    strengths beside it."""

    your_side: float = Field(
        description=(
            "Your side's strength, on the scale Levels are read on — the "
            "engine's, never the mean of the people on it."
        )
    )
    their_side: float = Field(description="The other side's strength.")
    gap: float = Field(
        description=(
            "`your_side − their_side`, **signed and served**, so nobody "
            "subtracts two rounded figures the engine subtracted unrounded."
        )
    )


class DetailsAtStakeSchema(BaseModel):
    """What a **counted** result on this game would do to your Level — *If you
    win +0,08 · If you lose −0,07* — priced by the very function a booked
    game's pairing prices its `at_stake` with, on the sides drawn here, so it
    is the pair that applies once the game is booked (`docs/adr/0207` §6)."""

    win_delta: float = Field(description="Above nought, never nought.")
    loss_delta: float = Field(description="Below nought, never nought.")


class DetailsVibeRowSchema(BaseModel):
    """One row of the Social vibe card's grid: one of **your** tags, and who
    at the table carries it."""

    tag: SocialTag = Field(
        description=(
            "A tag's code — the app owns its emoji and label, and skips a code "
            "it doesn't know."
        )
    )
    carried_by: list[UUID] = Field(
        description=(
            "Everybody on your version who carries it — **you first**, then "
            "the others in the tiles' order (`sides.yours`, then "
            "`sides.theirs`). Never empty: you carry every row. Only you: the "
            "row is yours alone."
        )
    )


class DetailsVibeSchema(BaseModel):
    """A For-fun game's **Social vibe card** (`docs/adr/0207` §6): how much the
    whole table shares, and who shares yours. Worked out from everybody's tags
    now, on every read, and stored nowhere."""

    pct: int = Field(
        description=(
            "The card's own number, counting everyone's tags — the % swiped on "
            "is the % looked at. 0–100, rounded half up."
        )
    )
    rows: list[DetailsVibeRowSchema] = Field(
        description=(
            "One per tag **you** hold, in the vocabulary's order — 💘 "
            "`OPEN_TO_MEET_SOMEONE` too, drawn like any other row though it "
            "never counts in `pct`. None of the others' tags you don't hold."
        )
    )


def _details_forecast(forecast: CardForecast | None) -> DetailsForecastSchema | None:
    if forecast is None:
        return None
    levels = invariant(
        forecast.levels,
        "a forecast the engine read always carries the strengths it read",
    )
    return DetailsForecastSchema(
        pct=forecast.pct,
        provisional=forecast.provisional,
        your_side=levels.yours,
        their_side=levels.theirs,
        gap=levels.gap,
    )


def _details_at_stake(stakes: Stakes | None) -> DetailsAtStakeSchema | None:
    if stakes is None:
        return None
    return DetailsAtStakeSchema(
        win_delta=stakes.win_delta, loss_delta=stakes.loss_delta
    )


def _details_vibe(vibe: TableVibe | None) -> DetailsVibeSchema | None:
    if vibe is None:
        return None
    return DetailsVibeSchema(
        pct=vibe.pct,
        rows=[
            DetailsVibeRowSchema(tag=row.tag, carried_by=list(row.carried_by))
            for row in vibe.rows
        ],
    )


class ProposalDetailsResponse(BaseModel):
    """A game still filling, as the reader opens it — the deck's card turned
    into a screen. **What it says about the game follows the kind**
    (`docs/adr/0207` §5, §6): a competitive game `forecast` and `at_stake`,
    with `vibe` `null`; a For-fun game `vibe`, with `forecast` and `at_stake`
    `null`."""

    proposal_id: UUID
    pool_id: UUID
    type: CardType = Field(
        description="`PICKED_FOR_YOU`, or `CHALLENGE` (a member's post)."
    )
    kind: SearchMode
    sport: Sport
    challenger: DeckChallengerSchema | None = Field(
        description=(
            "The poster of a challenge; `null` on a pick, and once its poster withdrew."
        )
    )
    read_at: datetime
    status: ProposalStatus = Field(
        description=(
            "`FILLING` — seats are open: *Filling · `in_count` of `seats` in*. "
            "`WAITING_FOR_A_PAYMENT` — every seat is In and one player's refused "
            "share is awaited until `payment_due_by` (#625): their seat is "
            "theirs alone, and paying in time books it. `FILLED` — booked: "
            "`GET /bookings/{proposal_id}`. `EXPIRED`, `WITHDRAWN`, "
            "`COURT_HOUR_LOST` — it ended unfilled."
        )
    )
    actions: list[ReaderAction] = Field(
        description=(
            "What the reader may do now, in the screen's order: `YES` and `NO` "
            "(*I'm in* / *Not this time*), `WITHDRAW` when they are In, `LEAVE` in "
            "its place while a payment is awaited — *Leave the game* with its "
            "sheet, sent as the withdrawal, `DELETE /proposals/{id}/yes` — and "
            "`CONFIRM_PAYMENT` when their seat waits on a refused payment "
            "(`your_payment`) — within their time to pay too, beside `LEAVE`; "
            "a payer refused for terms or a missing method has `YES` there, "
            "once fixed. Empty once the game is over or their answer is final."
        )
    )
    your_payment: YourPaymentSchema | None = Field(
        description=(
            "The payment to confirm to take the seat back — present exactly when "
            "`actions` holds `CONFIRM_PAYMENT`."
        )
    )
    in_count: int = Field(description="People In on the whole game.")
    seats: int = Field(description="Four in padel and badminton, two otherwise.")
    starts_at: datetime = Field(description="The court hour's start; games are 1 h.")
    where: WhereSchema = Field(
        description="The club and its distance — never a court, given at booking."
    )
    share_grosze: int = Field(description="*30 zł if it fills*.")
    book_by: datetime = Field(
        description="When the game leaves unfilled — *book by Sat 13:00*."
    )
    no_free_cancellation: bool = Field(
        description="The club's cut-off has already passed for this game."
    )
    indoor: bool | None = Field(
        description=(
            "The kind of court the game promises — `true` *Indoor*, `false` "
            "*Outdoor* — when every free court it could be booked on is of "
            "that kind; `null` when they are mixed (Q122). Shown, never chosen "
            "by."
        )
    )
    payment_due_by: datetime | None = Field(
        description=(
            "When the payment the game waits for is due — *Waiting for one "
            "payment · until 14:40 · Nobody pays until it's in* (#625) — "
            "never whose. `null` unless `WAITING_FOR_A_PAYMENT`. The reader's own "
            "is `your_payment.confirm_by`."
        )
    )
    time_to: TimeTo | None = Field(
        description=(
            "What the time to `payment_due_by` is for (#638; Q113): "
            "`FIX_THE_CARD` — a hold refused before the club's cut-off, where "
            "nothing is taken; `PAY` — refused from it on. The others read "
            "*Waiting for one payment* either way; the payer's own words are "
            "`your_payment.time_to`'s. `null` with `payment_due_by`."
        )
    )
    sides: DeckSidesSchema = Field(
        description=(
            "Everybody drawn, the reader on their own side: for a reader still "
            "deciding, their own card as the deck deals it; for a reader In, "
            "everybody In — the client draws the open seats empty."
        )
    )
    forecast: DetailsForecastSchema | None = Field(
        description=(
            "How even a **competitive** game drawn is forecast, with each "
            "side's level and the signed gap. **Always `null` on For fun** "
            "(`docs/adr/0207` §5), whose sides it still arranged; `null` too "
            "where it cannot be read — somebody on it holds no level in the "
            "sport."
        )
    )
    at_stake: DetailsAtStakeSchema | None = Field(
        description=(
            "What a counted result would do to **your** Level, on `sides` — "
            "**two values or none**, as on a booked game. `null` on For fun; "
            "while a seat is open (the court that will play isn't known yet); "
            "once the game is no longer yours to play — you said no, no longer "
            "fit, wait on a paused yes, or it ended; once it is booked, whose "
            "stakes are `GET /games/{game_id}/pairing`'s; and where there is "
            "nothing to price: you hold no level in the sport, or nobody "
            "across the net does."
        )
    )
    vibe: DetailsVibeSchema | None = Field(
        description=(
            "A **For-fun** game's Social vibe and the grid's rows. `null` on "
            "Competitive, and where the card draws none: fewer than two "
            "people named, or nobody at the table holding a tag that counts."
        )
    )
    overlap: DeckOverlapSchema

    @classmethod
    def from_details(
        cls, details: ProposalDetails, *, reader: UUID
    ) -> "ProposalDetailsResponse":
        proposal = details.proposal
        return cls(
            proposal_id=proposal.proposal_id,
            pool_id=proposal.pool.id,
            type=details.type,
            kind=proposal.kind,
            sport=proposal.sport,
            challenger=_challenger(details.challenger_id, details.people),
            read_at=details.read_at,
            status=details.status,
            actions=list(details.actions),
            your_payment=_your_payment(details),
            in_count=len(proposal.yeses),
            seats=proposal.seats,
            starts_at=proposal.start,
            where=WhereSchema(
                id=proposal.club_id,
                name=details.club_name,
                distance_km=details.distance_km,
            ),
            share_grosze=proposal.share_grosze,
            book_by=proposal.book_by,
            no_free_cancellation=details.no_free_cancellation,
            indoor=details.indoor,
            payment_due_by=details.pay_by,
            time_to=details.time_to,
            sides=_deck_sides(
                details.sides,
                reader=reader,
                people=details.people,
                in_=details.view.in_,
            ),
            forecast=_details_forecast(details.forecast),
            at_stake=_details_at_stake(details.at_stake),
            vibe=_details_vibe(details.vibe),
            overlap=_overlap(details.overlap),
        )


# --------------------------------------------------------------------------- #
# Fill in: seats to fill (#545)
# --------------------------------------------------------------------------- #


class SeatToFillSchema(BaseModel):
    """One *Seats to fill* row: a booked game that lost a player, and the
    reader fits and is free for it."""

    booking_id: UUID = Field(
        description=(
            "`POST /bookings/{id}/seats` takes the seat — *I'm in · "
            "`share_grosze`* — and `GET /bookings/{id}` is its details as the "
            "reader sees it from outside."
        )
    )
    sport: Sport
    kind: SearchMode = Field(
        description="Competitive, or for fun (*· friendly* on the title)."
    )
    starts_at: datetime = Field(description="The court hour's start; games are 1 h.")
    club: BookedClubSchema
    court_name: str = Field(description="What the club calls the court.")
    indoor: bool = Field(description="The court's kind — *Court 3 · indoor* (Q122).")
    share_grosze: int = Field(description="What *I'm in* charges at once.")
    open_seats: int = Field(
        description="The dashed **?** squares after the players' posters."
    )
    deadline: datetime = Field(
        description=(
            "When the row leaves the board — the club's cut-off while it is "
            "ahead, then the start."
        )
    )
    fills_by_the_cut_off: bool = Field(
        description=(
            "*fills by `deadline`* before the cut-off; `false` is *offered until "
            "the start*. Switches by itself at the cut-off."
        )
    )
    players: list[BookedTileSchema] = Field(
        description=(
            "Everybody on the game, each *paid* once the cut-off took their "
            "shares (#637) — the small posters, first side first. Long-press a "
            "poster for their record."
        )
    )

    @classmethod
    def of(
        cls,
        game: BookedGame,
        *,
        deadline: Instant,
        fills_by_the_cut_off: bool,
        club_name: str | None,
        reader: UUID,
        people: Mapping[UUID, DeckPerson],
    ) -> "SeatToFillSchema":
        return cls(
            booking_id=game.booking_id,
            sport=game.sport,
            kind=game.kind,
            starts_at=game.start,
            club=BookedClubSchema(id=game.club_id, name=club_name),
            court_name=game.court_name,
            indoor=game.indoor,
            share_grosze=game.share_grosze,
            open_seats=game.open_seats,
            deadline=deadline,
            fills_by_the_cut_off=fills_by_the_cut_off,
            players=[
                _tile(
                    player,
                    reader=reader,
                    sport_people=people,
                    # Held until the cut-off, taken at it (#637).
                    paid=not fills_by_the_cut_off,
                )
                for player in game.players
            ],
        )


class FillInResponse(BaseModel):
    """A group's **Fill in** tab for one sport: *Seats to fill* (#545)."""

    pool_id: UUID
    sport: Sport
    read_at: datetime = Field(
        description="The instant every row and deadline here was read against."
    )
    badge: int = Field(description="The tab's badge: the Seats to fill rows.")
    seats_to_fill: list[SeatToFillSchema] = Field(
        description=(
            "Every rescue in the group the reader fits — the pair rule, the "
            "kind their intent wants, free for the hour in their week, no game "
            "of theirs then, within their Games & money — **soonest first**, "
            "before or after the cut-off. Never a game still filling: that is "
            "the deck's. *You're In* is `GET /players/me/live-yeses`."
        )
    )

    @classmethod
    def from_fill_in(cls, fill_in: FillIn, *, reader: UUID) -> "FillInResponse":
        return cls(
            pool_id=fill_in.pool_id,
            sport=fill_in.sport,
            read_at=fill_in.read_at,
            badge=fill_in.badge,
            seats_to_fill=[
                SeatToFillSchema.of(
                    row.game,
                    deadline=row.deadline,
                    fills_by_the_cut_off=row.fills_by_the_cut_off,
                    club_name=row.club_name,
                    reader=reader,
                    people=fill_in.people,
                )
                for row in fill_in.seats_to_fill
            ],
        )


# --------------------------------------------------------------------------- #
# Posting a game (#546)
# --------------------------------------------------------------------------- #


class LevelRangeSchema(BaseModel):
    """A range of Levels, both bounds included."""

    low: float
    high: float

    @classmethod
    def of(cls, levels: LevelRange) -> "LevelRangeSchema":
        return cls(low=levels.low, high=levels.high)


class PostingCellSchema(BaseModel):
    """One day's range on the posting grid. **The client draws the nine looks
    from these values** (the screens A5.2): *dead* is `fits_free` nought; *few*
    or *enough* by `full_game`; a court glyph by `court_free`; *outside your
    hours*, *past* and the red dot by their own flags. *Your pick* is the
    client's."""

    range: DayRange = Field(
        description="Morning 07–12, Afternoon 12–17, Evening 17–23."
    )
    fits_free: int = Field(
        description=(
            "How many of the poster's best fits are free **together with them** "
            "at `best_starts_at` — the best hour in the range that has a free "
            "court, or with none, the best hour of the range — never people who "
            "overlap the poster at different hours. The client caps it at *5+*."
        )
    )
    best_starts_at: datetime | None = Field(
        description="The hour the number is read at; `null` with no hour ahead."
    )
    court_free: bool = Field(
        description=(
            "A court the post could be made at is free in the range — the cell "
            "can be picked when somebody fits too."
        )
    )
    full_game: bool = Field(
        description=(
            "A full game's worth are free: `fits_free` reaches `open_seats`. "
            "Pickable with a court but not full is *only 2 fit · may not fill*."
        )
    )
    outside_your_hours: bool = Field(
        description=(
            "The poster's own week covers no hour the number could be read at: "
            "dimmed and dashed, still pickable."
        )
    )
    past: bool = Field(description="Earlier today: inert.")
    happening: bool = Field(
        description=(
            "The red dot: a rescue the poster is offered, or somebody else's "
            "post still filling they could join, starts in the range."
        )
    )

    @classmethod
    def of(cls, cell: GridCell) -> "PostingCellSchema":
        return cls(
            range=cell.range,
            fits_free=cell.fits_free,
            best_starts_at=cell.best_start,
            court_free=cell.court_free,
            full_game=cell.full_game,
            outside_your_hours=cell.outside_your_hours,
            past=cell.past,
            happening=cell.happening,
        )


class PostingDaySchema(BaseModel):
    day: date = Field(description="The day on the club's clock.")
    is_today: bool = Field(description="*Today*, in coral, with its date.")
    cells: list[PostingCellSchema] = Field(description="Three: morning first.")


class PostingGridResponse(BaseModel):
    """**WHEN** — one week of the posting grid (the mechanics §9.1 step 5)."""

    pool_id: UUID
    sport: Sport
    kind: SearchMode
    who: Who
    week: int = Field(description="`1` starts today; `2` is the seven days after.")
    read_at: datetime = Field(description="The instant every cell was read against.")
    level_range: LevelRangeSchema = Field(
        description="The range the others' Levels were counted in."
    )
    engine_level_range: LevelRangeSchema = Field(
        description=(
            "The engine's own window for the kind around the poster's Level — "
            "the steppers' starting bounds, which may be narrowed in 0,05 steps "
            "and never widened."
        )
    )
    open_seats: int = Field(
        description="The seats besides the poster: three in doubles, one in singles."
    )
    days: list[PostingDaySchema] = Field(description="Seven, the first first.")

    @classmethod
    def from_week(cls, week: PostingWeek) -> "PostingGridResponse":
        read = week.read
        today = read.grid.days(1)[0]
        days = read.grid.days(week.week)
        return cls(
            pool_id=read.pool.id,
            sport=read.sport,
            kind=read.kind,
            who=read.posted_for.who,
            week=week.week,
            read_at=read.read_at,
            level_range=LevelRangeSchema.of(read.posted_for.levels),
            engine_level_range=LevelRangeSchema.of(read.window),
            open_seats=read.open_seats,
            days=[
                PostingDaySchema(
                    day=day,
                    is_today=day == today,
                    cells=[
                        PostingCellSchema.of(cell)
                        for cell in week.cells
                        if cell.day == day
                    ],
                )
                for day in days
            ],
        )


class SlotFitSchema(BaseModel):
    """One of the poster's best fits free then — *2,75 · 93*, the second
    figure being the kind's own number: how even, or on a For-fun post how
    much the two of them share."""

    player_id: UUID
    nickname: str | None = Field(
        description=(
            "Their nickname, whole and never with an @; `null` for an account "
            "that can no longer be named."
        )
    )
    photo_id: UUID | None
    photo_url: str | None
    level: float | None = Field(description="Their published Level in the sport.")
    friend: bool = Field(
        description=(
            "**Your** friend — the *FRIEND* tag (`docs/adr/0202` §2); only your "
            "own friends ever carry it."
        )
    )
    forecast: DeckForecastSchema | None = Field(
        description=(
            "How even a game of the poster and them is forecast. **Always "
            "`null` on a `FOR_FUN` post**, which says its `vibe` instead "
            "(`docs/adr/0207` §5). Also `null` where it cannot be read."
        )
    )
    vibe: DeckVibeSchema | None = Field(
        description=(
            "On a **`FOR_FUN`** post, the Social vibe of **the poster and "
            "them**, worked out from the two's tags now — and the fits are "
            "ranked by it, highest first, a tie falling to the forecast and "
            "then the pool's order (#834). **Always `null` on a `COMPETITIVE` "
            "post**, and where neither holds a tag."
        )
    )


class FreeCourtSchema(BaseModel):
    """One *Free courts* row: a club and hour the post could be made at."""

    club: BookedClubSchema
    home_club: bool = Field(description="The group's home club, listed first.")
    home_club_full: bool = Field(
        description=(
            "Offered **because the group's home club has no free court at this "
            "hour** — another club's, for an official group, which is offered "
            "other clubs only then: *Ogrody 33 is full at 10:00*. Always "
            "`false` for the home club and for a player group."
        )
    )
    distance_km: float | None = Field(
        description="How far it is from the poster; `null` with no Location area."
    )
    starts_at: datetime
    share_grosze: int = Field(description="*27 zł if it fills*, each.")
    book_by: datetime = Field(description="The latest the post can fill.")
    courts: int = Field(description="How many courts of the sport are free then.")
    fits_free: int = Field(
        description="Its own *n free*: the poster's best fits free at this hour."
    )


class PostStillFillingSchema(BaseModel):
    """Somebody else's post still filling that the poster could join — **I'm
    in** is `POST /proposals/{proposal_id}/yes`, free until it fills."""

    proposal_id: UUID
    kind: SearchMode
    starts_at: datetime
    club: BookedClubSchema
    share_grosze: int = Field(description="What a seat costs if it fills.")
    book_by: datetime
    challenger: DeckChallengerSchema | None = Field(
        description="Who posted it — `null` once they withdrew."
    )
    people_in: list[DeckTileSchema] = Field(
        description="Everybody In, in the order they said yes. No court number."
    )
    open_seats: int


class PostingSlotResponse(BaseModel):
    """A cell's sheet (the mechanics §9.1 step 6; the screens A5.3)."""

    pool_id: UUID
    sport: Sport
    kind: SearchMode
    who: Who
    day: date
    range: DayRange
    read_at: datetime
    level_range: LevelRangeSchema
    open_seats: int
    cell: PostingCellSchema = Field(description="The headline's cell.")
    fits: list[SlotFitSchema] = Field(
        description=(
            "The best fits free at the cell's best hour, best fit first: the "
            "most even game, or on a `FOR_FUN` post the highest `vibe`, a tie "
            "falling to the most even."
        )
    )
    free_courts: list[FreeCourtSchema] = Field(
        description="**Home club first**, then by hour. Tapping one picks it."
    )
    rescues: list[SeatToFillSchema] = Field(
        description=(
            "**Already happening here**, first: booked games in the range with a "
            "seat offered to the poster — *I'm in · `share_grosze`* pays at once "
            "(`POST /bookings/{id}/seats`)."
        )
    )
    posts: list[PostStillFillingSchema] = Field(
        description="Then: posts still filling in the range the poster could join."
    )

    @classmethod
    def from_slot(cls, slot: PostingSlot) -> "PostingSlotResponse":
        read = slot.read
        reader = read.poster.player_id
        people = slot.people

        def fit_of(fit: SlotFit) -> SlotFitSchema:
            person = people.get(fit.player_id)
            return SlotFitSchema(
                player_id=fit.player_id,
                nickname=None if person is None else person.nickname,
                photo_id=None if person is None else person.photo_id,
                photo_url=None if person is None else person.photo_url,
                level=None if person is None else person.level,
                friend=person is not None and person.friend,
                forecast=_forecast(fit.forecast),
                vibe=_vibe(fit.vibe),
            )

        return cls(
            pool_id=read.pool.id,
            sport=read.sport,
            kind=read.kind,
            who=read.posted_for.who,
            day=slot.cell.day,
            range=slot.cell.range,
            read_at=read.read_at,
            level_range=LevelRangeSchema.of(read.posted_for.levels),
            open_seats=read.open_seats,
            cell=PostingCellSchema.of(slot.cell),
            fits=[fit_of(fit) for fit in slot.fits],
            free_courts=[
                FreeCourtSchema(
                    club=BookedClubSchema(
                        id=court.hour.club_id,
                        name=slot.club_names.get(court.hour.club_id),
                    ),
                    home_club=court.home,
                    home_club_full=court.home_club_full,
                    distance_km=slot.distances.get(court.hour.club_id),
                    starts_at=court.hour.start,
                    share_grosze=court.hour.share_grosze,
                    book_by=court.hour.book_by,
                    courts=court.hour.courts,
                    fits_free=court.fits_free,
                )
                for court in slot.free_courts
            ],
            rescues=[
                SeatToFillSchema.of(
                    row.game,
                    deadline=row.deadline,
                    fills_by_the_cut_off=row.fills_by_the_cut_off,
                    club_name=row.club_name,
                    reader=reader,
                    people=people,
                )
                for row in slot.rescues
            ],
            posts=[
                PostStillFillingSchema(
                    proposal_id=row.proposal.proposal_id,
                    kind=row.proposal.kind,
                    starts_at=row.proposal.start,
                    club=BookedClubSchema(id=row.proposal.club_id, name=row.club_name),
                    share_grosze=row.proposal.share_grosze,
                    book_by=row.proposal.book_by,
                    challenger=_challenger(row.challenger_id, people),
                    people_in=_deck_sides(
                        Sides(yours=row.proposal.yeses, theirs=()),
                        reader=reader,
                        people=people,
                        in_=row.proposal.yeses,
                    ).yours,
                    open_seats=row.proposal.open_seats,
                )
                for row in slot.posts
            ],
        )


class PostRequest(BaseModel):
    """*Post — you're In*: the four controls and the court hour picked on a
    sheet. **Types only**: who it may be for and which court hours are offered
    are the domain's to refuse, each with its own code."""

    sport: Sport
    kind: SearchMode
    who: Who
    level_low: float | None = Field(
        default=None,
        description="The narrowed lower bound; `null` is the engine's own.",
    )
    level_high: float | None = Field(
        default=None,
        description="The narrowed upper bound; `null` is the engine's own.",
    )
    club_id: UUID
    starts_at: datetime = Field(description="The court hour's start, as listed.")


class PostedResponse(BaseModel):
    """The post, In with its poster — its id is the game's, in *You're In*."""

    proposal_id: UUID
    versions: int = Field(description="How many versions it was dealt in, up to 3.")
    dealt_to: int = Field(description="How many best fits were dealt it.")
    open_seats: int = Field(description="The seats open beside the poster.")

    @classmethod
    def from_posted(cls, posted: Posted) -> "PostedResponse":
        return cls(
            proposal_id=posted.proposal_id,
            versions=posted.versions,
            dealt_to=posted.dealt_to,
            open_seats=posted.open_seats,
        )


# --------------------------------------------------------------------------- #
# The friends card and Find a court (#750)
# --------------------------------------------------------------------------- #


class FriendsCardSidesSchema(BaseModel):
    """The sides the court and the card both draw (the friends README, note 3)
    — ids only: every face on them is one of the reader's friends, whom the
    picker already drew."""

    yours: list[UUID] = Field(
        description="The reader first, then their partner in doubles."
    )
    theirs: list[UUID]


class FriendsCourtSchema(BaseModel):
    """One court the line-up could take: a row of *Find a court* —
    *19:00 · Bonarka Arena · Court 2 · 32 zł each · Ania busy* — and the
    card's court panel."""

    starts_at: datetime = Field(description="The court hour's start; games are 1 h.")
    club: DeckClubSchema
    court_id: UUID = Field(
        description="Sent back as `court_id`, with `starts_at`, to pick this row."
    )
    court_name: str = Field(description="What the club calls it — *Court 3*.")
    indoor: bool = Field(description="*Indoor* or *Outdoor*.")
    share_grosze: int = Field(description="*25 zł each*.")
    home_club_full: bool = Field(
        description=(
            "Another club's court, offered **because the group's home club has "
            "no free court at this hour** — *Ogrody 33 is full at 10:00*. Always "
            "`false` for the home club and for a player group."
        )
    )
    free_count: int = Field(
        description=(
            "How many of the line-up, the reader among them, are free for the "
            "whole hour by their weekly hours — the row's tint: all of them "
            "*Everybody free*, then dimmer for each one fewer."
        )
    )
    busy: list[UUID] = Field(
        description=(
            "Those of the line-up who are not — *Ania busy*, *Magda and Ania "
            "busy* — in the line-up's order. **Busy** is outside their weekly "
            "hours and nothing else: an hour where one of them has a game is "
            "never listed."
        )
    )

    @classmethod
    def from_row(
        cls, row: CourtForFriends, *, club_names: Mapping[UUID, str]
    ) -> "FriendsCourtSchema":
        return cls(
            starts_at=row.start,
            club=DeckClubSchema(id=row.club_id, name=club_names.get(row.club_id)),
            court_id=row.court.court_id,
            court_name=row.court.name,
            indoor=row.court.indoor,
            share_grosze=row.share_grosze,
            home_club_full=row.home_club_full,
            free_count=len(row.free),
            busy=list(row.busy),
        )


_HOME_CLUB = "The group's home club — the name in *… is full at 10:00*."


def _home_club_of(read: FriendsLineUpRead, names: Mapping[UUID, str]) -> DeckClubSchema:
    return DeckClubSchema(id=read.home_club_id, name=names.get(read.home_club_id))


class FriendsCardResponse(BaseModel):
    """The friends card: the deck's card without its tiles."""

    pool_id: UUID
    sport: Sport
    kind: SearchMode = Field(description="The switch's kind for this one game.")
    home_club: DeckClubSchema = Field(description=_HOME_CLUB)
    sides: FriendsCardSidesSchema = Field(
        description=(
            "The evenest way the line-up can stand, or the sides sent "
            "(`partner_id`)."
        )
    )
    forecast: DeckForecastSchema | None = Field(
        description=(
            "*87% · Very even* for these sides. **Always `null` when `kind` is "
            "`FOR_FUN`**, which says its `vibe` instead (`docs/adr/0207` §5) — "
            "its sides are still the evenest. Also `null` where it cannot be "
            "read."
        )
    )
    vibe: DeckVibeSchema | None = Field(
        description=(
            "When `kind` is **`FOR_FUN`**, the Social vibe of the line-up — "
            "the reader and every friend seated, however they stand, so a swap "
            "never moves it; worked out from everybody's tags now (#834). "
            "Flipping the kind switch flips the card's number. **Always `null` "
            "on `COMPETITIVE`**, and where nobody seated holds a tag."
        )
    )
    court: FriendsCourtSchema | None = Field(
        description=(
            "The court picked (`court_id` and `starts_at`), or the one proposed: "
            "the soonest hour where the whole line-up is free, failing that the "
            "soonest where most of them are. `null` when no court is free in the "
            "next 14 days — the card's place says so, and *Pick a different "
            "court* is gone."
        )
    )
    overlap: DeckOverlapSchema | None = Field(
        description=(
            "The line-up's weeks, the court's hour ringed; `null` with no court, "
            "which draws no card."
        )
    )
    cut_off: datetime | None = Field(
        description=(
            "When the club's free cancellation ends for the court's game — the "
            "send sheet's *We hold 100 zł on your card until Fri 10:00*. `null` "
            "with no court."
        )
    )

    @classmethod
    def from_card(cls, card: FriendsCard) -> "FriendsCardResponse":
        names = card.club_names
        return cls(
            pool_id=card.read.pool_id,
            sport=card.read.sport,
            kind=card.kind,
            home_club=_home_club_of(card.read, names),
            sides=FriendsCardSidesSchema(
                yours=list(card.sides.yours), theirs=list(card.sides.theirs)
            ),
            forecast=_forecast(card.forecast),
            vibe=_vibe(card.vibe),
            court=None
            if card.court is None
            else FriendsCourtSchema.from_row(card.court, club_names=names),
            overlap=None if card.overlap is None else _overlap(card.overlap),
            cut_off=card.cut_off,
        )


class FriendsCourtsResponse(BaseModel):
    """*Find a court* for a line-up."""

    pool_id: UUID
    sport: Sport
    home_club: DeckClubSchema = Field(description=_HOME_CLUB)
    courts: list[FriendsCourtSchema] = Field(
        description=(
            "**Every court the line-up could take**, from the soonest hour still "
            "sellable to 14 days ahead, under the group's court rule: soonest "
            "first, the home club first within an hour, each club's courts in "
            "its own order. The client groups them by day. Every row can be "
            "picked."
        )
    )

    @classmethod
    def from_courts(cls, courts: FriendsCourts) -> "FriendsCourtsResponse":
        names = courts.club_names
        return cls(
            pool_id=courts.read.pool_id,
            sport=courts.read.sport,
            home_club=_home_club_of(courts.read, names),
            courts=[
                FriendsCourtSchema.from_row(row, club_names=names)
                for row in courts.read.courts
            ],
        )


# --------------------------------------------------------------------------- #
# A friends game: sending and answering (#751)
# --------------------------------------------------------------------------- #


class SendFriendsGameRequest(BaseModel):
    """*Send game and pay* on the send sheet (#751): the friends card as it was
    read, and how to pay."""

    sport: Sport
    kind: SearchMode = Field(description="The Friends tab's switch: this game only.")
    friend_ids: list[UUID] = Field(
        description=(
            "The friends seated beside the sender, in the order seated — as the "
            "card was read: three in doubles, one in singles."
        )
    )
    partner_id: UUID | None = Field(
        default=None,
        description="The friend beside the sender after a swap, as the card was "
        "read; `null` for the evenest sides.",
    )
    court_id: UUID = Field(description="The court the card names.")
    starts_at: datetime = Field(description="Its hour, as the card names it.")
    pay_mode: PayMode = Field(
        description=(
            "`SPLIT_THE_COST` — *We hold 100 zł on your card until Fri 10:00. You "
            "pay 25 zł, plus 25 zł for any seat still empty then.* "
            "`WHOLE_COURT` — *Send game and pay 100 zł*. The hold is the same: "
            "the whole court."
        )
    )
    booking_id: UUID | None = Field(
        default=None,
        description=(
            "Sending again after confirming a payment the last send was refused: "
            "the `booking_id` that send answered, so the payments confirmed are "
            "the ones taken. Left out on a first send."
        ),
    )


class SeatInvitationRequest(BaseModel):
    """*Invite a friend* into an empty seat (#752): which friend. The seat is
    the path's."""

    friend_id: UUID = Field(
        description="One of the reader's own friends, picked on the picker."
    )


class FriendsGameSentResponse(BaseModel):
    """What a send did: the court booked, or nothing booked and the sender's
    payments to confirm."""

    booking_id: UUID = Field(
        description=(
            "The friends game — booked, or, with `your_payments`, the id to send "
            "again under once they are confirmed."
        )
    )
    booked: BookedSchema | None = Field(
        description=(
            "Present when the court is booked: the sender's share and a cover "
            "for every other seat held on their card, the invitations sent, the "
            "chat open. `null` when a payment was refused."
        )
    )
    your_payments: list[YourPaymentSchema] = Field(
        description=(
            "**Nothing was booked**: each payment the sender's bank refused or "
            "wants confirmed — `GET /seat-charges/{id}`, confirm in the app, "
            "`POST /seat-charges/{id}/confirmation` — then send again with "
            "`booking_id`. Empty once booked."
        )
    )

    @classmethod
    def of(cls, sent: FriendsGameSent) -> "FriendsGameSentResponse":
        return cls(
            booking_id=sent.booking_id,
            booked=None
            if sent.booked is None
            else BookedSchema(
                booking_id=sent.booked.booking_id, game_id=sent.booked.game_id
            ),
            your_payments=[
                YourPaymentSchema(
                    seat_charge_id=refused.seat_charge_id, refusal=refused.refusal
                )
                for refused in sent.your_payments
            ],
        )


class FriendsGameAnswerResponse(BaseModel):
    """What *Accept* did: the reader In, or their share refused."""

    booking_id: UUID
    accepted: bool = Field(
        description="The reader is In: the card moves to Your games."
    )
    whole: bool = Field(
        description="Every seat is taken now — *It's a game!*, to all four."
    )
    your_payment: YourPaymentSchema | None = Field(
        description=(
            "With *Split the cost*, the reader's share could not be held: the "
            "seat is still theirs until `confirm_by`, their invitation's end. "
            "Confirm it in the app (`POST /seat-charges/{id}/confirmation`), or "
            "fix the card and accept again. `null` otherwise."
        )
    )

    @classmethod
    def of(cls, answer: FriendsGameAnswer) -> "FriendsGameAnswerResponse":
        return cls(
            booking_id=answer.booking_id,
            accepted=answer.accepted,
            whole=answer.whole,
            your_payment=None
            if answer.your_payment is None
            else YourPaymentSchema(
                seat_charge_id=answer.your_payment.seat_charge_id,
                refusal=answer.your_payment.refusal,
                confirm_by=answer.confirm_by,
            ),
        )

