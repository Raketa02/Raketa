"""The result-update rule — **what a confirmed game teaches us about a player.**

This is the arithmetic the whole marketplace's honesty rests on, and it is
decided in ``docs/adr/0139``. Onboarding produces a hypothesis; this is the only
thing on the platform that tests one.

**A result is evidence, weighed like every other.** The questionnaire fuses
answers by inverse variance and lets σ fall out of the fusion rather than out of
a second rule; this does the same for a result, and that is why the two cannot
develop two definitions of uncertainty. What differs is *what kind* of evidence a
result is: an answer is a statement about **you**, and a result is a statement
about **the gap between two people**. So the observation is relative, and the
shape is Elo's — an expected score over a Level difference — with the Bayesian
weight the questionnaire already uses wrapped around it.

**The relative form is not a preference; it is forced.** ``AtStake``'s invariant
is ``win_delta > 0 > loss_delta``, and any rule that reads a result as an
*absolute* observation of your Level breaks it: losing to somebody far above you
would raise your Level, because being on court with them at all is evidence you
are better than we thought. That sentence is defensible and the card cannot print
it, so the absolute form is out.

**Five constants and no more**, each a hypothesis with a measurement that would
falsify it:

``ODDS_DECADE_LEVELS``
    how much daylight makes the stronger player a ten-to-one favourite.
``RESULT_MOVE_CEILING``
    the most one evening may move a Level, whatever the pairing.
``SHARED_COURT_SHARE``
    how much of a four is evidence about any one of the four.
``STABLE_SIGMA``
    the uncertainty at which the platform is prepared to call a rating settled.
``SETTLED_SIGMA_FLOOR``
    the uncertainty below which it will never claim to know anybody.

**Pure Python, no clock, no randomness, no hidden state** — like the whole engines
layer (``docs/adr/0015``), and asserted rather than assumed: the rule is a
function of its arguments, so the same pairing settles the same way on every
machine and under every ``PYTHONHASHSEED``.

**It is a version directory and not a module beside ``core.py``**, on the same
ADR's *a version is a directory*: every constant below is an admitted hypothesis,
and retuning one in place would change what ``racketskill-result-update-v1`` means
on rows already in the store. ``core.py`` is for what outlives a version; this is
not that.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Sequence, final

from app.engines.assessment import BandView
from app.engines.racketskill.core import (
    STATUS_CALIBRATING,
    STATUS_INITIAL_ESTIMATE,
    STATUS_STABLE,
    Band,
    SkillEstimate,
    band_for,
    clamp_to_scale,
    confidence_percent,
    likely_range,
)
from app.kernel import SPORT_SPECS, Sport, invariant

#: The version stamp a moved rating carries. **A rating carries the engine
#: version that produced it**, and a Level that has been moved by results was
#: produced by two engines rather than one — the questionnaire that opened it and
#: the rule that has been testing it since. This is the second stamp, and it is
#: separate because the two are retuned independently.
RESULT_ENGINE_VERSION = "racketskill-result-update-v1"

#: How much Level difference makes the stronger player a **ten-to-one** favourite.
#:
#: One full Level of daylight is four to one (79,5%); half a Level is two to one
#: (66,3%); two Levels — a band and a half — is fifteen to one. The number does
#: two jobs and cannot be split: it decides both how decisive a gap is *and* how
#: much a result at that gap teaches, because a result between mismatched people
#: is exactly as uninformative as it was predictable.
ODDS_DECADE_LEVELS = 1.70

#: The most one counted game may move a Level, whatever the pairing.
#:
#: **A brake, not the rule.** Left to itself the arithmetic moves a rating fresh
#: out of onboarding by a third of a band on one evening, which is what Glicko
#: does with a provisional player and is right when a rating's σ is a *measured*
#: posterior. Ours is not: onboarding's σ is a **floor**, humility about
#: self-report rather than a belief anybody derived (``CONTEXT.md``: *enforced as
#: a floor on σ rather than as a display cap*), so treating it as a full prior
#: over-weights the first results. And ``docs/adr/0137`` makes silence confirm a
#: score, so an evening nobody on the other side ever looked at is worth this
#: much and never more.
#:
#: It binds for roughly the first ten counted games and never again — by the time
#: a rating is anywhere near Stable the rule is well inside it. **It is scaled by
#: the share**, so a four's ceiling is half of it: the sentence is *no single
#: whole observation moves a Level further than this*, and a four is half of one.
RESULT_MOVE_CEILING = 0.15

#: How much of a four is evidence about any one of the four.
#:
#: You were half of what happened, so it is half the evidence about you. It is
#: applied as a **weight on the whole observation** — the Level move and the
#: certainty it buys, together — because half an observation is what it is, not a
#: discount applied to one half of it.
SHARED_COURT_SHARE = 0.5

#: The uncertainty at which a rating is **Stable**: 75% confidence.
#:
#: About twenty-five counted games against people the platform knows, and longer
#: against strangers — which is the point of putting the bar on σ rather than on
#: a count. Twenty games against people we know nothing about is not certainty,
#: and a status that said otherwise would be lying to whoever they match next.
STABLE_SIGMA = 0.30

#: The uncertainty the platform will never claim to be inside. 92% confidence.
#:
#: The σ analogue of *confidence is never 100*: people change, take winters off
#: and find a coach, so even a player watched for years is not known to better
#: than ±0,10. Without it a heavy user's σ walks toward zero and the likely range
#: printed on their profile becomes a claim nobody could defend.
SETTLED_SIGMA_FLOOR = 0.10

#: ``ln(10)`` per Level of daylight — the odds-decade restated in natural logs,
#: which is the form both halves of the update are written in. Derived rather
#: than typed, so retuning the readable constant retunes the arithmetic.
_Q = math.log(10.0) / ODDS_DECADE_LEVELS

#: The opponent-uncertainty attenuation's own constant, ``3q²/π²``. Derived for
#: the same reason.
_ATTENUATION = 3.0 * _Q * _Q / (math.pi * math.pi)

#: How many decimals a Level carries, and how many a delta does. **They differ on
#: purpose.** A Level is what a player is shown, and the platform carries it to
#: two; a delta is priced against two σ values and is routinely smaller than a
#: hundredth, so rounding it to a Level's resolution would print ``+0,00`` on a
#: card whose whole invariant is that neither number is zero.
_LEVEL_DIGITS = 2
_DELTA_DIGITS = 4
_SIGMA_DIGITS = 4


@final
@dataclass(frozen=True, slots=True)
class Stakes:
    """What a counted win and a counted loss are worth, as a **pair**.

    Always computed together and never one at a time, which is what makes *at
    stake* the rule itself rather than a preview of it: the ceiling scales both
    sides by one factor, so a card promising ``+0,07`` and an update delivering
    something else is not a state this type can hold.

    Both signed, and neither zero — the invariant ``AtStake`` publishes on the
    wire, proved here where it is produced rather than checked where it arrives.
    """

    win: float
    loss: float

    def __post_init__(self) -> None:
        invariant(
            self.win > 0 > self.loss,
            "a counted result that changes nothing or moves the wrong way: "
            f"+{self.win} / {self.loss}",
        )


@final
@dataclass(frozen=True, slots=True)
class MovedRating:
    """A rating after one confirmed result, **whole**.

    Everything a screen needs travels together — the band's own edges included —
    because *a screen printing a range prints the published values rather than a
    second set of drawing constants*, and a mover that returned only μ and σ
    would leave four callers to re-derive the rest four ways.

    ``stakes`` rides along so that what moved and what the card said would move
    are the same object, and a caller recording the move records both.
    """

    mu: float
    sigma: float
    confidence: int
    range_low: float
    range_high: float
    band: BandView
    status: str
    stakes: Stakes
    engine_version: str = RESULT_ENGINE_VERSION


def information_share(sport: Sport) -> float:
    """How much of one game of this sport is evidence about one player.

    Read from the closed ``SPORT_SPECS`` registry rather than held here, on the
    precedent ``challenges/domain/seats.py`` set: *how many people play this*
    is the registry's fact, and a second table of it here would be a second place
    for padel to stop being doubles.
    """

    spec = invariant(SPORT_SPECS.get(sport), f"no spec for sport: {sport!r}")
    return SHARED_COURT_SHARE if spec.players == 4 else 1.0


def one_side(estimates: Sequence[SkillEstimate]) -> SkillEstimate:
    """One side of the net, as **one player**. Used for both sides.

    The Level is the average of theirs, and the uncertainty is the uncertainty of
    that average: independent σ values combine as ``√(σ₁² + σ₂²) / 2``, so a pair
    is a better-known quantity than either of the people in it.

    **Both sides go through here, and that is the whole of *all four move
    equally*.** The result is a statement about one pair against another, so the
    Level move is priced side against side and every player on a side gets it — a
    partner is not somebody you are rated *against*, and pricing each player on
    their own μ would move two people on the same side of the same scoreline by
    different amounts, which the card would then have to explain and which pays a
    strong player to pick a weak partner.

    It is also why carrying a weaker partner to a win still moves you up, with
    nothing extra written to make it happen: the average is what made the result
    the upset it was.
    """

    invariant(
        bool(estimates),
        "a side with nobody on it: a result is between two sides that played",
    )
    mu = sum(one.mu for one in estimates) / len(estimates)
    sigma = math.sqrt(sum(one.sigma**2 for one in estimates)) / len(estimates)
    return SkillEstimate(mu=mu, sigma=sigma)


def expected_score(player: SkillEstimate, opposition: SkillEstimate) -> float:
    """The chance this player takes the result, in ``(0, 1)`` and never an end.

    The logistic over the Level gap, flattened by how sure we are of the *other*
    side: a gap against somebody nobody has watched proves less than the same gap
    against somebody we know cold, so it is expected less strongly. That is the
    whole of *beating a player we barely know moves you a little*, and it is one
    expression rather than a rule beside the rule.
    """

    attenuation = _attenuation(opposition.sigma)
    gap = clamp_to_scale(player.mu) - clamp_to_scale(opposition.mu)
    odds: float = 10.0 ** (-attenuation * gap / ODDS_DECADE_LEVELS)
    return 1.0 / (1.0 + odds)


def stakes(
    *,
    player: SkillEstimate,
    opposition: SkillEstimate,
    share: float = 1.0,
) -> Stakes:
    """What a counted win and a counted loss against this side would be worth.

    **This is what the card prints and what the rule applies**, and there is one
    of it. The three steps are:

    1. *how surprising each outcome would be* — ``1 − E`` for a win, ``E`` for a
       loss, so the more expected an outcome the less it teaches;
    2. *how much room we have to be wrong* — the posterior variance, which is
       large while σ is large and vanishes as a rating settles;
    3. *the brake* — one factor over **both** sides, so a pairing whose raw win
       exceeds the ceiling keeps its shape. Capping each delta on its own would
       make losing to somebody far above you cost exactly what losing to an equal
       costs, which is the opposite of what the pairing said.
    """

    return _weighed(player=player, opposition=opposition, share=share).stakes


def status_for(*, sigma: float, results: int) -> str:
    """Which of the three words this rating's state is.

    **A count opens the door and certainty closes it** (``docs/adr/0139``).
    *Initial Estimate* is the honest word for a rating no game has ever tested,
    whatever σ says — onboarding cannot reach the Stable bar, and if a retune
    ever let it, the word would still be a lie about a player nobody has watched.
    *Stable* is a claim about certainty and is measured as one.
    """

    if results <= 0:
        return STATUS_INITIAL_ESTIMATE
    return STATUS_STABLE if sigma <= STABLE_SIGMA else STATUS_CALIBRATING


def rating_after(
    *,
    player: SkillEstimate,
    opposition: SkillEstimate,
    won: bool,
    results_so_far: int,
    share: float = 1.0,
    own_side: SkillEstimate | None = None,
) -> MovedRating:
    """This player's rating after one confirmed counted result.

    ``own_side`` is the player's **whole side as one player**, and it is what the
    Level move is priced from — ``None`` means a side of one, which is every
    singles game and every head-to-head reading of a card. In a four it is the
    pair's average, so **both partners move by the same amount**: a result is a
    statement about one pair against another, and two people on the same side of
    the same scoreline moving differently is a sentence the card would have to
    explain.

    **The Level move is the side's and the certainty is the player's own.** Skill
    and certainty are separate variables, and they are separate here too: what the
    evening taught is a property of the game, so everybody on the side gains the
    same information — and folds it into the uncertainty they actually had. A
    newcomer and a player watched for years do not come off the same court equally
    sure of themselves.

    ``results_so_far`` is how many counted results had already moved this rating,
    so the status can say *nothing has ever tested this* without the rule holding
    state of its own.

    **The Level is rounded to the scale's own resolution and the delta is not.**
    Rounding lands on the new Level rather than on the move, so a run of results
    each too small to show still climbs: ``3,00 → 3,0067 → 3,01`` and on from
    there. A pairing so lopsided that even the sum rounds back is a pairing the
    matcher would never have drawn.
    """

    weighed = _weighed(
        player=own_side if own_side is not None else player,
        opposition=opposition,
        share=share,
    )
    delta = weighed.stakes.win if won else weighed.stakes.loss
    mu = round(clamp_to_scale(player.mu + delta), _LEVEL_DIGITS)
    gained = 1.0 / math.sqrt(1.0 / (player.sigma * player.sigma) + weighed.gained)
    sigma = round(max(gained, SETTLED_SIGMA_FLOOR), _SIGMA_DIGITS)
    low, high = likely_range(mu, sigma)
    band = band_for(mu)
    return MovedRating(
        mu=mu,
        sigma=sigma,
        confidence=confidence_percent(sigma),
        range_low=round(low, _LEVEL_DIGITS),
        range_high=round(high, _LEVEL_DIGITS),
        band=BandView(name=band.label, lower=band.lower, upper=band.upper),
        status=status_for(sigma=sigma, results=results_so_far + 1),
        stakes=weighed.stakes,
    )


# --- internals ----------------------------------------------------------------


@final
@dataclass(frozen=True, slots=True)
class _Weighed:
    """One pairing, priced once. Both callers above read the same computation.

    ``gained`` is the information the result carried, already braked — handed back
    rather than folded here, because the Level move belongs to the **side** and
    the uncertainty belongs to the **player**, and one of those is shared.
    """

    stakes: Stakes
    gained: float


def _attenuation(sigma: float) -> float:
    """How much an opponent's own uncertainty flattens what a result proves.

    One against a rating nobody could be surer of, and about 0,85 against one
    fresh out of onboarding. It appears twice — once inside the expected score
    and once on the size of the move — because both are statements about the same
    thing: we were comparing this player against a yardstick that wobbles.
    """

    return 1.0 / math.sqrt(1.0 + _ATTENUATION * sigma * sigma)


def _weighed(
    *, player: SkillEstimate, opposition: SkillEstimate, share: float
) -> _Weighed:
    """The pairing priced, with the ceiling applied to the whole observation.

    The brake scales the deltas **and** the certainty they buy by one factor, and
    that pairing is the point: holding a Level back while letting σ tighten at
    full speed would leave the platform sure of a number it had just refused to
    move.
    """

    attenuation = _attenuation(opposition.sigma)
    expected = expected_score(player, opposition)

    # What one whole observation would be worth: the Fisher information of a
    # result, which is largest for an even game and near nothing for a foregone
    # one — a result is informative exactly to the degree it was in doubt.
    information = share * _Q * _Q * attenuation * attenuation * expected * (
        1.0 - expected
    )
    variance = 1.0 / (1.0 / (player.sigma * player.sigma) + information)
    step = variance * _Q * attenuation * share
    win = step * (1.0 - expected)
    loss = -step * expected

    # **The ceiling is share-scaled**, so a four keeps its lower weight even
    # while the brake is binding. Left absolute it would cap a padel evening and
    # a squash evening at the same figure for exactly the players the share was
    # decided for — the provisional ones — and *a four is half the evidence about
    # you* would be true of everybody except the people it was written about.
    brake = min(1.0, RESULT_MOVE_CEILING * share / max(win, -loss))
    return _Weighed(
        stakes=Stakes(win=_published(brake * win), loss=_published(brake * loss)),
        gained=brake * information,
    )


def _published(delta: float) -> float:
    """One delta at the precision it crosses the wire at, **never rounded to zero.**

    A foregone pairing prices the expected side at a few hundred-thousandths, and
    ``round`` would answer ``-0.0`` — which is not a small number, it is the
    claim that a counted game against this opponent moves the searcher's Level by
    nothing. So a delta smaller than the published resolution is published as the
    smallest thing that resolution can hold, and keeps its sign: *this is under a
    ten-thousandth* is the honest reading of it, and zero is not.
    """

    rounded = round(delta, _DELTA_DIGITS)
    if rounded == 0.0:
        return math.copysign(10.0**-_DELTA_DIGITS, delta)
    return rounded


__all__ = [
    "ODDS_DECADE_LEVELS",
    "RESULT_ENGINE_VERSION",
    "RESULT_MOVE_CEILING",
    "SETTLED_SIGMA_FLOOR",
    "SHARED_COURT_SHARE",
    "STABLE_SIGMA",
    "Band",
    "MovedRating",
    "Stakes",
    "expected_score",
    "information_share",
    "one_side",
    "rating_after",
    "stakes",
    "status_for",
]
