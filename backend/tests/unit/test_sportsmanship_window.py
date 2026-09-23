"""The card's two clocks, pinned at both edges.

**Neither of them is configuration**, and neither is derivable from anything
else on the platform, so this file is the only place they are asserted. The
window is the whole of *when may I be asked how that evening went*: it opens the
day after the game and closes seven days later.

The boundaries are asserted **inclusive at the open and exclusive at the close**,
because a window written the other way round either asks somebody on the evening
itself or leaves a card in the list for an eighth day. Both are the failure the
constants exist to prevent, and neither would fail a test that only checked the
middle.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from app.kernel import instant
from app.modules.sportsmanship.domain.window import (
    CARD_OPENS_AFTER,
    CARD_STAYS_OPEN_FOR,
    card_closes_at,
    card_is_open,
    card_opens_at,
)

PLAYED_AT = instant(datetime(2026, 9, 1, 21, 30, tzinfo=timezone.utc))


def test_the_card_opens_the_day_after_the_game():
    """*An answer given in the ten minutes after losing 6-2 6-1 is not the
    answer wanted.*"""

    assert CARD_OPENS_AFTER == timedelta(days=1)
    assert card_opens_at(PLAYED_AT) == PLAYED_AT + timedelta(days=1)


def test_the_card_stays_for_seven_days_after_it_opens():
    assert CARD_STAYS_OPEN_FOR == timedelta(days=7)
    assert card_closes_at(PLAYED_AT) == PLAYED_AT + timedelta(days=8)


def test_nothing_is_asked_on_the_evening_itself():
    assert not card_is_open(played_at=PLAYED_AT, now=PLAYED_AT)
    assert not card_is_open(
        played_at=PLAYED_AT, now=instant(PLAYED_AT + timedelta(hours=23, minutes=59))
    )


def test_the_day_after_is_the_first_moment_the_card_is_open():
    assert card_is_open(played_at=PLAYED_AT, now=card_opens_at(PLAYED_AT))


def test_the_last_moment_of_the_seventh_day_is_still_open():
    assert card_is_open(
        played_at=PLAYED_AT,
        now=instant(card_closes_at(PLAYED_AT) - timedelta(minutes=1)),
    )


def test_the_closing_moment_is_already_shut():
    """Exclusive at the close: a card that expires at the instant it is asked
    about is expired, so the week is seven days and never seven and a bit."""

    assert not card_is_open(played_at=PLAYED_AT, now=card_closes_at(PLAYED_AT))
    assert not card_is_open(
        played_at=PLAYED_AT, now=instant(card_closes_at(PLAYED_AT) + timedelta(days=30))
    )
