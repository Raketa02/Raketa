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

Stopping in this slice is the **hard ceiling only**; marginal-value stopping
arrives separately. Layoff widens uncertainty and never touches the estimate.
"""

from __future__ import annotations

from app.engines.assessment import (
    AnsweredQuestion,
    AskQuestion,
    AssessmentResult,
    BandView,
    Complete,
    Question,
    Step,
    Transcript,
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
    HISTORY_REGULARITY_OPTIONS,
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
    layoff_question,
    layoff_sigma,
    opening_question,
    regularity_evidence,
    relative_offset,
    relative_question,
    tactical_evidence,
    tactical_question,
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
            return Complete()

        # The hard ceiling. The sequence below never reaches it, but the guard
        # makes "never exceeds the ceiling under any answer pattern" unmissable.
        if len(transcript) >= MAX_QUESTIONS:
            return Complete()

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

        # Execution demonstrations: a minimum that scales with the estimate, each
        # at the tier the running estimate implies.
        asked_tiers = _asked_execution_tiers(transcript)
        if len(asked_tiers) < _required_demonstrations(estimate):
            tier = _next_execution_tier(estimate, asked_tiers)
            return _ask(
                execution_question(sport, tier), f"demonstration-{tier}", estimate
            )

        # One tactical answer.
        if not any(entry.question_id in TACTICAL_QUESTION_IDS for entry in transcript):
            return _ask(tactical_question(sport, 0), "tactical", estimate)

        return Complete()

    def finalize(self, *, sport: Sport, transcript: Transcript) -> AssessmentResult:
        estimate = _fuse(transcript)
        sigma = max(estimate.sigma, SIGMA_FLOOR)
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


def _next_execution_tier(estimate: SkillEstimate, asked: set[str]) -> str:
    """The unasked tier nearest the estimate's target, tie-broken toward the lower.

    Tie-breaking toward the lower tier is what keeps a developing player off a
    discriminating question when their target tier is already spent.
    """

    target = TIERS.index(_target_tier(estimate.mu))
    candidates = [tier for tier in TIERS if tier not in asked]

    def distance(tier: str) -> tuple[int, int]:
        index = TIERS.index(tier)
        return abs(index - target), index

    return min(candidates, key=distance)


# --- Fusion --------------------------------------------------------------------


def _biased(
    raw: tuple[float, float] | None, entry: AnsweredQuestion
) -> SkillEstimate:
    if raw is None:
        raise UnknownAnswer(f"{entry.question_id}/{entry.option_id} is not a v3 answer")
    mu, sigma = raw
    return SkillEstimate(mu=mu, sigma=combine_sigma(sigma, SELF_REPORT_BIAS))


def _evidence_points(transcript: Transcript) -> list[SkillEstimate]:
    """The μ-moving evidence in a transcript. Layoff is excluded — it is σ-only."""

    points: list[SkillEstimate] = []
    environment_option: str | None = None
    relative_option: str | None = None

    for entry in transcript:
        qid = entry.question_id
        if qid == OPENING_QUESTION_ID:
            points.append(_biased(regularity_evidence(entry.option_id), entry))
        elif qid == VOLUME_QUESTION_ID:
            points.append(_biased(volume_evidence(entry.option_id), entry))
        elif qid == ENVIRONMENT_QUESTION_ID:
            environment_option = entry.option_id
        elif qid == RELATIVE_QUESTION_ID:
            relative_option = entry.option_id
        elif qid == LAYOFF_QUESTION_ID:
            if layoff_sigma(entry.option_id) is None:
                raise UnknownAnswer(f"{qid}/{entry.option_id} is not a v3 answer")
            # σ only — folded in after fusion, never into μ.
        elif (tier := tier_for_execution_id(qid)) is not None:
            points.append(_biased(execution_evidence(tier, entry.option_id), entry))
        elif qid in TACTICAL_QUESTION_IDS:
            points.append(_biased(tactical_evidence(entry.option_id), entry))
        else:
            raise UnknownAnswer(f"{qid}/{entry.option_id} is not a v3 answer")

    context = _competitive_context(environment_option, relative_option)
    if context is not None:
        points.append(context)
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
    """Inverse-variance fusion of the prior and every μ-moving answer.

    A layoff widens σ afterwards and leaves μ untouched, so a player who was good
    two years ago is not assumed to have got worse without evidence.
    """

    precision = 1.0 / (POPULATION_PRIOR.sigma**2)
    weighted_mu = POPULATION_PRIOR.mu * precision
    for evidence in _evidence_points(transcript):
        p = 1.0 / (evidence.sigma**2)
        precision += p
        weighted_mu += evidence.mu * p
    mu = weighted_mu / precision
    sigma = (1.0 / precision) ** 0.5

    layoff = _layoff_penalty(transcript)
    if layoff > 0.0:
        sigma = combine_sigma(sigma, layoff)
    return SkillEstimate(mu=mu, sigma=sigma)
