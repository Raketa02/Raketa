"""The Match Fit scorer, version 1 — its stamp, ahead of its arithmetic.

``ENGINE_VERSION`` exists before the pipeline does because it is half of what
rides on every result, and because a stamp introduced later would leave the
searches recorded in between unable to say which maths produced them.
"""

from __future__ import annotations

#: The stamp every result carries beside its ruleset version. It follows
#: RacketSkill's spelling — a name and a version, so that a stamp read out of a
#: stored row says which engine as well as which version of it.
ENGINE_VERSION = "matchfit-v1"
