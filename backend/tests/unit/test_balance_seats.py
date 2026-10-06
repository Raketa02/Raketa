"""The sport decides how many sit on a side, never a request (#579).

``seats_per_side`` moved to ``matchmaking/domain/balance.py`` with the forecast
that reads it when the line-ups went; the claim it carries is unchanged.
"""

from __future__ import annotations

import pytest

from app.kernel import Sport
from app.modules.matchmaking.domain.balance import seats_per_side


@pytest.mark.parametrize(
    "sport,per_side",
    [
        (Sport.PADEL, 2),
        (Sport.BADMINTON, 2),
        (Sport.TENNIS, 1),
        (Sport.SQUASH, 1),
    ],
)
def test_the_seat_count_is_the_sports_own_fact(sport, per_side):
    """A singles side is **full at one**, and that is what keeps a singles
    forecast from being marked provisional about nothing."""

    assert seats_per_side(sport) == per_side
