"""The owed card, in a player's words (#673; the mechanics §17.2, Q123).

**The cancel notice promises the new game** its email already promises — *We'll
look for another game for you first* — to the players still in; a leaver's
cancel notice and a game called off at its cut-off promise nothing. **Your new
game** names the kind of court when the card is at the club and hour the
cancel took, since then the kind is what changed.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.kernel import Sport, instant
from app.modules.bookings.domain.booking import CancelReason
from app.modules.notifications.application.words import Said, words_for
from app.modules.notifications.domain.notices import NoticeKind, NoticeReason, Opens

#: Thursday 15 October 2026, 19:00 in Kraków.
THURSDAY_SEVEN = instant(datetime(2026, 10, 15, 17, tzinfo=timezone.utc))
PROMISE = "We'll look for another game for you first."


def _said(kind: NoticeKind, *, opens: Opens = Opens.BOOKING, **facts) -> Said:
    return Said(
        kind=kind,
        sport=Sport.PADEL,
        club="Bonarka Arena",
        starts_at=THURSDAY_SEVEN,
        opens=opens,
        **facts,
    )


@pytest.mark.parametrize(
    ("reason", "body"),
    [
        (
            CancelReason.REPAIR,
            "Bonarka Arena cancelled padel · Thu 15 Oct, 19:00 because a court "
            f"needs repair. {PROMISE}",
        ),
        (
            CancelReason.OTHER,
            f"Bonarka Arena cancelled padel · Thu 15 Oct, 19:00. {PROMISE}",
        ),
    ],
)
def test_the_club_s_cancel_promises_another_game_first(reason, body):
    held = words_for(_said(NoticeKind.GAME_CALLED_OFF, reason=reason.value))
    refunded = words_for(
        _said(NoticeKind.GAME_CALLED_OFF, reason=reason.value, amount_grosze=40_00)
    )

    assert (held.title, held.body) == ("Game called off · nothing was taken", body)
    assert (refunded.title, refunded.body) == (
        "Game called off · you're refunded 40 zł",
        body,
    )


def test_a_leaver_s_cancel_notice_promises_nothing():
    words = words_for(
        _said(
            NoticeKind.GAME_CALLED_OFF,
            reason=CancelReason.WEATHER.value,
            amount_grosze=40_00,
            you_left=True,
            opens=Opens.PROPOSAL,
        )
    )

    assert words.body == (
        "Bonarka Arena cancelled it because of the weather — you're refunded 40 zł."
    )


def test_a_game_called_off_at_its_cut_off_promises_nothing():
    words = words_for(
        _said(NoticeKind.GAME_CALLED_OFF, reason=NoticeReason.SHORT_AT_THE_CUT_OFF)
    )

    assert PROMISE not in words.body


@pytest.mark.parametrize(
    ("indoor", "body"),
    [
        (False, "The same players · outdoor · 40 zł a share — say yes to book it."),
        (True, "The same players · indoor · 40 zł a share — say yes to book it."),
        # Another club, another hour — or courts of both kinds free there.
        (None, "The same players · 40 zł a share — say yes to book it."),
    ],
)
def test_your_new_game_names_the_kind_of_court_when_it_is_known(indoor, body):
    words = words_for(
        _said(NoticeKind.NEW_GAME, amount_grosze=40_00, indoor=indoor, opens=Opens.DECK)
    )

    assert (words.title, words.body) == (
        "Your new game · Thu 19:00 at Bonarka Arena",
        body,
    )
