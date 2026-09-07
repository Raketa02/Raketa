"""The RacketSkill engines — one that opens a rating, one that tests it.

``core`` holds everything that must outlive an engine version — the 1,0–5,0 scale,
the four bands, the confidence transform, the three status words and the
σ-combination rule — so the two versioned engines here cannot develop two
definitions of uncertainty.

**Two versioned engines, and they are versioned apart because they are retuned
apart.** ``v3`` is the questionnaire that opens a rating; ``update_v1`` is the
rule that tests one against a confirmed result (``docs/adr/0139``). A rating
carries the stamp of whichever last wrote it.

Each shipped version is a directory that is never deleted: a version's question
definitions *are* the code that asked them, and a version's constants are what
the ratings attributed to it were computed from.
"""
