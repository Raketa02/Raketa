"""Match Fit, version 1.

**All ten terms ADR-0027 specifies**, and the whole of the mechanism they run
through: term kinds, renormalisation over what actually ran, Coverage as its own
number, reasons ranked by contribution, and one warning on the weakest contributor's
own value. ``constants.PENDING_WEIGHTS`` is empty and the constants still refuse to
be built unless the declared and the pending weights sum to a hundred — so the debt
that guard existed to declare is discharged in arithmetic rather than in a comment.
"""

from app.engines.matchfit.v1.constants import (
    CONSTANTS,
    ENGINE_VERSION,
    PENDING_WEIGHTS,
    WEIGHT_TOTAL,
    MatchFitConstants,
)
from app.engines.matchfit.v1.engine import MatchFitEngineV1, Scoring

__all__ = [
    "CONSTANTS",
    "ENGINE_VERSION",
    "PENDING_WEIGHTS",
    "WEIGHT_TOTAL",
    "MatchFitConstants",
    "MatchFitEngineV1",
    "Scoring",
]
