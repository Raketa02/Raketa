"""*Game moved*, in a player's words (#671, #672; the mechanics §17.2, Q122).

The club's own Move says where the game is and that nothing else changes. A
**move by cancel** also says why the court the game left can't be played, in
the words of the club's reason — *weather*, *repair*, *double booking* or
*other*.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.kernel import Sport, instant
from app.modules.bookings.domain.booking import CancelReason
from app.modules.notifications.application.words import Said, words_for
from app.modules.notifications.domain.notices import NoticeKind, Opens

#: Thursday 15 October 2026, 19:00 in Kraków.
THURSDAY_SEVEN = instant(datetime(2026, 10, 15, 17, tzinfo=timezone.utc))


def _moved(**facts) -> Said:
    return Said(
        kind=NoticeKind.GAME_MOVED,
        sport=Sport.PADEL,
        club="Bonarka Arena",
        starts_at=THURSDAY_SEVEN,
        opens=Opens.BOOKING,
        court_name="Court 3",
        indoor=True,
        **facts,
    )


def test_the_club_s_own_move_says_nothing_else_changes():
    words = words_for(_moved(moved_from="Court 2"))

    assert (words.title, words.body) == (
        "Bonarka Arena moved your game to Court 3 · Thu 19:00",
        "Padel · indoor · nothing else changes",
    )


@pytest.mark.parametrize(
    ("reason", "body"),
    [
        (
            CancelReason.REPAIR,
            "Court 2 can't be played · Padel · indoor · nothing else changes",
        ),
        (
            CancelReason.WEATHER,
            "Court 2 can't be played in this weather · Padel · indoor · nothing "
            "else changes",
        ),
        (
            CancelReason.DOUBLE_BOOKING,
            "Court 2 was booked twice · Padel · indoor · nothing else changes",
        ),
        (
            CancelReason.OTHER,
            "Court 2 isn't available · Padel · indoor · nothing else changes",
        ),
    ],
)
def test_a_move_by_cancel_says_why_the_court_it_left_can_t_be_played(reason, body):
    words = words_for(_moved(reason=reason.value, moved_from="Court 2"))

    assert words.title == "Bonarka Arena moved your game to Court 3 · Thu 19:00"
    assert words.body == body


def test_a_move_by_cancel_that_names_no_court_it_left_says_your_court():
    words = words_for(_moved(reason=CancelReason.REPAIR.value))

    assert words.body == (
        "Your court can't be played · Padel · indoor · nothing else changes"
    )
