"""Match Fit, version 1.

**A version is a directory that is never deleted**, because the maths a result
was computed with has to stay readable for as long as that result is
explainable — and a past search is explainable forever (``docs/adr/0118``). A
term computed differently is a new directory beside this one, never an edit here.

**The engine version is not the ruleset version.** This stamp says *how the maths
works*; the ruleset stamp says *what the numbers were*. Moving a weight leaves
this string untouched, which is the whole point of there being two.

**This directory is the arithmetic and nothing else.** ``terms`` is the eight
readings; ``fit`` renormalises them into the one printed number and wraps it as
``MatchFitV1``, the ``MatchFit`` Protocol's first implementation. Every *shape* —
what crosses the privacy fence, the closed evidence union, the ``Fit`` that comes
back — lives one directory up, because those outlive a version and a module
depends on the abstraction rather than on this directory's name
(``docs/adr/0015``).

The gates and candidate generation are the module's, on the other side of the
fence, where the I/O is. The modifiers, Liveness, the floor and the group
objective land in the tickets that follow, extending this directory rather than
replacing it.
"""

from app.engines.matchfit.v1.engine import ENGINE_VERSION
from app.engines.matchfit.v1.fit import MatchFitV1, renormalised_weights, score
from app.engines.matchfit.v1.terms import (
    TermOutcome,
    TermReading,
    availability_overlap,
    diminishing,
    diminishing_at_strengths,
    distance,
    intent_alignment,
    level_fit,
    playing_style,
    predicted_balance,
    read_terms,
    reliability,
    social_vibe,
)

__all__ = [
    "ENGINE_VERSION",
    "MatchFitV1",
    "TermOutcome",
    "TermReading",
    "availability_overlap",
    "diminishing",
    "diminishing_at_strengths",
    "distance",
    "intent_alignment",
    "level_fit",
    "playing_style",
    "predicted_balance",
    "read_terms",
    "reliability",
    "renormalised_weights",
    "score",
    "social_vibe",
]
