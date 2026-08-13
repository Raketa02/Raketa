from dataclasses import FrozenInstanceError

import pytest

from app.kernel import SPORT_SPECS, Sport


def test_sport_is_a_closed_enum_of_exactly_four_values():
    assert [s.value for s in Sport] == ["PADEL", "TENNIS", "SQUASH", "BADMINTON"]


def test_every_sport_has_a_spec_and_no_orphans():
    assert set(SPORT_SPECS) == set(Sport)


@pytest.mark.parametrize(
    ("sport", "players", "durations"),
    [
        (Sport.PADEL, 4, (60, 90, 120)),
        (Sport.TENNIS, 2, (60, 90)),
        (Sport.SQUASH, 2, (45, 60, 90)),
        (Sport.BADMINTON, 4, (60, 90)),
    ],
)
def test_spec_carries_player_count_and_durations(sport, players, durations):
    spec = SPORT_SPECS[sport]
    assert spec.players == players
    assert spec.durations == durations


def test_specs_are_frozen():
    with pytest.raises(FrozenInstanceError):
        SPORT_SPECS[Sport.PADEL].players = 99  # type: ignore[misc]
