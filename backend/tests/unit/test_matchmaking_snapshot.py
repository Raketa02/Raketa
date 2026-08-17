"""The shared snapshot vocabulary: the brands, and what a snapshot refuses.

The brands themselves are checked by the compiler — ``NewType`` erases, so
``tests/typecheck/kernel_misuse.py`` is what proves a Level cannot be passed where
an Uncertainty is wanted. What is left for a runtime test is the half a type
cannot carry: which values a constructor refuses, and which shapes a snapshot
refuses to be built in.
"""

from dataclasses import FrozenInstanceError
from fractions import Fraction

import pytest

from app.engines.matchmaking import (
    HUNDREDTHS,
    MatchSnapshot,
    PlayerRef,
    SeatSnapshot,
    level,
    uncertainty,
)
from app.kernel import SPORT_SPECS, InvariantViolated, Sport
from tests.unit.matchmaking_snapshots import doubles, singles, skill


# --- The two brands -------------------------------------------------------------


def test_a_level_is_carried_in_hundredths_and_is_exact():
    assert level(320) == Fraction(320, HUNDREDTHS)
    assert level(320) == Fraction(16, 5)


def test_a_level_multiplied_out_does_not_drift():
    """The reason the vocabulary is exact rather than floating point.

    Nine tenths of 3,20 is 2,88 and a double says 2.8800000000000003. Nothing in
    the singles path multiplies a Level, but a doubles team strength is a
    ``Ratio``-weighted blend of two of them, and the whole point of landing the
    exact type now is that the blend arrives correct rather than nearly.
    """

    assert level(320) * Fraction(9, 10) == Fraction(288, HUNDREDTHS)
    assert float(level(320)) * 0.9 != 2.88


def test_an_uncertainty_may_be_zero_and_a_level_may_not():
    """*We are perfectly sure* is a limit case; *nowhere on the scale* is not."""

    assert uncertainty(0) == Fraction(0)
    with pytest.raises(InvariantViolated, match="level in hundredths: 0"):
        level(0)


def test_a_negative_rating_is_refused_by_the_kernel_ratio():
    with pytest.raises(InvariantViolated):
        level(-320)
    with pytest.raises(InvariantViolated):
        uncertainty(-1)


@pytest.mark.parametrize("build", [level, uncertainty], ids=["level", "uncertainty"])
def test_a_bool_is_refused(build):
    """`bool` is an `int`, so `level(True)` typechecks and means 0,01 — the one
    value in the type that is always a mistake, and a wrong answer rather than a
    loud one."""

    with pytest.raises(InvariantViolated, match="from a bool"):
        build(True)


def test_the_top_of_the_scale_is_deliberately_not_restated_here():
    """1,0–5,0 belongs to ``racketskill/core``; a second copy is the drift.

    ADR-0022 records the correct move if a second engine needs the bounds as
    vocabulary — promote them to the kernel and have the rating core import them —
    and this ticket's rule is that the kernel is not modified. So the snapshot
    carries what it is given above the floor, and this test is here so that
    somebody adding the bound later does it as a relocation rather than a copy.
    """

    assert level(900) == Fraction(9)


# --- The snapshot ---------------------------------------------------------------


def test_the_sold_seat_count_is_read_from_the_registry_not_carried():
    """*A sport's player count is never club-configurable.*"""

    assert singles(skill("a", 300, 20), skill("b", 300, 20)).sold_seats == 2
    assert doubles(*[skill(str(i), 300, 20) for i in range(4)]).sold_seats == 4
    for sport, spec in SPORT_SPECS.items():
        seats = tuple(SeatSnapshot() for _ in range(spec.players))
        snapshot = MatchSnapshot(
            sport=sport, seats=seats, current_player=skill("a", 300, 20)
        )
        assert snapshot.sold_seats == spec.players


def test_a_snapshot_with_the_wrong_number_of_seats_is_refused():
    """A two-seat padel match is not a match this platform sells, and the refusal
    is a broken precondition — an assembler bug — rather than a domain state."""

    with pytest.raises(InvariantViolated, match="PADEL is sold in 4 seats"):
        MatchSnapshot(
            sport=Sport.PADEL,
            seats=(
                SeatSnapshot(skill("a", 300, 20)),
                SeatSnapshot(skill("b", 300, 20)),
            ),
            current_player=skill("a", 300, 20),
        )


def test_occupants_are_the_seated_players_in_seat_order():
    ada, bo = skill("ada", 320, 15), skill("bo", 280, 40)
    assert singles(ada, bo).occupants == (ada, bo)
    assert doubles(ada, None, bo, None).occupants == (ada, bo)
    assert doubles(None, None, None, None).occupants == ()


def test_a_snapshot_is_frozen():
    snapshot = singles(skill("ada", 320, 15), skill("bo", 280, 40))
    with pytest.raises(FrozenInstanceError):
        snapshot.seats = ()  # type: ignore[misc]


def test_a_player_is_identified_by_a_ref_the_engine_only_compares():
    """The engine asks *is the current player in this seat* and nothing else, so
    the assembler is free to hand over whatever identity Matches ends up with."""

    ada = skill("ada", 320, 15)
    assert ada.player == PlayerRef("ada")
