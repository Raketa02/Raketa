"""The wire shape of Now: the envelope, three regions, and the card contract.

Two clients generate their types from this and neither validates at runtime, so
every rule below is either a *shape* or it is nothing. Where a rule could be
written as a shape it is: three card types rather than one with holes, a nested
situation half rather than a flat card, two distinct payload forms rather than
one with a sometimes-absent field.

**Field names are ``snake_case``**, matching every schema this backend already
emits; **enum values are verbatim as the decisions name them** (``inventoryLost``,
``bestFit``, ``takeSeat``). That split is not cosmetic. A field name is this
repo's convention and a mixed-case document is worse than either convention; an
enum *value* is the key a client's exhaustive ``Record`` is written against, and
renaming one is a client release.

**Every enumeration crosses as a generated union**, never as a bare string — a
bare string degrades that ``Record`` into an index signature that never fires,
which is the one failure mode a typecheck cannot reach afterwards.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal, get_args
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.fit import (
    BalanceFact,
    FamiliarityFact,
    LadderFact,
    MatchTypeFact,
    PriceFact,
    ReliabilityFact,
    SkillOverlapFact,
    TermCode,
    TimeFact,
    TravelFact,
    ViabilityFact,
)
from app.engines.forecast import Certainty
from app.engines.matchmaking import (
    CourtHold,
    LadderQualification,
    MatchTypePreference,
    Weekday,
)
from app.kernel import Cause, Cover, Outcome, Situation, exhaustive, invariant

from app.modules.now.domain.screen import (
    Block,
    CardDeparture,
    ClubCard,
    DebtLine,
    DepartureNothingTaken,
    Door,
    EnrolledRegion,
    Fit,
    FitReason,
    HoldNote,
    Level,
    MatchCard,
    Money,
    NowScreen,
    OffersRegion,
    OwnerExposure,
    PersonCard,
    Place,
    Refund,
    ScoreLine,
    ScoreSide,
    SeatClaim,
    SeatCounts,
    SetScore,
    Shelf,
    ShelfCard,
    ShelvesRegion,
    SituationFacts,
    SituationHalf,
)
from app.modules.now.domain.vocabulary import (
    ActCode,
    BlockType,
    CaptionCode,
    CardHoldReason,
    CardType,
    Currency,
    DepartureForm,
    FitSide,
    DoorCode,
    RefundDestination,
    ShelfCode,
)


class MoneyResponse(BaseModel):
    """Integer grosze, with a currency beside it. The comma is the client's."""

    amount: int
    currency: Currency

    @classmethod
    def from_domain(cls, money: Money) -> "MoneyResponse":
        return cls(amount=int(money.amount), currency=money.currency)


class PlaceResponse(BaseModel):
    """Where: the club, its IANA zone, whether there is a roof, and how far."""

    club_id: UUID
    club_name: str
    # The zone is the club's clock face. A phone formatting a match in its own
    # zone is right for every player at home and wrong for every player
    # travelling.
    zone: str
    cover: Cover
    # Rounded kilometres or nothing. Absent is a fact about what the platform
    # knows, never a zero.
    distance_km: int | None = None

    @classmethod
    def from_domain(cls, place: Place) -> "PlaceResponse":
        return cls(
            club_id=place.club_id,
            club_name=place.club_name,
            zone=str(place.zone),
            cover=place.cover,
            distance_km=place.distance_km,
        )


class HourWindowResponse(BaseModel):
    """One stretch of a clock face a player said she can play, in minutes."""

    start: int
    end: int


class SkillOverlapPayload(BaseModel):
    """Her Level, the Level this match is aimed at, and which side she is on.

    ``band_half_width`` is **which of the two answers the target came from**,
    carried as the quantity rather than as a label: absent means the target is
    the exact *seat target*, present means it is the midpoint of a band that wide
    either side. So a client writes *"this seat is aimed at 3,10"* or *"this
    match is aimed at 2,60–3,60"* from one payload.

    ``side`` is the delta's *"which side a skill mismatch fell on"*. The term is
    symmetric — a Level too strong and a Level too weak are both *not the match
    you belong in* — so the score cannot say, and *"you would be the strongest
    here"* and *"you would be stretched"* are different sentences.
    """

    code: Literal[TermCode.SKILL_OVERLAP] = TermCode.SKILL_OVERLAP
    level: float
    target: float
    band_half_width: float | None = None
    side: FitSide


class BalancePayload(BaseModel):
    """The forecast this term read, and how sure of it the platform is.

    ``certainty`` crosses so that **suppression stays a presentation decision**:
    the term scores on the estimate whatever the grade is, and a client that
    declines to print a LOW forecast can only know to do that if the grade
    travels with it.
    """

    code: Literal[TermCode.PREDICTED_BALANCE] = TermCode.PREDICTED_BALANCE
    estimate: int
    margin: int
    certainty: Certainty
    imputed_seats: int


class TimePayload(BaseModel):
    """When the match starts on the club's clock face, and when she said.

    Both halves in the vocabulary the declaration is made in — a weekday number
    and a minute of the day — so the client owns the words and the locale, and
    the two are the **club's** local day and minute rather than anything read off
    a UTC instant.

    ``days`` and ``hours`` are the declaration itself and are absent when she
    made none, which is what lets a client say *"Tuesday 18:30"* rather than
    *"Tuesday 18:30, outside the hours you gave"* to somebody who gave none.
    """

    code: Literal[TermCode.TIME_FIT] = TermCode.TIME_FIT
    weekday: Weekday
    minute: int
    days: list[Weekday] | None = None
    hours: list[HourWindowResponse] | None = None


class ViabilityPayload(BaseModel):
    """The four facts behind *will this match actually be played*.

    ``paid_seats`` and ``sold_seats`` rather than the fraction between them,
    because *three of four* and *seventy-five per cent* are the same number and
    not the same sentence, and the one a card shows is the first.
    """

    code: Literal[TermCode.MATCH_VIABILITY] = TermCode.MATCH_VIABILITY
    paid_seats: int
    sold_seats: int
    hold: CourtHold
    minutes_to_cutoff: int
    crowding: float


class PricePayload(BaseModel):
    """What she owes for the seat, and the ceiling she declared, both in grosze.

    ``ceiling`` is absent when she declared none, which is what a client needs in
    order to say *"38 zł"* rather than *"38 zł, under your ceiling"* — the second
    sentence is a claim about a declaration that does not exist.
    """

    code: Literal[TermCode.PRICE] = TermCode.PRICE
    payable: int
    ceiling: int | None = None


class TravelPayload(BaseModel):
    """How far away it is and how far she said she would go, both in minutes."""

    code: Literal[TermCode.TRAVEL] = TermCode.TRAVEL
    minutes: int
    radius: int | None = None


class MatchTypePayload(BaseModel):
    """Whether the match is counted, and what she asked for.

    ``preference`` is the enum and not a rendered word, for the same reason
    ``counted`` is a bool: *"a friendly, and you asked for counted matches"* is a
    sentence the client owns, assembled from two machine values.
    """

    code: Literal[TermCode.MATCH_TYPE] = TermCode.MATCH_TYPE
    counted: bool
    preference: MatchTypePreference | None = None


class LadderPayload(BaseModel):
    """Which of the three ladder states this match is in for her."""

    code: Literal[TermCode.LADDER_QUALIFICATION] = TermCode.LADDER_QUALIFICATION
    qualification: LadderQualification


class ReliabilityPayload(BaseModel):
    """The reliability the term scored on, and how many records it read.

    ``observed`` against ``seated`` is the difference between *"this group turns
    up"* and *"one of these four has a record and the rest are strangers"*, which
    the term's value alone cannot separate.
    """

    code: Literal[TermCode.GROUP_RELIABILITY] = TermCode.GROUP_RELIABILITY
    least_reliable: float
    observed: int
    seated: int


class FamiliarityPayload(BaseModel):
    """How many of the others are new to her, out of how many."""

    code: Literal[TermCode.FAMILIARITY] = TermCode.FAMILIARITY
    new_faces: int
    others: int


#: What a reason says about itself, in quantities. **One member per term the
#: engine can emit**, discriminated on the same ``TermCode`` the reason carries.
#:
#: All ten are here and two of them cannot be produced today — group reliability
#: and familiarity are evidence terms whose sources ship dark, so they are
#: *excluded* rather than scored and an excluded term is never a reason. They are
#: modelled anyway, and that is the opposite of #98's defect rather than a repeat
#: of it: ``TermCode`` **already** crosses with all ten names, so a client already
#: holds ten rows, and the failure mode of leaving two out is a reason with no
#: payload the day a Player Score arrives — a screen that breaks on new data
#: rather than a field nobody fills.
FitReasonPayload = (
    SkillOverlapPayload
    | BalancePayload
    | TimePayload
    | ViabilityPayload
    | PricePayload
    | TravelPayload
    | MatchTypePayload
    | LadderPayload
    | ReliabilityPayload
    | FamiliarityPayload
)

FitReasonFact = Annotated[FitReasonPayload, Field(discriminator="code")]

#: Every code the payload union covers, read **off the union itself** rather
#: than restated. Adding an eleventh ``TermCode`` without a payload class for it
#: fails at import, which is the only moment anybody would notice.
_PAYLOAD_CODES = {
    member.model_fields["code"].default for member in get_args(FitReasonPayload)
}

invariant(
    _PAYLOAD_CODES == set(TermCode),
    "a term the engine can emit has no payload on the wire",
)


def _payload(reason: FitReason) -> FitReasonPayload:
    """One term's quantities, in the shape its own code discriminates.

    An ``isinstance`` chain closed with ``exhaustive``, so a member added to the
    engine's ``TermFact`` union is a **type error here** rather than a fall
    through to a payload it is not. The set comparison above catches the other
    half of the same mistake — a code with no payload class — and neither guard
    sees what the other does.
    """

    fact = reason.fact
    if isinstance(fact, SkillOverlapFact):
        return SkillOverlapPayload(
            level=float(fact.level),
            target=float(fact.target),
            band_half_width=(
                None if fact.band_half_width is None else float(fact.band_half_width)
            ),
            # Read off the domain reason, whose ``side`` is derived from the two
            # Levels the term scored on. Recomputing the comparison here would
            # be the second implementation of one subtraction's sign.
            side=reason.side or FitSide.EVEN,
        )
    if isinstance(fact, BalanceFact):
        return BalancePayload(
            estimate=fact.estimate,
            margin=fact.margin,
            certainty=fact.certainty,
            imputed_seats=fact.imputed_seats,
        )
    if isinstance(fact, TimeFact):
        return TimePayload(
            weekday=fact.weekday,
            minute=int(fact.minute),
            days=(
                None
                if fact.days is None
                else sorted(fact.days, key=lambda day: day.value)
            ),
            hours=(
                None
                if fact.hours is None
                else [
                    HourWindowResponse(start=int(one.start), end=int(one.end))
                    for one in fact.hours
                ]
            ),
        )
    if isinstance(fact, ViabilityFact):
        return ViabilityPayload(
            paid_seats=fact.paid_seats,
            sold_seats=fact.sold_seats,
            hold=fact.hold,
            minutes_to_cutoff=int(fact.minutes_to_cutoff),
            crowding=float(fact.crowding),
        )
    if isinstance(fact, PriceFact):
        return PricePayload(
            payable=int(fact.payable),
            ceiling=None if fact.ceiling is None else int(fact.ceiling),
        )
    if isinstance(fact, TravelFact):
        return TravelPayload(
            minutes=int(fact.minutes),
            radius=None if fact.radius is None else int(fact.radius),
        )
    if isinstance(fact, MatchTypeFact):
        return MatchTypePayload(counted=fact.counted, preference=fact.preference)
    if isinstance(fact, LadderFact):
        return LadderPayload(qualification=fact.qualification)
    if isinstance(fact, ReliabilityFact):
        return ReliabilityPayload(
            least_reliable=float(fact.least_reliable),
            observed=fact.observed,
            seated=fact.seated,
        )
    if isinstance(fact, FamiliarityFact):
        return FamiliarityPayload(new_faces=fact.new_faces, others=fact.others)
    exhaustive(fact)


class FitReasonResponse(BaseModel):
    """One reason behind the badge: a code, its quantities, and no sentence.

    **No weight, no value and no contribution.** All three are the engine's
    arithmetic and a player cannot act on any of them; a number that ranks is
    not a number that explains. What crosses is the term's own payload in the
    units the kernel keeps them in — grosze, minutes, exact ratios as decimals,
    a weekday, a Level — and the client writes the sentence.

    The specification had ``reasons: string[]``, three sentences the server
    wrote. That was the single precedent for server-held copy anywhere in this
    contract, and the two clients do not share a shape, a language or a currency
    symbol.
    """

    code: TermCode
    fact: FitReasonFact

    @classmethod
    def from_domain(cls, reason: FitReason) -> "FitReasonResponse":
        return cls(code=reason.code, fact=_payload(reason))


class FitResponse(BaseModel):
    """The badge, up to three reasons, and the aim. Coverage is never here.

    ``target`` is the Level this match is aimed at and crosses **only when it is
    precise** — the seat target, which exists only while exactly one seat is
    open. A target *band* is nearly always the viewer's own band restated, so
    printing it would be the card telling her what she already knows in the voice
    of a measurement.
    """

    score: int = Field(ge=20, le=99)
    unsure: bool
    reasons: list[FitReasonResponse]
    target: float | None = None

    @classmethod
    def from_domain(cls, fit: Fit) -> "FitResponse":
        return cls(
            score=fit.score,
            unsure=fit.unsure,
            reasons=[FitReasonResponse.from_domain(r) for r in fit.reasons],
            target=fit.target,
        )


class SeatClaimResponse(BaseModel):
    """A live claim on this card's seat, and when it lapses."""

    expires_at: datetime

    @classmethod
    def from_domain(cls, claim: SeatClaim) -> "SeatClaimResponse":
        return cls(expires_at=claim.expires_at)


class HoldNoteResponse(BaseModel):
    """Why a court is held, as one of five reasons. Never free text.

    ``age_minutes`` is the hold's **real** age and rides only on one the club has
    taken back — never the club's threshold, because the card weakening the
    marketplace's promise is the last place to print a number that is not the
    one meant.
    """

    reason: CardHoldReason
    age_minutes: int | None = None

    @classmethod
    def from_domain(cls, note: HoldNote) -> "HoldNoteResponse":
        return cls(reason=note.reason, age_minutes=note.age_minutes)


class SeatCountsResponse(BaseModel):
    """What a counting sentence counts. **Counting is by money.**

    ``paid`` and ``held`` are two numbers and never one: a held-and-unpaid seat
    is a name with no money behind it and can lapse, so folding it into the
    count tells four people a match is complete while a seat may still go.

    ``turned_up`` is present once the match has been played and absent before —
    it is the third thing ``{f} of {n}`` counts, and it is **sent** rather than
    derived, because *one less than the seats* stops being minus one the moment
    a doubles match loses two people.
    """

    seats: int
    paid: int
    held: int
    turned_up: int | None = None

    @classmethod
    def from_domain(cls, counts: SeatCounts) -> "SeatCountsResponse":
        return cls(
            seats=counts.seats,
            paid=counts.paid,
            held=counts.held,
            turned_up=counts.turned_up,
        )


class RefundResponse(BaseModel):
    """What a cancellation returns, and where it went.

    The destination fixes the tense, so it crosses rather than being derived
    from the cause on the phone: a card refund is never claimed to have landed,
    and a club credit is definite because it genuinely is instant.
    """

    amount: MoneyResponse
    destination: RefundDestination

    @classmethod
    def from_domain(cls, refund: Refund) -> "RefundResponse":
        return cls(
            amount=MoneyResponse.from_domain(refund.amount),
            destination=refund.destination,
        )


class OwnerExposureResponse(BaseModel):
    """A private court's two figures, which disagree on purpose.

    What has come back, and the whole court still guaranteed until the sold
    format is met. The gap between them **is** the product fact: she watches
    money arrive while owing exactly what she owed at the start.
    """

    recovered: MoneyResponse
    guaranteed: MoneyResponse

    @classmethod
    def from_domain(cls, owner: OwnerExposure) -> "OwnerExposureResponse":
        return cls(
            recovered=MoneyResponse.from_domain(owner.recovered),
            guaranteed=MoneyResponse.from_domain(owner.guaranteed),
        )


class ScoreSideResponse(BaseModel):
    """One side of the net, named by the players who were on it."""

    players: list[str]

    @classmethod
    def from_domain(cls, side: ScoreSide) -> "ScoreSideResponse":
        return cls(players=list(side.players))


class SetScoreResponse(BaseModel):
    """One set, two integers, and no tiebreak field in v1."""

    first: int
    second: int

    @classmethod
    def from_domain(cls, one: SetScore) -> "SetScoreResponse":
        return cls(first=one.first, second=one.second)


class ScoreLineResponse(BaseModel):
    """The score as sets of two integers, never a display string.

    ``sides[0]`` is the viewer's when she played, and ``first`` in every set is
    that side's games. **No level movement** rides beside it: no engine produces
    one, and a card must not invent a number nothing computed.
    """

    sides: list[ScoreSideResponse]
    sets: list[SetScoreResponse]

    @classmethod
    def from_domain(cls, score: ScoreLine) -> "ScoreLineResponse":
        return cls(
            sides=[ScoreSideResponse.from_domain(side) for side in score.sides],
            sets=[SetScoreResponse.from_domain(one) for one in score.sets],
        )


class DepartureRecoverableResponse(BaseModel):
    """A leaver who paid: what she paid, and what became of it.

    ``outcome`` is absent while nothing has decided it — whether the money comes
    back depends entirely on her seat refilling, which is why her card keeps the
    match's own progress beside this.
    """

    form: Literal[DepartureForm.RECOVERABLE] = DepartureForm.RECOVERABLE
    paid: MoneyResponse
    outcome: Outcome | None = None


class DepartureNothingTakenResponse(BaseModel):
    """A leaver whose money never left, and so a payload with no amount at all."""

    form: Literal[DepartureForm.NOTHING_TAKEN] = DepartureForm.NOTHING_TAKEN


#: Two forms, discriminated, and never one payload with a sometimes-absent
#: amount (ADR-0072): *nothing was taken* and *nothing has come back yet* are
#: opposite sentences and a blank cannot tell them apart.
DepartureResponse = Annotated[
    DepartureRecoverableResponse | DepartureNothingTakenResponse,
    Field(discriminator="form"),
]


def _departure(
    departure: CardDeparture,
) -> DepartureRecoverableResponse | DepartureNothingTakenResponse:
    if isinstance(departure, DepartureNothingTaken):
        return DepartureNothingTakenResponse()
    return DepartureRecoverableResponse(
        paid=MoneyResponse.from_domain(departure.paid),
        outcome=departure.outcome,
    )


class SituationFactsResponse(BaseModel):
    """The facts the situation's sentence prints.

    Two are always here — the counting and the court's total — and the rest are
    present exactly when the fact exists. That is a rule per fact rather than a
    table of thirty-six judgements: no situation is named anywhere in the
    composition, and a client reading a field that is absent has met a state
    where the fact does not exist rather than a state somebody forgot.
    """

    counts: SeatCountsResponse
    # The court's total, for **every** audience. The subject of `{price} settled
    # to the club` is the court, and what it tells the viewer is *this game is
    # happening*; her own share is on the spine beside it.
    court_total: MoneyResponse
    hold: HoldNoteResponse | None = None
    cause: Cause | None = None
    # The specific court, drawn only shortly before play. Everywhere earlier the
    # card says the category, because a court is assigned and may be reassigned.
    court: str | None = None
    refund: RefundResponse | None = None
    owner: OwnerExposureResponse | None = None
    score: ScoreLineResponse | None = None
    departure: DepartureResponse | None = None

    @classmethod
    def from_domain(cls, facts: SituationFacts) -> "SituationFactsResponse":
        return cls(
            counts=SeatCountsResponse.from_domain(facts.counts),
            court_total=MoneyResponse.from_domain(facts.court_total),
            hold=(
                None if facts.hold is None else HoldNoteResponse.from_domain(facts.hold)
            ),
            cause=facts.cause,
            court=facts.court,
            refund=(
                None
                if facts.refund is None
                else RefundResponse.from_domain(facts.refund)
            ),
            owner=(
                None
                if facts.owner is None
                else OwnerExposureResponse.from_domain(facts.owner)
            ),
            score=(
                None
                if facts.score is None
                else ScoreLineResponse.from_domain(facts.score)
            ),
            departure=(
                None if facts.departure is None else _departure(facts.departure)
            ),
        )


class SituationHalfResponse(BaseModel):
    """The half a client reads only when it knows the name.

    A phone that does not recognise ``situation`` draws the spine and omits the
    status line. It never skips the card, and it never asks the server for a
    compatibility map: losing the sentence loses exactly the thing that is
    actually missing.
    """

    situation: Situation
    facts: SituationFactsResponse

    @classmethod
    def from_domain(cls, half: SituationHalf) -> "SituationHalfResponse":
        return cls(
            situation=half.situation,
            facts=SituationFactsResponse.from_domain(half.facts),
        )


class MatchCardResponse(BaseModel):
    """A match card: the spine every phone draws, and the situation half."""

    card_type: Literal[CardType.MATCH] = CardType.MATCH
    match_id: UUID
    stamp: int
    # The one clock slot. Empty on a card that is over or cancelled — those count
    # to nothing rather than to zero.
    clock: datetime | None = None
    where: PlaceResponse
    price: MoneyResponse
    fit: FitResponse | None = None
    emphasis: bool = False
    # A code alone, with no target beside it: each of the seven determines its own
    # destination, and the card already identifies the thing it is about.
    act: ActCode | None = None
    may_depart: bool = False
    seat_claim: SeatClaimResponse | None = None
    situation: SituationHalfResponse

    @classmethod
    def from_domain(cls, card: MatchCard) -> "MatchCardResponse":
        return cls(
            match_id=card.match_id,
            stamp=card.stamp,
            clock=card.clock,
            where=PlaceResponse.from_domain(card.where),
            price=MoneyResponse.from_domain(card.price),
            fit=None if card.fit is None else FitResponse.from_domain(card.fit),
            emphasis=card.emphasis,
            act=card.act,
            may_depart=card.may_depart,
            seat_claim=(
                None
                if card.seat_claim is None
                else SeatClaimResponse.from_domain(card.seat_claim)
            ),
            situation=SituationHalfResponse.from_domain(card.situation),
        )


class LevelResponse(BaseModel):
    """A Level on the fixed 1,0-5,0 scale, and the quiet marker beside it.

    ``provisional`` is a **boolean and never a second number**. A rating that has
    seen no counted match cannot exceed 30 % Confidence, and a 3,2 from six
    questions is visually identical to a 3,4 from eleven matches — so the card
    says *this is an estimate* and stops there. Printing the percentage would be
    the second gauge ADR-0037 refused; printing nothing would claim a certainty
    the platform does not have.

    ``value`` crosses as a number. The comma is the client's, like every other
    value in ``docs/value-formatting.md``.
    """

    value: float
    provisional: bool

    @classmethod
    def from_domain(cls, level: Level) -> "LevelResponse":
        return cls(value=level.value, provisional=level.provisional)


class PersonCardResponse(BaseModel):
    """A player who has just arrived. No situation, no clock, no price.

    ``level`` is **required**: a player reaches this shelf only through a rating
    at the shelf's sport, so an optional Level would be a hole for a state the
    retrieval cannot produce — the same defect one card type with holes has.
    """

    card_type: Literal[CardType.PERSON] = CardType.PERSON
    player_id: UUID
    stamp: int
    nickname: str
    level: LevelResponse

    @classmethod
    def from_domain(cls, card: PersonCard) -> "PersonCardResponse":
        return cls(
            player_id=card.player_id,
            stamp=card.stamp,
            nickname=card.nickname,
            level=LevelResponse.from_domain(card.level),
        )


class ClubCardResponse(BaseModel):
    """A club that has just joined. No situation, no clock, no price."""

    card_type: Literal[CardType.CLUB] = CardType.CLUB
    club_id: UUID
    stamp: int
    name: str
    distance_km: int | None = None

    @classmethod
    def from_domain(cls, card: ClubCard) -> "ClubCardResponse":
        return cls(
            club_id=card.club_id,
            stamp=card.stamp,
            name=card.name,
            distance_km=card.distance_km,
        )


#: Discriminated on the card's own type, never on the shelf that holds it: a card
#: is identified by the thing it is about, so one answer corrects every copy of it
#: on the screen.
ShelfCardResponse = Annotated[
    MatchCardResponse | PersonCardResponse | ClubCardResponse,
    Field(discriminator="card_type"),
]


AnyCardResponse = MatchCardResponse | PersonCardResponse | ClubCardResponse


def _shelf_card(card: ShelfCard) -> AnyCardResponse:
    if isinstance(card, MatchCard):
        return MatchCardResponse.from_domain(card)
    if isinstance(card, PersonCard):
        return PersonCardResponse.from_domain(card)
    return ClubCardResponse.from_domain(card)


class ShelfResponse(BaseModel):
    """A code, an optional caption code, and cards. No title, and no tail card."""

    block_type: Literal[BlockType.SHELF] = BlockType.SHELF
    code: ShelfCode
    caption: CaptionCode | None = None
    cards: list[ShelfCardResponse]

    @classmethod
    def from_domain(cls, shelf: Shelf) -> "ShelfResponse":
        return cls(
            code=shelf.code,
            caption=shelf.caption,
            cards=[_shelf_card(card) for card in shelf.cards],
        )


class DoorResponse(BaseModel):
    """The way into a sport's questionnaire, where its shelves would have been.

    One code and nothing else. **Not the sport** — the client named it on the
    request and still holds it, and a second copy on the answer is a second thing
    that can disagree; the tail card into Find is composed by the client from the
    same two halves for the same reason. **Not a destination** either: the code
    determines one, exactly as an act code does.

    It is a block in the shelves list rather than a field beside it, so an old
    build that has never heard of it drops one entry from a list it already
    iterates, and every client that draws Now decides what to do with it rather
    than inferring it from absent shelves (ADR-0084).
    """

    block_type: Literal[BlockType.DOOR] = BlockType.DOOR
    code: DoorCode

    @classmethod
    def from_domain(cls, door: Door) -> "DoorResponse":
        return cls(code=door.code)


#: Discriminated on the block's own type, on the rule ``ShelfCardResponse``
#: follows one ring in: a shelf and a door are two shapes with nothing in common
#: but their position, so a union makes a client that fails to narrow a type error
#: rather than a row it draws blank.
BlockResponse = Annotated[
    ShelfResponse | DoorResponse,
    Field(discriminator="block_type"),
]


def _block(block: Block) -> ShelfResponse | DoorResponse:
    if isinstance(block, Shelf):
        return ShelfResponse.from_domain(block)
    return DoorResponse.from_domain(block)


class OffersRegionResponse(BaseModel):
    """Seats offered to this viewer, soonest-to-expire first."""

    stamp: int
    cards: list[MatchCardResponse]

    @classmethod
    def from_domain(cls, region: OffersRegion) -> "OffersRegionResponse":
        return cls(
            stamp=region.stamp,
            cards=[MatchCardResponse.from_domain(c) for c in region.cards],
        )


class EnrolledRegionResponse(BaseModel):
    """The matches this viewer is committed to, chronological."""

    stamp: int
    cards: list[MatchCardResponse]

    @classmethod
    def from_domain(cls, region: EnrolledRegion) -> "EnrolledRegionResponse":
        return cls(
            stamp=region.stamp,
            cards=[MatchCardResponse.from_domain(c) for c in region.cards],
        )


class ShelvesRegionResponse(BaseModel):
    """The shelves, in the server's order. A shelf with nothing in it is absent.

    The list may also carry **the door**, in the position the ranked shelves would
    occupy. The field keeps its name: renaming it would break every client reading
    a region that has not otherwise changed, for a word, on a screen whose list is
    shelves in every case but one.
    """

    stamp: int
    shelves: list[BlockResponse]

    @classmethod
    def from_domain(cls, region: ShelvesRegion) -> "ShelvesRegionResponse":
        return cls(
            stamp=region.stamp,
            shelves=[_block(block) for block in region.shelves],
        )


class DebtLineResponse(BaseModel):
    """What is owed, and the one consequence of owing it.

    ``blocked`` means *this player may not create a match or book a court*. She
    may still pay for a seat in somebody else's match: being cut off must not make
    her less likely to pay.
    """

    owed: MoneyResponse
    blocked: bool

    @classmethod
    def from_domain(cls, debt: DebtLine) -> "DebtLineResponse":
        return cls(owed=MoneyResponse.from_domain(debt.owed), blocked=debt.blocked)


class NowResponse(BaseModel):
    """The whole screen: three regions, and the one fact about the viewer.

    There is **no screen-level stamp** and no ``server_time``. A screen is never
    replaced as a unit except by a compose, and a compose is three stamped regions
    arriving together.
    """

    offers: OffersRegionResponse
    your_matches: EnrolledRegionResponse
    shelves: ShelvesRegionResponse
    debt: DebtLineResponse | None = None

    @classmethod
    def from_domain(cls, screen: NowScreen) -> "NowResponse":
        return cls(
            offers=OffersRegionResponse.from_domain(screen.offers),
            your_matches=EnrolledRegionResponse.from_domain(screen.your_matches),
            shelves=ShelvesRegionResponse.from_domain(screen.shelves),
            debt=(
                None
                if screen.debt is None
                else DebtLineResponse.from_domain(screen.debt)
            ),
        )
