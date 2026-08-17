"""The shared snapshot vocabulary: the brands, and what a snapshot refuses.

The brands themselves are checked by the compiler — ``NewType`` erases, so
``tests/typecheck/kernel_misuse.py`` is what proves a Level cannot be passed where
an Uncertainty is wanted. What is left for a runtime test is the half a type
cannot carry: which values a constructor refuses, and which shapes a snapshot
refuses to be built in.
"""

from dataclasses import FrozenInstanceError, replace
from datetime import date
from fractions import Fraction

import pytest

from app.engines.matchmaking import (
    HUNDREDTHS,
    ClubSnapshot,
    HourWindow,
    LadderQualification,
    PlayerProfile,
    PlayerScore,
    PlayHistory,
    PlayerRef,
    SeatSnapshot,
    SeatState,
    UnratedPlayer,
    Weekday,
    level,
    uncertainty,
)
from app.kernel import (
    SPORT_SPECS,
    CardAllowance,
    InvariantViolated,
    Sport,
    grosze,
    minute_of_day,
    minutes,
    percent,
)
from tests.unit.matchmaking_snapshots import (
    bare,
    doubles,
    on_seat,
    singles,
    skill,
    unrated,
)


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
        snapshot = bare(sport, seats, skill("a", 300, 20))
        assert snapshot.sold_seats == spec.players


def test_a_snapshot_with_the_wrong_number_of_seats_is_refused():
    """A two-seat padel match is not a match this platform sells, and the refusal
    is a broken precondition — an assembler bug — rather than a domain state."""

    with pytest.raises(InvariantViolated, match="PADEL is sold in 4 seats"):
        bare(
            Sport.PADEL,
            (on_seat(skill("a", 300, 20)), on_seat(skill("b", 300, 20))),
            skill("a", 300, 20),
        )


def test_occupants_are_the_seated_players_in_seat_order():
    ada, bo = skill("ada", 320, 15), skill("bo", 280, 40)
    assert singles(ada, bo).occupants == (ada, bo)
    assert doubles(ada, None, bo, None).occupants == (ada, bo)
    assert doubles(None, None, None, None).occupants == ()


# --- Seat states: borrowed vocabulary, and the one thing they cannot say ----------


def test_the_three_seat_states_are_the_commitment_rules_own_three_words():
    """Spelled verbatim, because renaming one here would fork the clock.

    The shared glossary's Roster entry is written in these three words — *the paid
    seats*, *a held seat*, *an empty seat* — so a fourth state or a different
    spelling is a change to a document, not to this file.
    """

    assert [state.value for state in SeatState] == ["paid", "held", "empty"]


def test_a_seated_occupant_and_an_empty_state_cannot_both_be_claimed():
    """An assembler that has lost track of a join, refused loudly.

    Both directions, because both are reachable and each one breaks a different
    count: an occupant on an empty seat inflates the roster, and an empty seat
    holding nobody-but-paid inflates the paid fraction viability will read.
    """

    ada = skill("ada", 320, 15)
    with pytest.raises(InvariantViolated, match="empty seat carrying occupant"):
        SeatSnapshot(state=SeatState.EMPTY, occupant=ada)
    with pytest.raises(InvariantViolated, match="paid seat carrying occupant None"):
        SeatSnapshot(state=SeatState.PAID)


def test_paid_and_held_seats_are_both_occupants_and_only_one_is_paid():
    """The distinction the balance forecast cannot see and viability lives on.

    ``occupants`` reads both, because a held seat's player is in the match and
    contributes their Level; ``paid_seats`` reads one, because whether they turn
    up is a different question and the only one the count is for.
    """

    ada, bo = skill("ada", 320, 15), skill("bo", 280, 40)
    match = singles(ada, bo, states=(SeatState.PAID, SeatState.HELD))
    assert match.occupants == (ada, bo)
    assert match.paid_seats == 1
    assert singles(ada, bo).paid_seats == 2
    assert doubles(ada, None, None, None).paid_seats == 1


# --- An occupant the platform cannot place on the scale ---------------------------


def test_an_unrated_player_carries_a_reference_and_nothing_else():
    """*A rating is never only a number*, so a player with none carries neither a
    Level nor an Uncertainty — rather than a Level-shaped hole beside a σ that
    would then be a σ of nothing."""

    nobody = unrated("cy")
    assert nobody == UnratedPlayer(player=PlayerRef("cy"))
    assert set(vars(nobody)) == {"player"}


def test_an_unrated_player_is_an_occupant_and_may_be_the_viewer():
    """A player rated at tennis and not at padel is still in the padel match they
    joined, and still the person a padel card is being drawn for."""

    ada = skill("ada", 320, 15)
    match = doubles(ada, unrated("cy"), None, None, viewer=unrated("dee"))
    assert match.occupants == (ada, unrated("cy"))
    assert match.current_player == unrated("dee")
    assert match.paid_seats == 2


def test_a_snapshot_is_frozen():
    snapshot = singles(skill("ada", 320, 15), skill("bo", 280, 40))
    with pytest.raises(FrozenInstanceError):
        snapshot.seats = ()  # type: ignore[misc]


def test_a_player_is_identified_by_a_ref_the_engine_only_compares():
    """The engine asks *is the current player in this seat* and nothing else, so
    the assembler is free to hand over whatever identity Matches ends up with."""

    ada = skill("ada", 320, 15)
    assert ada.player == PlayerRef("ada")


# --- What the player declared, and what a snapshot refuses to claim ---------------


def test_a_profile_that_declared_nothing_is_the_launch_state():
    """``PlayerProfile()`` is somebody who has said nothing, and every field is
    ``None`` — which a constraint term reads as *no limit* and never as *no
    measurement*."""

    silent = PlayerProfile()
    assert set(vars(silent).values()) == {None}
    assert len(vars(silent)) == 7


def test_an_empty_declaration_is_refused_rather_than_read_as_absence():
    """No declared day is silence; an empty *set* of days would mean *no day works*,
    which is not a state anybody can be in and would score every match at nothing.
    The two are one keystroke apart in an assembler."""

    with pytest.raises(InvariantViolated, match="empty day declaration"):
        PlayerProfile(days=frozenset())
    with pytest.raises(InvariantViolated, match="empty hour declaration"):
        PlayerProfile(hours=())


@pytest.mark.parametrize(
    "field_name, named",
    [
        ("maximum_per_seat", "maximum per seat"),
        ("travel_radius", "travel radius"),
        ("appetite", "appetite"),
        ("commitment_horizon", "commitment horizon"),
    ],
)
def test_a_negative_declaration_is_refused(field_name, named):
    """A ceiling of minus five złoty and a radius of minus ten minutes are
    assembler bugs, and every quantity derived from one would be quietly wrong."""

    with pytest.raises(InvariantViolated, match=f"a negative {named}"):
        PlayerProfile(**{field_name: -1})


def test_a_declared_window_runs_forwards_and_never_wraps_midnight():
    """A player who plays from 22:00 until 01:00 declares two windows, one either
    side. A wrapping window makes *is this start inside it* two comparisons joined
    by an ``or``, and leaves every reader to remember which kind they hold."""

    evening = HourWindow(start=minute_of_day(18 * 60), end=minute_of_day(21 * 60))
    assert (evening.start, evening.end) == (1080, 1260)
    with pytest.raises(InvariantViolated, match="an hour window from 1320 to 60"):
        HourWindow(start=minute_of_day(22 * 60), end=minute_of_day(60))
    with pytest.raises(InvariantViolated, match="an hour window from 600 to 600"):
        HourWindow(start=minute_of_day(600), end=minute_of_day(600))


def test_a_declared_day_is_numbered_the_way_a_date_numbers_it():
    """ISO numbering, so a match's local start day maps onto a declaration without
    a second convention being invented between the two. **Not a start of week**: a
    set of days has no first element and nothing here says a week begins on Monday."""

    assert [day.value for day in Weekday] == [1, 2, 3, 4, 5, 6, 7]
    assert Weekday(date(2026, 8, 17).isoweekday()) is Weekday.MONDAY


def test_the_three_ladder_states_are_three_facts_and_not_a_bool():
    """*Not in a ladder* and *in a ladder this match does not count for* are
    different facts, and a bool collapses them into the same low score."""

    assert [state.value for state in LadderQualification] == [
        "qualifies",
        "outside",
        "not_in_a_ladder",
    ]


def test_a_club_cannot_be_a_negative_distance_away():
    with pytest.raises(InvariantViolated, match="a negative travel time"):
        ClubSnapshot(travel_minutes=minutes(-1))


# --- The money the snapshot carries, and the pair that cannot contradict itself ---


def test_a_payable_above_its_share_is_refused():
    """The money kernel's own claim — *a payable is never negative and never exceeds
    its share* — holds by construction for anything built through ``payable_from``,
    and ``NewType`` erases. This is the one place that pair enters the engines, so it
    is the one place to check it."""

    match = doubles(*[skill(str(i), 300, 20) for i in range(4)])
    assert (match.seat_share, match.payable) == (2150, 2150)
    with pytest.raises(InvariantViolated, match="a payable of 3000"):
        replace(match, payable=grosze(3000))
    with pytest.raises(InvariantViolated, match="a payable of -1"):
        replace(match, payable=grosze(-1))


def test_a_club_card_lowers_the_payable_and_leaves_the_share_alone():
    """What a card is *for*, and the reason the price term reads the payable."""

    carded = doubles(
        *[skill(str(i), 300, 20) for i in range(4)],
        card=CardAllowance(amount=grosze(500)),
    )
    assert (carded.seat_share, carded.payable) == (2150, 1650)


# --- The two fields that ship dark ------------------------------------------------


def test_a_reliability_record_is_a_rate_and_lives_on_the_seat():
    """On the seat rather than beside the roster, so it cannot name somebody who is
    not in the match and needs no reference of its own to disagree with."""

    ada = skill("ada", 320, 15)
    seat = SeatSnapshot(
        state=SeatState.PAID, occupant=ada, score=PlayerScore(percent(90))
    )
    assert seat.score == PlayerScore(reliability=percent(90))
    for outside in (Fraction(-1, 100), Fraction(101, 100)):
        with pytest.raises(InvariantViolated, match="reliability outside 0..1"):
            PlayerScore(reliability=outside)


def test_an_empty_seat_has_nobody_to_have_a_record():
    """Otherwise a term reading it would be scoring a person who is not there."""

    with pytest.raises(InvariantViolated, match="empty seat carrying the record"):
        SeatSnapshot(state=SeatState.EMPTY, score=PlayerScore(percent(90)))


def test_the_dark_fields_are_absent_on_every_snapshot_the_helpers_build():
    """*Present and absent from day one*: the fields exist, and nothing the platform
    can assemble today fills them, so both evidence terms are excluded and Coverage
    says so. Lighting them up later is a constant change and not a signature one."""

    match = doubles(*[skill(str(i), 300, 20) for i in range(4)])
    assert match.history is None
    assert [seat.score for seat in match.seats] == [None] * 4


def test_no_play_history_and_an_empty_one_are_different_facts():
    """Absent is *the platform has never observed who plays with whom*; empty is
    *you have played none of these people*, which is an observation."""

    assert PlayHistory(played_recently=frozenset()) is not None
    assert PlayHistory(played_recently=frozenset({PlayerRef("bo")})) != PlayHistory(
        played_recently=frozenset()
    )
