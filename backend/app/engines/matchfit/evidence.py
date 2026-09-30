"""What each term hands back beside its number — the closed union, engine-side.

**A number is ruleset; a shape is the API contract** (``docs/adr/0106``). The
shapes below are the engine's own spelling of that contract: pure dataclasses
with no framework in them, one variant per ``EvidenceKind``, each keyed by the
kind it crosses under. ``app/modules/matchmaking/presentation/evidence.py`` is
the same union as a schema, and the two are held together by ``EvidenceKind`` —
one enum, in ``core``, that neither side may add to alone.

**Why two spellings at all.** An engine may not import Pydantic, and the schema
has to validate what arrives from a client as well as describe what leaves. The
engine's half computes; the module's half publishes. What must never differ is
the *set of kinds*, and that is a single enum rather than a convention:
``tests/unit/test_matchfit_evidence.py`` asserts this union is exhaustive over
it, and ``app/bootstrap/matchmaking.py`` asserts the wire union is too.

**An unknown kind is a named gap, never silence.** Every variant here carries its
``kind`` as a class attribute rather than as a value somebody passes in, so there
is no way to construct evidence under a kind that is not one of the eight — and
no term may emit a kind other than its own, which is ``Term.evidence_kind`` and
is checked per reading. A breakdown that quietly stops adding up is the same
class of lie as a recomputed score, and worse for being invisible.

**No display strings, anywhere.** The backend emits machine codes and never
display text (``docs/adr/0022``): the client writes *"4 shared slots · next
Tuesday evening"* over the count and the cell, in its own copy and its own
language. Tag ids, day parts, areas and intents cross as the platform's
**existing** machine codes.

**No Liveness number, ever.** There is no field on any variant here an offset
could be written to. The printed Fit is the only number a player is asked to
trust, and it stops meaning what it says the moment it silently contains *"they
open the app a lot"*.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, final, get_args

from app.engines.matchfit.core import (
    EvidenceKind,
    LevelDirection,
    ReliabilityStrand,
    SearchMode,
)


@final
@dataclass(frozen=True, slots=True)
class SharedSlot:
    """The next hour of the week both players ticked — a day, and the hour its
    cell starts at.

    **The grid is never rendered to anybody as a calendar.** Only the count of
    shared hours and the name of the next shared one are ever shown, because
    overlap is a fact about a pair where a calendar is a fact about a person.

    ``days_away`` is deliberately **not** here: it is derivable from the cell,
    and a reason line never restates a value the card already renders. It is
    recorded in the store, where it is the input to its own falsifier.
    """

    day: int
    hour: int


@final
@dataclass(frozen=True, slots=True)
class TagPair:
    """Two tag ids one relationship row fired on.

    Ids only. The row's kind is the field it sits under, its column is the term
    it sits under, and its strength or severity is a ruleset number the player is
    not shown — what is owed here is *which two things about you two this reads*.
    """

    a: str
    b: str


@final
@dataclass(frozen=True, slots=True)
class StrandReading:
    """One reliability strand that produced a reading.

    A strand below the observation bar **stands down and is absent from the
    list** rather than present at zero: *we have not seen enough* and *they are
    bad at this* are different facts, and a term may never be honestly neutral.
    """

    strand: ReliabilityStrand
    value: float


@final
@dataclass(frozen=True, slots=True)
class LevelFitEvidence:
    """How far apart the two Levels are, and which way."""

    kind: ClassVar[EvidenceKind] = EvidenceKind.LEVEL_FIT

    my_mu: float
    their_mu: float
    delta: float
    direction: LevelDirection


@final
@dataclass(frozen=True, slots=True)
class PredictedBalanceEvidence:
    """How even the game is forecast to be, and how sure of that the platform is.

    ``pct`` is the forecast the player is shown, as a whole percent. The term's
    own value is normalised across the clamp bounds — **the bounds are the term's
    zero and one, not cosmetics** — and that normalisation is not printed,
    because the sentence the card writes is *"an even game"* and not *"0.81"*.
    """

    kind: ClassVar[EvidenceKind] = EvidenceKind.PREDICTED_BALANCE

    pct: int
    my_sigma: float
    their_sigma: float
    confidence: int


@final
@dataclass(frozen=True, slots=True)
class IntentAlignmentEvidence:
    """What kind of evening each of them is after.

    **Intent is a weight and not a gate.** A candidate who declared the opposite
    loses the term's entire weight and takes no further charge — the zero is the
    whole answer, and a second dock would be a gate wearing a modifier's clothes.
    A candidate who has *not* declared has the term dropped and renormalised away
    instead, so declaring against the searcher already costs strictly more than
    saying nothing.
    """

    kind: ClassVar[EvidenceKind] = EvidenceKind.INTENT_ALIGNMENT

    my_mode: SearchMode
    their_intent: str
    aligned: bool


@final
@dataclass(frozen=True, slots=True)
class ReliabilityEvidence:
    """What the candidate's record says about turning up and following through.

    ``score`` is the **published Player Score** — the number on the player's own
    profile — and never the matcher's private per-mode blend of the same six
    strands. A penalty justified by a figure that exists nowhere a human can look
    is unexplainable, and a player who works their visible score back up must be
    able to see the penalty lift.
    """

    kind: ClassVar[EvidenceKind] = EvidenceKind.RELIABILITY

    score: int
    #: The strands that produced a reading, over the closed six, in the six's own
    #: declaration order. **Empty is impossible** — a term with no surviving
    #: strand stands down rather than reporting nothing.
    strands: tuple[StrandReading, ...]
    floor_breached: bool


@final
@dataclass(frozen=True, slots=True)
class AvailabilityOverlapEvidence:
    """How much of the searcher's week the candidate is free in.

    The term is ``|shared| / |mine|`` and has **no constants at all**. Overlap is
    evidence a game can be *arranged*, never a proposed time, which is why a
    candidate sharing no slot at all is still shown: the times rung exists for
    exactly that pairing.
    """

    kind: ClassVar[EvidenceKind] = EvidenceKind.AVAILABILITY_OVERLAP

    shared_count: int
    #: ``None`` is **a measured nothing**: both grids were read and there is no
    #: next shared slot. It is not *we did not look* — that case stands the term
    #: down and this evidence does not exist at all.
    next_slot: SharedSlot | None


@final
@dataclass(frozen=True, slots=True)
class PlayingStyleEvidence:
    """What the two of them are like during the hour on court.

    The split from social vibe is **by relationship, not by tag group**: every
    matrix row carries its own column, so a tag can be read for the hour on court
    in one row and for the evening around it in another.

    **All three lists may be empty, and empty is the term's own measured zero** —
    both sides hold tags in this column and nothing fired, which is *different,
    not incompatible*. The column that genuinely does not apply stands the term
    down, and then this evidence is absent rather than present and empty.
    """

    kind: ClassVar[EvidenceKind] = EvidenceKind.PLAYING_STYLE

    matched: tuple[str, ...]
    complementary: tuple[TagPair, ...]
    clashing: tuple[TagPair, ...]


@final
@dataclass(frozen=True, slots=True)
class SocialVibeEvidence:
    """What the two of them are like around the game.

    The same shape as playing style and deliberately a **separate variant**: the
    two terms carry different weights, invert between the modes, and a client
    renders them under different headings. One variant with a column field would
    make *which term is this* a value the client has to branch on rather than a
    type it can dispatch over.
    """

    kind: ClassVar[EvidenceKind] = EvidenceKind.SOCIAL_VIBE

    matched: tuple[str, ...]
    complementary: tuple[TagPair, ...]
    clashing: tuple[TagPair, ...]


@final
@dataclass(frozen=True, slots=True)
class DistanceEvidence:
    """How far away they are, and whether the searcher is outside *their* ring.

    ``outside_their_radius`` is printed and **never scored**: a candidate's own
    radius is a Liveness dock, because somebody who set a small ring is not
    refusing to be found. Judged case 6 asserts the identity — the same pairing
    with the candidate's radius at 1 km scores exactly what it scores at 10.
    """

    kind: ClassVar[EvidenceKind] = EvidenceKind.DISTANCE

    km: int
    area_code: str
    outside_their_radius: bool


#: The union itself. ``kind`` is the discriminator, and it is a class attribute
#: on every variant, so *what kind is this* is a property of the type rather than
#: a string a caller passes.
Evidence = (
    LevelFitEvidence
    | PredictedBalanceEvidence
    | IntentAlignmentEvidence
    | ReliabilityEvidence
    | AvailabilityOverlapEvidence
    | PlayingStyleEvidence
    | SocialVibeEvidence
    | DistanceEvidence
)

#: Every variant, in the order the union declares them — **read off the union
#: itself**, because a second list would be a second answer to *what can a term
#: hand back*, and the two would agree right up until somebody added a variant to
#: one of them.
EVIDENCE_VARIANTS: tuple[type[Evidence], ...] = get_args(Evidence)
