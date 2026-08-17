"""What must still be true after any constant retune.

The opposite file to ``test_pairing_personas.py``. Nothing here reads a literal
that a constant owns: every assertion is either structural — the percentage and
the bar are one number viewed twice — or it reads the constant it is about. A
retune that breaks one of these has broken the model, not the baseline.
"""

import ast
from pathlib import Path

import pytest

from app.engines.forecast import (
    BalanceForecast,
    BalanceForecastEngine,
    Certainty,
    PairingAnalysis,
    SidesNotFormed,
)
from app.engines.matchmaking import (
    MatchSnapshot,
    PlayerSkill,
    SeatSnapshot,
)
from app.engines.pairing.core import (
    Side,
    absolute_gap_deviation,
    as_float,
    expected_absolute_gap,
    round_half_away_from_zero,
)
from app.engines.pairing.v1 import CONSTANTS, ENGINE_VERSION, PairingEngineV1
from app.engines.pairing.v1.constants import PairingConstants
from app.kernel import Err, InvariantViolated, Ok, Sport
from tests.unit.matchmaking_snapshots import NOW, doubles, singles, skill

ROOT = Path(__file__).resolve().parents[2]
PAIRING = ROOT / "app" / "engines" / "pairing"

ENGINE = PairingEngineV1()

#: A spread of rosters wide enough to cross every branch: dead level, a hair
#: apart, half a level, past the clamp, and each of those at four Uncertainties
#: from certain to the onboarding floor. Written out rather than drawn at random,
#: because an invariant that only holds for the inputs a seed happened to pick is
#: not an invariant.
ROSTERS = tuple(
    (300, 300 + apart, sigma, other)
    for apart in (0, 5, 20, 50, 100, 130, 170, 250)
    for sigma in (0, 10, 35, 84)
    for other in (0, 20, 84)
)


def forecast_of(
    level_a: int, level_b: int, sigma_a: int, sigma_b: int
) -> BalanceForecast:
    """The forecast for one roster, through the Protocol and nothing else."""

    snapshot = singles(skill("a", level_a, sigma_a), skill("b", level_b, sigma_b))
    result = ENGINE.analyse(snapshot=snapshot, now=NOW)
    assert isinstance(result.forecast, Ok)
    return result.forecast.value


@pytest.fixture(scope="module")
def every_forecast() -> tuple[BalanceForecast, ...]:
    return tuple(forecast_of(*roster) for roster in ROSTERS)


# --- The identity between the percentage and the bar ----------------------------


def test_the_percentage_and_the_split_bar_satisfy_their_identity(every_forecast):
    """The bar is a *rendering* of the percentage, not a second opinion.

    The underdog holds half the balance percentage, and the two shares hold the
    whole bar between them. No correction term, for any input — which is what
    stops a card printing a floored number beside an unfloored picture.
    """

    for forecast in every_forecast:
        assert forecast.underdog_share == forecast.estimate // 2
        assert forecast.favourite_share + forecast.underdog_share == 100
        assert forecast.favourite_share >= forecast.underdog_share


def test_the_bar_is_derived_from_the_rounded_percentage_and_not_beside_it(
    every_forecast,
):
    """Round once. Both shares are functions of the integer estimate alone, so
    there is no second rounding for the two to disagree in."""

    for forecast in every_forecast:
        assert forecast.underdog_share == forecast.estimate // 2
        assert forecast.favourite_share == 100 - forecast.estimate // 2


def test_the_floor_and_the_cap_saturate_at_the_same_instant(every_forecast):
    """The failure this whole derivation exists to make unwritable: two clamps
    binding at two different gaps, printing the floored percentage beside a bar
    that has not reached its cap."""

    for forecast in every_forecast:
        assert forecast.estimate >= CONSTANTS.balance_floor
        assert forecast.estimate <= 100
        assert forecast.favourite_share <= CONSTANTS.favourite_cap
        floored = forecast.estimate == CONSTANTS.balance_floor
        capped = forecast.favourite_share == CONSTANTS.favourite_cap
        assert floored == capped


def test_the_floor_and_the_cap_are_derived_from_the_one_clamped_quantity():
    """Neither is written down. Retune the clamp and both move together."""

    exact = 100 - CONSTANTS.gap_coefficient * CONSTANTS.gap_clamp
    assert CONSTANTS.balance_floor == exact
    assert CONSTANTS.favourite_cap == 100 - CONSTANTS.balance_floor // 2


def test_a_balance_floor_that_is_not_a_whole_percent_is_refused():
    """A floor of 34,5% would be a number no card can print, and half a point of
    drift between the percentage and the bar derived from it."""

    from dataclasses import replace

    from app.kernel import ratio

    with pytest.raises(InvariantViolated, match="not a whole percent"):
        assert replace(CONSTANTS, gap_clamp=ratio(131, 100)).balance_floor


# --- The gap, and the one clamp on it -------------------------------------------


def test_the_reported_gap_is_never_below_the_absolute_expected_gap(every_forecast):
    """``E|X|`` and not ``|E X|``. Uncertainty inflates the gap; it can never be
    reported as a confident near-zero."""

    for forecast in every_forecast:
        assert forecast.expected_gap >= abs(
            as_float(forecast.side_a) - as_float(forecast.side_b)
        ) - 1e-12


def test_uncertainty_only_ever_widens_the_expected_gap():
    for mean in (0.0, 0.2, 0.5, 1.3, 2.0):
        widening = [
            expected_absolute_gap(mean, spread) for spread in (0.0, 0.1, 0.4, 1.2)
        ]
        assert widening == sorted(widening)
        assert widening[0] == pytest.approx(abs(mean))


def test_the_gap_is_the_only_quantity_that_is_clamped():
    """The percentage saturates; the gap the caller is handed does not.

    A caller ranking two mismatches still needs to know that one of them is
    worse, and a clamped field would make the two indistinguishable — as well as
    breaking *the reported gap is never below the absolute expected gap* at the
    top of the scale.
    """

    forecast = forecast_of(250, 500, 0, 0)
    assert forecast.estimate == CONSTANTS.balance_floor
    assert forecast.expected_gap > as_float(CONSTANTS.gap_clamp)


def test_beyond_scale_distinguishes_a_mismatch_from_a_floored_percentage():
    """Both print the floor. Only one of them means the scale ran out."""

    floored = forecast_of(300, 430, 0, 0)
    mismatch = forecast_of(300, 500, 0, 0)
    assert floored.estimate == mismatch.estimate == CONSTANTS.balance_floor
    assert floored.beyond_scale is False
    assert mismatch.beyond_scale is True


def test_the_percentage_is_rounded_half_away_from_zero_and_not_half_to_even():
    """The rule Python's built-in ``round`` does not implement.

    3,00 against 3,35 lands on exactly 82,5, and half-to-even sends it *down* to
    82 while sending its neighbours up — two forecasts a hundredth of a Level
    apart rounded in opposite directions, for no reason a player could be told.
    Away from zero is symmetric in sign and always the same direction for the
    same magnitude.
    """

    assert forecast_of(300, 335, 0, 0).estimate == 83
    assert round(82.5) == 82

    assert round_half_away_from_zero(82.5) == 83
    assert round_half_away_from_zero(83.5) == 84
    assert round_half_away_from_zero(-2.5) == -3
    assert round_half_away_from_zero(2.4999) == 2


def test_a_certain_roster_reports_the_gap_anybody_can_do_by_hand(every_forecast):
    """At zero Uncertainty the expectation collapses to the difference itself,
    which is the one case the arithmetic can be checked against mental arithmetic
    rather than against itself."""

    assert forecast_of(300, 350, 0, 0).expected_gap == pytest.approx(0.50)
    assert absolute_gap_deviation(0.5, 0.0) == 0.0


# --- The margin, and the grade of it --------------------------------------------


def test_there_is_no_separate_uncertainty_penalty(every_forecast):
    """The estimate is a function of the reported gap and nothing else.

    The source design subtracted a spread term from the percentage *after*
    computing it, which made the bar and the number two opinions and needed a
    correction to reconcile. Here uncertainty reaches the percentage only by
    widening the gap, so this reconstruction — from the reported gap, the clamp
    and the coefficient — has to reproduce the estimate exactly, for every
    roster. Anything subtracted on the way out would show up here as a constant
    offset.
    """

    clamp = as_float(CONSTANTS.gap_clamp)
    coefficient = as_float(CONSTANTS.gap_coefficient)
    for forecast in every_forecast:
        from_the_gap = round_half_away_from_zero(
            100.0 - coefficient * min(forecast.expected_gap, clamp)
        )
        assert forecast.estimate == from_the_gap


def test_the_margin_is_zero_exactly_when_the_platform_is_certain(every_forecast):
    for forecast in every_forecast:
        assert forecast.margin >= 0
    assert forecast_of(300, 350, 0, 0).margin == 0


def test_certainty_is_graded_from_the_margin_and_nothing_else(every_forecast):
    for forecast in every_forecast:
        if forecast.margin <= CONSTANTS.certain_margin:
            assert forecast.certainty is Certainty.HIGH
        elif forecast.margin <= CONSTANTS.unsure_margin:
            assert forecast.certainty is Certainty.MODERATE
        else:
            assert forecast.certainty is Certainty.LOW


def test_fit_to_print_reads_the_grade_rather_than_holding_its_own_copy(every_forecast):
    """Suppression is presentation. It is a property and not a field so that it
    cannot drift from the grade — and the estimate ranks either way."""

    for forecast in every_forecast:
        assert forecast.fit_to_print is (forecast.certainty is not Certainty.LOW)


def test_a_wider_uncertainty_never_raises_certainty():
    grades = [Certainty.HIGH, Certainty.MODERATE, Certainty.LOW]
    for level_b in (300, 320, 400):
        seen = [
            grades.index(forecast_of(300, level_b, sigma, sigma).certainty)
            for sigma in (0, 5, 15, 35, 60, 84, 120)
        ]
        assert seen == sorted(seen)


# --- No forecast, and why ---------------------------------------------------------


def test_a_seat_with_nobody_on_it_declines_rather_than_guessing():
    ada = skill("ada", 300, 20)
    empty = MatchSnapshot(
        sport=Sport.TENNIS,
        seats=(SeatSnapshot(ada), SeatSnapshot()),
        current_player=ada,
    )
    result = ENGINE.analyse(snapshot=empty, now=NOW).forecast
    assert isinstance(result, Err)
    assert result.reason == SidesNotFormed(sport="TENNIS", seated=1, sold=2)


def test_the_reason_is_a_machine_code_and_payload_never_a_sentence():
    """The clients own the words: a reason crosses the wire as ``{kind, …}``."""

    reason = SidesNotFormed(sport="PADEL", seated=4, sold=4)
    assert reason.kind == "sides_not_formed"
    assert not any(
        isinstance(value, str) and " " in value for value in vars(reason).values()
    )


def test_a_sport_this_version_cannot_split_declines_with_the_same_reason():
    """Four players admit three splits and this version enumerates none of them,
    so it says so rather than forecasting a pairing it did not choose."""

    snapshot = doubles(*[skill(str(i), 300 + 10 * i, 20) for i in range(4)])
    result = ENGINE.analyse(snapshot=snapshot, now=NOW).forecast
    assert isinstance(result, Err)
    assert result.reason.kind == "sides_not_formed"
    assert (result.reason.seated, result.reason.sold) == (4, 4)


# --- The engine's own contract ----------------------------------------------------


def test_the_engine_satisfies_the_protocol():
    assert isinstance(ENGINE, BalanceForecastEngine)
    assert ENGINE.version == ENGINE_VERSION


def test_every_result_carries_the_version_that_produced_it():
    """A constant is falsifiable only against results it can be attributed to."""

    for snapshot in (
        singles(skill("a", 300, 20), skill("b", 340, 20)),
        doubles(*[skill(str(i), 300, 20) for i in range(4)]),
    ):
        analysis = ENGINE.analyse(snapshot=snapshot, now=NOW)
        assert analysis.engine_version == ENGINE_VERSION


def test_the_same_inputs_produce_the_same_analysis():
    """No clock, no randomness, no state between calls."""

    snapshot = singles(skill("a", 300, 35), skill("b", 341, 22))
    first = ENGINE.analyse(snapshot=snapshot, now=NOW)
    second = ENGINE.analyse(snapshot=snapshot, now=NOW)
    assert first == second


@pytest.mark.parametrize("field", ["second", "microsecond"])
def test_an_instant_that_is_not_rounded_to_the_minute_is_refused(field):
    """A caller's bug, not a domain state: a result carrying seconds is one no
    cache can ever hit and no replay can reproduce."""

    snapshot = singles(skill("a", 300, 20), skill("b", 300, 20))
    with pytest.raises(InvariantViolated, match="not rounded to the minute"):
        ENGINE.analyse(snapshot=snapshot, now=NOW.replace(**{field: 1}))


def test_the_forecast_does_not_depend_on_the_instant_it_is_asked_at():
    """It takes ``now`` and reads nothing from it — asserted, because a term that
    starts reading it later should have to say so."""

    snapshot = singles(skill("a", 300, 35), skill("b", 341, 22))
    later = NOW.replace(year=2031, month=1, day=2, hour=3, minute=4)
    assert ENGINE.analyse(snapshot=snapshot, now=NOW).forecast == ENGINE.analyse(
        snapshot=snapshot, now=later
    ).forecast


@pytest.mark.parametrize("sport", [Sport.TENNIS, Sport.SQUASH])
def test_both_singles_sports_reach_the_same_arithmetic(sport):
    ada, bo = skill("ada", 300, 20), skill("bo", 350, 20)
    tennis = ENGINE.analyse(snapshot=singles(ada, bo, sport=Sport.TENNIS), now=NOW)
    other = ENGINE.analyse(snapshot=singles(ada, bo, sport=sport), now=NOW)
    assert tennis.forecast == other.forecast


def test_the_current_player_is_always_on_the_first_side():
    """A card drawing *you against them* from a result in seat order would draw
    it the wrong way round for half of all matches."""

    ada, bo = skill("ada", 320, 15), skill("bo", 280, 15)
    seated_first = forecast_of_snapshot(singles(ada, bo, viewer=ada))
    seated_second = forecast_of_snapshot(singles(ada, bo, viewer=bo))
    assert (seated_first.side_a, seated_first.side_b) == (ada.level, bo.level)
    assert (seated_second.side_a, seated_second.side_b) == (bo.level, ada.level)


def test_a_viewer_who_is_not_in_the_match_leaves_seat_order_alone():
    ada, bo = skill("ada", 320, 15), skill("bo", 280, 15)
    watcher = skill("cy", 300, 15)
    forecast = forecast_of_snapshot(singles(ada, bo, viewer=watcher))
    assert (forecast.side_a, forecast.side_b) == (ada.level, bo.level)


def test_orientation_does_not_move_the_prediction():
    """Sides are a rendering decision; the gap between them is symmetric."""

    ada, bo = skill("ada", 320, 15), skill("bo", 280, 40)
    one = forecast_of_snapshot(singles(ada, bo, viewer=ada))
    other = forecast_of_snapshot(singles(ada, bo, viewer=bo))
    assert (one.estimate, one.margin, one.certainty) == (
        other.estimate,
        other.margin,
        other.certainty,
    )


def forecast_of_snapshot(snapshot) -> BalanceForecast:
    result = ENGINE.analyse(snapshot=snapshot, now=NOW).forecast
    assert isinstance(result, Ok)
    return result.value


def test_every_value_object_in_the_vocabulary_is_frozen_and_closed():
    """``@final`` and ``frozen`` erase into nothing a behaviour test can see.

    The compiler *does* enforce both — ``tests/typecheck/kernel_misuse.py`` proves
    it, on a reason subclassed and a snapshot assigned to. What that harness
    cannot say is whether the decorator was applied to each class here, since a
    dropped one produces no error anywhere. So the list is written out: adding a
    value object means adding a line, which is the diff a reviewer should see.
    """

    vocabulary = (
        PlayerSkill,
        SeatSnapshot,
        MatchSnapshot,
        Side,
        SidesNotFormed,
        BalanceForecast,
        PairingAnalysis,
        PairingConstants,
    )
    unclosed = [
        cls.__name__ for cls in vocabulary if not getattr(cls, "__final__", False)
    ]
    unfrozen = [
        cls.__name__ for cls in vocabulary if not cls.__dataclass_params__.frozen
    ]
    assert unclosed == [], unclosed
    assert unfrozen == [], unfrozen


# --- Gates over the source, for the claims a runtime test cannot make -------------


def _modules_of(package: Path) -> list[Path]:
    return sorted(package.rglob("*.py"))


def _parsed(path: Path) -> ast.Module:
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def test_exactly_one_place_crosses_from_the_exact_vocabulary_into_floats():
    """*Where does this stop being exact* has one answer, and it is ``as_float``.

    A Level is a ``Ratio`` so that a doubles team strength is exact; a second
    ``float(...)`` somewhere else is a second place where that guarantee quietly
    ends, and it would end there for whoever reads that line only.
    """

    walked = _modules_of(PAIRING)
    crossings = [
        f"{path.relative_to(ROOT)}:{line} in {holder}"
        for path in walked
        for line, holder in _float_calls(_parsed(path))
    ]
    assert len(walked) >= 4, walked
    assert len(crossings) == 1, crossings
    assert crossings[0].endswith("in as_float"), crossings


def _float_calls(module: ast.Module) -> list[tuple[int, str]]:
    """Every ``float(...)`` in a module, with the function that holds it.

    Attributed by enclosing function rather than by line number: a pin on a line
    number goes red for a docstring edit, and a pin that goes red for the wrong
    reason is one somebody re-baselines without reading.
    """

    def calls(tree: ast.AST) -> list[int]:
        return [
            node.lineno
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "float"
        ]

    held = {
        line: node.name
        for node in ast.walk(module)
        if isinstance(node, ast.FunctionDef)
        for line in calls(node)
    }
    return sorted((line, held.get(line, "<module>")) for line in calls(module))


def test_the_pairing_engine_does_not_import_the_rating_engine():
    """Same algebra, different question — and a lineage that must stay its own.

    ``racketskill/core`` combines uncertainties about *one player*; this combines
    two independent estimates into the gap between two sides. Importing it would
    put a balance percentage at the mercy of a rating-engine retune, and the
    falsification programme rests on attributing a number to one lineage.
    """

    walked = _modules_of(PAIRING) + [
        ROOT / "app" / "engines" / "forecast.py",
        ROOT / "app" / "engines" / "matchmaking.py",
    ]
    offenders = [
        f"{path.relative_to(ROOT)}:{node.lineno}: {name}"
        for path in walked
        for node in ast.walk(_parsed(path))
        for name in _imported_names(node)
        if name.startswith("app.engines.racketskill")
    ]
    assert len(walked) >= 6, walked
    assert not offenders, (
        "the pairing engine reached for the rating engine:\n" + "\n".join(offenders)
    )


def _imported_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and not node.level:
        return [node.module or ""]
    return []


def test_every_constant_carries_the_measurement_that_would_falsify_it():
    """A constant with no falsifying measurement is a preference wearing a
    number's clothes, and retuning it is taste rather than science."""

    source = _parsed(PAIRING / "v1" / "constants.py")
    declared = next(
        node
        for node in ast.walk(source)
        if isinstance(node, ast.ClassDef) and node.name == "PairingConstants"
    )
    body = declared.body
    unfalsifiable = []
    for index, node in enumerate(body):
        if not isinstance(node, ast.AnnAssign) or not isinstance(node.target, ast.Name):
            continue
        following = body[index + 1] if index + 1 < len(body) else None
        note = (
            following.value.value
            if isinstance(following, ast.Expr)
            and isinstance(following.value, ast.Constant)
            and isinstance(following.value.value, str)
            else ""
        )
        if "Falsified by:" not in note:
            unfalsifiable.append(node.target.id)
    assert unfalsifiable == [], unfalsifiable
    assert (
        len([node for node in body if isinstance(node, ast.AnnAssign)]) == 4
    ), "the constant count moved — read the new one's falsifying note before pinning it"
