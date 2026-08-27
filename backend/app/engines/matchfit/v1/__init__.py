"""Match Fit, version 1.

**A version is a directory that is never deleted**, because the maths a result
was computed with has to stay readable for as long as that result is
explainable — and a past search is explainable forever (``docs/adr/0118``). A
term computed differently is a new directory beside this one, never an edit here.

**The engine version is not the ruleset version.** This stamp says *how the maths
works*; the ruleset stamp says *what the numbers were*. Moving a weight leaves
this string untouched, which is the whole point of there being two.

This version carries the vocabulary and the version stamp. The pipeline itself —
the gates, the eight terms, the modifiers, the floor, Liveness and the group
objective — lands in the tickets that follow, extending this directory rather
than replacing it.
"""

from app.engines.matchfit.v1.engine import ENGINE_VERSION

__all__ = ["ENGINE_VERSION"]
