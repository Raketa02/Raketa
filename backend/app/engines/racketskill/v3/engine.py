"""RacketSkill Fusion v3 — inverse-variance fusion and finalisation.

The engine is pure: ``next_step`` and ``finalize`` are functions of the
transcript alone. The beginner fast path is enforced *here*, never by the
client, because somebody who has never held a racket cannot report on getting a
ball back off the wall — and whatever they tapped would enter the fusion looking
exactly like evidence.
"""

from __future__ import annotations

from app.engines.assessment import (
    AnsweredQuestion,
    AskQuestion,
    AssessmentResult,
    BandView,
    Complete,
    Step,
    Transcript,
)
from app.engines.racketskill.core import (
    CONFIDENCE_SIGMA_CEILING,
    SkillEstimate,
    band_for,
    clamp_to_scale,
    combine_sigma,
    confidence_percent,
    likely_range,
)
from app.engines.racketskill.v3.questions import (
    NEVER_PLAYED_OPTION_ID,
    OPENING_QUESTION_ID,
    opening_question,
    raw_evidence_for,
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
        if (
            opening.question_id == OPENING_QUESTION_ID
            and opening.option_id == NEVER_PLAYED_OPTION_ID
        ):
            return Complete()

        # v3 carries only the opening question; adaptive routing (technique
        # tiers, tactical questions, layoff, marginal-value stopping) lands with
        # the question bank. Until then a single answer finalises.
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


def _encode(answered: AnsweredQuestion) -> SkillEstimate:
    raw = raw_evidence_for(answered)
    if raw is None:
        raise UnknownAnswer(
            f"{answered.question_id}/{answered.option_id} is not a v3 answer"
        )
    mu, sigma = raw
    return SkillEstimate(mu=mu, sigma=combine_sigma(sigma, SELF_REPORT_BIAS))


def _fuse(transcript: Transcript) -> SkillEstimate:
    """Inverse-variance fusion of the population prior and every answer."""

    precision = 1.0 / (POPULATION_PRIOR.sigma**2)
    weighted_mu = POPULATION_PRIOR.mu * precision
    for answered in transcript:
        evidence = _encode(answered)
        p = 1.0 / (evidence.sigma**2)
        precision += p
        weighted_mu += evidence.mu * p
    return SkillEstimate(mu=weighted_mu / precision, sigma=(1.0 / precision) ** 0.5)
