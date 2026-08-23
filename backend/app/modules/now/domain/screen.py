"""The composed screen: three ordered regions, one viewer fact, and a card.

This is ADR-0070's envelope as values rather than as prose. Nothing here reads a
clock, a repository or a request — a screen is *composed* by the application
layer and then rendered by the presentation layer, and this module is what the
two agree about.

**Three regions, always present, possibly empty.** A *shelf* with nothing in it
is **absent**, because a shelf makes a claim and a row that appears every week
saying *nothing worth waiting for* is a row players learn to scroll past. A
*region* with nothing in it is **present and empty**, because a region makes no
claim — and because *not there* and *there and empty* handled in one place and
not the other is the most productive bug in this class.

**A card is identified by the thing it is about** — a match, a person, a club —
never by its position or by the shelf it sits in. One match may appear on more
than one shelf, and under thing identity one answer corrects every copy.

**A card is two nested halves.** The **spine** is read always; the **situation
half** is read only when the client knows that situation. A client that meets a
name it cannot render draws the spine and omits the status line — it never skips
the card, because an app hiding a match the player has paid for reads as *your
app lost my booking*. That rule is a **shape** here rather than a discipline: a
flat card would leave the first person to add a situation-dependent field at the
top level breaking it in silence.

**What is deliberately absent** and must stay so: ``serverTime``,
``nextTransition``, a degrade marker, a policy version, the tag, the tone, the
alert, a ``phase``, and free text of any kind. The first two are ADR-0071's
*two fields with no reader are not forwards-compatibility*; the degrade marker
would be a fact about our infrastructure printed on a player's home screen; and
the last four are the client's own tables.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.engines.fit import SkillOverlapFact, TermCode, TermFact
from app.kernel import (
    Cause,
    Cover,
    Grosze,
    Instant,
    Outcome,
    Situation,
    Sport,
    Zone,
)

from app.modules.now.domain.vocabulary import (
    ActCode,
    BlockType,
    CaptionCode,
    CardHoldReason,
    CardType,
    Currency,
    DepartureForm,
    DoorCode,
    FitSide,
    RefundDestination,
    ShelfCode,
)

#: A monotonically increasing integer, carried once per region and once per card,
#: with **no screen-level stamp**: a screen is never replaced as a unit except by
#: a compose, and a compose is three stamped regions arriving together.
#:
#: The race it exists for is a pull and a tap racing — a compose composed
#: *before* an action that landed *after* it, undoing in front of the player what
#: they just did. Per-card stamps alone cannot resolve it, because the race is
#: over **membership and order**, which no per-card value can express; a single
#: screen stamp would discard a late compose whole, including the majority of it
#: that was genuinely newer. A region is the unit an update already replaces, so
#: it is the unit that can be compared.
#:
#: Increasing integers, not opaque strings: the reader they are waiting for is
#: the deferred live channel, whose monotonic acceptance asks *is this newer than
#: what I hold* — a question that needs an order.
Stamp = int


@final
@dataclass(frozen=True)
class Money:
    """Integer grosze with a currency beside it, and never a formatted string.

    ``payable == share`` for every player in v1: nothing in the product yet
    reduces what one player owes below their share of the court, so the card
    carries one money number and not two.
    """

    amount: Grosze
    currency: Currency = Currency.PLN


@final
@dataclass(frozen=True)
class Place:
    """Where — the club, its clock face, whether there is a roof, and how far.

    **The zone lives here and not on the moment.** ADR-0073 puts indoor-or-outdoor
    on the spine *"alongside the club, its timezone and its optional distance"*,
    and that is the reading this takes: a card whose clock slot is empty — every
    cancelled and every played card — still prints a time as words, and a zone
    that travelled with the clock would be absent exactly there. One spelling, on
    every card, present whether or not anything is counting down.

    An ``Instant`` is UTC and never a clock face, and the zone is a fact about the
    **club**. A phone formatting in its own zone is correct for every player at
    home and wrong for every player travelling, which is the worst available bug:
    invisible in testing, and aimed at a person ADR-0063 explicitly builds for.

    ``distance_km`` is optional because a player's anchor is optional, and it is
    the *rounded* number the card prints as ``~{n} km`` — never a precision the
    product does not have.
    """

    club_id: UUID
    club_name: str
    zone: Zone
    cover: Cover
    distance_km: int | None = None


@final
@dataclass(frozen=True)
class FitReason:
    """One reason behind the badge: a code, its quantities, and no sentence.

    Up to three ride on a card. The code is the stable key a client renders copy
    for, which is what lets the wording of a reason change without a backend
    release. **No weight, no value and no contribution ever crosses** — all
    three are the engine's arithmetic, a player cannot act on any of them, and a
    number that ranks is not a number that explains.

    ``fact`` is the term's own payload, carried whole and in the units the
    kernel keeps them in: grosze, minutes, exact ratios, a weekday, a Level. It
    is what turns *"price"* into *"38 zł, under your 45 zł ceiling"* on a phone
    that was never sent either sentence. The specification's `reasons: string[]`
    was three sentences the server wrote; this is the same three reasons with
    the words left to the client, which is where the two clients' shapes diverge
    anyway.

    The fact is the engine's object rather than a copy of it — the same
    ``ScoredTerm.fact`` the score was computed from, so a card can never show a
    reason drawn from arithmetic other than the badge beside it.
    """

    code: TermCode
    fact: TermFact

    @property
    def side(self) -> FitSide | None:
        """Which side of the aim she fell on, for the one term that has sides.

        Derived and never carried, for the reason every derived number in this
        map is: a stored copy is a value a later edit can leave disagreeing with
        the two Levels it came from. The skill-overlap term is symmetric — a
        Level too strong and a Level too weak are both *not the match you belong
        in* — so the side is recoverable from the payload and unreadable from
        the score.

        ``None`` for every other term, because no other term has two sides to
        fall on.
        """

        if not isinstance(self.fact, SkillOverlapFact):
            return None
        if self.fact.target > self.fact.level:
            return FitSide.STRETCHED
        if self.fact.target < self.fact.level:
            return FitSide.STRONGEST
        return FitSide.EVEN


@final
@dataclass(frozen=True)
class Fit:
    """The badge, and why.

    ``score`` is **already clamped to 20–99**. The engine keeps its 0–100 range
    and the true value ranks the list; the pill never shows 8 or 100, because *a
    score of 3 is not more useful than a score of 20 — both mean no*, and never
    100 because certainty is never warranted.

    ``unsure`` is the warning that replaces the number's confidence when the
    engine has too little to go on. It is the engine's own warning restated as a
    boolean — the threshold (0,40, on the *raw* value of the lowest contributor)
    lives in ``matchfit/v1/constants.py`` and is never spelled again here, or the
    card and the score would stop agreeing the day it is retuned.

    **Coverage never crosses this wire in any form**: it ranks, it gates
    emphasis, and it may become words in a reason line. It never becomes a
    second gauge on the card, because a card must be decidable at a glance and
    two numbers are harder to explain than one.

    The whole sub-object is optional: it is omitted for a viewer with no rating
    in that sport, and under degrade. Printing 91 to a player the platform cannot
    place is flattery through absence.
    """

    score: int
    unsure: bool = False
    reasons: tuple[FitReason, ...] = ()

    #: The Level this match is aimed at, **only when it is precise**.
    #:
    #: The pairing engine answers at two resolutions: a *seat target*, which is
    #: the exact Level that would even the match and exists only while one seat
    #: is open, and a *target band*, which is blunt. Only the first crosses. A
    #: band is nearly always the viewer's own band restated, so printing it
    #: would be the card telling her what she already knows in a voice that
    #: sounds like a measurement.
    #:
    #: A number and never ``2,71``: the comma is the client's, like every other
    #: value in ``docs/value-formatting.md``.
    target: float | None = None


@final
@dataclass(frozen=True)
class SeatClaim:
    """Five minutes of exclusive right to buy one seat, while it is running.

    Its presence is the fact the client needs: a card under a live claim shows no
    exit control, and its clock is filled even on a shelf where every other card's
    is empty. The client is never asked to infer that from the act code.

    ``expires_at`` and the card's clock hold the same instant, and that is the one
    clock rule producing the same answer rather than one fact written twice: the
    clock is *the next moment at which something happens to the viewer whether
    they act or not*, and a claim lapsing in five minutes is exactly that.
    """

    expires_at: Instant


@final
@dataclass(frozen=True)
class HoldNote:
    """Why a court is being kept aside — a named reason, never a sentence.

    ``hold.note`` in the specification set was a sentence the server wrote, and
    it would have been the single precedent for server-held copy anywhere in the
    contract. Dropping the reason entirely was the serious alternative and is the
    worse of the two losing options: *why* a court is held is the difference
    between relaxing and chasing friends for the last seat.

    ``age_minutes`` is *"the hold's real age"* and rides only on a hold the club
    has taken back — ``now - held_since``, and the **hold's** age rather than the
    club's threshold. A hold that has sat seventy-one hours under a
    forty-eight-hour cap says seventy-one: a card weakening the marketplace's
    promise is the last place to print a number that is not the one meant.

    It is an elapsed span and not the instant to subtract from, which is the one
    place on this screen ADR-0053's *the phone only subtracts* does not apply —
    because the hold is **over**. A card counting up from a reclaim that has
    already happened would tick a number nothing is waiting for.
    """

    reason: CardHoldReason
    age_minutes: int | None = None


@final
@dataclass(frozen=True)
class SeatCounts:
    """What a counting sentence counts, sent as the numbers it prints.

    **Counting is by money** (ADR-0073). ``paid`` is seats somebody has paid
    for, which is the only count that means anything; ``held`` is a name with no
    money behind it and is **its own number beside that count, never folded into
    it** — counting people would tell a player a match is full while a seat may
    still lapse, and suppressing holds produces the same lie in reverse.

    **Every number the sentence prints is sent as that number.** The sentences
    reading *one less than the seats* get three and four, never *four, now take
    one off*: it is only ever minus one until a doubles match loses two people,
    at which point the phone would confidently print *3 of 4* and the player
    would believe three people played.

    ``turned_up`` is present exactly while the match has been played, which is a
    fact about the clock rather than a judgement about a situation. Before that
    nobody has played and a number would be a claim about the future; the cost
    of sending ``paid`` there instead would be a card that counts attendance at
    a match nobody has been to.

    ``{f} of {n}`` no longer means one thing across the screen, so the copy says
    what it counts — **seats paid**, **shares paid**, **played** — and every one
    of those nouns is the client's.
    """

    seats: int
    paid: int
    held: int
    turned_up: int | None = None


@final
@dataclass(frozen=True)
class Refund:
    """What a cancellation returned, and where it went.

    Two fields and both load-bearing: the amount is what she is owed, and the
    destination is what makes the sentence's tense honest. Neither is derivable
    from the other, and the destination is not derivable on the phone at all
    without the phone holding a rule about which cancellation pays which way.
    """

    amount: Money
    destination: RefundDestination


@final
@dataclass(frozen=True)
class OwnerExposure:
    """A private court's two money figures, which disagree on purpose.

    ADR-0073 calls this *"the most surprising thing in the private-court
    model"*: an owner watches money come back while owing exactly what she owed
    at the start. ``recovered`` is what the marketplace has paid in;
    ``guaranteed`` is the **whole court**, which ADR-0045 says never shrinks —
    ADR-0044 refunds every marketplace payer in full when the sold format is
    unmet, so her exposure does not move until it fills.

    Showing the guarantee alone looks broken — thirty złoty just landed and the
    card acts as though nothing happened — and showing the recovery alone tells
    her she is covered when she is not. The **gap between them** is the fact.

    **Neither figure is about the viewer**, and that is a limitation stated
    rather than hidden: the record carries no owner (``Raketa02/Raketa#99``), so
    a private card composes the court's two figures and the copy addressing them
    to *you* is the client's. Every private situation in v1 arrives from seed
    (ADR-0086), so nobody meets the gap outside the seeded demo.
    """

    recovered: Money
    guaranteed: Money


@final
@dataclass(frozen=True)
class ScoreSide:
    """One side of the net, named by the players who were on it.

    ADR-0073: a bare *6-4, 3-6, 6-2* was refused because with four cards from
    four evenings on one screen it prints a number that is true of **somebody**
    — the same class of defect as deriving *n − 1*. The cost is that a card
    carries a **person**, which is the first time one does.
    """

    players: tuple[str, ...]


@final
@dataclass(frozen=True)
class SetScore:
    """One set, as games won by each side, and never a display string.

    Two integers. **No tiebreak field in v1** and none smuggled in as a third
    integer: a real 7-6 is two integers and the tiebreak's own points are not
    modelled.
    """

    first: int
    second: int


@final
@dataclass(frozen=True)
class ScoreLine:
    """The score, both sides named, **the viewer's first**.

    ``sides[0]`` is the side the viewer played on when she played at all, and
    ``first`` in each set is that side's games. A viewer looking in has no side,
    and then the order is the match's own — which is what the stored score
    already means, so nothing is invented for her.

    **No level movement.** ADR-0073 withdrew the Player Score line because no
    engine produces one: ``app/engines/`` holds seven engines and not one
    updates a rating from a result. The card prints the thing that actually
    happened instead of a number the app would have had to invent.
    """

    sides: tuple[ScoreSide, ScoreSide]
    sets: tuple[SetScore, ...]


@final
@dataclass(frozen=True)
class DepartureRecoverable:
    """A leaver who paid: what she paid, and what became of it.

    ``outcome`` is ``None`` while nothing has decided it — she left, and whether
    the money comes back depends **entirely** on her seat refilling. That is why
    her card keeps the match's own facts: a card that hid the match's progress
    would hide the only thing that determines her outcome.

    A settled ``FORFEITED`` still carries the amount, because *you paid 38,00 zł
    and got none of it back* is the sentence and a payload that dropped the
    figure could not say it.
    """

    paid: Money
    outcome: Outcome | None = None

    form: DepartureForm = DepartureForm.RECOVERABLE


@final
@dataclass(frozen=True)
class DepartureNothingTaken:
    """A leaver whose money never left, and therefore a payload with no amount.

    ADR-0030: before commitment the seat is cleared *and* unpaid, *"so there is
    nothing left to derive from and the card can name no amount at all."* It
    carries no outcome either — nothing taken is born settled as a reversal, so
    an outcome here would be a constant with a field around it.
    """

    form: DepartureForm = DepartureForm.NOTHING_TAKEN


#: A leaver's departure, in **two forms** and never one with a sometimes-absent
#: amount (ADR-0072). Reading ``paid`` without narrowing does not typecheck,
#: which is the same guarantee ``LeaverMoney`` gives the aggregate one ring in.
CardDeparture = DepartureRecoverable | DepartureNothingTaken


@final
@dataclass(frozen=True)
class SituationFacts:
    """The numbers and names the situation's sentence prints.

    **Two are always here and the rest arrive when the fact exists.** Counting
    and the court's total are properties of every match, so they are composed
    unconditionally; a hold, a court's name, a refund, an owner's exposure, a
    score and a departure each exist in some states and not in others, and each
    is present exactly when it exists. That is a rule per fact rather than
    ADR-0073's *"table of 36 judgements nobody can maintain"* — no situation is
    named anywhere in the composition.

    ``court_total`` is *"the court's total, for every audience"*. The subject of
    ``{price} settled to the club`` is the **court**, and what it tells the
    viewer is *this game is happening*; her own share answers a question she did
    not ask and answers it worse, because her money left days ago. It is the one
    money line on the screen that needs no audience at all — which is why it is
    beside the spine's ``price`` rather than replacing it.

    ``court`` is the specific court, and it is here rather than on the spine
    because it is *usually unassigned*: ``kernel.court_named_at`` does not name
    one until fifteen minutes before play, and a spine field that is empty
    almost always is one somebody eventually fills with something else.
    """

    counts: SeatCounts
    court_total: Money
    hold: HoldNote | None = None
    cause: Cause | None = None
    court: str | None = None
    refund: Refund | None = None
    owner: OwnerExposure | None = None
    score: ScoreLine | None = None
    departure: CardDeparture | None = None


@final
@dataclass(frozen=True)
class SituationHalf:
    """What the match is doing, and the facts behind the sentence.

    One name, one sentence: where a single name would make the client choose
    between two sentences from a fact on the wire, it is two names instead — a
    boolean whose only job is to pick which sentence the phone writes *is* a rule
    on the phone wearing a different hat.
    """

    situation: Situation

    #: **Required**, and it used to have an empty default. Every card counts —
    #: seats paid, the held seat beside them, the court's total — so a facts
    #: object that could be left out would be a card that says nothing about the
    #: match it is describing, which is not a state the composition can produce.
    facts: SituationFacts


@final
@dataclass(frozen=True)
class MatchCard:
    """A match, seen by one viewer at one instant.

    Everything above ``situation`` is the **spine** and is drawn by every phone
    that has ever shipped. Two of its fields are the composition's judgement
    rather than the match's — ``fit`` and ``emphasis`` — and both live here rather
    than in the situation half so that an old phone meeting an unknown name loses
    a sentence and not its badge.

    ``clock`` is the card's **one** clock slot, and which moment fills it is a
    rule and not thirty-six judgements: *the next moment at which something
    happens to the viewer whether they act or not*. A card that is over or
    cancelled counts to nothing and the slot is empty. Always-the-start-time was
    refused because it ticks five hundred hours down to a game nobody is worried
    about while the hold expires in silence; the-next-moment-you-can-still-act was
    refused for the opposite reason — a seat being rescued is precisely when a
    player can do nothing and precisely when they most need to see the deadline.
    **The clock is the app's warning, not its to-do list.**
    """

    match_id: UUID
    stamp: Stamp
    where: Place
    price: Money
    situation: SituationHalf
    clock: Instant | None = None
    fit: Fit | None = None
    emphasis: bool = False
    act: ActCode | None = None
    may_depart: bool = False
    seat_claim: SeatClaim | None = None

    card_type: CardType = CardType.MATCH


@final
@dataclass(frozen=True)
class Level:
    """A player's Level, and whether a questionnaire is all that is behind it.

    ``value`` is the glossary's **Level (μ)** on the fixed 1,0-5,0 scale, sent as
    the number and never as ``2,71`` — the comma is the client's, like every
    other value in ``docs/value-formatting.md``.

    ``provisional`` is the **quiet marker**, and it is a boolean because the
    alternative was a second number. A rating that has seen no counted match is
    the glossary's *Initial Estimate*, and onboarding cannot exceed 30 %
    confidence; printing that 30 % beside the Level is the gauge ADR-0037
    refused, and printing nothing at all claims a certainty the platform does not
    have. So the card says *this is an estimate* and stops there.

    Not the Rating status itself. *Initial Estimate*, *Calibrating* and *Stable*
    are a three-value vocabulary the client would have to hold a row for, and a
    person card has one thing to say about it: whether a questionnaire is the
    whole evidence. The day the middle one means something to a reader, this
    becomes a code and the boolean goes.
    """

    value: float
    provisional: bool


@final
@dataclass(frozen=True)
class PersonCard:
    """A player who has just arrived. Inert in v1 — no act, no clock, no price.

    A separate type rather than a match card with holes: one union would give
    every person card an always-empty situation half, an always-empty clock, an
    always-empty price and an emphasis flag that can never be set, with nothing
    preventing a later session filling one in.

    ``level`` is **required**, because a person reaches this shelf only through a
    rating at the shelf's sport. An optional Level would be a hole for a state
    the retrieval cannot produce, which is the same defect one card type with
    holes would have been.
    """

    player_id: UUID
    stamp: Stamp
    nickname: str
    level: Level

    card_type: CardType = CardType.PERSON


@final
@dataclass(frozen=True)
class ClubCard:
    """A club that has just joined. Inert in v1, for the same reason."""

    club_id: UUID
    stamp: Stamp
    name: str
    distance_km: int | None = None

    card_type: CardType = CardType.CLUB


#: What a shelf may hold. A shelf is homogeneous in practice — its code fixes
#: what it holds, because a shelf's title is its claim — but the *contract* is a
#: union, so a shelf carrying the wrong kind is a type error rather than a field
#: quietly left empty.
ShelfCard = MatchCard | PersonCard | ClubCard


@final
@dataclass(frozen=True)
class Shelf:
    """One claim, its cards, and no title.

    **No stamp.** A shelf is never in an update — dropping a joined match out of
    *Best fit* would be re-ordering a shelf under the player's thumb — so there is
    nothing for a stamp to arbitrate.

    **No tail card, either.** Every shelf has one unconditionally, so a flag would
    be ``true`` on every shelf of every screen forever; the client appends it and
    routes on the shelf code and the sport it already holds.
    """

    code: ShelfCode
    cards: tuple[ShelfCard, ...] = ()
    caption: CaptionCode | None = None

    block_type: BlockType = BlockType.SHELF


@final
@dataclass(frozen=True)
class Door:
    """The way into a sport's questionnaire, where its shelves would have been.

    ADR-0084: a player who taps a chip for a sport she holds no rating at is
    owed a destination rather than a better sentence, and the destination goes
    **in the shelves list, in order** — not beside it, and not as a flag. An
    inference drawn from absent shelves would fire wrongly on any day the city
    genuinely has no matches in a sport she *is* rated at, and the phone holds no
    rules to draw one with.

    It carries **which sentence** and nothing else. Not the sport: the client
    asked for one and still holds it, and a second copy on the answer is a second
    thing that can disagree — the same reason a shelf's tail card into Find is
    the client's own composition of *this shelf's code* and *the sport I hold*.
    And not a destination either, because the code determines one, exactly as an
    act code does.

    A door and a shelf are two types rather than one shelf with a nullable door
    code, on ADR-0070's *three card types, not one with holes* — a shelf has
    cards and a caption and a claim, and a door has none of the three.
    """

    code: DoorCode

    block_type: BlockType = BlockType.DOOR


#: What the shelves list may hold. A **door** takes the position the ranked
#: shelves would occupy and the two arrival shelves still compose beneath it, so
#: the list is heterogeneous by design rather than by accident — and a union
#: makes a client that fails to narrow a type error rather than a blank row.
Block = Shelf | Door


@final
@dataclass(frozen=True)
class OffersRegion:
    """Seats offered to this viewer, soonest-to-expire first.

    Its own region, not a sixth shelf and not part of the enrolled strip. As a
    shelf it would inherit a floor, a cap, a caption and a tail card — all wrong
    for it — and become something the server could order *below* a suggestion,
    when *above everything* is the whole point. As part of the strip it would be
    sorted chronologically, which sorts a player's offers by when the game is
    rather than by when the offer dies.
    """

    stamp: Stamp
    cards: tuple[MatchCard, ...] = ()


@final
@dataclass(frozen=True)
class EnrolledRegion:
    """The matches this viewer is committed to, chronological.

    Not a shelf either: it re-orders on the player's own action and the shelves
    never do; it has no floor, no cap, no caption and no tail card, where every
    shelf has all four. A uniform row type would invite exactly the mistake this
    map has spent itself avoiding — someone giving a player's own matches a
    quality floor.
    """

    stamp: Stamp
    cards: tuple[MatchCard, ...] = ()


@final
@dataclass(frozen=True)
class ShelvesRegion:
    """The server's fixed list of shelves, in the server's order.

    Empty when nothing composed — present and empty, like the other two.

    The name stays ``shelves`` now that the list may also hold a door. ADR-0084
    puts the door *in* this list rather than beside it, and renaming the field
    would break every client reading a region that has not otherwise changed —
    for a word, on a screen whose list is shelves in every case but one.
    """

    stamp: Stamp
    shelves: tuple[Block, ...] = ()


@final
@dataclass(frozen=True)
class DebtLine:
    """What the player owes, and the one consequence of owing it.

    An amount, a currency, and **one boolean** meaning *this player may not create
    a match or book a court*. Not the amount alone, which would make the phone
    conclude *she owes, therefore the create button is dead* — a rule, and the
    phone holds none. Not a list of blocked acts either, which invents a
    vocabulary to describe two things nothing else in the product would read.

    Absent when there is nothing owed, rather than present at zero: a zero the
    client has to compare against is the same rule wearing a third hat.
    """

    owed: Money
    blocked: bool


@final
@dataclass(frozen=True)
class NowScreen:
    """One request, one answer, the whole screen.

    ``sports`` is what the request's filter resolved to, and it is the one field
    here the wire does **not** carry. It is on the screen because every region
    below is composed under it, and because the door into an unrated sport's
    questionnaire is decided by it; ADR-0070 puts exactly one viewer fact on the
    envelope and this is not it.

    **The header is not on this screen.** The greeting and the city come from the
    *who am I* answer the app already holds. The city is a fact about the player
    and cannot change during a session, and repeating it in two answers is how
    two answers come to disagree.
    """

    offers: OffersRegion
    your_matches: EnrolledRegion
    shelves: ShelvesRegion
    sports: frozenset[Sport]
    debt: DebtLine | None = None
