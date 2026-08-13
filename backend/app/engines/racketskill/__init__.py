"""The RacketSkill assessment engine.

``core`` holds everything that must outlive an engine version — the 1,0–5,0 scale,
the four bands, the confidence transform and the σ-combination rule — so onboarding
and the later match-update engine cannot develop two definitions of uncertainty.
Each shipped version (``v3`` today) is a directory that is never deleted, because a
version's question definitions *are* the code that asked them.
"""
