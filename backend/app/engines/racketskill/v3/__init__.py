"""RacketSkill Fusion, version 3.

This slice carries only the opening regularity question, the evidence encoder,
inverse-variance fusion against the population prior, the confidence ceiling and
finalisation — the tracer bullet that takes "I have never played" to a stored
rating. The question bank and adaptive routing (technique tiers, tactical
questions, layoff, marginal-value stopping) arrive in later slices; because a
version is a directory that is never deleted, they extend this one rather than
replacing it.
"""

from app.engines.racketskill.v3.engine import ENGINE_VERSION, RacketSkillEngineV3

__all__ = ["ENGINE_VERSION", "RacketSkillEngineV3"]
