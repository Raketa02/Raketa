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
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.fit import TermCode
from app.kernel import Cause, Situation

from app.modules.now.domain.screen import (
    Block,
    ClubCard,
    DebtLine,
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
    PersonCard,
    Place,
    SeatClaim,
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
    Cover,
    Currency,
    DoorCode,
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


class FitReasonResponse(BaseModel):
    """One reason behind the badge, as a machine code. No weight, no sentence."""

    code: TermCode

    @classmethod
    def from_domain(cls, reason: FitReason) -> "FitReasonResponse":
        return cls(code=reason.code)


class FitResponse(BaseModel):
    """The badge and up to three reasons. Coverage is not here and never is."""

    score: int = Field(ge=20, le=99)
    unsure: bool
    reasons: list[FitReasonResponse]

    @classmethod
    def from_domain(cls, fit: Fit) -> "FitResponse":
        return cls(
            score=fit.score,
            unsure=fit.unsure,
            reasons=[FitReasonResponse.from_domain(r) for r in fit.reasons],
        )


class SeatClaimResponse(BaseModel):
    """A live claim on this card's seat, and when it lapses."""

    expires_at: datetime

    @classmethod
    def from_domain(cls, claim: SeatClaim) -> "SeatClaimResponse":
        return cls(expires_at=claim.expires_at)


class HoldNoteResponse(BaseModel):
    """Why a court is held, as one of five reasons. Never free text."""

    reason: CardHoldReason

    @classmethod
    def from_domain(cls, note: HoldNote) -> "HoldNoteResponse":
        return cls(reason=note.reason)


class SituationFactsResponse(BaseModel):
    """The facts the situation's sentence prints."""

    hold: HoldNoteResponse | None = None
    cause: Cause | None = None

    @classmethod
    def from_domain(cls, facts: SituationFacts) -> "SituationFactsResponse":
        return cls(
            hold=(
                None
                if facts.hold is None
                else HoldNoteResponse.from_domain(facts.hold)
            ),
            cause=facts.cause,
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
