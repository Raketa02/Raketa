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
    """The four plain-language bands, each spanning one whole level of range.

    Boundaries travel *on the estimate* (``docs/adr`` / PRD): a screen printing a
    range prints these values, never a second set of drawing constants, so a card
    can never name a band that disagrees with the number beside it.
    """

    NEW = ("New", 1.0, 2.0)
    DEVELOPING = ("Developing", 2.0, 3.0)
    ESTABLISHED = ("Established", 3.0, 4.0)
    ADVANCED = ("Advanced", 4.0, 5.0)

    def __init__(self, label: str, lower: float, upper: float) -> None:
        self.label = label
        self.lower = lower
        self.upper = upper


def clamp_to_scale(value: float) -> float:
    """Hold a Level inside the 1,0–5,0 scale."""

    return max(SCALE_MIN, min(SCALE_MAX, value))


def band_for(mu: float) -> Band:
    """The band a Level falls in; the top band is inclusive of the ceiling."""

    for band in Band:
        if mu < band.upper:
            return band
    return Band.ADVANCED


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
