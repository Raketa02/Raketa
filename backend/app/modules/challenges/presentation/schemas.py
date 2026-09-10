"""The challenge wire shapes — **a court, and never a verdict about a person.**

Three rules decide everything below.

**A refusal names nobody, so neither does a response about one.** There is no
shape here in which a withheld seat, a gate or a reason could arrive: a refused
send answers with a code and an empty body, and the client re-reads the two
sources it already owns.

**The standing is derived and travels as a code.** ``Standing`` is six values and
the words for them are the client's (``docs/adr/0022``). Five of them are a fold
of the seats against the moment the list was read; ``WITHDRAWN`` is the one a
recorded decision puts there, because no arrangement of the seats reaches it
(``docs/adr/0142``). Either way it is **not** on the aggregate, in the store, or
anywhere a second copy could go stale.

**A seat carries its own deadline and no standing of its own.** Whether it is
waiting, lapsed or open is read off ``answer`` and ``answer_by`` against the
clock, so a client renders *how long you have* from a moment the backend computed
rather than one a phone derived.

**Every nullable field here is ``null`` and never omitted**, which is the
matchmaking surface's own distinction applied deliberately rather than by
default: *``null`` means the field applies and the answer is a measured nothing.*
An empty seat has no occupant, a seat nobody has answered has no answer, the
organiser's seat has no deadline, a mutual-born challenge was proposed from no
grid and a challenge that still stands has not ended — five measured nothings,
and not five absences.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.engines.matchfit.core import DegradedReason, SearchMode, Term
from app.kernel import Sport
from app.modules.challenges.domain.ports import PairingAbsence
from app.modules.challenges.domain.seats import SeatAnswer, Side
from app.modules.challenges.domain.standing import Standing
from app.modules.challenges.presentation.evidence import CourtEvidence
from app.modules.player_profile.domain.availability import Window

#: The default that spells **omitted** — *this field does not apply here* — and
#: it is the matcher's sentinel spelled again for the matcher's reason, on the
#: one read in this context that needs it.
#:
#: A field carrying it is not in the schema's ``required`` list, so it generates
#: as ``field?: T``, and the detail route is declared
#: ``response_model_exclude_unset=True`` so it is genuinely absent from the JSON
#: rather than present as ``null``. **``null`` means the field applies and the
#: answer is a measured nothing**, which is itself a recorded fact — and the two
#: must never collapse into one optional-*and*-nullable field, which generates as
#: ``field?: T | null`` and says neither thing.
#:
#: **The list read does not use it and does not want it.** Every nullable field
#: on ``ChallengeSchema`` is ``null`` and never omitted, which is the same
#: distinction applied deliberately in the other direction: an empty seat has no
#: occupant, and that is a measured nothing rather than an absence.
OMITTED: Any = None


class SeatChoiceSchema(BaseModel):
    """One position on the court as the organiser left it.

    **An empty seat is a seat**, so ``player_id`` is genuinely optional: an A-side
    full with a B-side short is a different court from the reverse, and the next
    invitee's side is not a free choice.

    There is no origin field and no position. Where each invitation came from is
    resolved server-side against the cited search, because a position a client
    sent would be true only while the client was honest about where it had
    scrolled to.
    """

    side: Side = Field(..., description="Which side of the net this seat is on")
    player_id: UUID | None = Field(
        default=None,
        description=(
            "Who is to sit here, or omitted for a seat nobody was put in. The "
            "organiser holds one of these like anybody else."
        ),
    )


class SendChallengeRequest(BaseModel):
    """One press. **The court, and the search it was built on.**

    ``search_id`` is the origin, and it is one search for the whole court: the
    arrangement was built and forecast against a single answer, and a court
    assembled out of two searches is a court no forecast was ever computed for.

    **The sport, the kind of evening and the week are not sent.** All three are
    read off that search's own record — there is no window picker anywhere
    (``docs/adr/0100``), and a player changes their window by changing their grid.
    """

    search_id: UUID = Field(
        ...,
        description=(
            "The search this court was built from. **Required** — every invitee "
            "must have appeared in it, and each seat cites where they sat."
        ),
    )
    court: list[SeatChoiceSchema] = Field(
        ...,
        description=(
            "The sides as you arranged them, in the court's own order: every "
            "**A** seat, then every **B**. It must be the sport's shape and you "
            "must be in it."
        ),
    )


class FillSeatsRequest(BaseModel):
    """**The send's shape minus the mint**: the court, and the search behind it.

    The challenge is in the path, so what is left is the two things a fill has to
    say — and the two the send says. Everything else about the game is already on
    the challenge: the sport, the kind of evening, and the **window**, which is
    stamped when a challenge is sent and never again. A challenge born of two
    mutual yeses has no window at all and keeps none.

    ``court`` is the **whole** arrangement and not the seats being filled. An
    acceptance is to the game and not to the side, so the people already in may
    be moved across the net — and may not be taken out. A court that omitted one
    of them is refused.
    """

    search_id: UUID = Field(
        ...,
        description=(
            "The search this fill was built from — **yours, and run just now**. "
            "Everybody being newly asked must have appeared in it, and each new "
            "seat cites where they sat. The people already on the court are not "
            "looked up in it: they came from somewhere else, possibly weeks ago."
        ),
    )
    court: list[SeatChoiceSchema] = Field(
        ...,
        description=(
            "The whole court as it will stand, in the court's own order: every "
            "**A** seat, then every **B**. It must be the sport's shape, you "
            "must be in it, and **everybody already on the court must still be "
            "in it** — they may change sides and they may not lose their place."
        ),
    )


class SentChallengeResponse(BaseModel):
    """What a send answers with. **An id, and deliberately nothing else.**

    Not the challenge: nobody has answered it yet, so every seat says exactly
    what the organiser just sent, and a body repeating their own arrangement back
    at them is a round trip that says nothing. The id is what the client keeps.
    """

    challenge_id: UUID = Field(..., description="The challenge that now stands")


class SeatSchema(BaseModel):
    """One seat: a side, its occupant, their answer and their own deadline.

    ``answer_by`` is **this seat's own**, dated when this seat was invited — a
    seat filled later starts its own day and cannot inherit a deadline from a send
    it was not part of. It is absent exactly when nobody was asked: an empty seat,
    the organiser's, and both seats of a challenge born from a mutual yes.
    """

    side: Side
    player_id: UUID | None = Field(
        default=None,
        description=(
            "Who holds this seat. ``null`` on a seat nobody was put in."
        ),
    )
    answer: SeatAnswer | None = Field(
        default=None,
        description=(
            "What they did about being asked. ``null`` while they have not "
            "answered, and on a seat nobody was put in. **A lapse is not a "
            "refusal** — they are different facts and the platform counts them "
            "apart."
        ),
    )
    answer_by: datetime | None = Field(
        default=None,
        description=(
            "When this seat's answer stops being wanted. Past it the seat reads "
            "as lapsed whether or not anything has swept it, and a late answer "
            "is refused rather than accepted late. ``null`` exactly when nobody "
            "was asked: an empty seat, the organiser's, and both seats of a "
            "challenge born from a mutual yes."
        ),
    )
    nickname: str | None = Field(
        default=None,
        description=(
            "The whole handle, and **nothing may derive a familiar form from "
            "it** — every sentence naming somebody uses all of it or names "
            "nobody (``docs/adr/0107``).\n\n"
            "``null`` on a seat nobody was put in, and ``null`` where ``users`` "
            "no longer has the account. The seat stays either way: a seat with "
            "no handle is still a position on the court, and the screen has a "
            "side to name instead.\n\n"
            "**A handle is the whole of what a challenge borrows about a "
            "person here.** A Level, a band, an area and a photograph are a "
            "card's, and a card is drawn on the detail read alone."
        ),
    )


class ChallengeSchema(BaseModel):
    """One challenge, with its whole court and what it is right now."""

    challenge_id: UUID
    sport: Sport
    mode: SearchMode | None = Field(
        default=None,
        description=(
            "The kind of evening it was sent for. ``null`` when the surface it "
            "came from has none — the deck asks nobody to pick one — and on "
            "every challenge born of a mutual yes."
        ),
    )
    window: Window | None = Field(
        default=None,
        description=(
            "How soon the week this was proposed for comes round. **Derived at "
            "send from the grid the search ran on** and never asked for. "
            "``null`` on a mutual-born challenge: no grid was proposed from."
        ),
    )
    organiser_id: UUID = Field(
        ...,
        description=(
            "Whose proposal this is. Their seat is **accepted from birth** — they "
            "are the one asking."
        ),
    )
    standing: Standing = Field(
        ...,
        description=(
            "What this challenge is at the instant it was read. **Derived from "
            "the seats and the clock, never stored**, so it is right for the "
            "whole gap between a deadline and anything noticing."
        ),
    )
    opened_at: datetime
    ended_at: datetime | None = Field(
        default=None,
        description=(
            "When this challenge ended. ``null`` on the three standings that are "
            "not endings, and that is the whole of what the absence means: "
            "*this challenge has not ended*.\n\n"
            "**It is what a shelf life is subtracted from** — an ended row keeps "
            "its place for a day and then goes, which is `read_at` minus this "
            "and nothing else. **Not `read_at`**, which means the opposite: the "
            "instant every standing and deadline here was folded against.\n\n"
            "**The ending is the last departure, not the ending's own name.** A "
            "refusal outranks silence whatever order the two arrived in, so a "
            "`DECLINED` court may have gone on standing for days after the no — "
            "until the last seat still deciding ran out. This is when that "
            "happened.\n\n"
            "**A departure is dated exactly unless it was a decline**, and that "
            "is the whole of the precision here:\n\n"
            "- **A lapse is exact.** It *is* a deadline passing, so the instant "
            "is on the seat already and no sweep needs to have run.\n"
            "- **A withdrawal is exact.** A decision somebody took, carrying its "
            "own moment.\n"
            "- **A decline is an upper bound**, at or before which that person "
            "left. Nothing records when somebody said no, so it is bounded by "
            "the tighter of the two facts that are recorded: that seat's own "
            "deadline, and the last thing that happened to the challenge.\n\n"
            "So `LAPSED` and `WITHDRAWN` are always exact, and `DECLINED` is "
            "exact whenever the seat that left **last** was one that ran out — "
            "which a mixed court often is — and a bound otherwise. The bound is "
            "late rather than early, which is the safe direction for a shelf "
            "life: a row that outstays it is news gone stale, and one retired "
            "early is somebody never learning a seat reopened."
        ),
    )
    seats: list[SeatSchema] = Field(
        ...,
        description=(
            "The court in its fixed order — every **A** seat, then every **B**. "
            "Empty seats are in the list, because which side is short is part "
            "of what a court is: an A-side full with a B-side short is a "
            "different court from the reverse."
        ),
    )


class ChallengeListResponse(BaseModel):
    """Your challenges, newest first.

    **One list and not two.** *Challenge sent* and *Challenge for you* are one
    standing read from two sides, so nothing here splits them: the client tells
    them apart by whether ``organiser_id`` is yours.

    **Ended challenges are in it, and their standing says so.** A list that
    quietly dropped this morning's lapse would be the same class of lie as a
    read-back that got shorter.

    ``read_at`` is the instant every standing and deadline here was folded
    against. It travels so a client's countdowns and the standings beside them
    cannot come from two different readings of the clock — ``GameListResponse``'s
    field verbatim, for its written reason (``docs/adr/0143`` §7). The detail
    read carries **its own**, because it is its own fold against its own instant.
    """

    read_at: datetime
    challenges: list[ChallengeSchema]


# ---------------------------------------------------------------------------
# The detail read — the card block, and this context's own narrower schema
#
# ``docs/adr/0143`` §5. `PlayerCardSchema` and `ForecastSchema` live in
# ``matchmaking`` and appear nowhere else; there is no shared presentation-schema
# home and that record did not invent one. So these are a second spelling, on
# ``origins.py``'s argument verbatim — ``challenges`` may not import the matcher,
# and the alternative to two spellings is the matcher owning the vocabulary of
# the context that was built to take work off him.
#
# **Two blocks, because they have two different authors.** The person is facts
# about them; the pairing is a reading of the two of them together, computed in
# the reader's own direction and never replayed from the organiser's search.
#
# **What is refused, each for its own reason.** No bio and no free text of any
# kind — the refusal is *stronger* here than where it was written, because a
# searcher chose to look and an invitee was put in front of somebody without
# asking. No ``liveness_reasons``: *why did this person move* is a question about
# a list. No ``inclusion_reason``: *why are they here at all* is the same
# question, and neither exists when somebody asked you directly. No
# ``modifiers`` — engine internals. No counted games, no run of form and no photo
# verdict: card furniture this screen does not draw.
# ---------------------------------------------------------------------------


class CourtLikelyRangeSchema(BaseModel):
    """The **likely range** — μ ± σ, clamped to the scale — as `rating` published it.

    Nested rather than two flat fields, because a range is one value with two
    edges. **The client computes nothing here**: the rounding lives in the
    engine, and a range derived anywhere else is a second set of drawing
    constants.
    """

    low: float
    high: float


class CourtPersonSchema(BaseModel):
    """Who one person on this court is. **A closed list with two permanent gaps.**

    No bio and no free text of any kind, ever; and **no activity recency at any
    granularity** — not a timestamp, not *active today*, not a green dot.

    **``photo_id`` and ``photo_url`` are present exactly together.** An id with
    no link beside it is a photograph nothing can draw; neither means the client
    draws the generated court poster, which chooses by hash and needs nothing
    from the wire (``docs/adr/0134``). Refusing the photograph outright would
    make the person who asked you to play more anonymous than a stranger in your
    deck, which is the wrong way round.
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
        OMITTED,
        description=(
            "Their current photograph. Omitted when they have none, and omitted "
            "together with `photo_url` — the two travel as a pair or not at all."
        ),
    )
    photo_url: str = Field(
        OMITTED,
        description=(
            "A short-lived signed link to that photograph, minted for **this "
            "response**. It expires within minutes and is not a stored value: a "
            "client that keeps one keeps a dead link."
        ),
    )
    area_code: str = Field(..., description="Their coarse area, as a machine code")
    level: float = Field(..., description="Their Level, as RacketSkill published it")
    band: str = Field(..., description="The Level band's published name")
    range: CourtLikelyRangeSchema = Field(
        ..., description="Where their Level most likely sits"
    )
    player_score: int = Field(
        OMITTED,
        description=(
            "Their **published** Player Score, and never a re-derivation of one "
            "(`docs/adr/0140`).\n\n"
            "**Omitted where the platform has watched nothing**, which is most "
            "people today — the segment disappears rather than reading `Score "
            "0`, because a nought printed for somebody nothing was watched of "
            "is a claim where there is a gap."
        ),
    )


class CourtConcernSchema(BaseModel):
    """One term the platform is not comfortable about on this pairing."""

    term: Term


class CourtDegradedTermSchema(BaseModel):
    """One term that stood down, and **whose gap that is**.

    A pair rather than a bare ``Term``, because a flat list holds two different
    sentences as one fact: *reliability is not a thing on this platform yet* and
    *they have not said what kind of evening they want*.

    **It ships even though no *Why?* sheet is drawn over it**, and its own
    contract is the reason: without the renormalisation basis a Fit is
    uninterpretable — a 78 built on four terms and a 78 built on seven are
    different readings of one number. Printing a Fit without it is the exact
    failure this field exists to prevent, and the alternative — printing no Fit —
    throws away the number the screen exists to give.
    """

    term: Term
    reason: DegradedReason = Field(
        ...,
        description=(
            "Whose gap this is: nobody's (`NOT_YET_ON_THIS_PLATFORM` — the term "
            "has no provider on this platform at all), yours "
            "(`NOTHING_FROM_YOU`), or theirs (`NOTHING_FROM_THEM`). The last "
            "deliberately covers every reason a record could not be read, "
            "because separating them would publish activity recency."
        ),
    )


class CourtScoredTermSchema(BaseModel):
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
        ...,
        description=(
            "The weight times the value.\n\n"
            "**The contributions sum to the Fit before the modifiers**, and "
            "`fit` above is the figure after them — the same number every other "
            "surface prints for this pairing. Those are the reliability dock and "
            "its neighbours, engine internals this screen does not draw, so the "
            "breakdown explains the pairing rather than reconstructing the total "
            "to the decimal."
        ),
    )
    evidence: CourtEvidence


class CourtForecastSchema(BaseModel):
    """How even a game against this person is forecast to be.

    ``provisional`` travels **inside** the forecast rather than beside it: the
    failure being guarded against is a screen showing the number without its
    caveat, and a sibling boolean is exactly how the two get separated in a
    refactor.

    **One seat a side, whatever the sport's court seats.** The block is drawn per
    person, and *how would a game against **you** go* is the question somebody
    answering an invitation is asking; a four-way figure would be one answer
    printed once per seat.
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


class CourtAtStakeSchema(BaseModel):
    """What a **counted** game against this person would do to your Level."""

    win_delta: float
    loss_delta: float


class CourtPairingSchema(BaseModel):
    """What this platform makes of you **against** this person.

    **Recomputed when the screen is opened, in your own direction** — never
    copied at send and never replayed from the organiser's search
    (``docs/adr/0143`` §3). That is the only shape under which *Match score for
    you* is true: neither stored Fit is publishable, because one is the
    organiser's reading of the invitee and the other was scored with the
    searcher's own reliability deliberately set to null.
    """

    fit: float = Field(
        ...,
        description=(
            "The Fit, in your own direction. **The only number here you are "
            "asked to trust**, and it contains no Liveness offset."
        ),
    )
    distance_km: int = Field(
        OMITTED,
        description=(
            "Whole kilometres between your two areas. **Omitted and never zero** "
            "when the distance term stood down: somebody whose distance could "
            "not be read is not next door."
        ),
    )
    terms: list[CourtScoredTermSchema] = Field(
        ...,
        description=(
            "Every term that fired, **ranked by contribution**, each with the "
            "evidence behind it. The contributions sum to the Fit **before the "
            "modifiers** — see `contribution`, which is where that gap is "
            "explained rather than being two sentences that disagree."
        ),
    )
    degraded_terms: list[CourtDegradedTermSchema] = Field(
        ...,
        description=(
            "Every term that stood down, and whose gap each one is. **The Fit's "
            "renormalisation basis**, without which the number above cannot be "
            "read."
        ),
    )
    concerns: list[CourtConcernSchema] = Field(
        ...,
        description="Terms the platform is not comfortable about on this pairing.",
    )
    forecast: CourtForecastSchema = Field(
        OMITTED,
        description=(
            "What the court **as it stands** would leave on court, read in your "
            "direction — everybody still in, placed where they actually sit.\n\n"
            "**The same figure rides on every card**, because a forecast is a "
            "fact about the game rather than about one person. A seat still open "
            "reads as if whoever fills it matched the player already on that "
            "side, which is what `provisional` says.\n\n"
            "**Omitted where no game can be arranged out of what is left.** A "
            "side with nobody on it is not a side, so a court whose far side has "
            "all declined leaves nothing to forecast against — and an invented "
            "number would be worse than the absence."
        ),
    )
    at_stake: CourtAtStakeSchema = Field(
        OMITTED,
        description=(
            "What a counted game against this person would do to your Level — "
            "the rating engine's own update rule read forward.\n\n"
            "**Omitted in for fun**, where a counted result is meaningless "
            "rather than unavailable, and **omitted when either of you holds no "
            "rating in this sport** — never drawn as a pair of zeros."
        ),
    )


class SeatCardSchema(BaseModel):
    """The card for one seat: who they are, and what you make of them."""

    person: CourtPersonSchema
    pairing: CourtPairingSchema


class DetailSeatSchema(SeatSchema):
    """One seat on the detail read — the list's seat, and a card where one is drawn.

    **The card is per seat as well as per challenge** (``docs/adr/0143`` §8).
    Somebody who declined or lapsed inside a still-open court gets none: the pair
    releases the moment a seat leaves, and *that person is a stranger to you once
    more.* Their seat stays and keeps its handle, because the standing sentences
    name them.

    **Your own seat never carries one either.** A pairing with yourself is not a
    question.
    """

    card: SeatCardSchema = Field(
        OMITTED,
        description=(
            "Who this person is and what you make of them, drawn only while the "
            "arrangement is still being decided and only for somebody still in "
            "it. Omitted on your own seat, on an empty one, on a seat that "
            "declined or lapsed, and on every seat when `pairing_absence` says "
            "there is no pairing to draw."
        ),
    )


class ChallengeDetailResponse(BaseModel):
    """One challenge, richly — the arrangement, the people and the pairing.

    **Its own ``read_at``**, because it is its own fold against its own instant:
    the standing, every seat's deadline and which seats are still in were all
    read against this one moment.

    **The card block is drawn while the arrangement is being decided and at no
    other time** (``docs/adr/0143`` §8) — one rule stated on the two standings
    that draw one, so a standing added later is silent by default. `DECLINED` and
    `LAPSED` draw the arrangement and the handles alone; `ON` draws neither,
    because the game's own screen owns it the moment a game exists.

    **Nothing here is re-gated against who is reading** (§2). The four
    fail-closed gates ran over every pair of this court when it was minted, and a
    card that vanished from behind two buttons that still work would be the one
    disclosure a safety gate may never make.
    """

    read_at: datetime = Field(
        ...,
        description=(
            "The instant this whole answer was folded against — the standing, "
            "every deadline on it, and which seats are still in."
        ),
    )
    challenge_id: UUID
    sport: Sport
    mode: SearchMode | None = Field(
        default=None,
        description=(
            "The kind of evening it was sent for. ``null`` when the surface it "
            "came from has none, and on every challenge born of a mutual yes."
        ),
    )
    window: Window | None = Field(
        default=None,
        description=(
            "How soon the week this was proposed for comes round. ``null`` on a "
            "mutual-born challenge: no grid was proposed from."
        ),
    )
    organiser_id: UUID = Field(
        ...,
        description=(
            "Whose proposal this is. Their seat is **accepted from birth** — "
            "they are the one asking."
        ),
    )
    standing: Standing = Field(
        ...,
        description=(
            "What this challenge is at ``read_at``. **Derived from the seats and "
            "the clock, never stored.**"
        ),
    )
    opened_at: datetime
    seats: list[DetailSeatSchema] = Field(
        ...,
        description=(
            "The court in its fixed order — every **A** seat, then every **B**. "
            "Empty seats are in the list, because which side is short is part "
            "of what a court is."
        ),
    )
    pairing_absence: PairingAbsence = Field(
        OMITTED,
        description=(
            "Why no seat carries a card, when the arrangement is still being "
            "decided and none was drawn. **Omitted when there is no absence to "
            "report** — either the cards are on the seats, or this standing "
            "draws no card block at all and the standing already says so.\n\n"
            "`NOTHING_TO_COMPUTE` — you hold no rating, have declared no Play "
            "intent, or have committed no player profile in the sport you were "
            "challenged in. Being asked to play a sport you never declared for "
            "is how this works rather than a corner of it, and the screen does "
            "not apologise for it.\n\n"
            "`COULD_NOT_BE_READ` — somebody else's outage. **Three answers and "
            "not two**, because an outage drawing the identical absence as an "
            "unrated sport is indistinguishable from four erased accounts.\n\n"
            "**Answering is never gated on any of this.** The arrangement "
            "always answers and the buttons are drawn from the standing, so a "
            "matchmaking outage never becomes *you cannot answer your "
            "challenge*."
        ),
    )
