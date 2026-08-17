"""Pairing v1's constants — six numbers, each an admitted hypothesis.

Constants travel with the version as a frozen dataclass and every one of them
carries, as its docstring, the measurement that would falsify it (``docs/adr/0015``,
``docs/adr/0022``). A constant with no such measurement is a preference wearing a
number's clothes, and retuning it is then taste rather than science.

**Two more are not here**, deliberately: the balance floor and the
favourite cap are *derived* from the clamp, as properties below. The source
design clamped the percentage and the bar independently, and two independent
clamps bind at two different gaps — which shows up as 35% balanced printed beside
a bar that is not yet at its cap, a card contradicting itself in the interval
between the two. Deriving both from the one clamped quantity makes that
unwritable rather than watched for.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, final

from app.kernel import SPORT_SPECS, Ratio, Sport, invariant, ratio

#: The sports that have a pairing at all. Read from the kernel registry rather
#: than listed, because *a sport's player count is never club-configurable* and a
#: second list here is a second answer to how many people play padel.
PAIRED_SPORTS = frozenset(
    sport for sport, spec in SPORT_SPECS.items() if spec.players == 4
)

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

    weaker_partner_weight: Mapping[Sport, Ratio] = field(
        default_factory=lambda: MappingProxyType(
            {sport: ratio(55, 100) for sport in sorted(PAIRED_SPORTS)}
        )
    )
    """How much of a team's strength its **weaker** partner accounts for.

    A team is not the average of two Levels: the weaker side is attacked, so a
    4,5 partnered with a 2,0 plays like whatever the 2,0 can return. Above a half
    is what *weighted toward the weaker partner* means, and the guard below is
    what stops a retune quietly inverting it.

    **Solved from a document in this repository, not chosen.**
    [ADR-0025](../../../../docs/adr/0025-binding-pairing-for-counted-matches.md)
    records the canonical four-player padel roster — 2,71 / 2,80 / 2,64 / 2,92 —
    and states two of its three split gaps, *0,0155* and *0,1825*. Each of those
    is one linear equation in this weight, and both are solved by 0,55 and by
    nothing else. So the persona in the golden suite is not a baseline copied off
    a screen; it is the pair of figures this number was derived from.

    **Per sport, both sports the same at v1**, so *is a padel partnership more
    forgiving than a badminton one?* is a question the platform can answer by
    measurement instead of by rewriting the arithmetic. Keyed over the registry's
    own four-player sports, so a fifth one cannot be added without either a weight
    or a build failure.

    **Falsified by:** the elections ADR-0025 records. Every counted doubles match
    keeps both the split the engine chose and the split the roster elected, and a
    roster that consistently overrides in one direction is measuring this number
    directly — overriding *toward* the stronger pairing says the weaker partner is
    counted too heavily, and away from it says too lightly. Second, and slower:
    bucket counted doubles results by the difference between the two team
    strengths this weight produced, and check that the side the weight called
    stronger actually wins at the rate the balance percentage claimed.
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

    target_band_half_width: Ratio = field(default_factory=lambda: ratio(50, 100))
    """How far either side of the seated mean a forming match is aimed.

    **Taken from the commitment ``gap_coefficient`` was solved from, not chosen
    separately.** That reference scenario is *a singles match between 3,00 and
    3,50 — half a Level apart — is 75% balanced*, so half a Level is the widest
    difference the platform has said out loud is still a match worth playing. A
    target band is exactly that claim pointed the other way: the Levels this match
    is for. Picking a second number here would be the platform quietly holding two
    opinions about how far apart two players can be.

    Blunt on purpose, and a band rather than a point, because the mean of one, two
    or three seated Levels is a much weaker statement than a full roster is and
    should not be dressed as a precise one. The seat target is the precise answer
    and it is available only when the match is one seat from full.

    **Falsified by:** where the players who actually take the open seats fall.
    Every fill records the joiner's Level against the band that was advertised at
    the moment they joined. If nearly all of them land well inside it, the band is
    wider than the match really was and it told nobody anything; if a large share
    land outside it and those matches then played out balanced, it is narrower
    than the truth and it was turning people away from matches that were for them.
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

    def __post_init__(self) -> None:
        """The two things a retune of the weighting could silently get wrong.

        Both are checked here, once, at the moment the constants are built —
        rather than at every call site that forms a team — because this is where
        a retune happens and because failing at import is louder than failing on
        one home screen. A weight at or below a half is not a weaker-partner
        weighting at all; it is the model inverted, with every percentage still
        looking plausible.

        **The open upper end is not decoration.** At a weight of exactly one the
        stronger partner contributes nothing, so a team's strength can never be
        raised above its weaker member by any partner at all — and then a seat
        target does not exist for some rosters, because no Level in either
        direction would even the match. The weighting has to leave the stronger
        partner *some* share for the seat question to have an answer, so the range
        is above a half and below one.
        """

        invariant(
            set(self.weaker_partner_weight) == set(PAIRED_SPORTS),
            f"weights cover {sorted(self.weaker_partner_weight)}, "
            f"the registry pairs {sorted(PAIRED_SPORTS)}",
        )
        for sport, weight in self.weaker_partner_weight.items():
            invariant(
                ratio(1, 2) < weight < ratio(1, 1),
                f"{sport.value} does not weight the weaker partner: {weight}",
            )

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
