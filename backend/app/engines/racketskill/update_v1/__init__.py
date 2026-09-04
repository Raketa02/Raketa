"""The RacketSkill result-update rule, version 1.

**A version is a directory** (``docs/adr/0015``), and this is the second one
here: ``v3`` is the questionnaire that opens a rating, and this is the rule that
tests one. They are versioned apart because they are retuned apart — an
onboarding constant and a K-factor answer different questions and are falsified
by different measurements — and a rating that has been moved by results therefore
carries **this** stamp rather than the questionnaire's.

Its constants live inside it for the reason every version's do: retuning one in
place would silently change what ``racketskill-result-update-v1`` means on
``RatingMovedOnResult`` rows already in the store, and a constant you cannot
attribute a rating back to is one no measurement can falsify. A retune that is
meant to apply to history does not exist; a retune that is not is a ``v2``
directory beside this one.

What outlives both versions is in ``racketskill/core.py`` — the 1,0–5,0 scale,
the four bands, the confidence transform, the three status words and the
σ-combination rule — so onboarding and this rule cannot develop two definitions
of uncertainty.
"""

from app.engines.racketskill.update_v1.rule import (
    ODDS_DECADE_LEVELS,
    RESULT_ENGINE_VERSION,
    RESULT_MOVE_CEILING,
    SETTLED_SIGMA_FLOOR,
    SHARED_COURT_SHARE,
    STABLE_SIGMA,
    MovedRating,
    Stakes,
    expected_score,
    information_share,
    one_side,
    rating_after,
    stakes,
    status_for,
)

__all__ = [
    "ODDS_DECADE_LEVELS",
    "RESULT_ENGINE_VERSION",
    "RESULT_MOVE_CEILING",
    "SETTLED_SIGMA_FLOOR",
    "SHARED_COURT_SHARE",
    "STABLE_SIGMA",
    "MovedRating",
    "Stakes",
    "expected_score",
    "information_share",
    "one_side",
    "rating_after",
    "stakes",
    "status_for",
]
