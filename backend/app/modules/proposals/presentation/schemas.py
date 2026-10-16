"""The player surface's shapes for proposals (#538, #539), and Home and the
two details a game has — booked, or still filling (#542).

**Money crosses as integer grosze**, as every price on this platform does, and
the client renders it (``docs/value-formatting.md``). A yes answers only the
seats still open, and the live-yeses list is the reader's own: **the one shape
that draws other people is the deck's card** — each by their Name, never a
first name cut from it (``docs/adr/0171``), their photograph and published
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

from pydantic import BaseModel, Field

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport, instant
from app.modules.proposals.application.answers import YesAnswer
from app.modules.proposals.application.booking_details import BookingDetails
from app.modules.proposals.application.group_deck import GroupDeck
from app.modules.proposals.application.home import Home, HomeGame
from app.modules.proposals.application.live_yeses import LiveYeses, NamedLiveYes
from app.modules.proposals.application.payments_to_confirm import PaymentToConfirm
from app.modules.proposals.application.proposal_details import ProposalDetails
from app.modules.proposals.application.posting import (
    Posted,
    PostingSlot,
    PostingWeek,
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
from app.modules.proposals.domain.games_and_money import (
    GAMES_PER_WEEK,
    MOST_ILL_PAY_CHOICES_GROSZE,
    GamesAndMoney,
)
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
    ShareState,
    UncountedReason,
)
from app.modules.proposals.domain.ports import DeckPerson, PaymentRefusal
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
    name: str | None = Field(
        description=(
            "Their Name, whole — the tile may cut it short, never invent a first "
            "name. `null` for an account that can no longer be named."
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
    """Who a challenge names — *Kuba challenged you*."""

    player_id: UUID
    name: str | None


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
            "`null` where it cannot be read: somebody on the card holds no rating "
            "in the sport, or nobody faces the reader yet."
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
            name=None if person is None else person.name,
            photo_id=None if person is None else person.photo_id,
            photo_url=None if person is None else person.photo_url,
            level=None if person is None else person.level,
            is_in=player_id in in_,
            paid=player_id in paid,
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
        player_id=player_id, name=None if person is None else person.name
    )


def _forecast(forecast: CardForecast | None) -> DeckForecastSchema | None:
    if forecast is None:
        return None
    return DeckForecastSchema(pct=forecast.pct, provisional=forecast.provisional)


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
            "soonest first among two, with no mark (#673). Then seats open after "
            "the reader's yes (fewest first), then seat open › challenge › pick, "
            "then the soonest deadline, then the best forecast; the same people "
            "only at their best hour."
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
    name: str | None = Field(
        description=(
            "Their Name, whole — the tile may cut it short, never invent a first "
            "name. `null` for an account that can no longer be named."
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
        name=None if person is None else person.name,
        photo_id=None if person is None else person.photo_id,
        photo_url=None if person is None else person.photo_url,
        level=None if person is None else person.level,
        paid=paid,
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


class HomeResponse(BaseModel):
    """**Home**: the reader's games from the moment they fill."""

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

    @classmethod
    def from_home(cls, home: Home, *, reader: UUID) -> "HomeResponse":
        return cls(
            read_at=home.read_at,
            needing_you=home.needing_you,
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


class ProposalDetailsResponse(BaseModel):
    """A game still filling, as the reader opens it — the deck's card turned
    into a screen."""

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
    forecast: DeckForecastSchema | None = Field(
        description=(
            "How even the game drawn is forecast — `null` where it cannot be read."
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
            forecast=_forecast(details.forecast),
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
    """One of the poster's best fits free then — *2,75 · 93*."""

    player_id: UUID
    name: str | None = Field(
        description=(
            "Their Name, whole; `null` for an account that can no longer be named."
        )
    )
    photo_id: UUID | None
    photo_url: str | None
    level: float | None = Field(description="Their published Level in the sport.")
    forecast: DeckForecastSchema | None = Field(
        description=(
            "How even a game of the poster and them is forecast — `null` where "
            "it cannot be read."
        )
    )


class FreeCourtSchema(BaseModel):
    """One *Free courts* row: a club and hour the post could be made at."""

    club: BookedClubSchema
    home_club: bool = Field(description="The group's home club, listed first.")
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
        description="The best fits free at the cell's best hour, best fit first."
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

        def fit_of(player_id: UUID, forecast: CardForecast | None) -> SlotFitSchema:
            person = people.get(player_id)
            return SlotFitSchema(
                player_id=player_id,
                name=None if person is None else person.name,
                photo_id=None if person is None else person.photo_id,
                photo_url=None if person is None else person.photo_url,
                level=None if person is None else person.level,
                forecast=_forecast(forecast),
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
            fits=[fit_of(fit.player_id, fit.forecast) for fit in slot.fits],
            free_courts=[
                FreeCourtSchema(
                    club=BookedClubSchema(
                        id=court.hour.club_id,
                        name=slot.club_names.get(court.hour.club_id),
                    ),
                    home_club=court.home,
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
