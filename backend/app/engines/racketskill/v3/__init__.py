"""RacketSkill Fusion, version 3.

This version carries the full question bank for all four sports — regularity,
volume, layoff, competitive context, three execution tiers and two tactical
questions — routed adaptively, together with inverse-variance fusion against the
population prior, the confidence ceiling and finalisation. Stopping is the hard
ceiling only; marginal-value stopping and contradiction detection arrive in later
slices. Because a version is a directory that is never deleted, they extend this
one rather than replacing it.
"""

from app.engines.racketskill.v3.engine import ENGINE_VERSION, RacketSkillEngineV3

__all__ = ["ENGINE_VERSION", "RacketSkillEngineV3"]
