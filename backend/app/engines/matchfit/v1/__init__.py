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
fence, where the I/O is. ``modifiers``, ``floor`` and ``liveness`` are stages 4,
5 and 6 — the nudge, the bar and the reordering — and ``group`` is the objective
that seats four people, which extended this directory rather than replacing it.

**``group`` calls the same functions ``terms`` does and defines none of its own.**
A cross reading is Fit's own person-to-person sub-score renormalised over the
same three weights, read off the same matrix rows through the same seat scope —
so *how do these two get on* has one implementation, called six times in a four.
That is what ``docs/adr/0117``'s admissibility rule buys: a group term reads
something no seat's Fit read, and it reads it with Fit's own arithmetic.
"""

from app.engines.matchfit.v1.engine import ENGINE_VERSION
from app.engines.matchfit.v1.fit import MatchFitV1, renormalised_weights, score
from app.engines.matchfit.v1.floor import Admission, Refusal, admits, live_terms
from app.engines.matchfit.v1.group import (
    CROSS_TERMS,
    arrange,
    arrangements,
    best,
    cross_reading,
    deciding_reason,
    evenest,
    forecast,
    group_availability,
    objective,
    seat_delta,
)
from app.engines.matchfit.v1.liveness import (
    challenge_load,
    read_signals,
    reciprocal_asymmetry,
    reverse_mode,
)
from app.engines.matchfit.v1.modifiers import (
    ModifierOutcome,
    absorbed,
    calibration_value,
    familiarity,
    modify,
    reading_for,
    reliability_floor_breach,
    strength_of,
    welcoming_record,
)
from app.engines.matchfit.v1.terms import (
    TagColumnReading,
    TermOutcome,
    TermReading,
    availability_overlap,
    balance_norm,
    clamp_unit,
    diminishing,
    diminishing_at_strengths,
    distance,
    forecast_pct,
    intent_alignment,
    level_fit,
    playing_style,
    predicted_balance,
    read_terms,
    reliability,
    social_vibe,
    tag_column,
)

__all__ = [
    "CROSS_TERMS",
    "ENGINE_VERSION",
    "Admission",
    "MatchFitV1",
    "ModifierOutcome",
    "Refusal",
    "TagColumnReading",
    "TermOutcome",
    "TermReading",
    "absorbed",
    "admits",
    "arrange",
    "arrangements",
    "availability_overlap",
    "balance_norm",
    "best",
    "calibration_value",
    "challenge_load",
    "clamp_unit",
    "cross_reading",
    "deciding_reason",
    "diminishing",
    "diminishing_at_strengths",
    "distance",
    "evenest",
    "familiarity",
    "forecast",
    "forecast_pct",
    "group_availability",
    "intent_alignment",
    "level_fit",
    "live_terms",
    "modify",
    "objective",
    "playing_style",
    "predicted_balance",
    "read_signals",
    "read_terms",
    "reading_for",
    "reciprocal_asymmetry",
    "reliability",
    "reliability_floor_breach",
    "renormalised_weights",
    "reverse_mode",
    "score",
    "seat_delta",
    "social_vibe",
    "strength_of",
    "tag_column",
    "welcoming_record",
]
