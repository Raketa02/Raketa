"""The player surface's shapes for proposals (#538, #539).

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

from collections.abc import Mapping, Sequence
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.matchfit.core import SearchMode
from app.kernel import Sport
from app.modules.proposals.application.answers import YesAnswer
from app.modules.proposals.application.group_deck import GroupDeck
from app.modules.proposals.application.live_yeses import LiveYeses, NamedLiveYes
from app.modules.proposals.application.payments_to_confirm import PaymentToConfirm
from app.modules.proposals.domain.deck import CardType, CourtState, DeckCard
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
from app.modules.proposals.domain.ports import DeckPerson, PaymentRefusal


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


class YesAnswerResponse(BaseModel):
    """What a yes left on the game — and, when it was the last, what the fill
    did."""

    proposal_id: UUID
    open_seats: int = Field(
        description=(
            "Seats nobody is In on yet, this player's yes counted. Nought on a "
            "game that booked — and on a full game an On request club has still "
            "to confirm. A payment that could not be held opens its seat again."
        )
    )
    booked: BookedSchema | None = Field(
        default=None,
        description=(
            "Present when this yes booked the game: every seat was charged, and "
            "the booking and its Game are open. `null` otherwise."
        ),
    )
    your_payment: YourPaymentSchema | None = Field(
        default=None,
        description=(
            "Present when **this player's** share could not be held: nobody paid "
            "and the game did not book. `null` otherwise — including when "
            "somebody else's could not, which leaves `open_seats` above nought."
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
                    seat_charge_id=mine.seat_charge_id, refusal=mine.refusal
                )
            ),
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
        )


class LiveYesesResponse(BaseModel):
    """You › Payments' **LIVE YESES**: every yes of the reader's on a game that
    has not filled, across groups, soonest game first."""

    yeses: list[LiveYesSchema]
    cap_per_sport: int = Field(
        description="How many live yeses a player may have in one sport."
    )

    @classmethod
    def from_live(cls, live: LiveYeses) -> "LiveYesesResponse":
        return cls(
            yeses=[LiveYesSchema.from_named(named) for named in live.yeses],
            cap_per_sport=live.cap_per_sport,
        )


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

    proposal_id: UUID
    type: CardType = Field(
        description=(
            "`PICKED_FOR_YOU`, `CHALLENGE` (a member's post) or `SEAT_OPEN` (a "
            "rescue — dealt once rescues exist, #545)."
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
    share_grosze: int = Field(description="What this player pays if it fills.")
    deadline: datetime = Field(
        description=(
            "When the card leaves unfilled — its book-by. The client counts down "
            "only under 24 h."
        )
    )
    in_count: int = Field(
        description="People In on the whole game, every version counted."
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
            "fills the game and books it."
        )
    )
    no_free_cancellation: bool = Field(
        description="The club's cut-off has already passed for this game."
    )
    club_confirms: bool = Field(
        description=(
            "An On request club: a full game waits for the club's yes before "
            "anybody pays, so *Book it now* charges nobody at once and its stamp "
            "carries no price."
        )
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
        def name_of(player_id: UUID) -> str | None:
            person = people.get(player_id)
            return None if person is None else person.name

        def tile(player_id: UUID) -> DeckTileSchema:
            person = people.get(player_id)
            return DeckTileSchema(
                player_id=player_id,
                is_you=player_id == reader,
                name=name_of(player_id),
                photo_id=None if person is None else person.photo_id,
                photo_url=None if person is None else person.photo_url,
                level=None if person is None else person.level,
                is_in=player_id in card.in_,
            )

        challenger = card.challenger_id
        return cls(
            proposal_id=card.proposal_id,
            type=card.type,
            kind=card.kind,
            challenger=None
            if challenger is None
            else DeckChallengerSchema(player_id=challenger, name=name_of(challenger)),
            starts_at=card.start,
            club=DeckClubSchema(id=card.club_id, name=club_names.get(card.club_id)),
            share_grosze=card.share_grosze,
            deadline=card.deadline,
            in_count=len(card.in_),
            version_count=card.version_count,
            open_seats_after_your_yes=card.open_seats_after_your_yes,
            court=card.court,
            no_free_cancellation=card.no_free_cancellation,
            club_confirms=card.club_confirms,
            sides=DeckSidesSchema(
                yours=[tile(player) for player in card.sides.yours],
                theirs=[tile(player) for player in card.sides.theirs],
            ),
            forecast=None
            if card.forecast is None
            else DeckForecastSchema(
                pct=card.forecast.pct, provisional=card.forecast.provisional
            ),
            overlap=_overlap(card.overlap),
        )


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
            "This segment's cards in the order dealt: seats open after the "
            "reader's yes (fewest first), then seat open › challenge › pick, "
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
                )
                for one in owed
            ]
        )
