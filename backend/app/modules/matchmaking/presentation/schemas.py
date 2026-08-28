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
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.matchfit.core import SearchMode, Term
from app.kernel import Sport
from app.modules.matchmaking.domain.prompts import Prompt
from app.modules.matchmaking.domain.relaxation import RelaxationAsk, Rung
from app.modules.matchmaking.domain.searches import SearchSurface, SortOption
from app.modules.matchmaking.presentation.evidence import Evidence
# **The same cell shape the profile route takes**, deliberately reused rather
# than restated: asking for a week in two shapes is how availability data goes
# stale, and one client grid editor should be able to post to either route.
from app.modules.player_profile.presentation.schemas import AvailabilitySlotResource
from app.modules.player_profile.domain.availability import Window


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
    """What a deal is asked for. **One field, and that is the whole contract.**

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
    """

    sport: Sport = Field(..., description="Which sport this deal is for")


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
    slot: str = Field(
        OMITTED,
        description=(
            "The one cell this rung would add to your week, on a `TIMES` rung, "
            "as `day:PART`. For this search only."
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
    slots: list[str] = Field(
        OMITTED, description="The week this search actually ran on, as codes"
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


class PlayerCardSchema(BaseModel):
    """Who this person is, on a card. **A closed list with two permanent gaps.**

    No bio and no free text of any kind, ever; and **no activity recency at any
    granularity** — not a timestamp, not *active today*, not a green dot.
    Liveness reaches a screen the one way it is sanctioned to: as a reason code.
    """

    nickname: str = Field(
        ...,
        description=(
            "The whole handle. There is no name in this platform and **nothing "
            "may derive a familiar form from it** — every sentence naming "
            "somebody uses the whole handle or names nobody."
        ),
    )
    photo_id: UUID = Field(
        default=OMITTED,
        description=(
            "The first photo — order is meaning in a photo list. **An id, never "
            "a URL**: a presigned link cannot live in a record kept forever, so "
            "the link is minted per response. **Omitted** when the player has "
            "no photo, and the client draws the generated court poster."
        ),
    )
    area_code: str = Field(..., description="Their coarse area, as a machine code")
    social_tags: list[str] = Field(..., description="The Social tag ids they hold")
    level: float = Field(..., description="Their Level, as RacketSkill published it")
    band: str = Field(..., description="The Level band's published name")
    counted_games: int = Field(
        default=OMITTED,
        description=(
            "How many counted games they have played. **Omitted today**: the "
            "games ledger has no provider in this build, and a zero would be an "
            "invented one rather than a measured nothing."
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

    Filled by the backend, never by the matcher and never by the client. Omitted
    in for-fun, where a counted result is meaningless rather than unavailable.
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
    distance_km: int = Field(
        default=OMITTED,
        description=(
            "Whole kilometres between the two coarse areas. **Promoted out of "
            "the distance evidence** so the *Closest* sort reads a field rather "
            "than reaching into a variant, and **omitted** rather than sent as "
            "zero when the distance term stood down — which is what lets a "
            "stood-down row sort last instead of first."
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
    degraded_terms: list[Term] = Field(
        ...,
        description=(
            "The terms that stood down: the renormalisation basis. Without it a "
            "Fit is uninterpretable — a 78 built on four terms and a 78 built "
            "on seven are different readings of the same number."
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
            "Omitted in for fun, where a counted result is meaningless rather "
            "than unavailable, and omitted today in competitive because the "
            "result-update rule does not exist."
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


#: Every enum this contract publishes that is not already published by the
#: evidence union. Read by the contract test, so that *what a client generates*
#: is enumerated once for code rather than collected by eye.
PUBLISHED_VOCABULARIES: tuple[type[StrEnum], ...] = (
    OptimisedFor,
    WireInclusionReason,
    LivenessReason,
    ModifierCode,
)