"""What crosses the privacy fence, and what deliberately does not.

**The fence is the package boundary with no exceptions in it**
(``docs/adr/0093``). Gating and candidate generation live in the *module*, where
the I/O is; the scorer receives an **already-gated, already-fenced** set and does
the arithmetic. Splitting gates by kind — *identity* outside, *arithmetic*
inside — was rejected, because a fence with a judgement call in it is not a
fence.

So the sentence *a term cannot read a protected characteristic because the value
is not in the process* is made **literally true** here rather than aspirational:
``ScorableCandidate`` carries **no gender, no name, no photo, no birthdate, no
precise location and no shard key**, and
``tests/unit/test_scorable_candidate_fence.py`` walks this source — transitively,
through every type a field is annotated with — and fails the build if one appears.
A walk rather than a review, because the field that breaks this rule will be
added by somebody who has a good reason for it.

**Three kinds of fact live on a candidate, and the difference is worth naming.**

*Facts about the candidate* — their Level, their tags, their grid, their radius —
are copies of what the index holds.

*Facts about the pair* — the combined uncertainty, the distance — are measured
outside and handed in. They are here because the fence puts them here, not
because it is tidier: ``combine_sigma`` and the confidence transform are
RacketSkill's, *the single place any engine is allowed to combine two standard
deviations*, and ``.importlinter`` forbids one engine to import the other. Match
Fit reads that rule **through the module that composes the two**, never by
re-deriving it — so ``CombinedUncertainty`` arrives already combined, beside the
two σs the evidence has to print.

*Facts a pure process cannot have* — ``today``, and how many days old a Player
Score is. An engine reads the time it is given (``docs/adr/0015``); ``datetime``
is forbidden to this layer outright, so an age arrives as a whole number of days
and a weekday arrives as the kernel's ``IsoWeekday``, exactly as
``docs/adr/0100``'s ``window_of(grid, today)`` takes one.

**Vocabularies the platform owns cross as the machine codes they already are** —
Social tag ids, parts of the day, Play intent declarations. An engine may not
import the module that owns a vocabulary, and retyping one here would be a second
spelling of a closed set, which is how two halves of one system begin disagreeing
about the same word (``core``). What the engine is told instead is the *shape* it
needs: ``day_parts`` says where each part sits inside a day, so the soonest
shared slot can be found without the engine ever learning what a morning is.

**A player id is a string and not a ``UUID``.** ``uuid`` is ambience and is
forbidden to the engines beside ``random``, ``secrets`` and ``time``: an id the
engine cannot construct is an id it cannot invent. Ties break on it ascending
(``docs/adr/0105``), and a string compares in a stable order without a clock or a
hash seed behind it.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, final

from app.engines.matchfit.core import ReliabilityStrand, SearchMode
from app.kernel import IsoWeekday, invariant


@final
@dataclass(frozen=True, slots=True)
class LevelReading:
    """A player's Level and Uncertainty, as RacketSkill published them.

    Copied rather than re-derived. The scorer reads μ and σ; it never asks how
    they were arrived at, and it never calls ``band_for`` — the shipped bands are
    deliberately uneven because *evidence* is unevenly available down the scale,
    not because a tenth of a point means less at the top.
    """

    mu: float
    sigma: float

    def __post_init__(self) -> None:
        invariant(self.sigma >= 0.0, f"a negative Uncertainty: {self.sigma}")


@final
@dataclass(frozen=True, slots=True)
class GridCell:
    """One cell of the ordinary week both players may have ticked.

    The day is the kernel's ``IsoWeekday`` because Monday-first is already what
    ISO means. The part is **the platform's own machine code**, opaque here: the
    engine compares parts for equality and orders them by ``Searcher.day_parts``,
    and never learns that one of them is called a morning.
    """

    day: IsoWeekday
    part: str

    def __post_init__(self) -> None:
        invariant(1 <= int(self.day) <= 7, f"a grid cell outside the week: {self.day}")
        invariant(bool(self.part), "a grid cell with no part of the day")


@final
@dataclass(frozen=True, slots=True)
class RatioObservation:
    """One of the five ratio strands: the published figure, and how much of it.
    (Five of the six names — sportsmanship is a mean and crosses as the other
    shape below.)

    ``published_value`` is **the number the player is shown on their own Player
    Score screen** and is never re-derived from a count — a card explaining a
    match with a figure the player's own profile disagrees with breaks the
    explainability promise more thoroughly than saying nothing would.
    ``observations`` is the denominator, the *opportunity*: the matcher's entire
    policy over these facts is standing a strand down below the bar, and one
    no-show out of one game is not thirty-five out of thirty-eight.
    """

    published_value: int
    observations: int

    def __post_init__(self) -> None:
        invariant(
            0 <= self.published_value <= 100,
            f"a strand value outside 0..100: {self.published_value}",
        )
        invariant(
            self.observations >= 1,
            "a strand with no opportunity behind it is an absence, not a zero: "
            f"{self.observations}",
        )


#: The ends of the sportsmanship rating scale. They live beside the shape that
#: carries a mean rather than beside the arithmetic that reads one, because they
#: are the **scale's** own bounds and not a ruleset number: moving them would mean
#: the product had started asking a different question, not that it had reweighed
#: an answer. One home, so the refusal below and the reading in ``terms`` cannot
#: come to disagree about what the worst rating is.
RATING_FLOOR = 1.0
RATING_CEILING = 5.0


@final
@dataclass(frozen=True, slots=True)
class MeanObservation:
    """Sportsmanship — **a mean of 1–5, not a ratio.**

    The sixth strand is the one with no good outcome to count, so it crosses as
    its mean and the number of ratings behind it. A separate type rather than a
    ratio with a convention, because a mean smuggled through a numerator would be
    a strand nobody could interpret and nothing could refuse.

    **It is the one strand whose 0–1 reading the engine derives**, and it derives
    it because there is nothing published to read: ``(mean − 1) / 4``, which is
    the only map the scale's own bounds license — a mean of 1 is the worst a
    player can be rated and reads zero, a mean of 5 reads one.
    """

    mean: float
    observations: int

    def __post_init__(self) -> None:
        invariant(
            RATING_FLOOR <= self.mean <= RATING_CEILING,
            f"a sportsmanship mean outside {RATING_FLOOR}..{RATING_CEILING}: "
            f"{self.mean}",
        )
        invariant(
            self.observations >= 1,
            f"a sportsmanship mean with no ratings behind it: {self.observations}",
        )


#: What a strand crosses the fence as. Two shapes, because five of the six are
#: ratios and the sixth is a mean, and one shape covering both would be a shape
#: that describes neither.
StrandObservation = RatioObservation | MeanObservation


@final
@dataclass(frozen=True, slots=True)
class ReliabilityRecord:
    """A candidate's Player Score, **as strands and never as one number.**

    ``published_score`` is not a blend of the strands the term weighs and may
    never be weighed as one. It is the figure on the player's own profile, read
    by exactly one consumer — the reliability floor — because a penalty justified
    by a figure that exists nowhere a human can look is unexplainable.

    ``days_since_last_observation`` is the horizon's input, measured outside
    because a pure process has no clock. It is one number over the whole record
    rather than six: the strands share one cause — *this player stopped playing* —
    and six ages would be six places for it to disagree with itself.

    **A record with no strand in it is not a record.** Absence has one spelling:
    the candidate simply carries no record at all, and the term stands down.
    """

    strands: Mapping[ReliabilityStrand, StrandObservation]
    published_score: int
    days_since_last_observation: int

    def __post_init__(self) -> None:
        invariant(
            bool(self.strands),
            "a reliability record with no strands is an absence, and an absence "
            "is spelled by carrying no record at all",
        )
        invariant(
            0 <= self.published_score <= 100,
            f"a published Player Score outside 0..100: {self.published_score}",
        )
        invariant(
            self.days_since_last_observation >= 0,
            f"an observation in the future: {self.days_since_last_observation} days",
        )
        for strand, observation in self.strands.items():
            expected: type[StrandObservation] = (
                MeanObservation
                if strand is ReliabilityStrand.SPORTSMANSHIP
                else RatioObservation
            )
            invariant(
                isinstance(observation, expected),
                f"{strand.value} crossed as {type(observation).__name__} rather "
                f"than {expected.__name__}",
            )


@final
@dataclass(frozen=True, slots=True)
class CombinedUncertainty:
    """What RacketSkill says about a pair of Levels, combined on its own side.

    ``sigma`` is ``combine_sigma(σ_searcher, σ_candidate)`` — independent
    uncertainties adding in quadrature — and ``confidence`` is the same library's
    σ-to-percent transform, held in ``[0, 99]`` because the platform can never
    tell a player it is certain about them.

    **Both are computed outside this engine and neither is re-derived inside
    it.** Two engines with two opinions about a Level is the failure the
    engine-to-engine fence exists for, and ``√(σ² + σ²)`` written out here would
    be a second definition of an identity that already has an owner.
    """

    sigma: float
    confidence: int

    def __post_init__(self) -> None:
        invariant(self.sigma >= 0.0, f"a negative combined σ: {self.sigma}")
        invariant(
            0 <= self.confidence <= 99,
            f"a confidence outside 0..99: {self.confidence}",
        )


@final
@dataclass(frozen=True, slots=True)
class Searcher:
    """The person searching, and the settings this one search runs under.

    ``mode`` is a ``SearchMode`` and has two values; a candidate's declaration is
    a Play intent and has three. The arities differ on purpose, so the likeliest
    bug in the matcher is a type error rather than a paragraph in a document.

    ``grid`` is the **denominator** of the availability term — *how much of my
    week does this person cover* — which is what makes that reading asymmetric
    and a fact about the pair rather than about either person.

    ``today`` and ``day_parts`` are the two things a pure process cannot work out
    for itself: which day it is, and which part of a day comes first.
    """

    level: LevelReading
    mode: SearchMode
    tags: tuple[str, ...]
    grid: tuple[GridCell, ...]
    radius_km: float
    today: IsoWeekday
    #: The parts of a day in the order the platform lays them out. One vocabulary
    #: fact, supplied once per search: it is the whole of what the engine needs to
    #: say *the soonest cell you both ticked* without holding a second copy of a
    #: closed vocabulary it may not import.
    day_parts: tuple[str, ...]

    def __post_init__(self) -> None:
        invariant(self.radius_km > 0.0, f"a search radius of {self.radius_km} km")
        invariant(
            1 <= int(self.today) <= 7, f"a weekday outside the week: {self.today}"
        )
        invariant(bool(self.day_parts), "a week with no parts of the day in it")
        invariant(
            len(set(self.day_parts)) == len(self.day_parts),
            f"a part of the day listed twice: {self.day_parts}",
        )
        _no_repeated_cell(self.grid)
        for cell in self.grid:
            invariant(
                cell.part in self.day_parts,
                "a grid cell in a part of the day this search cannot order: "
                f"{cell.part}",
            )


@final
@dataclass(frozen=True, slots=True)
class ScorableCandidate:
    """One candidate, as the scorer is allowed to see them.

    **No gender, no name, no photo, no birthdate, no precise location and no
    shard key** — asserted by a source walk, not by this docstring. The player
    card is assembled outside the engine and attached afterwards
    (``docs/adr/0107``); gender reaches generation and gating and stops at this
    line (``docs/adr/0096``); the area is a **coarse** machine code, which is the
    finest location fact that has ever crossed here.

    Every field below is either read by a term or printed as that term's
    evidence. A field that is neither has no business on this side of the fence.
    """

    #: The candidate's id, as an opaque string. Ties break on it ascending.
    player_id: str
    level: LevelReading
    #: The candidate's Play intent for this sport, as the machine code it already
    #: is — or ``None`` when they have not declared. Not declaring stands the term
    #: down and renormalises it away; declaring *against* the searcher reads the
    #: table's zero, which already costs strictly more than silence.
    declared_intent: str | None
    tags: tuple[str, ...]
    grid: tuple[GridCell, ...]
    #: The candidate's **own** ring. It is a Liveness dock and never a gate:
    #: somebody who set a small radius is not refusing to be found, so the
    #: searcher is shown the fact rather than having the person removed — and it
    #: enters no term, which is the whole of judged case 6's verdict.
    radius_km: float
    #: The candidate's coarse area, as a machine code.
    area_code: str
    #: Cell to cell — the term reads this measurement and prints it whole in its
    #: evidence. The one-decimal ``distance_km`` on the wire is the module's own,
    #: measured between two drawn spots, and never reaches this type.
    distance_km: float
    #: What RacketSkill says about the two Levels together — combined outside,
    #: see the module docstring. The engine prints the two σs and weighs this.
    combined: CombinedUncertainty
    reliability: ReliabilityRecord | None

    def __post_init__(self) -> None:
        invariant(bool(self.player_id), "a candidate with no id")
        invariant(self.radius_km > 0.0, f"a candidate radius of {self.radius_km} km")
        invariant(
            self.distance_km >= 0.0, f"a negative distance: {self.distance_km} km"
        )
        invariant(bool(self.area_code), "a candidate with no area")
        _no_repeated_cell(self.grid)


def _no_repeated_cell(grid: tuple[GridCell, ...]) -> None:
    """A grid is what somebody ticked, and a cell ticked twice is still one cell.

    Refused rather than folded, because the fold has an owner on the other side
    of the fence and a duplicate arriving here means that fold did not run — and
    the availability term would then divide by an inflated denominator and read
    *less* overlap than the pair has.
    """

    invariant(
        len(set(grid)) == len(grid),
        f"a grid with a cell ticked twice: {[(int(c.day), c.part) for c in grid]}",
    )


@final
@dataclass(frozen=True, slots=True)
class SharedHistory:
    """What the two of them have already played together. A fact about the pair.

    ``days_since_last_game`` and the count are the two inputs familiarity's decay
    reads — ``0.5 ^ (days / half_life) × (1 − φⁿ)`` — and they arrive measured
    rather than as a strength, because the half-life and φ are ruleset numbers
    and a provider that had already applied them would be a second place for them
    to live.

    **Absence has one spelling: no history at all.** A pair who have never played
    carry ``None`` rather than a zero-game record, on the rule this whole layer
    runs on — a zero here would be an invented one, and it would decay from full
    strength like a game somebody actually played.
    """

    days_since_last_game: int
    games_played_together: int

    def __post_init__(self) -> None:
        invariant(
            self.days_since_last_game >= 0,
            f"a game played in the future: {self.days_since_last_game} days",
        )
        invariant(
            self.games_played_together >= 1,
            "a shared history of no games is an absence, and an absence is "
            f"spelled by carrying no history at all: {self.games_played_together}",
        )


@final
@dataclass(frozen=True, slots=True)
class ModifierFacts:
    """What stage 4 reads, and nothing a term may see.

    Separate from ``ScorableCandidate`` because every field on that type is read
    by a term or printed as that term's evidence, and none of these is: a
    modifier is applied *after* the eight terms and prints a line of its own. It
    crosses the same fence — the walk in
    ``tests/unit/test_scorable_candidate_fence.py`` reads this type as a root —
    because *what is in the process* is the claim, not *what a term reads*.

    **Two of the three cannot fire today and say so by being absent**, rather
    than by arriving as a false or a zero. Familiarity and the welcoming record
    both need ``matches``, which is unwritten; calibration is the one modifier
    whose input exists.
    """

    #: The candidate's ``calibration_priority``, as the binary it is. Not a ramp:
    #: the rating aggregate has two values, and a 0…+4 range read off a field
    #: with two states is 0 or +4. **Competitive only** — it applies where a
    #: rating is at stake — and it prints, because a player is entitled to know
    #: when they are being matched partly for somebody else's benefit.
    calibration_elevated: bool
    #: ``None`` when the two of them have never played.
    shared_history: SharedHistory | None
    #: The welcoming record, reduced to its one unpaid input (#175): *has played
    #: opponents whose rating was still settling*. ``None`` is **no answer** and
    #: not *no*, because the provider is ``matches`` and it does not exist.
    welcomed_settling_opponents: bool | None
    #: How often this candidate has already been volunteered into a **newcomer's**
    #: shortlist this week, in this sport — ``NEWCOMER_ABSORPTION_CAP``'s tally,
    #: and the welcoming record's bound alone. It is read **here and nowhere
    #: else**, because the welcoming record is the thumb that selects the
    #: experienced players the cap is about (``docs/adr/0114``).
    #:
    #: ``None`` when the search asking is not a newcomer's, which is the only
    #: search the cap counts and the only one it can bind in: the bound is on
    #: *the ask*, so a search that adds nothing to somebody's absorption may not
    #: take anything away for it either.
    #:
    #: The **count** crosses and never the verdict, because the cap that prices
    #: it is ruleset data (``docs/adr/0106``) — a bool decided outside would be a
    #: released number applied where nothing could re-derive it.
    newcomer_appearances: int | None

    def __post_init__(self) -> None:
        invariant(
            self.newcomer_appearances is None or self.newcomer_appearances >= 0,
            f"a negative absorption tally: {self.newcomer_appearances}",
        )


@final
@dataclass(frozen=True, slots=True)
class LivenessFacts:
    """What stage 6 reads: ten facts that move a position and never a number.

    **Four of the ten arrive as a reading in ``[0, 1]`` rather than as a
    measurement**, and that is a decision rather than a convenience. A signal's
    *points* are ruleset data; the curve from *days since they last opened the
    app* to a reading is a **measurement**, and it belongs on the other side of
    the fence with the clock and the ledgers. Putting it here would mean
    inventing a threshold per signal — four curves nobody measured, in the one
    file whose whole discipline is that every number has a falsifier.

    **The full inbox is the exception, and it is the exception on purpose.** Its
    three thresholds were measured and published (§14.4) and ``docs/adr/0125``
    adopted them whole, so it reads the count and the ruleset holds the rungs.

    **A fact that is not there is ``None``, never a neutral reading.** A signal
    that does not fire is absent from the offset rather than present at zero, and
    a 0.5 standing in for *we did not look* is the invented neutral this layer
    refuses everywhere else.
    """

    #: How long ago they said *Let's play* to the searcher, when a live one
    #: exists. The lift is **flat for the whole life of the yes and then absent**
    #: (``docs/adr/0127``) — the age crosses as evidence and a taper would charge
    #: one fact twice — so this is read as *whether*, and printed as *how long*.
    interest_days_ago: int | None
    #: Whether the candidate is inside the newcomer window. **The absorption cap
    #: is not read here**: it bounds how often an *experienced* player is
    #: volunteered into newcomers' lists, and this lift is a newcomer's own
    #: subsidy (``docs/adr/0114``).
    newcomer: bool
    previously_accepted: bool
    previously_declined: bool
    #: How well and how fast they answer challenges, as one reading.
    answer_rate: float | None
    #: *This week* … *dormant*, projected outside from refresh-token events.
    recent_activity: float | None
    #: How soon the next slot the two of them share comes round.
    overlap_proximity: float | None
    #: How many challenges are sitting unanswered in their inbox. A **count**,
    #: because this is the one signal whose thresholds were measured.
    open_challenges: int | None
    #: How little the candidate has been shown this week, from the exposure
    #: ledger. Silent, and the searcher is owed no version of it.
    exposure: float | None

    def __post_init__(self) -> None:
        for field, reading in (
            ("answer_rate", self.answer_rate),
            ("recent_activity", self.recent_activity),
            ("overlap_proximity", self.overlap_proximity),
            ("exposure", self.exposure),
        ):
            invariant(
                reading is None or 0.0 <= reading <= 1.0,
                f"{field} read {reading}, which is outside [0, 1]",
            )
        invariant(
            self.interest_days_ago is None or self.interest_days_ago >= 0,
            f"a *Let's play* sent in the future: {self.interest_days_ago} days",
        )
        invariant(
            self.open_challenges is None or self.open_challenges >= 0,
            f"a negative inbox: {self.open_challenges}",
        )
