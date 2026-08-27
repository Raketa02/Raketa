"""The Match Fit vocabulary — everything that outlives a version and a ruleset.

``racketskill/core`` holds the scale, the bands and the σ rule for the same
reason this module exists: a name two rulesets disagree about is a name that has
stopped meaning anything. A ruleset *names* these; a version *computes* with
them; neither may add one.

**Tag ids are not here, deliberately.** The nineteen Social tag ids are the
platform's own closed vocabulary, owned by
``app/modules/player_profile/domain/social_tags.py`` and served to the clients —
and an engine may not import a module. So a relationship row carries the tag id
as the **machine code string it already is**, and the check that those strings
are real tags happens where both vocabularies are visible, in the composition
root (``app/bootstrap/matchmaking.py``). A second ``SocialTag`` enum in here
would be a second spelling of a closed vocabulary, which is how two halves of
one system begin disagreeing about the same word.
"""

from __future__ import annotations

from enum import Enum


class SearchMode(str, Enum):
    """What kind of evening this search is for. **Two values, never three.**

    ``PlayIntent`` is the *candidate's* declaration and has three values;
    ``SearchMode`` is the *searcher's* setting — which tab they are on, right
    now — and has two. ``app/modules/player_profile/domain/play_intent.py`` says
    where this type belongs when it arrives: *"it belongs to the matcher and not
    to this module"*. Here it is.

    **There is never a ``NO_PREFERENCE`` weight vector.** A candidate who
    declared ``NO_PREFERENCE`` is indifferent about the kind of evening, so their
    reverse fit runs under the *searcher's* mode: ``NO_PREFERENCE`` never selects
    a weight vector, it inherits one (``ranking-weights.md`` §9). The arities
    differ on purpose, so the likeliest bug in the matcher is a type error rather
    than a paragraph in a document.
    """

    COMPETITIVE = "COMPETITIVE"
    FOR_FUN = "FOR_FUN"


class EvidenceKind(str, Enum):
    """The discriminator a term's evidence crosses the wire under.

    **This is contract and not configuration** (``docs/adr/0106``). A ruleset may
    move any number it likes without touching this enum; adding, removing or
    reshaping a variant is an API release, because the client generates an
    exhaustive renderer per variant and a kind it has never seen renders as
    nothing at all — on the one screen whose whole promise is showing its
    working.

    The values are the wire discriminators verbatim, lower-snake as
    ``the-engine.md`` §5.3 writes them, so the engine and the schema cannot
    disagree about the string.
    """

    LEVEL_FIT = "level_fit"
    PREDICTED_BALANCE = "predicted_balance"
    INTENT_ALIGNMENT = "intent_alignment"
    RELIABILITY = "reliability"
    AVAILABILITY_OVERLAP = "availability_overlap"
    PLAYING_STYLE = "playing_style"
    SOCIAL_VIBE = "social_vibe"
    DISTANCE = "distance"


class Term(str, Enum):
    """The eight terms of Fit, weighted per mode and renormalised per comparison.

    Eight and not seven: the prototype's single ``vibe`` merges what the split
    below keeps apart, and intent alignment is the term the prototype never had.
    **The split between playing style and social vibe is by *relationship*, not
    by tag group** — every matrix row carries its own column
    (``ranking-weights.md`` §1).

    Day one **reliability stands down** and the live seven renormalise; that is
    the basis every judged reading and the quality floor were computed on.
    """

    LEVEL_FIT = "LEVEL_FIT"
    PREDICTED_BALANCE = "PREDICTED_BALANCE"
    INTENT_ALIGNMENT = "INTENT_ALIGNMENT"
    RELIABILITY = "RELIABILITY"
    AVAILABILITY_OVERLAP = "AVAILABILITY_OVERLAP"
    PLAYING_STYLE = "PLAYING_STYLE"
    DISTANCE = "DISTANCE"
    SOCIAL_VIBE = "SOCIAL_VIBE"

    @property
    def evidence_kind(self) -> EvidenceKind:
        """The variant this term's evidence crosses as.

        One kind per term, and the mapping is here rather than in a ruleset
        because it is exactly the half ``docs/adr/0106`` makes contract: a
        ruleset that could re-aim a term at a different variant would be a
        weight release changing what the product claims it can explain.
        """

        return EvidenceKind[self.name]


class LevelDirection(str, Enum):
    """Which side of the searcher a candidate's Level sits on.

    A code and not a sign on ``delta``, because the client's sentence differs in
    all three cases and a renderer deriving *"above"* from a sign is the display
    logic the presentation boundary exists to keep out.

    It lives here rather than beside the wire shape for the reason
    ``EvidenceKind`` does: the engine computes it and the schema publishes it, so
    a second spelling on the schema's side would be two answers to *which way is
    up*. A module may import an engine; the reverse is the fence.
    """

    ABOVE = "ABOVE"
    LEVEL = "LEVEL"
    BELOW = "BELOW"


class ReliabilityStrand(str, Enum):
    """The six strands a reliability reading is built from, read separately.

    They are weighted **per mode** and the two vectors order people oppositely —
    a candidate strong on *confirms results* and weak on *sportsmanship* wins in
    competitive and loses in for fun. A single blended score cannot express that,
    which is the whole argument for the decomposition, and it is justified for
    exactly as long as such a pair exists (``ranking-weights.md`` §6).

    **Three different blends of these six exist in this system and confusing them
    is a live risk:** the published Player Score at 35/20/15/12/10/8, and these
    two. The reliability *floor* reads the published one — the one deliberate
    exception, because a penalty justified by a figure that exists nowhere a
    human can look is unexplainable.
    """

    SHOWS_UP = "SHOWS_UP"
    ANSWERS_CHALLENGES = "ANSWERS_CHALLENGES"
    CONFIRMS_RESULTS = "CONFIRMS_RESULTS"
    KEEPS_PLANS = "KEEPS_PLANS"
    SETTLES_UP = "SETTLES_UP"
    SPORTSMANSHIP = "SPORTSMANSHIP"


class TagRelationshipKind(str, Enum):
    """What a matrix row claims about two tag ids.

    A ``MATCH`` is two people independently choosing the same string, so its row
    has ``a == b`` and carries no strength — ``dr(matches)`` is a count. A
    ``COMPLEMENT`` is product's editorial claim about two *different* strings,
    which is why it is discounted by default. A ``CLASH`` carries a severity and
    is capped, because being wrong about a match costs a duller evening and being
    wrong about a clash buries a person.
    """

    MATCH = "MATCH"
    COMPLEMENT = "COMPLEMENT"
    CLASH = "CLASH"


class TagColumn(str, Enum):
    """Which of the two tag terms a relationship feeds.

    **A column's tag domain is derived from the matrix** — the ids appearing in
    any row carrying that column — and never declared separately, so it
    re-derives itself the moment product edits a row. A tag may sit in both
    domains, and a tag with no row at all is in neither.
    """

    STYLE = "STYLE"
    VIBE = "VIBE"


class Seat(str, Enum):
    """Where two people sit relative to each other in a four.

    **Where no seat is assigned, a pair reads the ``OPPONENT`` row and a
    ``PARTNER``-only row does not fire at all** — the unseated shortlist takes
    the more forgiving reading, and the harsher one applies only once somebody is
    being seated as a partner. Singles and unseated doubles therefore read
    identically, which is one fewer rule.
    """

    PARTNER = "PARTNER"
    OPPONENT = "OPPONENT"


class ClashSeverity(str, Enum):
    """How badly a clash row is judged to bite. Two grades, priced in the tags."""

    REAL = "REAL"
    MILD = "MILD"


class FamiliarityReading(str, Enum):
    """Which way familiarity points for a searcher holding a given tag.

    Read from the **searcher's** own declared tags and never the candidate's, over
    a second and separate map from the relationship matrix. **This is not a
    double-count against the tag terms**, which read the same ids: the tag does
    not add points through familiarity, it *selects which direction familiarity
    points*, and a selector is not an addend.

    ``NEITHER`` is a real answer rather than a gap — ``HERE_TO_COMPETE`` wants
    good opposition and says nothing about repetition; ``HERE_FOR_THE_EXERCISE``
    says nothing about *who*.
    """

    REPETITION = "REPETITION"
    VARIETY = "VARIETY"
    NEITHER = "NEITHER"


class LivenessSignal(str, Enum):
    """The ten things that move a candidate's position without moving their Fit.

    ``rank_key = fit + liveness_offset``. **No Liveness number ever crosses the
    wire in any shape** — a candidate carries ``fit`` and a list of reason
    *codes*, and the printed Fit stops meaning what it says the moment it
    silently contains *"they open the app a lot"*.

    Each signal is either **printable** — it owes the player an explanation when
    it moves them — or **silent**. ``docs/adr/0123`` budgets the silent *stack*
    at ``MOVE_NOTICE`` per player rather than bounding each silent signal, so no
    signal weakens and the printing promise falls out of the arithmetic: any
    player moved more than the notice threshold necessarily has a printable
    contributor to name.
    """

    INTEREST_RECEIVED = "INTEREST_RECEIVED"
    PREVIOUS_ACCEPT = "PREVIOUS_ACCEPT"
    ANSWER_RATE_AND_SPEED = "ANSWER_RATE_AND_SPEED"
    RECENT_ACTIVITY = "RECENT_ACTIVITY"
    OVERLAP_PROXIMITY = "OVERLAP_PROXIMITY"
    CHALLENGE_LOAD = "CHALLENGE_LOAD"
    RECIPROCAL_ASYMMETRY = "RECIPROCAL_ASYMMETRY"
    PREVIOUS_DECLINE = "PREVIOUS_DECLINE"
    NEWCOMER_LIFT = "NEWCOMER_LIFT"
    EXPOSURE_ADJUSTMENT = "EXPOSURE_ADJUSTMENT"


class ChallengeLoad(str, Enum):
    """How full a candidate's inbox is, as a **coarse code and never the number**.

    ``docs/adr/0125`` deletes the withholding at eight open challenges and adopts
    §14.4's three thresholds whole as a Liveness sink. What survives of the
    measurement on the wire is this: their inbox depth is theirs, and *they have
    a lot on* is the whole of what a searcher is owed about a third party's
    unanswered mail.

    **There is no fourth code for an empty inbox.** A signal that does not fire
    is absent from the list rather than present at zero, so an unloaded candidate
    prints nothing at all — which is a different statement from *we counted and
    it was low*. Each rung names its own code in the ruleset, so a threshold
    moving does not silently re-point a code at a different depth.
    """

    SOME = "SOME"
    BUSY = "BUSY"
    FULL = "FULL"


class Modifier(str, Enum):
    """The three modifiers that survive, plus the penalty that sits outside them.

    ``MODIFIER_BUDGET`` clamps the **summed stack** rather than each modifier, so
    a stack of small positives cannot lift somebody over a recent no-show. The
    reliability floor breach is **outside** the budget and derived as
    ``budget + 1``, which is the smallest penalty that keeps that promise and
    which moves by itself if the budget ever does.

    Two are struck rather than deferred and the difference matters. *Language*
    read a field that exists nowhere and is the nearest available proxy for the
    nationality the privacy line excludes by name — *a protected characteristic
    may gate; it may never score*. *Intent opposition* was a second charge for a
    fact the intent term already scores at 0.00, which is a gate wearing a
    modifier's clothes.
    """

    CALIBRATION_VALUE = "CALIBRATION_VALUE"
    FAMILIARITY = "FAMILIARITY"
    WELCOMING_RECORD = "WELCOMING_RECORD"
    RELIABILITY_FLOOR_BREACH = "RELIABILITY_FLOOR_BREACH"


class GroupTerm(str, Enum):
    """The six terms of the doubles objective ``G``.

    **A four contains six pairs and the searcher is in three of them.** Every
    term here reads something no seat's Fit read, which is the admissibility rule
    ``docs/adr/0117`` sets: the three cross pairs contain no searcher and are
    invisible to Fit by construction, and a four-way slot intersection is not
    implied by three good pairwise ones.

    **``G`` is recorded and never returned as a number.** It is only ever
    compared to another ``G``; there is no group floor. A second score the player
    must trust is worse than none, because it competes with Fit and nobody can
    act on it.
    """

    BALANCE = "BALANCE"
    SEAT_FIT = "SEAT_FIT"
    MIN_SEAT_FIT = "MIN_SEAT_FIT"
    CROSS = "CROSS"
    CROSS_MIN = "CROSS_MIN"
    AVAILABILITY = "AVAILABILITY"


class RelaxationRung(str, Enum):
    """The three offers a short shortlist may carry. **Offered, never applied.**

    **A rung may only relax something the searcher themselves asked for.** It may
    never touch a measurement, a term, a weight or the quality floor — the input
    document's other three rungs raised scores against a fixed floor, which is
    arithmetically indistinguishable from lowering the bar.

    Times before distance: a slot you were already free in costs nothing, where
    distance costs travel on every game forever. **There is no third radius
    rung** — tripling still leaves 15% of searches under five candidates at
    launch density.

    **The declaration order below is the ladder, and it is not ruleset data.**
    ``max_rung`` and the ordered-rung list are struck: both were keys over a fact
    this enum already states, and a ruleset that could reorder or extend the
    ladder would be a weight release changing what the product offers. What a
    release may move is how far each radius rung reaches.
    """

    #: Single-slot additions to the searcher's own grid, for this one search.
    TIMES = "TIMES"
    #: The searcher's own radius, multiplied — clamped to the maximum the profile
    #: slider itself allows, because a rung may never offer a radius the player
    #: could not have set for themselves.
    RADIUS_NEAR = "RADIUS_NEAR"
    RADIUS_FAR = "RADIUS_FAR"


#: The engine-side ceiling on the doubles candidate cap.
#:
#: ``K`` is ruleset data — ``docs/adr/0093`` names *a cap* as ruleset material —
#: but the enumeration is **cubic in K with a flat per-combination cost**, so the
#: one number that can destroy the line-up latency budget must not ship as "just
#: configuration". At 24 the group objective is 27% of the 90 ms budget; at 32
#: the budget is gone (``scale-posture.md`` §6). A ruleset above this refuses to
#: load, on the same rule that refuses any other malformed one.
K_CEILING = 24
