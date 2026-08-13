"""RacketSkill Fusion v3 — adaptive routing, inverse-variance fusion, finalisation.

The engine is pure: ``next_step`` and ``finalize`` are functions of the transcript
alone. It holds no state between calls, so replaying an assessment's event stream
reproduces exactly the questions it asked.

Routing runs as an **ordered sequence of checks**, each firing only if everything
above it has passed:

1. the opening regularity question, always;
2. the beginner fast path — "never played" ends the assessment, so no technique
   question of any tier is ever asked of somebody who has never held a racket;
3. match volume, only when the regularity answer was genuinely ambiguous;
4. layoff, only when volume came back low *and* the player has a history;
5. one competitive-context question (environment, then relative performance)
   before any execution question;
6. a minimum number of execution demonstrations that **scales with the
   estimate** — two normally, three once the estimate reaches Established, because
   that band spans a whole level and two answers cannot place somebody inside it —
   each at the difficulty tier the running estimate implies;
7. one tactical answer.

Once those minimums are met, two rules decide whether to keep going. **Extreme-
answer bracketing** notices that an answer at either end of the scale proves "at
least this good" and bounds nothing above, so — confidence having already hit its
ceiling — it asks another demonstration at the tier the updated estimate implies,
the one place the questionnaire lengthens for a strong player. **Marginal-value
stopping** otherwise ends the assessment the moment the best remaining question
would not tighten the floored estimate meaningfully; because the self-report bias
never shrinks, that value decays to zero on its own. The hard ceiling still caps
every path. Layoff widens uncertainty and never touches the estimate.

Between the minimums and those two rules sits the **contradiction** check. Claims
(how much you play, what you compete in, how you do against your usual group) are
fused separately from demonstrations (what happens inside a point); a gap beyond
tolerance between the two earns exactly one tie-breaker, and it is the execution
question at the tier the *claims* imply — an easier one would not test the claim
and a harder one would test something the claim never made. If the player can do
the thing their claims imply, the claims were right; if not, they were not. When
that question has already been answered the claims have been tested at their own
level already, so nothing extra is asked. An unresolved gap resolves without a
direction — claims keep only part of their precision, σ widens in proportion to
the gap, and calibration priority is raised. Nobody is moved up, moved down, or
accused. A gap *within* tolerance is not a disagreement at all: a strong smash
and a weak backhand is an uneven game, and it widens the band through dispersion.

That resolution is applied in ``finalize`` and not to the running estimate, so a
widened σ can never buy the player extra questions: routing already has its own
answer to a contradiction, which is the tie-breaker.

``finalize`` also **explains** the number it produces. One factor row per evidence
category the player answered — recent activity, competitive context, match
execution, tactical execution — each fused on its own evidence and compared
against the final estimate, so its direction is computed rather than authored and
retuning a constant moves the arrows with no copy edited. Separately, the things
that widened *uncertainty* rather than moving the estimate are listed as such,
each carrying the σ it actually added: a contributor the floor absorbed entirely
did nothing and says nothing. The confidence sentence branches on whichever of
those actually dominated, falling back to the case every onboarding rating
shares — we have not seen the player play yet.
"""

from __future__ import annotations

from dataclasses import dataclass

from app.engines.assessment import (
    CALIBRATION_PRIORITY_ELEVATED,
    CALIBRATION_PRIORITY_STANDARD,
    FACTOR_DIRECTION_DOWN,
    FACTOR_DIRECTION_NEUTRAL,
    FACTOR_DIRECTION_UP,
    AnsweredQuestion,
    AskQuestion,
    AssessmentResult,
    BandView,
    Complete,
    ConfidenceReason,
    Question,
    ResultFactor,
    Step,
    Transcript,
    UncertaintyFactor,
)
from app.engines.racketskill.core import (
    CONFIDENCE_SIGMA_CEILING,
    Band,
    SkillEstimate,
    band_for,
    clamp_to_scale,
    combine_sigma,
    confidence_percent,
    likely_range,
)
from app.engines.racketskill.v3.questions import (
    AMBIGUOUS_REGULARITY_OPTIONS,
    ENVIRONMENT_QUESTION_ID,
    EXECUTION_QUESTION_IDS,
    FACTOR_COMPETITIVE_CONTEXT,
    FACTOR_KEYS,
    FACTOR_LABELS,
    HISTORY_REGULARITY_OPTIONS,
    KIND_CLAIM,
    KIND_DEMONSTRATION,
    LAYOFF_QUESTION_ID,
    LOW_VOLUME_OPTION_ID,
    NEVER_PLAYED_OPTION_ID,
    OPENING_QUESTION_ID,
    RELATIVE_QUESTION_ID,
    RELATIVE_SIGMA,
    TACTICAL_QUESTION_IDS,
    TIERS,
    VOLUME_QUESTION_ID,
    environment_evidence,
    environment_question,
    execution_evidence,
    execution_question,
    execution_sigma,
    factor_for,
    is_extreme_execution,
    is_extreme_tactical,
    kind_for,
    layoff_question,
    layoff_sigma,
    opening_question,
    regularity_evidence,
    relative_offset,
    relative_question,
    tactical_evidence,
    tactical_question,
    tactical_sigma,
    tier_for_execution_id,
    volume_evidence,
    volume_question,
)
from app.kernel import Sport

ENGINE_VERSION = "racketskill-fusion-v3"

# The population prior every player starts from, before any answer.
POPULATION_PRIOR = SkillEstimate(mu=2.60, sigma=2.60)

# The irreducible self-report bias, folded into every answer's σ in quadrature.
SELF_REPORT_BIAS = 0.75

# The single confidence ceiling, enforced as a floor on σ rather than a display
# cap: nobody leaves onboarding above 30% confident, by design.
CONFIDENCE_CAP = 0.30
SIGMA_FLOOR = CONFIDENCE_SIGMA_CEILING * (1.0 - CONFIDENCE_CAP)

# The estimate at which a whole extra demonstration is warranted: Established and
# Advanced each span a full level, so two answers cannot place somebody inside one.
ESTABLISHED_FLOOR = Band.ESTABLISHED.lower

# The hard ceiling on questionnaire length. The ordered sequence already caps at
# this under any answer pattern; the guard makes the invariant unmissable.
MAX_QUESTIONS = 9

# Marginal-value stopping: once the hard minimums are met, the questionnaire ends
# as soon as the best remaining question would not tighten the *floored* estimate
# by at least this much. Because the irreducible self-report bias never shrinks, σ
# reaches its floor within a couple of answers and every further question's value
# decays to zero on its own — so the rule terminates without needing a count.
MIN_MARGINAL_GAIN = 0.01


# --- Contradiction ------------------------------------------------------------

# The gap, in level units, beyond which the fused claims and the fused
# demonstrations are genuinely disagreeing rather than merely imprecise. Below it
# the two are read as one uneven profile, which widens the band through dispersion
# and is never reported as a disagreement.
CONTRADICTION_TOLERANCE = 0.80

# A comparison needs both sides, and one demonstration is a data point rather than
# a side: the routing minimums guarantee at least this many before the check runs.
MIN_DEMONSTRATIONS_COMPARED = 2

# The share of their precision claims keep when the tie-breaker did not settle the
# disagreement. Broad claims are the softer evidence, so they give way to the
# demonstrations — but only partly, and by exactly as much whichever side is the
# higher one. That symmetry is the whole anti-sandbagging design: claiming too
# little costs precision exactly as fast as claiming too much.
CLAIM_PRECISION_RETAINED = 0.50

# The σ an unresolved gap adds, in quadrature and in proportion to its size, with
# a cap so that even the widest disagreement leaves a usable range. It is combined
# with the *floored* σ, because "we kept your starting range wider" is a statement
# about the range the player would otherwise have left with.
CONTRADICTION_SIGMA_PER_LEVEL = 0.35
CONTRADICTION_SIGMA_MAX = 0.60

# A contradiction buys exactly one question beyond the hard ceiling — the
# tie-breaker itself, and nothing else.
CONTRADICTION_EXTRA_QUESTIONS = 1

# Dispersion: how unevenly the demonstrations sit around their own fused level. A
# strong smash and a weak backhand is an uneven game, not a lie, so it earns a
# wider band. The tolerance absorbs the scatter every honest answer set carries.
DISPERSION_TOLERANCE = 0.55
DISPERSION_SIGMA_MAX = 0.50

# --- The explained result: factor rows, uncertainty rows, the confidence reason -

# How far one category's own level has to sit from the final estimate before the
# row claims a direction. Below it the category agrees with where the estimate
# landed, and an arrow would be reading noise as meaning.
FACTOR_DIRECTION_TOLERANCE = 0.15

# A widener is reported only if it survives the rounding its own σ is reported
# at: a short break the σ floor absorbs entirely did nothing, and saying it did
# would be the explanation drifting from the arithmetic.
SIGMA_REPORTING_DIGITS = 4

# The things that widen uncertainty rather than moving the estimate. Each carries
# the σ it actually added, so the rows add up to the range the player sees.
UNCERTAINTY_TIME_AWAY = "time-away"
UNCERTAINTY_UNEVEN_PROFILE = "uneven-profile"
UNCERTAINTY_ANSWERS_DISAGREED = "answers-disagreed"

UNCERTAINTY_LABELS: dict[str, str] = {
    UNCERTAINTY_TIME_AWAY: "Time away from the game",
    UNCERTAINTY_UNEVEN_PROFILE: "An uneven game",
    UNCERTAINTY_ANSWERS_DISAGREED: "Answers pointing to different ranges",
}

UNCERTAINTY_DETAILS: dict[str, str] = {
    UNCERTAINTY_TIME_AWAY: (
        "You have been away from the game, so we widened your range rather than "
        "lowering your level."
    ),
    UNCERTAINTY_UNEVEN_PROFILE: (
        "Your game is stronger in some areas than in others, so your range is a "
        "little wider."
    ),
    UNCERTAINTY_ANSWERS_DISAGREED: (
        "Your answers point to more than one range, so we kept the range wider "
        "rather than picking one."
    ),
}

# The confidence-reason branches, one per situation that actually produces one.
# Which applies is decided by the contributor that widened uncertainty most, and
# the base case is the one every onboarding rating shares: we have not seen the
# player play yet.
CONFIDENCE_REASON_LIMITED_EVIDENCE = "limited-match-evidence"
CONFIDENCE_REASON_TIME_AWAY = UNCERTAINTY_TIME_AWAY
CONFIDENCE_REASON_CONTRADICTION = UNCERTAINTY_ANSWERS_DISAGREED

LIMITED_EVIDENCE_SENTENCE = (
    "We have not seen you play yet, so this is a starting estimate built from "
    "your answers. Your first matches will sharpen it quickly."
)
TIME_AWAY_SENTENCE = (
    "You have been away from the game for a while, so we widened your starting "
    "range rather than lowering it. Your first matches will show where you are now."
)
CONTRADICTION_SENTENCE = (
    "Some of your answers point to different skill ranges, so we kept your "
    "starting range wider. Your first matches will help us calibrate it quickly."
)

CONFIDENCE_SENTENCES: dict[str, str] = {
    CONFIDENCE_REASON_LIMITED_EVIDENCE: LIMITED_EVIDENCE_SENTENCE,
    CONFIDENCE_REASON_TIME_AWAY: TIME_AWAY_SENTENCE,
    CONFIDENCE_REASON_CONTRADICTION: CONTRADICTION_SENTENCE,
}

# An uneven profile widens the range but authors no confidence sentence: "your
# game is uneven" is not a reason we cannot be confident *yet*, it is a fact
# about the player, and it is already reported as its own uncertainty row.
CONFIDENCE_AUTHORING_WIDENERS: tuple[str, ...] = (
    UNCERTAINTY_TIME_AWAY,
    UNCERTAINTY_ANSWERS_DISAGREED,
)

# The reasons a stop is recorded under — the counterpart to an ``AskQuestion``'s
# routing reason, so the value that caused the stop is never lost.
STOP_BEGINNER = "beginner-fast-path"
STOP_CEILING = "hard-ceiling"
STOP_MARGINAL = "marginal-value-below-threshold"

TIE_BREAKER_REASON = "contradiction-tie-breaker"

# Every onboarding rating is a hypothesis, not a verdict.
RESULT_STATUS = "Initial Estimate"


class UnknownAnswer(ValueError):
    """A transcript entry the engine version does not recognise."""


class RacketSkillEngineV3:
    """The version-3 assessment engine."""

    @property
    def version(self) -> str:
        return ENGINE_VERSION

    def next_step(self, *, sport: Sport, transcript: Transcript) -> Step:
        if not transcript:
            return AskQuestion(
                question=opening_question(sport),
                reason="opening",
                mu=POPULATION_PRIOR.mu,
                sigma=POPULATION_PRIOR.sigma,
            )

        # The beginner fast path: the "never played" anchor ends the assessment,
        # enforced in the engine so no technique question of any tier is ever
        # asked of somebody who has never held a racket.
        opening = transcript[0]
        regularity_option = opening.option_id
        if (
            opening.question_id == OPENING_QUESTION_ID
            and regularity_option == NEVER_PLAYED_OPTION_ID
        ):
            return Complete(reason=STOP_BEGINNER, value=0.0)

        # The hard ceiling, which a contradiction raises by exactly one — the
        # tie-breaker, and nothing else. The sequence below never reaches it, but
        # the guard makes "never exceeds the ceiling" unmissable.
        tie_breaker_at = _tie_breaker_at(transcript)
        ceiling = MAX_QUESTIONS + (
            CONTRADICTION_EXTRA_QUESTIONS if tie_breaker_at is not None else 0
        )
        if len(transcript) >= ceiling:
            return Complete(reason=STOP_CEILING, value=float(len(transcript)))

        estimate = _fuse(transcript)
        answered = {entry.question_id for entry in transcript}

        # Volume, only after a genuinely ambiguous regularity answer.
        if (
            regularity_option in AMBIGUOUS_REGULARITY_OPTIONS
            and VOLUME_QUESTION_ID not in answered
        ):
            return _ask(volume_question(sport), "volume-ambiguous-regularity", estimate)

        # Layoff, only when volume came back low and the player has a history —
        # never of a beginner, who has already left by the fast path above.
        if (
            VOLUME_QUESTION_ID in answered
            and _answer_for(transcript, VOLUME_QUESTION_ID) == LOW_VOLUME_OPTION_ID
            and regularity_option in HISTORY_REGULARITY_OPTIONS
            and LAYOFF_QUESTION_ID not in answered
        ):
            return _ask(
                layoff_question(sport), "layoff-low-volume-with-history", estimate
            )

        # One competitive-context question before any execution question, so the
        # execution answers are read in the right context.
        if ENVIRONMENT_QUESTION_ID not in answered:
            return _ask(environment_question(sport), "competitive-context", estimate)
        if RELATIVE_QUESTION_ID not in answered:
            return _ask(relative_question(sport), "relative-performance", estimate)

        # Hard minimums. Execution demonstrations, a count that scales with the
        # estimate, each at the tier the running estimate implies; then one
        # tactical answer.
        asked_tiers = _asked_execution_tiers(transcript)
        if len(asked_tiers) < _required_demonstrations(estimate):
            tier = _next_execution_tier(estimate.mu, asked_tiers)
            return _ask(
                execution_question(sport, tier), f"demonstration-{tier}", estimate
            )

        tactical_asked = [
            entry for entry in transcript if entry.question_id in TACTICAL_QUESTION_IDS
        ]
        if not tactical_asked:
            return _ask(tactical_question(sport, 0), "tactical", estimate)

        # Minimums satisfied, so the two sides can now be compared. A gap beyond
        # tolerance earns one question at the level the *claims* imply: if the
        # player can do the thing their claims imply, the claims were right, and
        # if not, they were not. ``tie_breaker_at`` is the position it is asked
        # at, so an earlier position means it has been asked already and this
        # transcript does not get a second one.
        if tie_breaker_at == len(transcript):
            sides = _contradiction(_evidence_points(transcript))
            assert sides is not None  # a tie-breaker is due only with both sides
            tie_breaker_tier = _tie_breaker_tier(sides, asked_tiers)
            assert tie_breaker_tier is not None  # and with that tier unasked
            return _ask(
                execution_question(sport, tie_breaker_tier),
                TIE_BREAKER_REASON,
                estimate,
            )

        # Extreme-answer bracketing next: a last demonstration
        # at an end of the scale earns another at the tier the estimate now implies.
        if _last_demonstration_was_extreme(transcript):
            bracket = _bracketing_demonstration(
                sport, estimate, asked_tiers, tactical_asked
            )
            if bracket is not None:
                question, reason = bracket
                return _ask(question, reason, estimate)

        # Otherwise stop as soon as the best remaining question would not tighten
        # the floored estimate meaningfully.
        gain, candidate = _best_marginal_candidate(
            sport, estimate, asked_tiers, tactical_asked
        )
        if candidate is not None and gain >= MIN_MARGINAL_GAIN:
            question, reason = candidate
            return _ask(question, reason, estimate)
        return Complete(reason=STOP_MARGINAL, value=round(gain, 4))

    def finalize(self, *, sport: Sport, transcript: Transcript) -> AssessmentResult:
        points = _evidence_points(transcript)

        # A disagreement the tie-breaker did not settle resolves without a
        # direction: the claims — the softer evidence — keep only part of their
        # precision, and by exactly as much whichever side is the higher one.
        # Nobody is moved up, moved down, or accused.
        contradiction = _contradiction(points)
        claim_weight = CLAIM_PRECISION_RETAINED if contradiction is not None else 1.0
        layoff = _layoff_penalty(transcript)
        estimate = _fuse_points(points, layoff=layoff, claim_weight=claim_weight)

        # The floor first: "we kept your starting range wider" is a statement
        # about the range the player would otherwise have left with.
        sigma = max(estimate.sigma, SIGMA_FLOOR)
        wideners: list[UncertaintyFactor] = []

        # What the layoff actually cost, measured against the same transcript
        # without it. A short break disappears into the floor, and a widener that
        # widened nothing is not reported.
        if layoff > 0.0:
            unaffected = _fuse_points(points, layoff=0.0, claim_weight=claim_weight)
            _record_widener(
                wideners,
                UNCERTAINTY_TIME_AWAY,
                sigma - max(unaffected.sigma, SIGMA_FLOOR),
            )

        dispersion = _dispersion_sigma(points)
        if dispersion > 0.0:
            widened = combine_sigma(sigma, dispersion)
            _record_widener(wideners, UNCERTAINTY_UNEVEN_PROFILE, widened - sigma)
            sigma = widened

        calibration_priority = CALIBRATION_PRIORITY_STANDARD
        if contradiction is not None:
            widened = combine_sigma(sigma, _contradiction_sigma(contradiction.gap))
            _record_widener(wideners, UNCERTAINTY_ANSWERS_DISAGREED, widened - sigma)
            sigma = widened
            calibration_priority = CALIBRATION_PRIORITY_ELEVATED

        mu = clamp_to_scale(estimate.mu)
        low, high = likely_range(mu, sigma)
        band = band_for(mu)
        return AssessmentResult(
            mu=round(mu, 2),
            sigma=round(sigma, 4),
            confidence=confidence_percent(sigma),
            range_low=round(low, 2),
            range_high=round(high, 2),
            band=BandView(name=band.label, lower=band.lower, upper=band.upper),
            status=RESULT_STATUS,
            questions_asked=len(transcript),
            engine_version=ENGINE_VERSION,
            calibration_priority=calibration_priority,
            confidence_reason=_confidence_reason(wideners),
            # Compared against the *reported* Level, so a row can never contradict
            # the two numbers printed either side of it.
            factors=_factors(points, round(mu, 2)),
            uncertainty_factors=tuple(wideners),
        )


# --- Routing helpers -----------------------------------------------------------


def _ask(question: Question, reason: str, estimate: SkillEstimate) -> AskQuestion:
    """An ``AskQuestion`` carrying the reason and the estimate at this moment."""

    return AskQuestion(
        question=question,
        reason=reason,
        mu=round(clamp_to_scale(estimate.mu), 4),
        sigma=round(estimate.sigma, 4),
    )


def _answer_for(transcript: Transcript, question_id: str) -> str | None:
    for entry in transcript:
        if entry.question_id == question_id:
            return entry.option_id
    return None


def _asked_execution_tiers(transcript: Transcript) -> set[str]:
    ids_to_tier = {qid: tier for tier, qid in EXECUTION_QUESTION_IDS.items()}
    return {
        ids_to_tier[entry.question_id]
        for entry in transcript
        if entry.question_id in ids_to_tier
    }


def _required_demonstrations(estimate: SkillEstimate) -> int:
    return 3 if estimate.mu >= ESTABLISHED_FLOOR else 2


def _target_tier(mu: float) -> str:
    if mu < 2.5:
        return TIERS[0]  # basic
    if mu < 3.5:
        return TIERS[1]  # standard
    return TIERS[2]  # discriminating


def _next_execution_tier(mu: float, asked: set[str]) -> str:
    """The unasked tier nearest ``mu``'s target, tie-broken toward the lower.

    Tie-breaking toward the lower tier is what keeps a developing player off a
    discriminating question when their target tier is already spent. The caller
    chooses whose level to pitch at: the running estimate normally, the fused
    *claims* for a tie-breaker.
    """

    target = TIERS.index(_target_tier(mu))
    candidates = [tier for tier in TIERS if tier not in asked]

    def distance(tier: str) -> tuple[int, int]:
        index = TIERS.index(tier)
        return abs(index - target), index

    return min(candidates, key=distance)


def _last_demonstration_was_extreme(transcript: Transcript) -> bool:
    """Whether the most recent demonstration landed at an end of the scale.

    A demonstration is an execution or tactical answer — what happens inside a
    point. Claims (regularity, volume, competitive context) are not demonstrations
    and never trigger bracketing.
    """

    for entry in reversed(transcript):
        if tier_for_execution_id(entry.question_id) is not None:
            return is_extreme_execution(entry.option_id)
        if entry.question_id in TACTICAL_QUESTION_IDS:
            return is_extreme_tactical(entry.option_id)
    return False


def _bracketing_demonstration(
    sport: Sport,
    estimate: SkillEstimate,
    asked_tiers: set[str],
    tactical_asked: list[AnsweredQuestion],
) -> tuple[Question, str] | None:
    """The next demonstration to bracket an extreme answer, or ``None`` if spent.

    An unasked execution tier nearest the implied level comes first — that is the
    "at the tier the updated estimate implies" the specification asks for — then a
    remaining tactical question, which is a demonstration too.
    """

    if len(asked_tiers) < len(TIERS):
        tier = _next_execution_tier(estimate.mu, asked_tiers)
        return execution_question(sport, tier), f"extreme-bracketing-{tier}"
    index = _next_tactical_index(tactical_asked)
    if index is not None:
        return tactical_question(sport, index), "extreme-bracketing-tactical"
    return None


def _next_tactical_index(tactical_asked: list[AnsweredQuestion]) -> int | None:
    asked_ids = {entry.question_id for entry in tactical_asked}
    for index, question_id in enumerate(TACTICAL_QUESTION_IDS):
        if question_id not in asked_ids:
            return index
    return None


def _best_marginal_candidate(
    sport: Sport,
    estimate: SkillEstimate,
    asked_tiers: set[str],
    tactical_asked: list[AnsweredQuestion],
) -> tuple[float, tuple[Question, str] | None]:
    """The remaining demonstration that would tighten the estimate most, and by how.

    Each candidate's gain is projected as if it were answered exactly at the
    current estimate, measured against the σ floor: once the estimate has reached
    the floor, no question can improve the result it produces, so the best gain is
    zero and the caller stops.
    """

    best_gain = 0.0
    best: tuple[Question, str] | None = None
    for tier in TIERS:
        if tier in asked_tiers:
            continue
        sigma = execution_sigma(tier)
        assert sigma is not None
        gain = _projected_gain(estimate.sigma, sigma)
        if gain > best_gain:
            best_gain, best = gain, (execution_question(sport, tier), "marginal-value")
    index = _next_tactical_index(tactical_asked)
    if index is not None:
        gain = _projected_gain(estimate.sigma, tactical_sigma())
        if gain > best_gain:
            best_gain = gain
            best = (tactical_question(sport, index), "marginal-value")
    return best_gain, best


def _projected_gain(current_sigma: float, candidate_sigma: float) -> float:
    """How much one more answer of ``candidate_sigma`` tightens the floored σ."""

    biased = combine_sigma(candidate_sigma, SELF_REPORT_BIAS)
    precision = 1.0 / (current_sigma**2) + 1.0 / (biased**2)
    projected = (1.0 / precision) ** 0.5
    return max(current_sigma, SIGMA_FLOOR) - max(projected, SIGMA_FLOOR)


# --- Fusion --------------------------------------------------------------------


@dataclass(frozen=True)
class _Evidence:
    """One μ-moving answer: what it is a statement about, and what it encodes to.

    Both the kind and the category are read off the question, never off the
    answer, so neither the claim / demonstration split nor the factor rows can
    drift with the copy.
    """

    kind: str
    category: str
    estimate: SkillEstimate


def _biased(raw: tuple[float, float] | None, entry: AnsweredQuestion) -> SkillEstimate:
    if raw is None:
        raise UnknownAnswer(f"{entry.question_id}/{entry.option_id} is not a v3 answer")
    mu, sigma = raw
    return SkillEstimate(mu=mu, sigma=combine_sigma(sigma, SELF_REPORT_BIAS))


def _point(entry: AnsweredQuestion, raw: tuple[float, float] | None) -> _Evidence:
    kind = kind_for(entry.question_id)
    category = factor_for(entry.question_id)
    # The caller has already matched a known, μ-moving question id.
    assert kind is not None and category is not None
    return _Evidence(kind=kind, category=category, estimate=_biased(raw, entry))


def _fuse_estimates(estimates: list[SkillEstimate]) -> SkillEstimate:
    """Inverse-variance fusion of a set of estimates, with no prior."""

    precision = sum(1.0 / (estimate.sigma**2) for estimate in estimates)
    weighted_mu = sum(estimate.mu / (estimate.sigma**2) for estimate in estimates)
    return SkillEstimate(mu=weighted_mu / precision, sigma=(1.0 / precision) ** 0.5)


def _evidence_points(transcript: Transcript) -> list[_Evidence]:
    """The μ-moving evidence in a transcript. Layoff is excluded — it is σ-only."""

    points: list[_Evidence] = []
    environment_option: str | None = None
    relative_option: str | None = None

    for entry in transcript:
        qid = entry.question_id
        if qid == OPENING_QUESTION_ID:
            points.append(_point(entry, regularity_evidence(entry.option_id)))
        elif qid == VOLUME_QUESTION_ID:
            points.append(_point(entry, volume_evidence(entry.option_id)))
        elif qid == ENVIRONMENT_QUESTION_ID:
            environment_option = entry.option_id
        elif qid == RELATIVE_QUESTION_ID:
            relative_option = entry.option_id
        elif qid == LAYOFF_QUESTION_ID:
            if layoff_sigma(entry.option_id) is None:
                raise UnknownAnswer(f"{qid}/{entry.option_id} is not a v3 answer")
            # σ only — folded in after fusion, never into μ.
        elif (tier := tier_for_execution_id(qid)) is not None:
            points.append(_point(entry, execution_evidence(tier, entry.option_id)))
        elif qid in TACTICAL_QUESTION_IDS:
            points.append(_point(entry, tactical_evidence(entry.option_id)))
        else:
            raise UnknownAnswer(f"{qid}/{entry.option_id} is not a v3 answer")

    context = _competitive_context(environment_option, relative_option)
    if context is not None:
        # Where you play and how you do there is a statement about standing. The
        # two questions fuse into one point, so they are also one factor row.
        points.append(
            _Evidence(
                kind=KIND_CLAIM,
                category=FACTOR_COMPETITIVE_CONTEXT,
                estimate=context,
            )
        )
    return points


def _competitive_context(
    environment_option: str | None, relative_option: str | None
) -> SkillEstimate | None:
    """Environment fused with relative performance as an offset, never a level.

    Relative performance shifts the environment's μ and, when present, widens the
    band to the widest in the bank — because winning most of your matches means
    something completely different in two different clubs.
    """

    if environment_option is None:
        if relative_option is not None:
            raise UnknownAnswer("relative performance without an environment answer")
        return None
    base = environment_evidence(environment_option)
    if base is None:
        raise UnknownAnswer(f"{ENVIRONMENT_QUESTION_ID}/{environment_option}")
    env_mu, env_sigma = base
    if relative_option is None:
        return SkillEstimate(env_mu, combine_sigma(env_sigma, SELF_REPORT_BIAS))
    offset = relative_offset(relative_option)
    if offset is None:
        raise UnknownAnswer(f"{RELATIVE_QUESTION_ID}/{relative_option}")
    sigma = combine_sigma(RELATIVE_SIGMA, SELF_REPORT_BIAS)
    return SkillEstimate(env_mu + offset, sigma)


def _layoff_penalty(transcript: Transcript) -> float:
    penalty = 0.0
    for entry in transcript:
        if entry.question_id == LAYOFF_QUESTION_ID:
            sigma = layoff_sigma(entry.option_id)
            if sigma is None:
                raise UnknownAnswer(f"{entry.question_id}/{entry.option_id}")
            penalty = sigma
    return penalty


def _fuse(transcript: Transcript) -> SkillEstimate:
    """The running estimate: every answer at full weight.

    Routing reads this one, so a contradiction's resolution — which ``finalize``
    applies — can never widen σ into extra questions. Routing already has its own
    answer to a disagreement, and that is the tie-breaker.
    """

    return _fuse_points(
        _evidence_points(transcript), layoff=_layoff_penalty(transcript)
    )


def _fuse_points(
    points: list[_Evidence], *, layoff: float, claim_weight: float = 1.0
) -> SkillEstimate:
    """Inverse-variance fusion of the prior and every μ-moving answer.

    A layoff widens σ afterwards and leaves μ untouched, so a player who was good
    two years ago is not assumed to have got worse without evidence.
    ``claim_weight`` is the share of its precision each claim keeps: the whole of
    it normally, part of it when the tie-breaker did not settle a disagreement.
    """

    precision = 1.0 / (POPULATION_PRIOR.sigma**2)
    weighted_mu = POPULATION_PRIOR.mu * precision
    for point in points:
        weight = claim_weight if point.kind == KIND_CLAIM else 1.0
        p = weight / (point.estimate.sigma**2)
        precision += p
        weighted_mu += point.estimate.mu * p
    mu = weighted_mu / precision
    sigma = (1.0 / precision) ** 0.5

    if layoff > 0.0:
        sigma = combine_sigma(sigma, layoff)
    return SkillEstimate(mu=mu, sigma=sigma)


# --- Contradiction: the two sides, the tie-breaker, the resolution -------------


@dataclass(frozen=True)
class _Sides:
    """The two sides of the comparison, each fused on its own evidence alone.

    The population prior is deliberately left out of both: pulling the claims and
    the demonstrations toward the average would hide exactly the disagreement the
    check exists to find.
    """

    claims: SkillEstimate
    demonstrations: SkillEstimate

    @property
    def gap(self) -> float:
        """How far apart the two sides are, in level units and without a sign.

        Unsigned because the resolution has no direction: a player who claims
        more than they demonstrate and one who demonstrates more than they claim
        are the same amount of disagreement, and cost the same.
        """

        return abs(self.claims.mu - self.demonstrations.mu)


def _sides(points: list[_Evidence]) -> _Sides | None:
    """The fused claims and demonstrations, or ``None`` without both sides.

    One demonstration is a data point rather than a side, so the comparison waits
    for ``MIN_DEMONSTRATIONS_COMPARED`` — which the routing minimums guarantee.
    """

    claims = [point.estimate for point in points if point.kind == KIND_CLAIM]
    demonstrations = [
        point.estimate for point in points if point.kind == KIND_DEMONSTRATION
    ]
    if not claims or len(demonstrations) < MIN_DEMONSTRATIONS_COMPARED:
        return None
    return _Sides(
        claims=_fuse_estimates(claims),
        demonstrations=_fuse_estimates(demonstrations),
    )


def _contradiction(points: list[_Evidence]) -> _Sides | None:
    """The two sides when they genuinely disagree, or ``None`` when they do not.

    Below the tolerance the two are read as one uneven profile, which earns a
    wider band through dispersion rather than an accusation.
    """

    sides = _sides(points)
    if sides is None or sides.gap <= CONTRADICTION_TOLERANCE:
        return None
    return sides


def _minimums_met(transcript: Transcript) -> bool:
    """Whether the hard-minimum phase of the routing sequence is complete.

    The same conditions the sequence checks, read off a transcript rather than
    driven from one — which is what lets the engine locate the tie-breaker in a
    replayed transcript without holding any state between calls.
    """

    answered = {entry.question_id for entry in transcript}
    if ENVIRONMENT_QUESTION_ID not in answered or RELATIVE_QUESTION_ID not in answered:
        return False
    if not any(qid in answered for qid in TACTICAL_QUESTION_IDS):
        return False
    return len(_asked_execution_tiers(transcript)) >= _required_demonstrations(
        _fuse(transcript)
    )


def _tie_breaker_tier(sides: _Sides, asked_tiers: set[str]) -> str | None:
    """The tier a tie-breaker would be asked at, or ``None`` when there is none.

    Exactly the tier the *claims* imply, and nothing else: an easier question
    does not test the claim, and a harder one tests something the claim never
    made. When that question has already been answered the claims have been
    tested at their own level already, so no extra question is earned and the
    disagreement goes to ``finalize`` unaided.
    """

    tier = _target_tier(sides.claims.mu)
    return None if tier in asked_tiers else tier


def _tie_breaker_at(transcript: Transcript) -> int | None:
    """The position the tie-breaker is (or was) asked at, or ``None`` for never.

    The first position at which the minimums were met, the two sides disagreed,
    and the claims' own tier was still unasked. Returning the *first* such
    position is what makes the tie-breaker at most one question: a position
    earlier than the transcript's end means it has been asked already, whether or
    not the disagreement survived it.
    """

    for index in range(len(transcript) + 1):
        prefix = transcript[:index]
        if not _minimums_met(prefix):
            continue
        sides = _contradiction(_evidence_points(prefix))
        if sides is None:
            continue
        if _tie_breaker_tier(sides, _asked_execution_tiers(prefix)) is not None:
            return index
    return None


def _contradiction_sigma(gap: float) -> float:
    """The σ an unresolved disagreement adds, in proportion to its size."""

    return min(CONTRADICTION_SIGMA_MAX, CONTRADICTION_SIGMA_PER_LEVEL * gap)


def _dispersion_sigma(points: list[_Evidence]) -> float:
    """The σ an uneven profile adds: how far the demonstrations scatter.

    A strong smash and a weak backhand is an uneven game, not a lie. It widens
    the band and is never reported as a disagreement — the tolerance absorbs the
    scatter every honest answer set carries.
    """

    demonstrations = [
        point.estimate for point in points if point.kind == KIND_DEMONSTRATION
    ]
    if len(demonstrations) < MIN_DEMONSTRATIONS_COMPARED:
        return 0.0
    fused = _fuse_estimates(demonstrations)
    total_weight = sum(1.0 / (estimate.sigma**2) for estimate in demonstrations)
    variance = (
        sum(
            (estimate.mu - fused.mu) ** 2 / (estimate.sigma**2)
            for estimate in demonstrations
        )
        / total_weight
    )
    return min(DISPERSION_SIGMA_MAX, max(0.0, variance**0.5 - DISPERSION_TOLERANCE))


# --- The explanation: factor rows, uncertainty rows, the confidence reason -----


def _factors(points: list[_Evidence], mu: float) -> tuple[ResultFactor, ...]:
    """One row per evidence category the player actually answered.

    Each category is fused on its **own evidence alone** — deliberately without
    the population prior, which would pull every category toward the average and
    flatten the very differences the rows exist to show — and its level is
    compared against the final estimate. The direction therefore falls out of the
    arithmetic: retune a constant in the bank and the arrows move with it, with
    no copy edited anywhere.

    Both sides of the comparison are the values the player is actually shown, so
    a row saying "up" always sits above the Level printed beside it.
    """

    rows: list[ResultFactor] = []
    for key in FACTOR_KEYS:
        estimates = [point.estimate for point in points if point.category == key]
        if not estimates:
            continue
        level = round(_fuse_estimates(estimates).mu, 2)
        rows.append(
            ResultFactor(
                key=key,
                label=FACTOR_LABELS[key],
                direction=_direction(level, mu),
                level=level,
            )
        )
    return tuple(rows)


def _direction(level: float, mu: float) -> str:
    """Where one category sits relative to the estimate the player is given."""

    difference = level - mu
    if difference > FACTOR_DIRECTION_TOLERANCE:
        return FACTOR_DIRECTION_UP
    if difference < -FACTOR_DIRECTION_TOLERANCE:
        return FACTOR_DIRECTION_DOWN
    return FACTOR_DIRECTION_NEUTRAL


def _record_widener(
    wideners: list[UncertaintyFactor], key: str, sigma_added: float
) -> None:
    """Record a widener, but only once it has actually widened something.

    The σ floor absorbs a small contribution entirely, and a row claiming credit
    for a range it did not change is the explanation drifting from the numbers.
    """

    added = round(sigma_added, SIGMA_REPORTING_DIGITS)
    if added <= 0.0:
        return
    wideners.append(
        UncertaintyFactor(
            key=key,
            label=UNCERTAINTY_LABELS[key],
            detail=UNCERTAINTY_DETAILS[key],
            sigma_added=added,
        )
    )


def _confidence_reason(wideners: list[UncertaintyFactor]) -> ConfidenceReason:
    """The branch the situation that actually produced it belongs to.

    Whichever widener contributed the most σ authors the sentence, so the reason
    is chosen by the arithmetic rather than by an authored precedence list. With
    nothing having widened beyond the floor, the base case every onboarding
    rating shares applies: we have not seen the player play yet.
    """

    candidates = [
        widener for widener in wideners if widener.key in CONFIDENCE_AUTHORING_WIDENERS
    ]
    key = (
        max(candidates, key=lambda widener: widener.sigma_added).key
        if candidates
        else CONFIDENCE_REASON_LIMITED_EVIDENCE
    )
    return ConfidenceReason(key=key, sentence=CONFIDENCE_SENTENCES[key])
