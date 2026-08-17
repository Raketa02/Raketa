"""Pairing v1's constants — four numbers, each an admitted hypothesis.

Constants travel with the version as a frozen dataclass and every one of them
carries, as its docstring, the measurement that would falsify it (``docs/adr/0015``,
``docs/adr/0022``). A constant with no such measurement is a preference wearing a
number's clothes, and retuning it is then taste rather than science.

**Two of the four are not here**, deliberately: the balance floor and the
favourite cap are *derived* from the clamp, as properties below. The source
design clamped the percentage and the bar independently, and two independent
clamps bind at two different gaps — which shows up as 35% balanced printed beside
a bar that is not yet at its cap, a card contradicting itself in the interval
between the two. Deriving both from the one clamped quantity makes that
unwritable rather than watched for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import final

from app.kernel import Ratio, invariant, ratio

#: This lineage, permanently. It travels on every analysis, because a constant
#: below can only be falsified against results it can be attributed to.
ENGINE_VERSION = "pairing-v1"


@final
@dataclass(frozen=True)
class PairingConstants:
    """The v1 hypotheses, and the derivations that must not be second-guessed."""

    gap_coefficient: Ratio = field(default_factory=lambda: ratio(50, 1))
    """Percentage points of balance lost per Level point of gap.

    **Derived from a stated product commitment, not chosen.** The reference
    scenario is: *a singles match between 3,00 and 3,50 — half a Level apart — is
    quoted at 75% balanced, which is a 63/37 split.* That fixes the coefficient at
    ``(100 − 75) / 0,50 = 50`` and nothing else does. Retuning it therefore means
    revising a claim the platform makes to players about what a percentage means,
    rather than nudging a number until a screenshot looks right.

    **Falsified by:** the distribution of result margins in counted matches,
    bucketed by the percentage that was quoted before they were played. If matches
    quoted at 75% are routinely won 6-1 6-1, half a Level costs more than a
    quarter of the scale and the coefficient is too shallow; if they are routinely
    decided in a tie-break, it is too steep.
    """

    gap_clamp: Ratio = field(default_factory=lambda: ratio(130, 100))
    """The gap, in Level points, at which the scale stops reporting usefully.

    Beyond it the honest answer is *this is a mismatch*, not a small percentage,
    and ``beyond_scale`` is how the two are said differently. 1,30 is wider than
    any single Band — Established spans 1,1 and Advanced 1,1 — so two players a
    clamp apart cannot be described by the same word, which is the point at which
    a number stops adding anything to that word.

    **The floor and the cap are derived from this and never written down beside
    it**, so they saturate at the same instant by construction.

    **Falsified by:** the share of matches quoted at the floor whose result was
    actually competitive. If a meaningful fraction of floored matches are decided
    by two games or fewer, the scale is being stopped while it still had something
    to say and the clamp is too tight; if matches well inside the floor are
    routinely walkovers, it is too loose.
    """

    certain_margin: int = 8
    """The margin, in percentage points, up to which certainty is HIGH.

    **Falsified by:** the calibration of the margin itself. Bucket played matches
    by their quoted certainty and compare the quoted balance against the balance
    the result implies; if HIGH-certainty forecasts miss by as much as MODERATE
    ones, this boundary is in the wrong place — and if HIGH is never reached by
    any real roster, it is a grade the platform cannot award and should not carry.
    """

    unsure_margin: int = 18
    """The margin beyond which certainty is LOW and the estimate is not fit to
    print.

    Suppression is presentation and nothing else: a LOW forecast still ranks, on
    its point estimate, because the best estimate remains the best estimate when
    it is unfit to print. Withholding it from the ranking would make an uncertain
    match unrankable rather than honest.

    **Falsified by:** what players do with a suppressed card. If matches whose
    forecast was withheld are joined and enjoyed at the same rate as printed ones,
    the platform is hiding a number it could stand behind; if printed forecasts at
    the top of this band are followed by complaints about walkovers, it is
    printing one it cannot.
    """

    @property
    def balance_floor(self) -> int:
        """The lowest balance percentage the scale reports — derived, not chosen.

        Whole-percent by construction, and the invariant says so: a floor of
        34,5% would be a number no card could print and half a point of drift
        between the percentage and the bar derived from it.
        """

        exact = 100 - self.gap_coefficient * self.gap_clamp
        invariant(
            exact.denominator == 1,
            f"the balance floor is not a whole percent: {exact}",
        )
        return int(exact.numerator)

    @property
    def favourite_cap(self) -> int:
        """The largest share of the split bar the favourite is ever given.

        The same derivation every share uses — the underdog holds half the
        balance percentage — applied to the floor. So the cap binds at exactly the
        gap the floor binds at, and the 35 / 83 pair the source design wrote down
        as two independent numbers falls out of one.
        """

        return 100 - self.balance_floor // 2


#: The v1 constants, frozen. One instance, so a caller cannot hold a retuned copy.
CONSTANTS = PairingConstants()
