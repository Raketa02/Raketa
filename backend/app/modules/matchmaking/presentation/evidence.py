"""The evidence vocabulary — a closed, discriminated union keyed by ``kind``.

**A number is ruleset; a shape is the API contract** (``docs/adr/0106``). Moving
a weight is free — no contract change, no client work, no regeneration. Adding,
removing or reshaping a variant below is an **API release**, because the client
generates an exhaustive type and a renderer per variant and must never be handed
a shape it cannot draw. That is the friction we want, in the place we want it: a
weight is a hypothesis about ranking and should be cheap to move, an evidence
shape is a promise about what the product can explain.

**Why it is closed rather than an open blob.** An open ``terms`` object generates
into TypeScript as ``Record<string, unknown>``, and the client then hand-writes
the evidence types after all — which is exactly the failure ``docs/adr/0006``
exists to prevent, arriving through a hole in the schema rather than because
anybody broke the rule. And the failure is **silent**: an evidence kind the
client does not know renders as nothing at all, on the one screen whose entire
promise is that it shows its working, where a missing reason line looks identical
to a term that stood down.

**Storage stays open and the two are allowed to differ.** The stored
``search_candidate.terms`` blob must still deserialise in five years under a
ruleset nobody runs any more; the wire type must be exhaustive *today*, for the
ruleset that is live. Openness is the right property for the first and the wrong
one for the second. One check stands between them: **every evidence kind the
loaded ruleset can emit is present in this union**, and a ruleset that can
produce a kind this file does not publish refuses to load
(``app/bootstrap/matchmaking.py``).

**No display strings, anywhere.** The backend emits machine codes and never
display text (``docs/adr/0022``): the client writes *"4 shared hours · next
Tuesday 19:00"* over ``{"kind": "availability_overlap", "shared_count": 4,
"next_slot": {…}}``, in its own copy and its own language. Sports, tags and
intents cross as the platform's **existing** machine codes — a second
spelling of a closed vocabulary is how two systems begin disagreeing about the
same word.

**No Liveness number, ever.** A candidate carries ``fit`` and a list of liveness
reason *codes*, and there is no field on any variant here a Liveness offset could
be written to. The printed Fit is the only number a player is asked to trust, and
the moment it silently contains *"they open the app a lot"* it stops meaning what
it says.

**An unknown kind is a named gap, never silence.** A deployed build can be months
older than the backend, so *"the client regenerates"* is true of the repository
and false of the phone in somebody's hand. A card drops a reason it cannot render
— it shows three of eight anyway — and the breakdown renders a **named gap**
saying this app is out of date. A term quietly vanishing from a breakdown is the
same class of lie as a recomputed score, and worse for being invisible.

## Absence has two spellings, and they are not interchangeable

- **Omitted** — *this field does not apply here.* It generates as ``field?: T``
  and the client branches on its presence.
- **``null``** — *this field applies, and the answer is a measured nothing that
  is itself a recorded fact.* It generates as ``field: T | null``.

``shared_count: 0`` with ``next_slot: null`` is the second: both grids were read
and there is no next shared slot, which is not the claim *we did not look*. The
first spelling's first users are candidate-level fields that land with the routes
— ``at_stake`` in a for-fun search is *meaningless* rather than unavailable, and
``rung_offers: null`` means the offers were not computed at all because the
shortlist cleared its minimum.

The two must never collapse into one optional-*and*-nullable field, which
generates as ``field?: T | null`` and says neither thing.
``tests/unit/test_matchmaking_evidence_vocabulary.py`` refuses one.
"""

from __future__ import annotations

from typing import Annotated, Literal, Union

from pydantic import BaseModel, Field

from app.engines.matchfit.core import (
    EvidenceKind,
    LevelDirection,
    ReliabilityStrand,
    SearchMode,
)
from app.modules.player_profile.domain.play_intent import PlayIntent
from app.modules.player_profile.domain.weekly_hours import (
    DAYS_IN_THE_GRID,
    FIRST_HOUR,
    LAST_HOUR,
)


class SharedSlot(BaseModel):
    """The next hour of the week both players ticked.

    **The grid is never rendered to anybody as a calendar.** Only the count of
    shared hours and the name of the next shared one are ever shown, because
    overlap is a fact about a pair where a calendar is a fact about a person.
    """

    day: int = Field(
        ...,
        ge=1,
        le=DAYS_IN_THE_GRID,
        description="ISO weekday — 1 is Monday, 7 is Sunday. The grid is Monday-first.",
    )
    hour: int = Field(
        ...,
        ge=FIRST_HOUR,
        le=LAST_HOUR,
        description="The hour that cell starts at, wall clock — 19 is 19:00 to 20:00",
    )


class TagPair(BaseModel):
    """Two tag ids one relationship row fired on.

    Ids only. The row's kind is the field it sits under, its column is the term
    it sits under, and its strength or severity is a ruleset number the player is
    not shown — what is owed here is *which two things about you two this reads*.
    """

    a: str = Field(..., description="A Social tag id")
    b: str = Field(..., description="The other Social tag id")


class StrandReading(BaseModel):
    """One reliability strand that produced a reading.

    A strand with too few observations **stands down and is absent from the
    list** rather than present at zero: *we have not seen enough* and *they are
    bad at this* are different facts, and a term may never be honestly neutral.
    """

    strand: ReliabilityStrand = Field(..., description="Which of the six")
    value: float = Field(..., ge=0, le=1, description="The strand's own reading")


class LevelFitEvidence(BaseModel):
    """How far apart the two levels are, and which way.

    The tolerance behind the curve is absolute on μ and never reads a band: the
    shipped bands are deliberately uneven because *evidence* is unevenly
    available down the scale, not because a tenth of a point means less at the
    top.
    """

    kind: Literal[EvidenceKind.LEVEL_FIT] = EvidenceKind.LEVEL_FIT
    my_mu: float = Field(..., description="The searcher's Level")
    their_mu: float = Field(..., description="The candidate's Level")
    delta: float = Field(..., ge=0, description="The gap, unsigned")
    direction: LevelDirection = Field(..., description="Which side of the searcher")


class PredictedBalanceEvidence(BaseModel):
    """How even the game is forecast to be, and how sure of that the platform is.

    ``pct`` is the forecast the player is shown; ``confidence`` is the platform's
    existing σ transform and never a second spelling of certainty.
    """

    kind: Literal[EvidenceKind.PREDICTED_BALANCE] = EvidenceKind.PREDICTED_BALANCE
    pct: int = Field(..., ge=0, le=100, description="The evenness forecast")
    my_sigma: float = Field(..., ge=0, description="The searcher's Uncertainty")
    their_sigma: float = Field(..., ge=0, description="The candidate's Uncertainty")
    confidence: int = Field(
        ...,
        ge=0,
        le=99,
        description=(
            "The platform's confidence transform over the combined σ, as a whole "
            "percent. Never 100: the platform cannot tell a player it is certain."
        ),
    )


class IntentAlignmentEvidence(BaseModel):
    """What kind of evening each of them is after.

    **Intent is a weight and not a gate.** A candidate who declared the opposite
    loses the term's entire weight and takes no further charge — the zero is the
    whole answer, and a second dock would be a gate wearing a modifier's clothes.
    A candidate who has *not* declared has the term dropped and renormalised away
    instead, so declaring against the searcher already costs strictly more than
    saying nothing.
    """

    kind: Literal[EvidenceKind.INTENT_ALIGNMENT] = EvidenceKind.INTENT_ALIGNMENT
    my_mode: SearchMode = Field(..., description="The searcher's mode, this search")
    their_intent: PlayIntent = Field(
        ..., description="The candidate's declaration for this sport"
    )
    aligned: bool = Field(..., description="Whether the two read the same evening")


class ReliabilityEvidence(BaseModel):
    """What the candidate's record says about turning up and following through.

    ``score`` is the **published Player Score** — the number on the player's own
    profile — and never the matcher's private per-mode blend of the same six
    strands. A penalty justified by a figure that exists nowhere a human can look
    is unexplainable, and a player who works their visible score back up must be
    able to see the penalty lift.
    """

    kind: Literal[EvidenceKind.RELIABILITY] = EvidenceKind.RELIABILITY
    score: int = Field(..., ge=0, le=100, description="The published Player Score")
    #: **Required, and empty is a measurement.** The six strands were read and
    #: this is what came back; a strand below the observation bar is absent from
    #: the list rather than present at zero, because *we have not seen enough*
    #: and *they are bad at this* are different facts. Made optional it would
    #: generate as ``strands?: T[]`` and say *this does not apply*, which is
    #: never true of a reliability reading that exists at all.
    strands: tuple[StrandReading, ...] = Field(
        ..., description="The strands that produced a reading, over the closed six"
    )
    floor_breached: bool = Field(
        ..., description="Whether the published score sits under the reliability bar"
    )


class AvailabilityOverlapEvidence(BaseModel):
    """How much of the searcher's week the candidate is free in.

    The term is ``|shared| / |mine|`` and has **no constants at all** — the
    denominator is the searcher's own ticked cells, which is what makes the
    reading asymmetric and what makes it a fact about the pair.

    Overlap is evidence a game can be *arranged*, never a proposed time, which is
    why a candidate sharing no slot at all is still shown: the times rung exists
    for exactly that pairing.
    """

    kind: Literal[EvidenceKind.AVAILABILITY_OVERLAP] = EvidenceKind.AVAILABILITY_OVERLAP
    shared_count: int = Field(
        ..., ge=0, description="Hours of the week both of them ticked"
    )
    #: **A measured nothing, and required-nullable for it.** ``null`` says both
    #: grids were read and there is no next shared slot — the answer a searcher
    #: with an empty intersection is owed. Omitting it instead would say *this
    #: does not apply*, which is a different and untrue claim.
    next_slot: SharedSlot | None = Field(
        ..., description="The soonest hour both ticked, or null when there is none"
    )


class PlayingStyleEvidence(BaseModel):
    """What the two of them are like during the hour on court.

    The split from social vibe is **by relationship, not by tag group**: every
    matrix row carries its own column, so a tag can be read for the hour on court
    in one row and for the evening around it in another.

    A pair with nothing firing is *different, not incompatible* — the term's zero
    is a real clash, never an absence of relationship.
    """

    kind: Literal[EvidenceKind.PLAYING_STYLE] = EvidenceKind.PLAYING_STYLE
    #: **All three are required, and all three may be empty.** An empty set here
    #: is the term's own *measured* zero — both sides hold tags in this column
    #: and nothing fired, which is *different, not incompatible*. The column that
    #: genuinely *does not apply* stands down, and then this whole variant is
    #: absent rather than present and empty.
    matched: tuple[str, ...] = Field(
        ..., description="Tag ids they both hold, in this column"
    )
    complementary: tuple[TagPair, ...] = Field(
        ..., description="Pairs product claims fit together"
    )
    clashing: tuple[TagPair, ...] = Field(
        ..., description="Pairs product claims do not"
    )


class SocialVibeEvidence(BaseModel):
    """What the two of them are like around the game.

    The same shape as playing style and deliberately a **separate variant**: the
    two terms carry different weights, invert between the modes, and a client
    renders them under different headings. One variant with a column field would
    make *which term is this* a value the client has to branch on rather than a
    type it can dispatch over.
    """

    kind: Literal[EvidenceKind.SOCIAL_VIBE] = EvidenceKind.SOCIAL_VIBE
    #: **All three are required, and all three may be empty.** An empty set here
    #: is the term's own *measured* zero — both sides hold tags in this column
    #: and nothing fired, which is *different, not incompatible*. The column that
    #: genuinely *does not apply* stands down, and then this whole variant is
    #: absent rather than present and empty.
    matched: tuple[str, ...] = Field(
        ..., description="Tag ids they both hold, in this column"
    )
    complementary: tuple[TagPair, ...] = Field(
        ..., description="Pairs product claims fit together"
    )
    clashing: tuple[TagPair, ...] = Field(
        ..., description="Pairs product claims do not"
    )


class DistanceEvidence(BaseModel):
    """How far away they are, and whether the searcher is outside *their* ring.

    A candidate's own radius is a Liveness dock and **never a gate**: somebody
    who set a small radius is not refusing to be found, and the searcher is
    shown the fact rather than having the person removed. The standalone flat
    dock for it is struck — the reciprocal reading already prices it, and
    proportionately.
    """

    kind: Literal[EvidenceKind.DISTANCE] = EvidenceKind.DISTANCE
    km: int = Field(..., ge=0, description="Whole kilometres between the two areas")
    area_code: str = Field(
        ..., description="The candidate's coarse area, as a machine code"
    )
    outside_their_radius: bool = Field(
        ..., description="Whether the searcher sits outside the candidate's own ring"
    )


#: The union itself. ``kind`` is the discriminator, so a client generates one
#: exhaustive type and a renderer per variant, and a variant it has never seen is
#: a compile-time error in the repository rather than a blank line in production.
Evidence = Annotated[
    Union[
        LevelFitEvidence,
        PredictedBalanceEvidence,
        IntentAlignmentEvidence,
        ReliabilityEvidence,
        AvailabilityOverlapEvidence,
        PlayingStyleEvidence,
        SocialVibeEvidence,
        DistanceEvidence,
    ],
    Field(discriminator="kind"),
]

#: Every variant, in the order the union declares them. The one place the union's
#: membership is enumerated for code to read — a second list would be a second
#: answer to *what can cross*.
EVIDENCE_VARIANTS: tuple[type[BaseModel], ...] = (
    LevelFitEvidence,
    PredictedBalanceEvidence,
    IntentAlignmentEvidence,
    ReliabilityEvidence,
    AvailabilityOverlapEvidence,
    PlayingStyleEvidence,
    SocialVibeEvidence,
    DistanceEvidence,
)

#: The kinds this contract publishes. **A ruleset that can emit a kind absent
#: from here refuses to load**, because the client cannot draw what it has never
#: been given a shape for.
WIRE_EVIDENCE_KINDS: frozenset[EvidenceKind] = frozenset(
    variant.model_fields["kind"].default for variant in EVIDENCE_VARIANTS
)
