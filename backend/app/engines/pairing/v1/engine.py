"""Pairing v1 — the balance forecast and the pairing that produces it.

This version forecasts a match at either arity, full or forming: tennis and squash,
two seats and two sides of one player each; padel and badminton, four seats, three
splits, ranked.

**A forming match is forecast rather than hidden.** The roster is resolved before
any arithmetic happens — the people on seats, then the current player if they could
still join, then a stand-in drawn from the target band for every seat still empty —
so a padel court with two players gets a number, a wide margin, and a count of how
much of it was stood in for. The two states that cannot be rescued are the two the
band cannot answer: a court nobody has joined, and one where nobody seated has a
rating at this sport. Both have no Level to draw a stand-in from, so *imputation
stands in for gaps in a roster, never for the whole roster* is a consequence of
where a stand-in comes from rather than a rule written down beside it.

The seat target is stricter than the forecast on purpose: it is the *exact* answer,
so it needs the match one seat from full **and** every seated player rated, and the
band is its stated fallback.

The whole balance calculation, in the order it happens:

0. **The roster first**, because a forecast of the wrong roster is worse than no
   forecast. A held seat contributes its occupant's Level and not their attendance;
   an empty seat contributes the band's midpoint at a wide Uncertainty; an unrated
   occupant contributes exactly what an empty seat does, because a Level the
   platform does not have is a Level the platform does not have. Nothing here is a
   penalty: the margin widens because the roster's Uncertainty widened, and that is
   the only channel imputation has.
1. **In doubles, the pairing next**, because the same four Levels give a
   near-perfect match or a walkover depending entirely on how they are split —
   ADR-0025's canonical roster splits one way into a gap of 0,0155 and another
   into 0,1825, an order of magnitude apart from the same four people. All three
   arrangements are enumerated and forecast, and they are ranked on the
   **expected absolute gap** rather than on the gap between the two paper
   strengths. Choosing on the paper gap would pick whichever split the platform's
   own uncertainty had made *look* closest, an optimism that grows with σ; here a
   split the platform is unsure about is not preferred to one it is sure of.
2. **Two sides.** A team of one is that player, so singles reaches the arithmetic
   with no pairing step in front of it. A team of two is weighted toward the
   weaker partner. Sides are oriented so that the current player, when they are
   on a seat, is the first one.
3. **The gap between them**, as a distribution rather than a number: its mean is
   the difference of the two strengths and its spread is the two Uncertainties
   combined in quadrature — into the gap, not across the roster.
4. **The expected absolute gap.** ``E|X|``, never ``|E X|``, so a wide Uncertainty
   inflates the gap instead of being reported as a confident near-zero.
5. **One clamp, on that gap.** The percentage floor and the favourite cap are both
   derived from it, so they saturate at the same instant and a card cannot print a
   floored number beside an unfloored bar.
6. **One rounding.** The percentage is rounded, and the split bar is derived from
   the rounded value, so the two cannot drift apart in the last decimal.
7. **A margin, and a grade of it.** The margin is the standard deviation of the
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
    NoForecast,
    NoSeatTarget,
    NobodySeated,
    NoTargetBand,
    PairingAnalysis,
    SeatUnderDetermined,
    SidesNotFormed,
    Split,
    TargetBand,
    UnratedSeat,
)
from app.engines.matchmaking import (
    Level,
    MatchSnapshot,
    Occupant,
    PlayerSkill,
)
from app.engines.pairing.core import (
    SPLITS,
    Contender,
    Roster,
    Side,
    absolute_gap_deviation,
    as_float,
    combine_uncertainty,
    contender_for,
    evening_levels,
    expected_absolute_gap,
    mean_level,
    middle_level,
    round_half_away_from_zero,
    seated_contender,
    side_of_one,
    side_of_two,
)
from app.engines.pairing.v1.constants import CONSTANTS, ENGINE_VERSION
from app.kernel import Err, Instant, Ok, Ratio, Result, Sport, invariant

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

        seated = snapshot.occupants
        forecast, splits = _balance(snapshot, _roster(snapshot, seated))
        return PairingAnalysis(
            forecast=forecast,
            splits=splits,
            seat_target=_seat_target(snapshot, seated),
            target_band=_target_band(snapshot, seated),
            engine_version=ENGINE_VERSION,
        )


def _roster(
    snapshot: MatchSnapshot, seated: tuple[Occupant, ...]
) -> Result[Roster, NoForecast]:
    """Everybody the forecast is about, with a Level for every place.

    Three things happen here, in this order, and the order is the design:

    1. **The people on seats**, paid and held alike. A held seat contributes its
       occupant's Level and nothing else; whether they turn up is viability's
       question and is never spent as Uncertainty here.
    2. **The current player, taking the first seat nobody is on**, if they are not
       already on one. So the forecast answers *what would this match be like if I
       joined* rather than *what is it like without me* — which is the question a
       player scrolling a list is actually asking, and the difference between the
       two is a whole side in singles.
    3. **The seats still empty**, stood in for from the band.

    **The roster is built by walking the seats**, one place per seat, so it is
    exactly as long as the sport is sold in by construction rather than by a length
    check — and *"if there is room"* is not a condition anybody had to write: a
    match with no empty seat has nowhere to put a joiner, so a spectator looking at
    a full match is looking at somebody else's match and stays out of it.

    **Imputation stands in for gaps in a roster, never for the whole roster**, and
    the reason is arithmetic rather than a rule: a stand-in is drawn from the target
    band, the band's midpoint is the mean of the seated Levels, and there is no mean
    of nothing. So the two states that decline here are exactly the two the band
    declines for, and neither is a rule anybody chose — a court nobody has joined,
    and a court where nobody seated is rated at this sport.

    They are *reported* differently, and that is deliberate. Nobody seated is
    ``SidesNotFormed``, which is what the forecast has always called having nobody
    to put on a side; nobody rated is ``UnratedSeat``. Both come from the shared
    helpers below rather than being built here, so the same fact reaches every field
    that answers it with the same payload.
    """

    if not seated:
        return Err(_no_sides(snapshot, seated))
    stand_in = _seated_mean(seated)
    if stand_in is None:
        return Err(_unrated(snapshot, seated))

    spread = CONSTANTS.imputation_uncertainty
    joining = _joining(snapshot, seated)
    places = []
    for seat in snapshot.seats:
        occupant = seat.occupant
        if occupant is None and joining is not None:
            occupant, joining = joining, None
        places.append(contender_for(occupant, stand_in=stand_in, spread=spread))
    return Ok(Roster(contenders=tuple(places)))


def _joining(snapshot: MatchSnapshot, seated: tuple[Occupant, ...]) -> Occupant | None:
    """The current player, when they are not already on a seat.

    *"If they are not already in it"* — a player looking at a match they joined is
    in the roster once, not twice, and double-counting them would replace an open
    seat with a duplicate of the reader. Whether there is anywhere to put them is
    the seat walk's business rather than this one's.
    """

    current = snapshot.current_player
    if any(occupant.player == current.player for occupant in seated):
        return None
    return current


def _seated_mean(seated: tuple[Occupant, ...]) -> Level | None:
    """The mean of the Levels the platform actually has, or nothing.

    **The one place the seated mean is computed.** The target band advertises it
    and every imputed seat is drawn from it, so a second implementation is a card
    whose band says one thing while its own forecast quietly imputed another.

    ``None`` when no seated player has a Level here — which is a different state
    from an empty court and is reported as one.
    """

    levels = tuple(
        occupant.level for occupant in seated if isinstance(occupant, PlayerSkill)
    )
    return mean_level(levels) if levels else None


def _balance(
    snapshot: MatchSnapshot, roster: Result[Roster, NoForecast]
) -> tuple[Result[BalanceForecast, NoForecast], tuple[Split, ...]]:
    """The forecast and the arrangements it was chosen from, together.

    Returned as a pair rather than assembled separately, so the winner and the
    headline number are the same object and not two computations of it.
    """

    if isinstance(roster, Err):
        return roster, ()
    members = roster.value.contenders
    imputed = roster.value.imputed_seats
    if snapshot.sold_seats == _SINGLES:
        return Ok(
            _singles_forecast(members, snapshot.current_player, imputed=imputed)
        ), ()
    if snapshot.sold_seats == _DOUBLES:
        splits = _ranked_splits(members, snapshot, imputed=imputed)
        return Ok(splits[0].forecast), splits
    return Err(_no_sides(snapshot, snapshot.occupants)), ()


def _no_sides(snapshot: MatchSnapshot, seated: tuple[Occupant, ...]) -> SidesNotFormed:
    """No sides can be made of this roster, so there is nothing to forecast.

    Two reasons reach here and they are one reason: there is nobody to put on a
    side. A roster with **nobody at all** in it cannot be imputed into existence —
    a stand-in is drawn from the band and an empty court has no band — and a sport
    sold in some arity this version has no pairing rule for has no sides either.
    The engine declines rather than guessing, because a forecast built on a player
    who is not there is the failure this whole spec exists to remove.

    **Declining the forecast is not declining the analysis.** The same half-formed
    roster that has no two sides still has a seat aimed somewhere and a band it is
    aimed at, and those are answered beside this. The reason is built here and
    wrapped at each caller, because it is one fact given as the answer to two
    different questions.
    """

    return SidesNotFormed(
        sport=snapshot.sport.value,
        seated=len(seated),
        sold=snapshot.sold_seats,
    )


def _unrated(snapshot: MatchSnapshot, seated: tuple[Occupant, ...]) -> UnratedSeat:
    """A seated player the platform cannot place on the scale at this sport.

    Built here and wrapped at three callers, the same way ``_no_sides`` is, because
    it is one fact answering three questions at two thresholds: the band and the
    forecast need *one* rated player, the seat target needs *all* of them. The
    payload carries both counts so a client can tell which case it is looking at.
    """

    unrated = sum(1 for occupant in seated if not isinstance(occupant, PlayerSkill))
    return UnratedSeat(
        sport=snapshot.sport.value,
        unrated=unrated,
        seated=len(seated),
        sold=snapshot.sold_seats,
    )


def _seat_target(
    snapshot: MatchSnapshot, seated: tuple[Occupant, ...]
) -> Result[Level, NoSeatTarget]:
    """What Level the one open seat is aimed at — when there is exactly one.

    **One open seat, or no answer.** With two open there are two Levels to choose
    and one equation between them, so every Level across a wide interval evens the
    match given some answer for the other seat; naming one would be reporting a
    preference as a calculation. With none open there is no seat. Both decline,
    and a caller falls back to the band.

    Singles is the case with nothing to solve: the two sides are one player each,
    so the Level that evens the match is the seated player's own. Doubles inverts
    the team strength — see ``even_partner_level`` — once per arrangement, and
    takes the middle of the three answers, which for any weighting above a half
    and below one is the only one of the three guaranteed to land between the
    Levels already seated. That is asserted over a sweep in both test suites
    rather than guarded here, because it is a theorem about the weighting's range
    and the constants refuse a weight outside it: a check here could not fire.

    **Every seated player rated, or no answer.** This is the *exact* answer, solved
    from the Levels already in the match, and one the platform does not have cannot
    be stood in for without the answer quietly ceasing to be exact — an imputed
    Level is a claim about a band, and a seat target advertised off one would carry
    a precision it does not have. The band is the stated fallback for exactly this.
    """

    open_seats = snapshot.sold_seats - len(seated)
    if open_seats != 1:
        return Err(
            SeatUnderDetermined(
                sport=snapshot.sport.value,
                open_seats=open_seats,
                sold=snapshot.sold_seats,
            )
        )
    rated = tuple(
        seated_contender(occupant)
        for occupant in seated
        if isinstance(occupant, PlayerSkill)
    )
    if len(rated) != len(seated):
        return Err(_unrated(snapshot, seated))
    if snapshot.sold_seats == _SINGLES:
        return Ok(rated[0].level)
    if snapshot.sold_seats == _DOUBLES:
        weight = _weaker_weight(snapshot.sport)
        return Ok(middle_level(evening_levels(rated, weaker_weight=weight)))
    return Err(_no_sides(snapshot, seated))


def _target_band(
    snapshot: MatchSnapshot, seated: tuple[Occupant, ...]
) -> Result[TargetBand, NoTargetBand]:
    """The Level range a forming match is aimed at — the blunt answer.

    One seated *Level* is the whole requirement, so this is answered in every state
    the seat target declines in except the two where the platform has no Level at
    all, which is what makes it the fallback rather than a second opinion. It is
    answered for a *full* match too: the match is still aimed somewhere, and a
    caller ranking a full match beside a forming one needs both to say the same
    kind of thing.

    It is also what every imputed seat is drawn from, which is why the midpoint
    comes from ``_seated_mean`` rather than being computed here: the band a card
    advertises and the Level the forecast stood in are the same number by
    construction.
    """

    if not seated:
        return Err(
            NobodySeated(sport=snapshot.sport.value, sold=snapshot.sold_seats),
        )
    midpoint = _seated_mean(seated)
    if midpoint is None:
        return Err(_unrated(snapshot, seated))
    return Ok(
        TargetBand(
            midpoint=midpoint,
            half_width=CONSTANTS.target_band_half_width,
        )
    )


def _singles_forecast(
    roster: tuple[Contender, ...], current: Occupant, *, imputed: int
) -> BalanceForecast:
    """Two players, no pairing decision, and a team of one is that player."""

    left, right = _oriented(*_SINGLES_SEATS, roster=roster, current=current)
    return _forecast(
        side_of_one(roster[left[0]]), side_of_one(roster[right[0]]), imputed=imputed
    )


def _ranked_splits(
    roster: tuple[Contender, ...], snapshot: MatchSnapshot, *, imputed: int
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

    weight = _weaker_weight(snapshot.sport)
    current = snapshot.current_player
    options = tuple(
        _split(
            roster,
            *_oriented(left, right, roster=roster, current=current),
            weight,
            imputed=imputed,
        )
        for left, right in SPLITS
    )
    return tuple(sorted(options, key=lambda option: option.forecast.expected_gap))


def _split(
    roster: tuple[Contender, ...],
    left: tuple[int, ...],
    right: tuple[int, ...],
    weaker_weight: Ratio,
    *,
    imputed: int,
) -> Split:
    """One arrangement: who is with whom, and what that would play like.

    Membership and strengths are built here together and travel together, so no
    caller can pair a forecast with an arrangement it was not computed from. A
    ``None`` on a side is an imputed seat, carried rather than dropped so that
    *which side the open seat is on* survives to the card.
    """

    return Split(
        side_a=tuple(roster[seat].player for seat in left),
        side_b=tuple(roster[seat].player for seat in right),
        forecast=_forecast(
            _team(roster, left, weaker_weight),
            _team(roster, right, weaker_weight),
            imputed=imputed,
        ),
    )


def _team(
    roster: tuple[Contender, ...], seats: tuple[int, ...], weaker_weight: Ratio
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
    roster: tuple[Contender, ...],
    current: Occupant,
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
    roster: tuple[Contender, ...], seats: tuple[int, ...], current: Occupant
) -> bool:
    return any(roster[seat].player == current.player for seat in seats)


def _forecast(side_a: Side, side_b: Side, *, imputed: int) -> BalanceForecast:
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
        # Carried out, never read in. Imputation reaches the estimate through the
        # roster's Uncertainties and through nothing else, so there is no thin-
        # roster penalty above and nothing below this line reads the count.
        imputed_seats=imputed,
    )


def _grade(margin: int) -> Certainty:
    """The margin, graded. The only thing that decides whether a card prints."""

    if margin <= CONSTANTS.certain_margin:
        return Certainty.HIGH
    if margin <= CONSTANTS.unsure_margin:
        return Certainty.MODERATE
    return Certainty.LOW
