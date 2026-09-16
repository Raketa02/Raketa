"""The shortlist's wire shapes — one envelope, and a row that is a person or not.

**The full breakdown ships with the search, not behind a tap.** *Why 78?* is the
moment the product's central claim is tested, and a spinner there is the claim
failing — so every term, its weight, its value, its contribution and its evidence
ride on every row. Twenty rows of codes and numbers is tens of kilobytes; two
payload shapes for one concept is two generated types that drift.

**Absence has two spellings and they are not interchangeable** (``docs/adr/0106``
§4).

- **Omitted** — *this field does not apply here.* It generates as ``field?: T``,
  and the route is declared ``response_model_exclude_unset=True`` so an omitted
  field is genuinely absent from the JSON rather than present as ``null``.
- **``null``** — *this field applies, and the answer is a measured nothing that
  is itself a recorded fact.*

A field that was both would generate as ``field?: T | null`` and say neither
thing, which ``tests/unit/test_matchmaking_shortlist_contract.py`` refuses.

**No Liveness number, in any shape.** A candidate carries ``fit`` and a list of
reason **codes**; there is no field here an offset could be written to, and the
assertion that none exists anywhere on the surface is made centrally over the
emitted contract rather than route by route.

**The near-miss band is never returned.** Layer 3 of the telemetry is
engine-internal: a player may ask why somebody was shown; nobody may ask who was
withheld. There is no schema here it could arrive in.

**A row is a candidate or a tombstone, and the second one carries no person.**
The read-back re-evaluates the gates that fail closed, and a row they no longer
admit keeps its place and states that it is withheld (``docs/adr/0109``). It is a
**union rather than a candidate with holes**, so *render a card for somebody the
product has agreed to stop showing* is not a shape this contract can hold — and
the tombstone names no gate, because ``docs/adr/0095`` says the other side sees
no trace anywhere in any response and a read-back is not an exception to that.

**The staged pool counts do not cross.** ``n_generated``, ``excluded_by_gate``,
``n_scored`` and ``n_cleared_floor`` live on the record. The client gets the
post-gate description and nothing else, because the mutual gender gate makes a
pre-gate count and a post-gate count differ **per searcher**, and the delta would
be readable — which is precisely what a mutual gate must never be.
"""

from __future__ import annotations

from datetime import datetime
from enum import StrEnum
from typing import Any, Literal, TypeVar
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.engines.matchfit.core import (
    DegradedReason,
    GroupReason,
    SearchMode,
    Term,
)
from app.kernel import SPORT_SPECS, Sport
from app.modules.matchmaking.domain.lineups import (
    Relationship,
    Side as CourtSide,
    UnfilledReason,
)
from app.modules.matchmaking.domain.prompts import Prompt
from app.modules.matchmaking.domain.relaxation import RelaxationAsk, Rung
from app.modules.matchmaking.domain.searches import (
    GameResult,
    SearchSurface,
    SortOption,
)
from app.modules.matchmaking.presentation.evidence import Evidence
# **The same cell shape the profile route takes**, deliberately reused rather
# than restated: asking for a week in two shapes is how availability data goes
# stale, and one client grid editor should be able to post to either route.
from app.modules.player_profile.presentation.schemas import AvailabilitySlotResource
from app.modules.player_profile.domain.availability import Window
from app.modules.player_profile.domain.intro import INTRO_MAX_CHARACTERS
from app.modules.player_profile.domain.photos import PhotoReviewDecision


#: The default that spells **omitted** — *this field does not apply here*.
#:
#: A field carrying it is not in the schema's ``required`` list, so it generates
#: as ``field?: T``, and the routes are declared
#: ``response_model_exclude_unset=True`` so it is genuinely absent from the JSON
#: rather than present as ``null``. That is the difference the whole contract
#: turns on: **``null`` means the field applies and the answer is a measured
#: nothing**, which is itself a recorded fact.
#:
#: It is typed ``Any`` so that the field keeps its own non-nullable type. A field
#: annotated ``T | None`` *and* defaulted would generate as ``field?: T | null``
#: and say neither thing — which is what
#: ``tests/unit/test_matchmaking_shortlist_contract.py`` refuses.
OMITTED: Any = None

#: Bound so the shared court check hands each request its own type back, which is
#: what a Pydantic ``model_validator(mode="after")`` must return.
_RequestT = TypeVar("_RequestT", bound=BaseModel)


class OptimisedFor(StrEnum):
    """Whom this search was run for.

    ``GROUP`` exists because a line-up with seats locked is no longer optimising
    for the searcher, who may end up with a worse individual match than an empty
    builder would have given them — and the screen has to say so. A shortlist is
    always ``SEARCHER``, and the field is on the envelope rather than implied by
    the surface so that one renderer reads one fact.
    """

    SEARCHER = "SEARCHER"
    GROUP = "GROUP"


class LivenessReason(StrEnum):
    """Why somebody moved, as a code. **Never as a number.**

    Ten values: the eight printable signals, with the full inbox spelled as its
    three coarse rungs instead of its own name. Their inbox depth is theirs — the
    rung crosses and the count does not — and each rung names its own code, so a
    threshold moving does not silently re-point a code at a different depth.

    The two **silent** signals are absent by construction rather than by
    omission: a silent move carries points and no code, so there is no name on
    the value to print. ``tests/unit/test_matchmaking_shortlist_contract.py``
    holds this enum to exactly the printable roster.
    """

    INTEREST_RECEIVED = "INTEREST_RECEIVED"
    PREVIOUS_ACCEPT = "PREVIOUS_ACCEPT"
    ANSWER_RATE_AND_SPEED = "ANSWER_RATE_AND_SPEED"
    RECENT_ACTIVITY = "RECENT_ACTIVITY"
    OVERLAP_PROXIMITY = "OVERLAP_PROXIMITY"
    RECIPROCAL_ASYMMETRY = "RECIPROCAL_ASYMMETRY"
    NEWCOMER_LIFT = "NEWCOMER_LIFT"
    CHALLENGE_LOAD_SOME = "CHALLENGE_LOAD_SOME"
    CHALLENGE_LOAD_BUSY = "CHALLENGE_LOAD_BUSY"
    CHALLENGE_LOAD_FULL = "CHALLENGE_LOAD_FULL"


class WireInclusionReason(StrEnum):
    """Why this person is in the list at all — **and it is a union of one.**

    The store keeps three values and the wire publishes this one, which is the
    whole of ``the-two-contracts.md`` §4's *the store is open where the wire is
    closed*. Only an **interest lift** admits anybody; the other two **reorder**,
    and a reorder is not a reason a searcher is owed:

    - ``NEWCOMER_WINDOW`` reaches the client as a Liveness reason instead, which
      is where a printable reorder belongs.
    - ``ZERO_EXPOSURE`` never crosses at all. *You are seeing this person because
      nobody has been shown them all week* is a third party's unpopularity, and
      the searcher is owed no version of it.

    It stays an enum of one rather than a bare literal so the next reason that
    genuinely **admits** somebody has somewhere to go.
    """

    INTEREST_LIFT = "INTEREST_LIFT"


class ModifierCode(StrEnum):
    """The three modifiers inside the budget, and the dock outside it.

    Every one of them **prints**: a modifier that could move a score without
    owing a sentence would be Liveness wearing stage 4's clothes, and Liveness
    has a budget for exactly that.
    """

    CALIBRATION_VALUE = "CALIBRATION_VALUE"
    FAMILIARITY = "FAMILIARITY"
    WELCOMING_RECORD = "WELCOMING_RECORD"
    RELIABILITY_FLOOR_BREACH = "RELIABILITY_FLOOR_BREACH"


class RunSearchRequest(BaseModel):
    """What a client may send. **Asks only, never a fact about the searcher.**

    There is deliberately **no radius here, and there never will be.** The
    searcher's ask *is* their profile radius, read at request time; widening
    happens only by taking a rung offer. A radius supplied by a phone is a gate
    evaluated on a lie, and this is the field it would arrive through.
    """

    sport: Sport = Field(..., description="Which sport this search is for")
    mode: SearchMode = Field(
        ...,
        description=(
            "Competitive or for fun — the weight vector for this one search, "
            "and nothing else. Two values, where a Play intent has three."
        ),
    )
    availability_override: list[AvailabilitySlotResource] = Field(
        OMITTED,
        description=(
            "The week to run **this one search** against, when the player "
            "edited it on the search screen. Omit to use the grid on your "
            "profile — **omit it, never send `null`**.\n\n"
            "**It is an ask and never a correction.** Nothing here writes your "
            "profile; the app offers to save it afterwards."
        ),
    )
    offered_by_search_id: UUID = Field(
        OMITTED,
        description=(
            "The search whose relaxation offer this one accepts. **Taking a "
            "rung is a new search citing the one that offered it**, never a "
            "silent change to your saved preferences."
        ),
    )
    rung: Rung = Field(
        OMITTED,
        description=(
            "Which rung of that search's offer you are taking. Sent with "
            "`offered_by_search_id` or not at all — and the widening itself is "
            "**not** sent: the backend reads it off the offer it made."
        ),
    )


class DealDeckRequest(BaseModel):
    """What a deal is asked for. **The sport, and the week you are asking about.**

    This said *one field, and that is the whole contract* until the week was
    added, and the three refusals it was written to protect are untouched by
    that: **a mode, a widening and a pass window** may not arrive here, and a
    grid is none of the three.

    **There is no `mode` here and there never will be.** The deck reads your own
    declared Play intent for this sport, resolved backend-side, and *no
    preference* is a working deck rather than a blocked one — indecision is not a
    state this product refuses. A mode on this body would be the field the
    telemetry constraint refuses: `mode` is null exactly when the surface is the
    deck.

    **There is no widening here either.** The relaxation ladder does not reach
    the deck, so a deal carries no rung offers and there is no offer for one to
    cite.

    **There is nothing about a pass.** The suppression window crosses the wire in
    no shape at all — no field, no code, no timestamp — which is what makes a
    pass unable to become something stronger by way of a request.

    **The week is an ask and never a correction**, exactly as it is on a search.
    It is here because the alternative was a deck that silently ranks on a week
    the player has just replaced, and because a client cannot compute the
    difference itself: a search that took a times rung ran on a grid with a slot
    the player never ticked, and only this backend knows that.
    """

    sport: Sport = Field(..., description="Which sport this deal is for")
    availability_override: list[AvailabilitySlotResource] = Field(
        OMITTED,
        description=(
            "The week to run **this one deal** against, when the player edited "
            "it on the Play screen. Omit to use the grid on your profile — "
            "**omit it, never send `null`**.\n\n"
            "**It is an ask and never a correction.** Nothing here writes your "
            "profile; the app offers to save it afterwards."
        ),
    )


class RecordPassRequest(BaseModel):
    """One *not today*, and where the card came from. **Write-only.**

    Nothing is returned by this route and no route anywhere returns a pass — not
    to you, not as a count, not as *"you have passed on twelve people"*.

    `search_id` is the **Origin key** and is required, exactly as it is for a
    yes: a pass citing a search that is unknown, that belongs to somebody else or
    that never showed that person is refused rather than recorded with an empty
    link. **The position is not sent** — the backend reads it off the cited
    search's own rows.

    **How long it lasts is not yours to name**, and there is no field here for
    it. A pass keeps somebody out of *your deck* only, for a window this backend
    decides; it never reaches a shortlist, a line-up or a forecast, it never
    touches their deck, and a second pass buys exactly the same window and no
    more. The control that removes a person from a person is a **block**, and it
    is deliberately a heavier gesture.
    """

    sport: Sport = Field(..., description="Which sport this card was for")
    player_id: UUID = Field(..., description="Whose card you are passing on")
    search_id: UUID = Field(
        ...,
        description=(
            "The deal this person was dealt to you in. **Required** — a pass "
            "with no origin is refused rather than recorded with a null link."
        ),
    )


class ResetDeckRequest(BaseModel):
    """One *Show them again*, for one sport. **Write-only.**

    Nothing is returned by this route and no route anywhere returns a reset.

    **The sport is the whole ask.** The button is on a deck and a deck is one
    sport, so a padel reset says nothing about tennis. There is no field for
    *what* to clear: the three things a reset lifts — every pass suppression,
    the day's dealt memory and the cool-off — lift together, and a client that
    could pick would be a client that could clear the cool-off and keep its
    passes, which is not a thing the product offers.
    """

    sport: Sport = Field(..., description="Which sport's deck to deal whole again")


class RecordPromptDeclineRequest(BaseModel):
    """One *not now*, about a question. **Write-only.**

    Nothing is returned by this route and no route anywhere returns a decline —
    not to you, not as a count, not as *"you have said no to this four times"*.

    **There is no `search_id` and no idempotency key.** A pass carries an origin
    because *pass rate on re-shown profiles* is unmeasurable without one; nothing
    a decline is measured by needs one, and two of these questions are raised by
    a background loop that has no search to cite. A second *not now* is a second
    row with its own moment, exactly as a second pass is, and it buys the same
    month the first did.

    **How long it lasts is not yours to name**, and there is no field here for
    it. What it buys is that this question is not raised at you again for a
    while; it retires nothing — the standing prompt still expires on its own —
    and it changes no value on your profile. Saying *yes* is a write through the
    route that owns the value, and it is a different request entirely.
    """

    prompt: Prompt = Field(
        ...,
        description=(
            "Which question you are answering, as the code the search sent "
            "you.\n\n**`KEEP_THESE_TIMES` is refused** — an improvised week is "
            "a different week next Tuesday, so that one is asked again and the "
            "app does not offer *not now* for it."
        ),
    )
    sport: Sport = Field(
        ...,
        description=(
            "Which sport's screen raised it. **It is not the key**: a play "
            "intent is declared per sport, so declining that one is per sport, "
            "while a search radius and an availability grid are one fact each "
            "for the whole player — those go quiet everywhere."
        ),
    )


class PoolSchema(BaseModel):
    """What the searcher is told about the pool this answer came from.

    Sent on **every** search and not only on empty ones: a thin pool and a broken
    floor are indistinguishable without it.
    """

    sport: Sport
    radius_km_used: int = Field(
        ..., ge=1, description="The searcher's own radius, in whole kilometres"
    )
    players_in_range: int = Field(
        ...,
        ge=0,
        description=(
            "How many candidates cleared every gate. **Post-gate, always** — a "
            "pre-gate count beside this one would be the delta a mutual "
            "preference hid, per searcher."
        ),
    )
    window: Window = Field(
        ...,
        description=(
            "When a game found on this grid would plausibly be played, as a "
            "code. Derived by the backend from the grid the search ran on; "
            "there is no window picker anywhere."
        ),
    )
    post_gate: bool = Field(
        True,
        description="Always true. It travels so the count cannot be misread.",
    )
    remaining: int = Field(
        OMITTED,
        ge=0,
        description=(
            "**On a deal only.** How many people are eligible for your deck "
            "beyond this hand — after every deck exclusion, and not in the "
            "cards you were just dealt. It is what lets a counter say *N left* "
            "and be true of the whole pool rather than of ten; it drops by a "
            "hand as hands are dealt. Omitted on every other surface and on a "
            "read-back, where a count about a pool that has moved on would be "
            "a number about nothing."
        ),
    )
    want_to_play_you: int = Field(
        OMITTED,
        ge=0,
        description=(
            "**On a deal only.** How many people have a live *Let's play* "
            "towards you in this sport that would be dealt to you: every gate "
            "passed, not passed on by you within the pass window, not cooling "
            "off after a court you shared, and not already mutual. Somebody "
            "dealt this morning and unanswered still counts — the dealt "
            "memory is not applied. **A count and never a list**: nothing on "
            "any route names who. `0` is a measured nought, so a chip drawn "
            "from it is drawn at one and above."
        ),
    )


class RungOfferSchema(BaseModel):
    """One rung of the relaxation ladder, priced. **Offered, never applied.**

    The engine computes what relaxing one of *your own* asks would be worth and
    hands you the number; it never takes the offer for you, because only you can
    say truthfully that you are free on a Saturday.

    **The count is real.** It comes from re-running the whole search at this
    rung — not from an estimate, and not from the strict count plus something.
    """

    rung: Rung = Field(
        ...,
        description=(
            "Which rung. The list is in the engine's recommended order — times "
            "first, because a slot you were already free in costs nothing where "
            "distance costs travel on every game forever — but the order is a "
            "recommendation and any rung may be taken directly."
        ),
    )
    ask: RelaxationAsk = Field(
        ...,
        description=(
            "Which of **your own** asks it relaxes. A rung never touches a "
            "measurement, a term, a weight, or the quality floor."
        ),
    )
    candidates_above_floor: int = Field(
        ...,
        ge=0,
        description=(
            "How many people would clear the quality floor at this rung, from a "
            "genuine re-run. The number on the button is true."
        ),
    )
    window: Window = Field(
        ...,
        description=(
            "This rung's **own** window. A challenge sliding from `WEEKEND` to "
            "`THIS_WEEK` is part of what widening costs, and you see it before "
            "you pay it."
        ),
    )
    radius_km: int = Field(
        OMITTED,
        ge=1,
        description=(
            "The widened radius, on a `RADIUS` rung. Always inside the same 1-50 "
            "km your own slider holds: a relaxation never offers a radius you "
            "could not have set yourself, so a searcher already at 50 km is "
            "offered no radius rung at all."
        ),
    )
    slot: AvailabilitySlotResource = Field(
        OMITTED,
        description=(
            "The one cell this rung would add to your week, on a `TIMES` rung, "
            "and **for this search only**. The same two named fields every "
            "other slot crosses in, because this one is drawn on the same "
            "seven-by-three grid the player just filled in — ticked there as "
            "belonging to this search and to no later one."
        ),
    )


class PromptSchema(BaseModel):
    """A question the app is offering to ask. **It never changes a value.**

    The platform notices that you improvised a week, that you keep widening to
    the same radius, that your searches disagree with what you declared, or that
    the week on your profile is months old — and in every case it asks. The
    payload is the value already in play, so the sheet can show the change rather
    than describe it.
    """

    prompt: Prompt = Field(..., description="Which question, as a code")
    radius_km: int = Field(
        OMITTED, ge=1, description="The widening you keep taking"
    )
    slots: list[AvailabilitySlotResource] = Field(
        OMITTED,
        description=(
            "The week this search actually ran on, in the same two named fields "
            "every other week on the wire crosses in — because the sheet **draws** "
            "this one on the seven-by-three grid beside the profile's own and "
            "quotes its count off the same list. **An empty list is a cleared "
            "week** — the player unticked every cell, which is a legal edit and a "
            "legal thing to be offered — where the field being absent means this "
            "is not the times prompt at all."
        ),
    )
    mode: SearchMode = Field(
        OMITTED, description="The mode your recent searches keep choosing"
    )


class SearchEnvelope(BaseModel):
    """Every fact about *the search*, as opposed to about a candidate.

    One object, identical on every route that creates a search: one renderer, one
    type.
    """

    search_id: UUID = Field(
        ...,
        description=(
            "The answer's identity. Minted server-side and recorded before this "
            "response was returned."
        ),
    )
    at: datetime
    surface: SearchSurface
    mode: SearchMode | None = Field(
        ...,
        description="Null exactly on the deck, which has no mode.",
    )
    my_area_code: str = Field(
        OMITTED,
        description=(
            "**Your own** coarse area, as the code the candidate's card carries "
            "one in, and as this search ran on it.\n\n"
            "It is here so a card can say *in your area* — a comparison between "
            "two codes, which is the one sentence an `area_code` licenses a "
            "client to write. The card is handed both codes rather than reading "
            "the profile for the second: a card that reached for a value nobody "
            "passed it would be drawing from global state.\n\n"
            "**Omitted on a search recorded before it was kept**, and on those "
            "only. It is the search's area rather than the profile's current "
            "one, so a read-back reproduces the answer that was given rather "
            "than the one that would be given now — and an absent code drops "
            "the sentence, where an empty one would quietly claim *never in "
            "your area*."
        ),
    )
    ruleset_version: str = Field(..., description="What the numbers were")
    engine_version: str = Field(..., description="How the maths works")
    optimised_for: OptimisedFor
    index_stale: bool = Field(
        ...,
        description=(
            "Whether the candidate index was more than fifteen minutes behind "
            "the log. The search was served either way; past a day it would "
            "have been refused instead."
        ),
    )
    pool: PoolSchema
    radius_clamp: bool = Field(
        ...,
        description=(
            "Whether a widening offer hit the profile slider's own ceiling. "
            "False on a search that widened nothing."
        ),
    )
    sorts_available: list[SortOption] = Field(
        ...,
        description=(
            "Which re-sorts the client may draw over rows it already holds. "
            "**A sort that would reorder nothing is not in this list**, and the "
            "control is not drawn — a visible control that does nothing is the "
            "product lying quietly. Re-sorting costs no round trip."
        ),
    )
    rung_offers: list[RungOfferSchema] | None = Field(
        ...,
        description=(
            "What relaxing your own asks would be worth, each with a real "
            "count from a genuine re-run.\n\n"
            "**`null` means the offers were not computed at all** — your "
            "shortlist was long enough that nobody needed them. An empty list "
            "means they were computed and there is nothing left to offer, which "
            "is the honest empty state: the pool beside it is the whole answer."
            "\n\n"
            "**A search that took a rung is offered none**: one climb per search "
            "screen, so the widest any accepted offer reaches is twice the "
            "radius you saved. That search's list is empty rather than `null`, "
            "and `rung_taken` beside it is what tells the two empties apart."
        ),
    )
    prompts: list[PromptSchema] = Field(
        OMITTED,
        description=(
            "Questions this search raises, each of which changes nothing until "
            "you answer it. Present on a search and **omitted on a read-back**, "
            "where a month-old question would be asked about a value that has "
            "since moved."
        ),
    )


class LikelyRangeSchema(BaseModel):
    """The **likely range** — μ ± σ, clamped to the scale — as `rating` published it.

    Nested rather than two flat fields, because a range is one value with two
    edges and the rating routes already spell it this way; a card that carried
    ``range_low`` and ``range_high`` loose beside ``level`` would be the same
    fact in a second shape.

    **The client computes nothing here.** It is projected onto the index row
    from ``rating.rating_initialised`` and copied onto the card, because
    ``likely_range()`` returns unrounded values and the rounding lives in the
    engine — a range derived anywhere else is a second set of drawing constants.
    """

    low: float
    high: float


class PlayerCardSchema(BaseModel):
    """Who this person is, on a card. **A closed list with one permanent gap.**

    **No activity recency at any granularity** — not a timestamp, not *active
    today*, not a green dot. Liveness reaches a screen the one way it is
    sanctioned to: as a reason code. The other gap the list was closed with —
    *no bio, and no free-text field of any kind* — was opened by exactly one
    field, `intro`, on the terms that refusal set: its own decision with a
    moderation story attached (``docs/adr/0170``). Still no bio, no paragraph,
    no second field, and no free text that is scored.

    **The last three fields are the record block, and every one of them is
    omitted rather than nought.** They are what the platform has watched this
    person do — a Player Score, a count of counted games and a run of form — and
    a nought printed for somebody it has watched do nothing would be a claim
    where there is a gap. ``last_five`` is the one that has to keep the recency
    rule while carrying five events: it is **outcomes in order and no dates**,
    which is a run of form rather than a statement about when anybody was last
    here.
    """

    name: str = Field(
        ...,
        description=(
            "The whole name, and **nothing may derive a familiar form from it** "
            "— every sentence naming somebody uses the whole name or names "
            "nobody (``docs/adr/0171``). Never the nickname: a handle is drawn "
            "on a record and their own You tab, and said nowhere."
        ),
    )
    photo_id: UUID = Field(
        default=OMITTED,
        description=(
            "The first photo — order is meaning in a photo list. **The id is "
            "what is stored**: a presigned link cannot live in a record kept "
            "for ever, so the record keeps this one and the link beside it is "
            "minted per response. **Omitted** when the player has no photo, "
            "and the client draws the generated court poster."
        ),
    )
    photo_url: str = Field(
        default=OMITTED,
        description=(
            "Short-lived signed URL that draws that photo. **Minted per "
            "response and stored nowhere**: it dies within minutes, and two "
            "reads of the same search carry two different links to the same "
            "photograph.\n\n"
            "**You cannot sign one yourself.** `GET /photos/{photo_id}` signs "
            "only *your own* photos and refuses a stranger's id deliberately, "
            "and a card's photo is by definition somebody else's — so this is "
            "the only address this photograph has.\n\n"
            "**Present exactly when `photo_id` is.** A link that has expired is "
            "not an error to report: draw the generated court poster, which is "
            "what a player with no photo gets in any case."
        ),
    )
    review: PhotoReviewDecision = Field(
        default=OMITTED,
        description=(
            "What the on-court check concluded about `photo_id`, or **omitted** "
            "where this photograph has not been checked.\n\n"
            "**Omitted is not `allowed`, and only `allowed` earns a shield.** "
            "Three answers, not two: checked and passed, checked and flagged, "
            "and *nobody looked* — a photo that arrived while the reviewer could "
            "not be reached, or before the check existed at all. A client that "
            "drew a tick on the absence would be claiming a check happened on "
            "every photograph on the platform.\n\n"
            "**A fact about this photograph and not about the player.** It is "
            "present only beside `photo_id`, it is search-time like every other "
            "fact on this card, and `flagged` blocks nothing — the photo is "
            "stored, it is shown, and the check is wrong sometimes.\n\n"
            "**The evidence never crosses.** No confidence, no similarity "
            "vector, no model, no prompt-set fingerprint: those are collected so "
            "the threshold can be re-derived, and they are not a number a player "
            "can do anything with. A code, not copy — the words belong to the "
            "client."
        ),
    )
    area_code: str = Field(..., description="Their coarse area, as a machine code")
    social_tags: list[str] = Field(..., description="The Social tag ids they hold")
    intro: str = Field(
        default=OMITTED,
        # **No `max_length` here, deliberately.** The cap binds the write and
        # not the read: a line already on a search record was admitted when it
        # was written, and a response schema that refused it after the cap
        # moved would take a deal down for a fact the platform recorded.
        description=(
            "One line this player wrote about themselves — their **intro** — "
            f"verbatim: at most {INTRO_MAX_CHARACTERS} characters, no line "
            "breaks, in whatever language they wrote it. **Omitted where they wrote "
            "none**, and never an empty string: the intro is optional and a "
            "player who skipped has no line, so the card closes up rather than "
            "drawing a blank quotation.\n\n"
            "**A fact about the person, assembled by `player_profile`** — the "
            "one field this closed list has gained, under its own admission "
            "rule: it is what its subject published, it does not change with "
            "who is looking, and it is projected to the candidate index like "
            "the tags. It is **never scored**: no term reads it and the "
            "scorer's fence refuses the word.\n\n"
            "**Fenced at the write, not here.** A line carrying a phone "
            "number, an email, a URL or an `@handle` was refused before it "
            "was stored, so what arrives is a line about a player and not a "
            "way to reach one. What it says is theirs; a line you object to "
            "is what a block is for.\n\n"
            "**Drawn on the deck card and the record sheet, and not on Find a "
            "game's cards** — those are about the game, and the line is about "
            "the person. Never spoken as the player's name and never "
            "truncated: the cap is what makes an ellipsis unnecessary."
        ),
    )
    level: float = Field(..., description="Their Level, as RacketSkill published it")
    band: str = Field(..., description="The Level band's published name")
    range: LikelyRangeSchema = Field(
        ...,
        description=(
            "The **likely range** their Level sits in, μ ± σ as RacketSkill "
            "published it. Always present: a card that stated a Level without "
            "it would show two players at the same Level with no way to tell "
            "that one of them is a guess. **The band's numeric edges are not "
            "here** — they are not a second range to compare this one against."
        ),
    )
    player_score: int = Field(
        default=OMITTED,
        ge=0,
        le=100,
        description=(
            "Their **Player Score** out of a hundred — reliability, as the "
            "platform watched it: whether games arranged for them were played, "
            "and whether challenges sent to them were answered inside their "
            "window.\n\n"
            "**The published figure and never a re-derivation of it.** It is the "
            "same number this player's own profile prints, at the same "
            "player-facing weights, because a card explaining a match with a "
            "figure their own screen disagrees with is worse than a card that "
            "says nothing.\n\n"
            "**Omitted where the platform has watched nothing**, which is most "
            "people today. Never `0`: somebody nothing was ever arranged for has "
            "not failed to turn up, and the absence is what lets *Most reliable* "
            "sort them last instead of first."
        ),
    )
    counted_games: int = Field(
        default=OMITTED,
        ge=1,
        description=(
            "How many **counted** games they have played. A friendly is not one "
            "— it was never evidence about anybody, by the choice of the people "
            "who arranged it — and a game nobody agreed a score for **is**: an "
            "unscored game is an evening rather than evidence, so it says these "
            "people were on a court and it moves nobody's Level.\n\n"
            "**Omitted where they have played none**, and never `0`. Absence has "
            "one spelling on this card."
        ),
    )
    last_five: list[GameResult] = Field(
        default=OMITTED,
        max_length=5,
        description=(
            "Their last five counted results, **oldest to newest** — the run of "
            "form a card draws left to right. Only games whose result was "
            "agreed are here; an unscored one moved nobody's Level and is in "
            "`counted_games` instead.\n\n"
            "**Fewer than five is a real answer and it is never padded.** Three "
            "entries means three counted results, and the client draws the gap "
            "rather than filling it.\n\n"
            "**There are no dates here, at any granularity.** This is a run of "
            "outcomes in order, and a moment beside one of them would be "
            "activity recency, which no card carries in any shape.\n\n"
            "**Omitted where nothing of theirs has been counted and agreed.**"
        ),
    )


class ConcernSchema(BaseModel):
    """The engine's own statement that a term is genuinely weak.

    Judged where the weights and the curves are, over **points forgone** rather
    than over a raw value — a social vibe of 0.20 costs under four points of a
    competitive match and nearly twenty of a friendly, and only one of those is
    worth warning anybody about. A client thresholding a value would be that
    judgement in TypeScript, written differently in every client.

    **Ranked by the engine, capped by the client**: a card shows one, *Why 78?*
    shows all of them.
    """

    term: Term


class DegradedTermSchema(BaseModel):
    """One term that stood down, and **whose gap that is**.

    A pair rather than a bare ``Term``, because the flat list held two different
    sentences as one fact: *reliability is not a thing on this platform yet* and
    *they have not said what kind of evening they want*. The engine draws that
    line to decide a number — the evidence gate counts person-specific gaps and
    never platform-wide absence — and it now survives the wire.

    **The reason is a code and the client writes the sentence** (``docs/adr/0106``).
    A client deriving *"they haven't declared"* from ``INTENT_ALIGNMENT`` alone
    would be an engine rule in TypeScript, and *"nobody has a record yet"* is a
    sentence that goes silently false the day ``matches`` ships. The term supplies
    the other half: ``INTENT_ALIGNMENT`` and ``SOCIAL_VIBE`` under one code are two
    different sentences.

    **The platform tier repeats on every row and is drawn once.** It is here
    because it is this candidate's renormalisation basis — a 78 built on four
    terms and a 78 built on seven are different readings of the same number, and
    dropping it would make the row's own arithmetic unreadable — and
    ``NOT_YET_ON_THIS_PLATFORM`` is a fact about the platform rather than about
    twenty people, so the sheet states it once beside the version stamps
    (``the-play-screens.md`` §8). Suppressing it on the wire instead was refused:
    the basis is not decoration.
    """

    term: Term
    reason: DegradedReason = Field(
        ...,
        description=(
            "Whose gap this is: nobody's (`NOT_YET_ON_THIS_PLATFORM` — the term "
            "has no provider on this platform at all), yours "
            "(`NOTHING_FROM_YOU`), theirs (`NOTHING_FROM_THEM`), or the "
            "surface's (`NOT_READ_ON_THIS_SURFACE` — the deck reads no intent "
            "for anybody, so the term stood down for every card and says "
            "nothing about either of you). `NOTHING_FROM_THEM` deliberately "
            "covers every reason a record could not be read, because "
            "separating them would publish activity recency."
        ),
    )


class ScoredTermSchema(BaseModel):
    """One term that produced a reading, and what it was worth here."""

    term: Term
    weight: float = Field(
        ...,
        description=(
            "The **renormalised** weight — this term's share of a hundred over "
            "the terms that actually fired."
        ),
    )
    value: float = Field(..., ge=0, le=1)
    contribution: float = Field(
        ..., description="The weight times the value. The contributions sum to the Fit."
    )
    evidence: Evidence


class ModifierSchema(BaseModel):
    """One modifier that fired, and what it was worth on this pairing."""

    code: ModifierCode
    points: float


class AtStakeSchema(BaseModel):
    """What a **counted** game against this opponent would do to your Level.

    Filled by the backend, never by the matcher and never by the client — it is
    the rating engine's own update rule read forward (``docs/adr/0139``), so the
    pair printed here is the pair the game will deliver if it is played. Omitted
    in for-fun, where a counted result is meaningless rather than unavailable.

    **Neither figure is ever zero**, and it is priced head-to-head: in a doubles
    sport the game will be a four and the other two seats are unknown when the
    card is drawn, so the magnitude carries that sport's weighting while the
    pairing is the one you are looking at.
    """

    win_delta: float
    loss_delta: float


class ForecastSchema(BaseModel):
    """How even a game is forecast to be. One type, everywhere it appears.

    ``provisional`` travels **inside** the forecast rather than beside it: the
    failure being guarded against is a screen showing the number without its
    caveat, and a sibling boolean is exactly how the two get separated in a
    refactor.
    """

    pct: int = Field(..., ge=0, le=100)
    sigma_group: float = Field(
        ..., description="The confidence is part of the claim, so it crosses with it"
    )
    provisional: bool
    assumption: str | None = Field(
        ...,
        description=(
            "What the provisional figure assumed, as a code the client renders "
            "in its own words. Null when nothing was assumed."
        ),
    )


class CandidateSchema(BaseModel):
    """One row of the shortlist: the pairing, and the person.

    Three field families have a **different author** from the rest and are
    attached by the backend after the scorer returns — the card, the at-stake
    block and the distance. None of them is a fact the scorer may see, and none
    may be computed by the client.

    On a read-back this row means *the live gates still admit this person*, and
    it says so: ``withheld`` is ``false``, positively, rather than absent. A row
    the gates no longer admit is a :class:`WithheldRowSchema` instead, and the
    two are a union precisely so that **rendering a person the product has agreed
    not to show is not a shape this contract can hold** (``docs/adr/0109``).
    """

    #: ``false`` on a read-back, and **omitted on a fresh search**, where every
    #: row is live by construction and the question does not arise.
    withheld: Literal[False] = Field(
        default=OMITTED,
        description=(
            "Present only on a read-back, where it is always `false`: the "
            "fail-closed gates were re-evaluated and this row still stands. A "
            "row they no longer admit arrives as the withheld shape instead."
        ),
    )
    player_id: UUID
    fit: float = Field(
        ...,
        description=(
            "The printed number, out of a hundred, and the only one a player is "
            "asked to trust. It contains no Liveness."
        ),
    )
    distance_km: float = Field(
        default=OMITTED,
        description=(
            "Kilometres to one decimal, measured between the two **drawn "
            "spots** — one fixed point inside each player's coarse area, the "
            "same for every viewer — and never below `0.1`. The Fit does not "
            "read it: the distance term and the radius gate measure cell to "
            "cell, so a player at the very edge may print `10.3` inside a "
            "10 km reach. **Promoted out of the distance evidence** so the "
            "*Closest* sort reads a field rather than reaching into a variant, "
            "and **omitted** rather than sent as zero when the distance term "
            "stood down — which is what lets a stood-down row sort last "
            "instead of first."
        ),
    )
    player_card: PlayerCardSchema
    concerns: list[ConcernSchema]
    terms: list[ScoredTermSchema] = Field(
        ...,
        description=(
            "Every term that fired, **ranked by contribution** — the reasons, in "
            "the order the arithmetic puts them in. The cap is the client's."
        ),
    )
    degraded_terms: list[DegradedTermSchema] = Field(
        ...,
        description=(
            "The terms that stood down, each with **whose gap it is**: the "
            "renormalisation basis. Without it a Fit is uninterpretable — a 78 "
            "built on four terms and a 78 built on seven are different readings "
            "of the same number — and without the reason beside it, *reliability "
            "is not a thing here yet* and *they have not said what kind of "
            "evening they want* arrive as one flat list."
        ),
    )
    modifiers: list[ModifierSchema]
    liveness_reasons: list[LivenessReason] = Field(
        ...,
        description=(
            "Why this person moved, ranked by how far. **Codes only** — there "
            "is no field here a Liveness number could be written to."
        ),
    )
    inclusion_reason: WireInclusionReason = Field(
        default=OMITTED,
        description=(
            "Why this person is in the list at all, when the reason is one the "
            "searcher is owed. **A union of one**: only an interest lift "
            "*admits* anybody, and the two reasons that merely reorder stay in "
            "the store — one reaches you as a liveness reason instead, and the "
            "other is a third party's unpopularity you are owed no version of. "
            "Omitted otherwise."
        ),
    )
    at_stake: AtStakeSchema = Field(
        default=OMITTED,
        description=(
            "What a counted game against this person would do to your Level — "
            "the rating engine's own update rule read forward, so the pair "
            "printed here is the pair the game will deliver if it is played.\n\n"
            "**Omitted in for fun**, where a counted result is meaningless "
            "rather than unavailable, and **omitted in competitive when either "
            "of you holds no rating in this sport** — never drawn as a pair of "
            "zeros."
        ),
    )
    would_be_forecast: ForecastSchema = Field(
        default=OMITTED,
        description=(
            "What this candidate would leave on court. Precomputed only when a "
            "line-up has exactly one seat open, so **omitted on every "
            "shortlist**."
        ),
    )


class WithheldRowSchema(BaseModel):
    """A row that was recorded, and that the live gates no longer admit.

    **Stated, never vanished.** A read-back that quietly returned nineteen rows
    where twenty were recorded is the same class of lie as a breakdown that
    quietly stops adding up, and worse for being invisible — so the row keeps its
    place in the list and says what happened to it.

    **It names no gate, and it carries no person.** The four fail-closed gates
    are a block either way, a hold, an account that may not be shown, and the
    mutual gender preference; naming which one fired would tell a searcher that a
    particular person blocked them, was suspended, or changed a safety setting.
    ``docs/adr/0095`` is explicit that *neither party is ever notified and the
    other side sees no trace anywhere in any response*, and that rule does not
    weaken because the surface has a longer memory. So this shape has one field,
    and there is nowhere on it for a reason, an id, a card or a breakdown to be
    written.

    The searcher loses nothing they are owed: they saw this row when they ran the
    search, and what has changed since is only that the product will no longer
    show it to them.
    """

    withheld: Literal[True] = Field(
        ...,
        description=(
            "Always `true`. This row was recorded and is no longer shown: the "
            "fail-closed gates were re-evaluated at read time and one of them "
            "excludes it now. **Which one is deliberately not said.**"
        ),
    )


class ShortlistResponse(BaseModel):
    """The whole answer: one envelope, and at most twenty rows.

    **Bounded and unpaginated.** There is no page two; past the last row there
    are rung offers or an honest empty state. The bound is ruleset data, so a
    client never reads twenty from anywhere — it renders the rows it is given.
    """

    search: SearchEnvelope
    candidates: list[CandidateSchema | WithheldRowSchema] = Field(
        ...,
        description=(
            "Ranked. **An empty list is a `200`** — the honest empty state is an "
            "answer, not a failure.\n\n"
            "A read-back may carry withheld rows: the record is immutable and "
            "the gates are live, so a row the product has since agreed not to "
            "show keeps its place and states that it is withheld. Branch on "
            "`withheld` — a fresh search never carries one."
        ),
    )


class RunLineupRequest(BaseModel):
    """⚡ *Fill the seats.* **The line-up and fill-seats are one request.**

    They differ by `locked_seats` being non-empty, which is a property of what
    you send rather than of where you send it — so hand-seating somebody and
    pressing ⚡ is the same shape as ⚡ on an empty court, and there is no second
    route for a client to get wrong.

    There is **no seat count** here and there never will be: how many people sit
    down is the sport's own fact. There is no radius either, for the reason the
    shortlist has none.

    **A fill names the challenge it completes and says nothing else about the
    court** (`ADR-0150`). Send `completing_challenge_id` and `sport`, `mode` and
    `locked_seats` are **refused** beside it rather than made optional: all three
    are facts that challenge already holds, and a caller supplying one is
    offering a second place for a fact to be true — which is how somebody who is
    not in the challenge gets locked, or somebody who is gets forgotten.
    """

    sport: Sport = Field(
        OMITTED,
        description=(
            "Which sport this line-up is for. **Required, except beside "
            "`completing_challenge_id`** — a challenge already knows what game "
            "is being arranged, and sending both is refused."
        ),
    )
    mode: SearchMode = Field(
        OMITTED,
        description=(
            "Competitive or for fun — the weight vector for this one search. "
            "It selects the **group** vector too, which inverts against the "
            "shortlist's: for fun puts more weight on how the four get on than "
            "on how even the sides are.\n\n"
            "**Required, except beside `completing_challenge_id`**, and refused "
            "there. A challenge sent with a mode keeps it — a competitive court "
            "must not have its last seat filled by a for-fun search — and one "
            "sent without a mode takes yours, resolved from your declared Play "
            "intent. **There is no mode picker anywhere.**"
        ),
    )
    locked_seats: list[UUID] = Field(
        default_factory=list,
        description=(
            "Players you have already seated by hand, **in seat order**. Send "
            "none and the engine fills every seat; send one or two and it fills "
            "the rest **around them**, which is when it starts optimising for "
            "the group rather than for you — `search.optimised_for` says so.\n\n"
            "Everybody named must be somebody this search can still seat, and "
            "they must be able to share a court **with each other** — every gate "
            "binds all six pairs. Either refusal is "
            "`locked_seat_not_available`, naming nobody, rather than a quiet "
            "replacement.\n\n"
            "Nobody twice, and never more than the sport seats.\n\n"
            "**Refused beside `completing_challenge_id`.** The people already "
            "on that court are its locked seats, read off the challenge."
        ),
    )
    completing_challenge_id: UUID = Field(
        OMITTED,
        description=(
            "The half-built challenge this fill completes. **Send it and send "
            "nothing else about the court**: the sport, the kind of evening and "
            "the locked seats are all read off it.\n\n"
            "**Any live member may fill; ending a court is a different act** — "
            "removing one that was never a game is the organiser's while nobody "
            "has joined and nobody's once somebody has, and calling off the game "
            "a court became is any player's on it. A "
            "challenge born of two mutual yeses has an organiser who is only "
            "whoever said yes second, and leaving the other one unable to finish "
            "the four would be an arbitrary tiebreak deciding whose game it "
            "is.\n\n"
            "The people who accepted come back as **ordinary candidate rows**, "
            "so the builder can draw them; the open-challenge gate steps aside "
            "for this one challenge and for nothing else, and the four "
            "fail-closed gates are untouched — so somebody blocked, held or "
            "deactivated since they accepted is still "
            "`locked_seat_not_available`.\n\n"
            "Everybody who has already **answered** this challenge is out of its "
            "own pool, including the people who declined it.\n\n"
            "**The window is never re-stamped**, and a challenge born of a "
            "mutual yes has none at all: a newly-invited player answers against "
            "the label the original send derived, and the plan is the authority "
            "on when anybody actually plays."
        ),
    )

    @model_validator(mode="after")
    def _is_a_court_that_could_exist(self) -> "RunLineupRequest":
        """The same two refusals the forecast makes, plus the one this route owns.

        A court with the same person on it twice and a court with more people
        than it has seats are malformed **asks**, and both are refused here
        rather than inside — where the second would surface as a `503` about the
        engine, which is a sentence about the platform for a mistake in the
        request.

        **The third is the fill's own** (`ADR-0150` §2): `completing_challenge_id`
        and the three facts that challenge already holds are mutually exclusive,
        and this is the boundary that says so. Refusing here rather than making
        the three optional is what stops a caller locking somebody who is not in
        the challenge, or forgetting somebody who is.
        """

        if self.completing_challenge_id is not None:
            named = [
                field
                for field, sent in (
                    ("sport", self.sport is not None),
                    ("mode", self.mode is not None),
                    ("locked_seats", bool(self.locked_seats)),
                )
                if sent
            ]
            if named:
                raise ValueError(
                    "a fill names the challenge it completes and nothing else "
                    f"about the court: remove {', '.join(named)}"
                )
            return self
        if self.sport is None or self.mode is None:
            raise ValueError(
                "a line-up that completes no challenge has to name its sport "
                "and its mode"
            )
        return _a_court_that_could_exist(self, self.sport, self.locked_seats)
    availability_override: list[AvailabilitySlotResource] = Field(
        OMITTED,
        description=(
            "The week to run **this one line-up** against. Omit to use the grid "
            "on your profile — **omit it, never send `null`**."
        ),
    )
    offered_by_search_id: UUID = Field(
        OMITTED,
        description=(
            "The search whose relaxation offer this one accepts. Taking a rung "
            "is a **new search citing the one that offered it**."
        ),
    )
    rung: Rung = Field(
        OMITTED,
        description=(
            "Which rung of that search's offer you are taking. Sent with "
            "`offered_by_search_id` or not at all."
        ),
    )


class ForecastRequest(BaseModel):
    """What a four you composed yourself would leave on court.

    **This route creates no search and records nothing.** Re-posting `/lineups`
    per swap would enter a six-edit builder session into *searches run* as six
    searches, which is a lie in the one table the product uses to judge itself.

    `search_id` is **required**, and every player named must have appeared in
    that search's returned rows. Unbounded, this would be a level lookup for any
    player in the city reachable by id; bounded, it tells you nothing the
    shortlist did not already show you.
    """

    sport: Sport = Field(..., description="Which sport this four would play")
    mode: SearchMode = Field(
        ..., description="Competitive or for fun — the vector this reads under"
    )
    search_id: UUID = Field(
        ...,
        description=(
            "The search these people came off. **Required** — a forecast about "
            "somebody no search of yours showed is refused, not computed."
        ),
    )
    players: list[UUID] = Field(
        ...,
        min_length=1,
        description=(
            "The people beside you, **in seat order**: the first is your partner "
            "in the arrangement the response marks `is_current`. One, two or "
            "three — a seat may be empty, and the forecast comes back "
            "**provisional** when one is.\n\n"
            "Nobody twice, and never more than the sport seats. An empty seat is "
            "read *as if the missing player matched the one already there*, which "
            "is a claim about somebody who is not there — sending the same person "
            "twice would make that assumption look like a fact."
        ),
    )

    @model_validator(mode="after")
    def _is_a_court_that_could_exist(self) -> "ForecastRequest":
        """The two ways a composed line-up is not one.

        Checked at the boundary rather than inside, because both are malformed
        **asks** rather than answers the engine has to have an opinion about: a
        court with the same person on it twice, and a court with more people than
        it has seats.
        """

        return _a_court_that_could_exist(self, self.sport, self.players)


def _a_court_that_could_exist(
    request: _RequestT, sport: Sport, seats: list[UUID]
) -> _RequestT:
    """Nobody twice, and never more than the sport seats.

    One implementation for the two routes that name people to put on a court,
    because *how many sit down* is the sport's own fact
    (``kernel/sports.py``) and a second copy of that arithmetic is a second place
    for a sport to be added without it.
    """

    room = SPORT_SPECS[sport].players - 1
    if len(seats) > room:
        raise ValueError(
            f"{sport.value} seats {room} beside you, and you named {len(seats)}"
        )
    if len(set(seats)) != len(seats):
        raise ValueError("the same player cannot take two seats")
    return request


class ArrangementSeatSchema(BaseModel):
    """One seat within one arrangement: where it is, and who is in it.

    `relationship` is **stated and never inferred from the side** — the whole
    partner/opponent asymmetry hangs on it, and a client deriving it would be a
    second implementation of a domain rule.
    """

    seat_index: int = Field(
        ...,
        ge=0,
        description=(
            "Which seat, stable across all three arrangements: 0 is you, 1 is "
            "beside you, 2 and 3 are across the net."
        ),
    )
    relationship: Relationship
    player_id: UUID = Field(
        default=OMITTED,
        description=(
            "Who is in this seat. **Omitted on an open seat** — the top-level "
            "`seats` list says why that one is open."
        ),
    )


class SidesSchema(BaseModel):
    """The two sides of the net. **You are always on `A`.**

    There is no arrangement in which the searcher crosses the net, because
    *which side am I on* is not a question a builder asks: what varies is who is
    beside you.
    """

    A: list[ArrangementSeatSchema] = Field(
        ..., description="Your own side, you first"
    )
    B: list[ArrangementSeatSchema] = Field(..., description="The opposition")


class SplitSchema(BaseModel):
    """The two side strengths this arrangement's forecast was read from.

    **The evidence behind the percentage**, and never a second score
    (``docs/adr/0136``). ``pct`` says *how even*; this says *between what and
    what*, on the Skill scale a player already reads levels on — which is
    ``matchmaking-engine.md`` §12 rule 1 applied to the figure that was already
    crossing, exactly as it put ``sigma_group`` beside ``pct``. The group
    objective stays where ADR-0117 left it: recorded, and never returned.

    **On the arrangement rather than on the forecast.** ``ForecastSchema`` is
    *one type, everywhere it appears* and rides on every shortlist row's
    ``would_be_forecast``; a response carries at most three arrangements and tens
    of candidate rows, and this is a fact about an arrangement.

    **These are numbers only the engine has.** A side's strength is not the mean
    of the two people on it, so a client averaging seated levels would print a
    different pair — which is the arithmetic ``the-play-screens.md`` §11.3
    refuses, in the one check that looks for arithmetic rather than reading
    intent.
    """

    your_side: float = Field(
        ...,
        description=(
            "Your half's combined strength, on the Skill scale. **You are always "
            "side `A`** — there is no arrangement in which you cross the net."
        ),
    )
    their_side: float = Field(..., description="Theirs, on the same scale")
    gap: float = Field(
        ...,
        description=(
            "`your_side` − `their_side`, **signed**. Served rather than left to "
            "a subtraction: a client subtracting two rounded figures and an "
            "engine subtracting two unrounded ones disagree at the boundary, and "
            "the card prints all three.\n\n"
            "Signed because the bar takes an *advantage* — an unsigned gap would "
            "leave the client deciding which half of it is bigger, which is the "
            "same arithmetic in a smaller disguise."
        ),
    )


class ArrangementSchema(BaseModel):
    """One way round, with its own forecast. **All of them cross.**

    There are exactly three pairings of four people and the engine walks all
    three to choose. Returning what it already knows costs nothing and makes
    *Even it out* a **selection** rather than a calculation — every swap the
    builder permits is one of these, so there is no arithmetic left for a client
    to be tempted by.
    """

    pairing_id: int = Field(
        ..., ge=1, description="Which of the arrangements, stable within one answer"
    )
    is_current: bool = Field(
        ...,
        description=(
            "The one being drawn: **the evenest on a line-up**, and the seat "
            "order you sent on a forecast.\n\n"
            "A line-up opens on the closest game of the three, in both modes — "
            "the same re-seating *Even it out* performs by hand. **Who is on the "
            "court is still the group objective's choice** and `group_reason` "
            "still says why; what this decides is only which way round they sit. "
            "`lineup.seats` follows it."
        ),
    )
    is_best: bool = Field(
        default=OMITTED,
        description=(
            "Best by the group objective. **The objective itself is never "
            "returned** — a second score you would have to trust is worse than "
            "none — so `group_reason` names what decided it instead.\n\n"
            "**Omitted on every arrangement when no objective was computed**, "
            "rather than pointed at something else: a line-up with a seat still "
            "open, a singles line-up, and every forecast. There is nothing to be "
            "best *by* in any of them — no cross pairs, no seat delta, no mean "
            "over three Fits — and *Even it out* is then the only selection "
            "there is. Draw `is_evenest`."
        ),
    )
    is_evenest: bool = Field(
        ...,
        description=(
            "The closest game of the three — what *Even it out* selects. **A "
            "separate boolean from `is_best` because the two can differ**, which "
            "happens precisely when the four's levels are near-equal and balance "
            "has nothing left to say."
        ),
    )
    sides: SidesSchema
    forecast: ForecastSchema
    split: SplitSchema = Field(
        ...,
        description=(
            "The two side strengths the forecast was computed from, and the "
            "signed difference between them. **The same computation `pct` is** — "
            "an arrangement whose sides are equal reads `gap` 0 and the evenest "
            "`pct` of the three.\n\n"
            "**A provisional arrangement carries one like any other**, under the "
            "same assumption `pct` is carried under: the empty seat is read as if "
            "the missing player matched the one already there, and `provisional` "
            "carries that caveat for all four numbers at once."
        ),
    )


class LineupSeatSchema(BaseModel):
    """One place on the court, with the person in it or the reason it is empty.

    **The person is named by id and their breakdown rides once**, in
    `candidates[]` — the same list every other surface returns, carrying **the
    same number the shortlist showed**, because nothing is re-scored behind your
    back when somebody sits down. Four breakdowns repeated across a court and
    three arrangements is four chances for two copies to disagree, on a payload
    that is already tens of kilobytes.
    """

    side: CourtSide
    seat_index: int = Field(..., ge=0)
    relationship: Relationship
    player_id: UUID = Field(
        default=OMITTED,
        description=(
            "Who is in this seat, to look up in `candidates[]`. **Omitted on an "
            "open seat**, and on your own — you are not a row of your own search."
        ),
    )
    unfilled_reason: UnfilledReason = Field(
        default=OMITTED,
        description=(
            "Why this seat is empty. **A seat is never filled below the quality "
            "floor to complete a four**, a newcomer least of all — *three of "
            "four* is an honest answer, and so is nobody.\n\n"
            "`NO_ADMISSIBLE_COMBINATION` is the one worth reading twice: there "
            "were people, and no four of you could share a court. Omitted on a "
            "seat that is taken."
        ),
    )


class LineupSchema(BaseModel):
    """The court, every way round it can sit, and one reason it won.

    **A partial line-up is this shape with fewer people in it** — never a
    different one, and never an error. *Nobody* is this shape with every seat
    carrying a reason, so a client renders one thing.
    """

    seats: list[LineupSeatSchema] = Field(
        ...,
        description=(
            "The court as it currently stands, seat by seat, in the arrangement "
            "marked `is_current`."
        ),
    )
    arrangements: list[ArrangementSchema] = Field(
        ...,
        description=(
            "Every way round, each with its own forecast. Empty only when "
            "nobody could be seated at all."
        ),
    )
    group_reason: GroupReason = Field(
        default=OMITTED,
        description=(
            "Why this four beat the runner-up, as one closed code the client "
            "writes the sentence for. **Omitted when there was no runner-up** — "
            "one admissible four is not a four that won an argument."
        ),
    )
    dock: UnfilledReason = Field(
        default=OMITTED,
        description=(
            "`NO_SHARED_SLOTS` when the four of you have no hour in common. **A "
            "dock, never a refusal**: nobody is removed from the court for it, "
            "and the honest line is that you would all have to bend."
        ),
    )


class LineupResponse(ShortlistResponse):
    """The shortlist's envelope, the pool, and the court seated out of it.

    One envelope and one row shape across every surface, so the read-back has one
    renderer to reproduce: what a line-up adds is the seating, not a second way
    of describing a person. `candidates` is the **pool** ⚡ seated from — in Fit
    order, up to the ruleset's own candidate cap, the seated among them — and
    not the seated alone, so *Pick players myself* on this answer has the rest
    of the ranking to offer ([#407](https://github.com/Raketa02/Raketa/issues/407)).
    """

    lineup: LineupSchema


class ForecastResponse(BaseModel):
    """Three arrangements of a four you composed. **And no `search_id`.**

    Nothing was searched and nothing was recorded, so there is no id to read this
    back by and no breakdown to open. The two version stamps cross because a
    forecast nobody can reproduce is a number nobody should trust.
    """

    arrangements: list[ArrangementSchema]
    engine_version: str = Field(..., description="How the maths works")
    ruleset_version: str = Field(..., description="What the numbers were")


#: Every enum this contract publishes that is not already published by the
#: evidence union. Read by the contract test, so that *what a client generates*
#: is enumerated once for code rather than collected by eye.
PUBLISHED_VOCABULARIES: tuple[type[StrEnum], ...] = (
    OptimisedFor,
    WireInclusionReason,
    LivenessReason,
    ModifierCode,
)