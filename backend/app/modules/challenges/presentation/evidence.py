"""The evidence vocabulary again — **a second spelling, and it is the decision.**

``challenges`` may not import the matcher (the arrow runs ``matchmaking ->
challenges`` and never back), and ``docs/adr/0143`` §5 records that there is no
shared presentation-schema home and does not invent one. So the detail read's
scored terms carry their evidence in this context's own copy of the union, on
``origins.py``'s argument verbatim: *the alternative to two spellings is the
matcher owning the vocabulary of the context that was built to take work off him.*

**Every class here is prefixed ``Court``, and that is about the contract rather
than about taste.** Two Pydantic models of the same name in one OpenAPI document
are disambiguated by their module path, so the client would generate
``app__modules__challenges__presentation__evidence__LevelFitEvidence`` and a
reader would meet the repository's directory layout in their own type names. The
prefix is what ``docs/adr/0143``'s *the client generates two types for what a
designer sees as one component* looks like when it is spelled deliberately. **The
payload is identical either way** — ``kind`` carries the same ``EvidenceKind``
values, so one renderer can draw both.

**The two may not drift, and a test is what says so.**
``tests/unit/test_challenge_card_is_a_second_spelling.py`` compares the two unions
variant by variant — the kinds, the field names and the JSON schema each
generates — and goes red the day one grows a field the other does not. A test
rather than an import, because the import is the thing the fence forbids; it is
the same guard ``games_match_history.py`` puts on its own duplicated constant,
one kind of duplication over.

Everything below is the matcher's file, and every rule in its own docstring holds
here unchanged: the union is **closed and discriminated on ``kind``**, so a client
generates one exhaustive type and a renderer per variant; a **number is ruleset
and a shape is the API contract**, so moving a weight is free and reshaping a
variant is a release; there are **no display strings anywhere**, because the
backend emits machine codes and the client writes the sentence; and **absence has
two spellings** — omitted is *this does not apply*, ``null`` is *this applies and
the answer is a measured nothing*.

One rule is **stronger** here than where it was written. A searcher chose to look
at a stranger; an invitee was put in front of one without asking. Nothing in this
file carries free text, and nothing in it ever will.
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
from app.modules.player_profile.domain.availability import DAYS_IN_THE_GRID, DayPart
from app.modules.player_profile.domain.play_intent import PlayIntent


class CourtSharedSlot(BaseModel):
    """The next cell of the week both players ticked.

    **The grid is never rendered to anybody as a calendar.** Only the count of
    shared slots and the name of the next shared one are ever shown, because
    overlap is a fact about a pair where a calendar is a fact about a person.
    """

    day: int = Field(
        ...,
        ge=1,
        le=DAYS_IN_THE_GRID,
        description="ISO weekday — 1 is Monday, 7 is Sunday. The grid is Monday-first.",
    )
    part: DayPart = Field(..., description="Which part of that day")


class CourtTagPair(BaseModel):
    """Two tag ids one relationship row fired on.

    Ids only. The row's kind is the field it sits under, its column is the term
    it sits under, and its strength or severity is a ruleset number the player is
    not shown — what is owed here is *which two things about you two this reads*.
    """

    a: str = Field(..., description="A Social tag id")
    b: str = Field(..., description="The other Social tag id")


class CourtStrandReading(BaseModel):
    """One reliability strand that produced a reading.

    A strand with too few observations **stands down and is absent from the
    list** rather than present at zero: *we have not seen enough* and *they are
    bad at this* are different facts, and a term may never be honestly neutral.
    """

    strand: ReliabilityStrand = Field(..., description="Which of the six")
    value: float = Field(..., ge=0, le=1, description="The strand's own reading")


class CourtLevelFitEvidence(BaseModel):
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


class CourtPredictedBalanceEvidence(BaseModel):
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


class CourtIntentAlignmentEvidence(BaseModel):
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


class CourtReliabilityEvidence(BaseModel):
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
    strands: tuple[CourtStrandReading, ...] = Field(
        ..., description="The strands that produced a reading, over the closed six"
    )
    floor_breached: bool = Field(
        ..., description="Whether the published score sits under the reliability bar"
    )


class CourtAvailabilityOverlapEvidence(BaseModel):
    """How much of the searcher's week the candidate is free in.

    The term is ``|shared| / |mine|`` and has **no constants at all** — the
    denominator is the searcher's own ticked cells, which is what makes the
    reading asymmetric and what makes it a fact about the pair.

    Overlap is evidence a game can be *arranged*, never a proposed time, which is
    why a candidate sharing no slot at all is still shown: the times rung exists
    for exactly that pairing.
    """

    kind: Literal[EvidenceKind.AVAILABILITY_OVERLAP] = EvidenceKind.AVAILABILITY_OVERLAP
    shared_count: int = Field(..., ge=0, description="Cells both of them ticked")
    #: **A measured nothing, and required-nullable for it.** ``null`` says both
    #: grids were read and there is no next shared slot — the answer a searcher
    #: with an empty intersection is owed. Omitting it instead would say *this
    #: does not apply*, which is a different and untrue claim.
    next_slot: CourtSharedSlot | None = Field(
        ..., description="The soonest cell both ticked, or null when there is none"
    )


class CourtPlayingStyleEvidence(BaseModel):
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
    complementary: tuple[CourtTagPair, ...] = Field(
        ..., description="Pairs product claims fit together"
    )
    clashing: tuple[CourtTagPair, ...] = Field(
        ..., description="Pairs product claims do not"
    )


class CourtSocialVibeEvidence(BaseModel):
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
    complementary: tuple[CourtTagPair, ...] = Field(
        ..., description="Pairs product claims fit together"
    )
    clashing: tuple[CourtTagPair, ...] = Field(
        ..., description="Pairs product claims do not"
    )


class CourtDistanceEvidence(BaseModel):
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
CourtEvidence = Annotated[
    Union[
        CourtLevelFitEvidence,
        CourtPredictedBalanceEvidence,
        CourtIntentAlignmentEvidence,
        CourtReliabilityEvidence,
        CourtAvailabilityOverlapEvidence,
        CourtPlayingStyleEvidence,
        CourtSocialVibeEvidence,
        CourtDistanceEvidence,
    ],
    Field(discriminator="kind"),
]

#: Every variant, in the order the union declares them. The one place the union's
#: membership is enumerated for code to read — a second list would be a second
#: answer to *what can cross*.
COURT_EVIDENCE_VARIANTS: tuple[type[BaseModel], ...] = (
    CourtLevelFitEvidence,
    CourtPredictedBalanceEvidence,
    CourtIntentAlignmentEvidence,
    CourtReliabilityEvidence,
    CourtAvailabilityOverlapEvidence,
    CourtPlayingStyleEvidence,
    CourtSocialVibeEvidence,
    CourtDistanceEvidence,
)

#: The kinds this contract publishes. **A ruleset that can emit a kind absent
#: from here refuses to load**, because the client cannot draw what it has never
#: been given a shape for.
COURT_EVIDENCE_KINDS: frozenset[EvidenceKind] = frozenset(
    variant.model_fields["kind"].default for variant in COURT_EVIDENCE_VARIANTS
)
