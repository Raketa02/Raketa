"""Pairing v1 — the balance forecast and the pairing that produces it.

This version forecasts a **full** match at either arity: tennis and squash, two
seats and two sides of one player each; padel and badminton, four seats, three
splits, ranked. The seat target, the target band and seat imputation extend this
version rather than replacing it, because a shipped version is a directory that
is never deleted — a forecast is interpretable only through the code that
produced it.

The whole calculation, in the order it happens:

0. **In doubles, the pairing first**, because the same four Levels give a
   near-perfect match or a walkover depending entirely on how they are split —
   ADR-0025's canonical roster splits one way into a gap of 0,0155 and another
   into 0,1825, an order of magnitude apart from the same four people. All three
   arrangements are enumerated and forecast, and they are ranked on the
   **expected absolute gap** rather than on the gap between the two paper
   strengths. Choosing on the paper gap would pick whichever split the platform's
   own uncertainty had made *look* closest, an optimism that grows with σ; here a
   split the platform is unsure about is not preferred to one it is sure of.
1. **Two sides.** A team of one is that player, so singles reaches the arithmetic
   with no pairing step in front of it. A team of two is weighted toward the
   weaker partner. Sides are oriented so that the current player, when they are
   on a seat, is the first one.
2. **The gap between them**, as a distribution rather than a number: its mean is
   the difference of the two strengths and its spread is the two Uncertainties
   combined in quadrature — into the gap, not across the roster.
3. **The expected absolute gap.** ``E|X|``, never ``|E X|``, so a wide Uncertainty
   inflates the gap instead of being reported as a confident near-zero.
4. **One clamp, on that gap.** The percentage floor and the favourite cap are both
   derived from it, so they saturate at the same instant and a card cannot print a
   floored number beside an unfloored bar.
5. **One rounding.** The percentage is rounded, and the split bar is derived from
   the rounded value, so the two cannot drift apart in the last decimal.
6. **A margin, and a grade of it.** The margin is the standard deviation of the
   same absolute gap, in the same percentage points as the estimate. There is no
   separate uncertainty penalty anywhere: uncertainty reaches the percentage only
   through the gap, which is what makes the percentage and the bar two views of
   one number with no correction term.
"""

from __future__ import annotations

from typing import final

from app.engines.forecast import (
    BalanceForecast,
    Certainty,
    PairingAnalysis,
    SidesNotFormed,
    Split,
)
from app.engines.matchmaking import MatchSnapshot, PlayerSkill
from app.engines.pairing.core import (
    SPLITS,
    Side,
    absolute_gap_deviation,
    as_float,
    combine_uncertainty,
    expected_absolute_gap,
    round_half_away_from_zero,
    side_of_one,
    side_of_two,
)
from app.engines.pairing.v1.constants import CONSTANTS, ENGINE_VERSION
from app.kernel import Err, Instant, Ok, Ratio, Sport, invariant

#: The two seat counts this version has a pairing rule for. Read from the
#: snapshot's own sold count, which comes from the kernel registry, so an arity
#: is recognised by the registry and never by a list of sport names kept here — a
#: fifth sport played by six would reach the same decline as a half-empty court,
#: rather than a wrong answer.
_SINGLES = 2
_DOUBLES = 4

#: Singles as an arrangement of seats, so that *the current player's side comes
#: first* is one rule with one implementation rather than one per arity.
_SINGLES_SEATS: tuple[tuple[int, ...], tuple[int, ...]] = ((0,), (1,))


@final
class PairingEngineV1:
    """The v1 balance-forecast engine. Pure: no clock, no randomness, no state."""

    @property
    def version(self) -> str:
        return ENGINE_VERSION

    def analyse(self, *, snapshot: MatchSnapshot, now: Instant) -> PairingAnalysis:
        """Everything this engine concludes about one match, in one object.

        ``now`` is unread by the balance forecast — nothing about how even a match
        will be depends on when it is asked — and it is still an explicit input,
        because the analysis object grows terms that do depend on it and because a
        result reproducible from its stored inputs is the whole basis of the
        falsification programme. That it is **rounded to the minute** is a
        precondition and is checked as one: an engine handed a instant carrying
        seconds would produce a result no cache could ever hit and no replay could
        reproduce, which is a caller's bug and not a domain state.
        """

        invariant(
            now.second == 0 and now.microsecond == 0,
            f"now is not rounded to the minute: {now!r}",
        )

        roster = snapshot.occupants
        if len(roster) != snapshot.sold_seats:
            return _declined(snapshot)
        if snapshot.sold_seats == _SINGLES:
            return _analysis(_singles_forecast(roster, snapshot.current_player), ())
        if snapshot.sold_seats == _DOUBLES:
            splits = _ranked_splits(roster, snapshot.sport, snapshot.current_player)
            return _analysis(splits[0].forecast, splits)
        return _declined(snapshot)


def _analysis(forecast: BalanceForecast, splits: tuple[Split, ...]) -> PairingAnalysis:
    """The one place a forecast becomes an analysis, so the winner and the
    headline number are the same object and not two computations of it."""

    return PairingAnalysis(
        forecast=Ok(forecast), splits=splits, engine_version=ENGINE_VERSION
    )


def _declined(snapshot: MatchSnapshot) -> PairingAnalysis:
    """No sides can be made of this roster, so there is nothing to forecast.

    Two reasons reach here in this version and they are one reason: there is
    nobody to put on a side. A seat with no occupant needs imputation, which is
    the next slice; a sport sold in some arity this version has no pairing rule
    for has no sides either. Until then the engine declines rather than guessing,
    because a forecast built on a player who is not there is the failure this
    whole spec exists to remove.
    """

    return PairingAnalysis(
        forecast=Err(
            SidesNotFormed(
                sport=snapshot.sport.value,
                seated=len(snapshot.occupants),
                sold=snapshot.sold_seats,
            )
        ),
        splits=(),
        engine_version=ENGINE_VERSION,
    )


def _singles_forecast(
    roster: tuple[PlayerSkill, ...], current: PlayerSkill
) -> BalanceForecast:
    """Two players, no pairing decision, and a team of one is that player."""

    left, right = _oriented(*_SINGLES_SEATS, roster=roster, current=current)
    return _forecast(side_of_one(roster[left[0]]), side_of_one(roster[right[0]]))


def _ranked_splits(
    roster: tuple[PlayerSkill, ...], sport: Sport, current: PlayerSkill
) -> tuple[Split, ...]:
    """All three arrangements, forecast, best first.

    **Ranked on the expected absolute gap**, which is the whole reason the
    forecast reports one. Ranking on the difference between the two paper
    strengths would choose whichever split the platform's own uncertainty had
    made look closest — a selection bias that grows with σ, so it bites hardest
    on exactly the rosters the platform knows least about. Sorting is stable, so
    two arrangements the engine genuinely cannot separate stay in enumeration
    order rather than in whichever order the last sort happened to leave them.
    """

    weight = _weaker_weight(sport)
    options = tuple(
        _split(roster, *_oriented(left, right, roster=roster, current=current), weight)
        for left, right in SPLITS
    )
    return tuple(sorted(options, key=lambda option: option.forecast.expected_gap))


def _split(
    roster: tuple[PlayerSkill, ...],
    left: tuple[int, ...],
    right: tuple[int, ...],
    weaker_weight: Ratio,
) -> Split:
    """One arrangement: who is with whom, and what that would play like.

    Membership and strengths are built here together and travel together, so no
    caller can pair a forecast with an arrangement it was not computed from.
    """

    return Split(
        side_a=tuple(roster[seat].player for seat in left),
        side_b=tuple(roster[seat].player for seat in right),
        forecast=_forecast(
            _team(roster, left, weaker_weight), _team(roster, right, weaker_weight)
        ),
    )


def _team(
    roster: tuple[PlayerSkill, ...], seats: tuple[int, ...], weaker_weight: Ratio
) -> Side:
    """The pair on those two seats, weighted toward whichever of them is weaker."""

    first, second = seats
    return side_of_two(roster[first], roster[second], weaker_weight=weaker_weight)


def _weaker_weight(sport: Sport) -> Ratio:
    """This sport's weaker-partner weight, narrowed from the constants' map.

    The map is proved to cover every four-player sport in the registry when the
    constants are built, so this cannot fail for a sport that got here — the
    ``invariant`` is what turns *cannot fail* into a type the rest of the
    function can rely on.
    """

    return invariant(
        CONSTANTS.weaker_partner_weight.get(sport),
        f"no weaker-partner weight for {sport.value}",
    )


def _oriented(
    left: tuple[int, ...],
    right: tuple[int, ...],
    *,
    roster: tuple[PlayerSkill, ...],
    current: PlayerSkill,
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    """Seat order, except that the current player's side comes first.

    Every matchmaking answer is relative to somebody, and a card drawing *you
    against them* from a result whose sides are in seat order would draw it the
    wrong way round for half of all matches. Orientation is the engine's job
    because the engine is the only place that knows which side each strength
    belongs to — and it is one rule over seat indices rather than one per arity,
    so singles and doubles cannot develop two ideas of which side is yours.
    """

    if _holds(roster, right, current) and not _holds(roster, left, current):
        return right, left
    return left, right


def _holds(
    roster: tuple[PlayerSkill, ...], seats: tuple[int, ...], current: PlayerSkill
) -> bool:
    return any(roster[seat].player == current.player for seat in seats)


def _forecast(side_a: Side, side_b: Side) -> BalanceForecast:
    """The arithmetic, once both sides exist."""

    mean = as_float(side_a.strength) - as_float(side_b.strength)
    spread = combine_uncertainty(side_a.sigma, side_b.sigma)

    gap = expected_absolute_gap(mean, spread)
    deviation = absolute_gap_deviation(mean, spread)

    clamp = as_float(CONSTANTS.gap_clamp)
    coefficient = as_float(CONSTANTS.gap_coefficient)
    beyond_scale = gap > clamp

    # The clamp is what the *scale* does, and it is applied to exactly one
    # quantity. `expected_gap` below carries the unclamped expectation, because a
    # caller comparing two mismatches still needs to know that one of them is
    # worse — and because "the reported gap is never below the absolute expected
    # gap" is an invariant a clamped field would break at the top of the scale.
    estimate = round_half_away_from_zero(100.0 - coefficient * min(gap, clamp))

    # The margin is deliberately not clamped with it. It says how wrong the
    # estimate could be, and a mismatch the platform is unsure about is a
    # different claim from a mismatch it is sure of.
    margin = round_half_away_from_zero(coefficient * deviation)

    underdog_share = estimate // 2
    return BalanceForecast(
        estimate=estimate,
        margin=margin,
        certainty=_grade(margin),
        favourite_share=100 - underdog_share,
        underdog_share=underdog_share,
        beyond_scale=beyond_scale,
        side_a=side_a.strength,
        side_b=side_b.strength,
        expected_gap=gap,
    )


def _grade(margin: int) -> Certainty:
    """The margin, graded. The only thing that decides whether a card prints."""

    if margin <= CONSTANTS.certain_margin:
        return Certainty.HIGH
    if margin <= CONSTANTS.unsure_margin:
        return Certainty.MODERATE
    return Certainty.LOW
