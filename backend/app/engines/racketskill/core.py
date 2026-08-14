"""The RacketSkill core — everything that must outlive an engine version.

The 1,0–5,0 scale, the four bands, the confidence transform and the
σ-combination rule live here, extracted now so that onboarding and the later
match-update engine cannot develop two definitions of uncertainty. A version
directory (``v3``) owns the *questions and constants*; this module owns the
arithmetic those constants feed.

Pure Python, no clock, no randomness, no hidden state — like the whole engines
layer (``docs/adr/0015``).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

# The rating scale. A Level (μ) always lives inside these bounds.
SCALE_MIN = 1.0
SCALE_MAX = 5.0

# The σ at which the confidence transform reaches 0%. A version's σ floor is
# expressed as a fraction of this ceiling, which is why it lives in the core:
# every engine reads the same definition of "maximally uncertain".
CONFIDENCE_SIGMA_CEILING = 1.20


@dataclass(frozen=True)
class SkillEstimate:
    """A Level/Uncertainty pair — the currency the fusion produces and consumes."""

    mu: float
    sigma: float


class Band(Enum):
    """The four plain-language bands, **deliberately uneven in width**.

    New and Developing are narrow; Established and Advanced each span close to a
    full level of range. That asymmetry is load-bearing, not an accident of
    rounding: two demonstrations are enough to separate New from Developing
    because the bands down there are narrow and the basic questions decisive,
    which is exactly why an estimate that climbs into Established earns a *third*
    demonstration before the engine will consider stopping (``ESTABLISHED_FLOOR``
    in the v3 router is this band's lower edge, less the same tolerance
    ``band_for`` applies).

    Boundaries travel *on the estimate* (``CONTEXT.md``, PRD): a screen printing a
    range prints these values, never a second set of drawing constants, so a card
    can never name a band that disagrees with the number beside it.
    """

    NEW = ("New", 1.0, 1.5)
    DEVELOPING = ("Developing", 1.6, 2.6)
    ESTABLISHED = ("Established", 2.7, 3.8)
    ADVANCED = ("Advanced", 3.9, 5.0)

    def __init__(self, label: str, lower: float, upper: float) -> None:
        self.label = label
        self.lower = lower
        self.upper = upper


def clamp_to_scale(value: float) -> float:
    """Hold a Level inside the 1,0–5,0 scale."""

    return max(SCALE_MIN, min(SCALE_MAX, value))


#: The printed bands leave a gap between them (1,5 → 1,6), so a Level landing in
#: one has to be assigned somewhere. It goes to the *higher* band from halfway
#: across the gap: the effective edges are 1,55 · 2,65 · 3,85.
BAND_EDGE_TOLERANCE = 0.05


def band_for(mu: float) -> Band:
    """The band a Level falls in — the highest whose lower edge it reaches.

    Compared against ``lower - BAND_EDGE_TOLERANCE`` rather than ``upper`` so the
    gaps between printed bands are covered and the top band stays inclusive of
    the ceiling.
    """

    chosen = Band.NEW
    for band in Band:
        # Rounded because the subtraction is not exact in binary: 2,7 − 0,05 is
        # 2.6500000000000004, which would push a Level of exactly 2,65 down a
        # band. Levels are carried to two decimals, so the edges are too.
        if mu >= round(band.lower - BAND_EDGE_TOLERANCE, 2):
            chosen = band
    return chosen


def combine_sigma(a: float, b: float) -> float:
    """The σ-combination rule: independent uncertainties add in quadrature.

    Used to fold the irreducible self-report bias into each answer's σ, and the
    single place any engine is allowed to combine two standard deviations.
    """

    return math.sqrt(a * a + b * b)


def confidence_percent(sigma: float) -> int:
    """The confidence transform: σ → a whole percent, and never 100.

    ``confidence = 100 × (1 − σ / ceiling)``, held in ``[0, 99]`` so the platform
    can never tell a player it is certain about them when it cannot be.
    """

    raw = 100.0 * (1.0 - sigma / CONFIDENCE_SIGMA_CEILING)
    return max(0, min(99, int(round(raw))))


def likely_range(mu: float, sigma: float) -> tuple[float, float]:
    """The one-σ likely range, clamped to the scale."""

    return clamp_to_scale(mu - sigma), clamp_to_scale(mu + sigma)
