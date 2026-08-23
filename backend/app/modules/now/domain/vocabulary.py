"""The codes Now composes, and the one projection it makes off the kernel.

Everything here is a **closed enumeration that crosses the wire**, and each is
closed for the same reason: a client renders copy per code through a total table
(``docs/adr/0041-tone-is-editorial-so-the-wire-carries-a-situation-and-its-facts.md``),
and a bare string degrades that table into an index signature that never fires.
The words themselves are the client's and are never here — this module holds no
sentence, in any language.

What is *not* here, deliberately: the **tag**, the **tone** and the **alert**.
All three are total functions of the situation, so ADR-0072 puts them in the
client's own thirty-six-row table and they cross no wire. A flag would let the
server and the phone disagree about whether a card is urgent, which is exactly
the two-derivations failure ADR-0040 exists to make unreachable.

**``Cover`` is not here either, and it used to be.** It was Now's while Now was
its only reader; ADR-0090 gave it an author — a club authors it on a court
category — and a closed set two contexts read verbatim belongs in the innermost
ring on ADR-0022's own test. It is ``kernel.Cover``, imported by the two files
below that draw a card's ``where``, and the wire is unchanged.
"""

from __future__ import annotations

from enum import Enum
from types import MappingProxyType
from typing import Mapping

from app.kernel import Cause, HoldReason, Situation, invariant


class CardType(str, Enum):
    """Three card types, not one with holes.

    ADR-0070: a person and a club have no situation, no clock, no price and no
    emphasis, so one union type would give every person card four permanently
    empty fields and nothing preventing a later session filling one in. The
    discriminator rides on the card itself and never on the shelf that holds it,
    because a card is identified by *the thing it is about*.
    """

    MATCH = "match"
    PERSON = "person"
    CLUB = "club"


class ActCode(str, Enum):
    """The one act a card may name, from a closed set of seven.

    ADR-0083 opened the set at six and fixed the rule that governs it — *a card
    names an act when the viewer can take it now and a v1 surface can receive
    it* — and ADR-0087 exercised that rule once, adding ``leaveStandby`` **with**
    the write that receives it. That is the only way an eighth arrives.

    Twenty-six of the thirty-six situations name none, and that is not a hole to
    be patched with a button that opens something irrelevant: ``Open match`` died
    with its destination when the match-detail screen went out of scope.

    The act rides in the **spine**, as a code alone and with no target beside it.
    Each code determines its own destination and the card already identifies the
    thing it is about, so a target would be a second answer to one question. It
    is in the spine rather than the situation half because it is the
    composition's judgement about *this viewer* — and because a phone that cannot
    name a new situation must still be able to take the seat.
    """

    TAKE_SEAT = "takeSeat"
    FINISH_PAYING = "finishPaying"
    ENTER_RESULT = "enterResult"
    ANSWER_RESULT = "answerResult"
    SEE_ALTERNATIVES = "seeAlternatives"
    GETTING_IN = "gettingIn"
    LEAVE_STANDBY = "leaveStandby"


#: Pinned rather than counted. ADR-0083 closed the enumeration and ADR-0087 is
#: the one addition made since; an eighth is a decision somebody made in a diff.
ACT_COUNT = 7

invariant(
    len(ActCode) == ACT_COUNT,
    f"the enumeration names {len(ActCode)} acts, not {ACT_COUNT}",
)


class BlockType(str, Enum):
    """What one entry in the shelves list is: a shelf, or the door.

    ADR-0084 puts the door **in the list, in order** rather than beside it, so
    the list stops being homogeneous and the client needs one field to tell the
    two apart. The discriminator rides on the block itself, on the same rule
    ``CardType`` follows: an entry is identified by what it *is*, never by its
    position, so one reader narrows once and the server may reorder freely.

    Two members and not a boolean. A third block is a decision somebody makes in
    a diff, where ``is_door: true`` would make the third one either a lie or a
    second boolean beside the first.
    """

    SHELF = "shelf"
    DOOR = "door"


class DoorCode(str, Enum):
    """Which sentence the door shows, as a code and never as the sentence.

    ADR-0084 gives the door two sentences — one for a player who has never
    started this sport's questionnaire, one for a player whose run is parked —
    and makes them **one block type** so the client never learns the difference.
    What the block carries is which of the two it is.

    Named for the **fact** rather than for the words, like every other code here:
    the copy is the client's and changes without a backend release, where *has
    she started* is the thing the server actually knows. A run parks however old
    it is and never expires, so these two are exhaustive over a player the door
    is drawn for at all.
    """

    NO_RUN_YET = "noRunYet"
    RUN_PARKED = "runParked"


#: Pinned rather than counted, on ``ACT_COUNT``'s rule. ADR-0084 names two
#: sentences; a third is a copy decision, and a copy decision arriving as a
#: silent enum member is one no client is holding a row for.
DOOR_CODE_COUNT = 2

invariant(
    len(DoorCode) == DOOR_CODE_COUNT,
    f"the enumeration names {len(DoorCode)} door codes, not {DOOR_CODE_COUNT}",
)


class ShelfCode(str, Enum):
    """Which claim a shelf makes, as a code and never as a title string.

    ADR-0070 put shelf **presence** and shelf **order** on the server precisely
    so both can change without an app release, and left the words with the
    client: *"the words were never the part that needed to move without a client
    release; shelf presence and shelf order were."*

    ``BEST_FIT`` and ``SAME_LEVEL`` are two codes for one shelf — the second is
    what shelf 1 is retitled to when nothing clears its floor, which is how it
    never goes silent. ``RECENTLY_VIEWED`` ships **dark**: ADR-0085 keeps the
    code in the enum and never composes it, so the shelf's return is a server
    change rather than a client release.
    """

    BEST_FIT = "bestFit"
    SAME_LEVEL = "sameLevel"
    FULL_WORTH_WAITING = "fullWorthWaiting"
    RECENTLY_VIEWED = "recentlyViewed"
    NEW_PLAYERS = "newPlayers"
    NEW_CLUBS = "newClubs"


class CaptionCode(str, Enum):
    """Which one-line caption a shelf carries, when it carries one.

    A code and not a sentence, on ADR-0070's rule. ADR-0066 requires the caption
    to be *composed by the server* and the client to *evaluate nothing*: both
    hold, because the server decides whether a caption fires and which one it
    is, and the phone draws the one it was handed.

    There is exactly one in v1, and it fires only when a term the ranking
    **actually reads** is undeclared — hours, price, radius-and-anchor,
    competitive or social. A player who declined all four sees nothing on Now,
    forever, at whatever percentage.
    """

    UNDECLARED_PREFERENCES = "undeclaredPreferences"


class Currency(str, Enum):
    """The currency an amount is in, beside the amount and never inside it.

    ADR-0023 already fixes the integer; the comma in *38,00 zł* is formatting and
    formatting is the client's. The currency ships even though there is one
    market, for ADR-0063's own reason: a city field exists precisely so no reader
    may assume one market, and a hard-coded currency beside it would assume the
    thing the city field exists to prevent. **This does not make Raketa
    multi-currency. It stops the contract claiming Raketa never can be.**

    An enum rather than a bare ISO-4217 string, on the same rule as every other
    code here: the client formats per currency, and a total table over one member
    is a table that keeps working when there are two.
    """

    PLN = "PLN"


class RefundDestination(str, Enum):
    """Where a cancellation's money went, which is what fixes the tense.

    ADR-0073: *"A cancellation names the amount **and where it went**, and the
    destination fixes the tense"* — *on its way back to your card* against
    *credit at Sport Club Kraków*. A card refund is **never** claimed to have
    landed, because a card lives twenty-four hours and a refund rarely arrives
    inside one; a club credit is definite because it genuinely is instant
    (ADR-0058 makes it a club card entry rather than a payment).

    It is a **total function of the cause** — the three refunds return money to
    the method it came from and the checkpoint ending issues credit — and it
    crosses anyway, because deriving it is a rule and the phone holds none
    (ADR-0053). The server applying it once is what stops thirty-six client
    tables each having to know which cancellation pays which way.
    """

    CARD = "card"
    CLUB_CREDIT = "clubCredit"


class DepartureForm(str, Enum):
    """Which of a leaver's **two payload forms** her card carries.

    ADR-0072 refuses one payload holding an amount that is sometimes absent:
    *nothing was taken* and *nothing has come back yet* are opposite sentences
    and a blank cannot tell them apart. So the discriminator rides on the
    payload, the same way ``CardType`` rides on a card — and reading an amount
    off the wrong form is then a narrowing error rather than a blank line.
    """

    #: She paid, and whether any of it comes back is the outcome's answer.
    RECOVERABLE = "recoverable"
    #: Her money never left. There is no amount, so the payload holds no field
    #: that could carry one.
    NOTHING_TAKEN = "nothingTaken"


class CardHoldReason(str, Enum):
    """Why a court is being kept aside, in the five reasons that reach a card.

    ADR-0073 replaced ``hold.note`` — a sentence the server wrote, which would
    have been the single precedent for server-held copy anywhere in the contract
    — with a named reason plus the numbers it needs. The client writes all five
    sentences.

    Five, not the kernel's thirteen. The rest are diagnosis: *a card that is not
    describing a court does not name one*, and shipping the diagnostic names
    would oblige every client to hold seven rows it can never render.
    """

    COMMITTED = "committed"
    FAR = "far"
    NEAR = "near"
    STALE = "stale"
    EXTENDED = "extended"


#: The projection off the kernel's own vocabulary, **total** and asserted
#: exhaustive at module load — never a second ladder over the record. It is the
#: same shape ``MATCH_PHASE_OF`` takes one ring out from here, and it is written
#: out row by row rather than derived from a name prefix, so a fourteenth kernel
#: reason cannot be silently absorbed into ``None``.
CARD_HOLD_REASON_OF: Mapping[HoldReason, CardHoldReason | None] = MappingProxyType(
    {
        # The five a card names.
        HoldReason.COMMITTED: CardHoldReason.COMMITTED,
        HoldReason.FAR: CardHoldReason.FAR,
        HoldReason.NEAR: CardHoldReason.NEAR,
        HoldReason.STALE: CardHoldReason.STALE,
        HoldReason.EXTENDED: CardHoldReason.EXTENDED,
        # A private court belongs to whoever bought it, and a club-committed
        # court is the club's own decision: both are already the card's
        # situation, so naming them again as a hold reason would be one fact
        # spelled twice.
        HoldReason.PRIVATE: None,
        HoldReason.CLUB: None,
        # Diagnosis. A full match's card is not describing a court, and the four
        # below describe the *absence* of a hold, which the situation states.
        HoldReason.FULL: None,
        HoldReason.NEAR_LAPSED: None,
        HoldReason.FAR_LAPSED: None,
        HoldReason.THIN: None,
        HoldReason.NO_SPECULATIVE_HOLD: None,
        # A cancelled card has a cancellation to say and no court to describe.
        HoldReason.OVER: None,
    }
)

invariant(
    set(CARD_HOLD_REASON_OF) == set(HoldReason),
    "the card's hold-reason projection is not total over the kernel's reasons",
)

invariant(
    {reason for reason in CARD_HOLD_REASON_OF.values() if reason is not None}
    == set(CardHoldReason),
    "a card hold reason exists that nothing projects onto",
)


#: Which cancellation a card is describing, as a **cause**, projected off the
#: ladder's first four rungs rather than re-read off the record's flags.
#:
#: Four rows and not thirty-six: a cause is a fact about a match that **ended**,
#: and a table with thirty-two ``None``s in it would be thirty-two rows nobody
#: could ever get wrong. What keeps it honest instead is the assertion below —
#: the four names it produces are exactly the enumeration's own, less the one
#: ADR-0073 says *"never appears on a card"* — so a sixth cause that belongs on a
#: card cannot be added without this table being the place it is noticed.
CANCELLATION_CAUSE_OF: Mapping[Situation, Cause] = MappingProxyType(
    {
        Situation.INVENTORY_LOST: Cause.INVENTORY_LOST,
        # One name for two flags, and it is the ladder's own reading: a club
        # cancelling and the weather taking it resolve to one sentence, and a
        # cause names the rule that fired rather than the meteorology.
        Situation.CANCELLED_CLUB: Cause.CLUB_CANCELLED,
        Situation.CANCELLED_INCOMPLETE: Cause.FORM_CANCELLED,
        Situation.CANCELLED_CHECKPOINT: Cause.CHECKPOINT_CANCELLED,
    }
)

invariant(
    set(CANCELLATION_CAUSE_OF.values()) == set(Cause) - {Cause.SETTLEMENT_REOPENED},
    "the card's causes are not the enumeration less the ledger-only one",
)


#: Where a cancellation's money goes, per cause. **Total over the enumeration**,
#: so a sixth cause is a build error here rather than a silent card refund.
#:
#: Three of the four are one arithmetic and four names (ADR-0073) — money back to
#: the method it came from — and the checkpoint ending is club credit (ADR-0058).
#: ``SETTLEMENT_REOPENED`` is a ledger cause that reaches no card, and it is in
#: the table anyway rather than beside it: a cause the ledger may write and this
#: table may not name is the same defect in the other direction.
REFUND_DESTINATION_OF: Mapping[Cause, RefundDestination] = MappingProxyType(
    {
        Cause.INVENTORY_LOST: RefundDestination.CARD,
        Cause.CLUB_CANCELLED: RefundDestination.CARD,
        Cause.FORM_CANCELLED: RefundDestination.CARD,
        Cause.CHECKPOINT_CANCELLED: RefundDestination.CLUB_CREDIT,
        # Reopening a settlement returns money the way the original did, which
        # is the card. It reaches no card, so nothing renders this row.
        Cause.SETTLEMENT_REOPENED: RefundDestination.CARD,
    }
)

invariant(
    set(REFUND_DESTINATION_OF) == set(Cause),
    "a cause exists with nowhere for its money to go",
)
