"""When a room stops existing, and what it is anchored on.

``docs/adr/0153``, with §3 superseded by ``docs/adr/0164`` §6. Every test here
names the anchor it is defending, because the whole record is about *which fact
the instant is read off* rather than about the number: an end dated from the
plan's agreed point would be one two people could walk forward by tapping a chip,
and an end stored in a column would be a second copy of the fact that decides
whether a room exists at all.

**There is no departure anchor, and half of this file is that absence.** A room
without a game has no clock of its own: it lives as long as its challenge, which
is read through a port and asserted one seam out
(``test_a_room_lives_as_long_as_its_challenge.py``).

**Nothing here reads a clock.** The derivation takes the room and answers an
instant; ``ended_by_its_game`` takes the instant as well. That is what lets a
test say *a game played on day 1 ends its room on day 3* without moving
anything.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from app.kernel import Sport, instant
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import (
    COUNT,
    DEPARTURE,
    SeatDeparture,
    SystemLineCode,
)
from app.modules.conversations.domain.lifetime import (
    CONVERSATION_GRACE,
    ended_by_its_game,
    game_ends_it_at,
)
from app.modules.games.domain.windows import (
    ENTRY_GRACE,
    PLAN_HORIZON,
    entry_closes_at,
)

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))


def _later(**kwargs) -> "datetime":
    return instant(NOW + timedelta(**kwargs))


def _opened() -> Conversation:
    return Conversation.opened(
        conversation_id=uuid4(),
        challenge_id=uuid4(),
        sport=Sport.PADEL,
        occurred_at=NOW,
    )


def _line(room: Conversation, code: SystemLineCode, *, at, values=None) -> None:
    room.record_line(
        code=code,
        actor_id=uuid4(),
        values=values or {},
        source_event_id=uuid4(),
        occurred_at=at,
    )


def _departure(room: Conversation, *, at) -> None:
    _line(
        room,
        SystemLineCode.SEAT_LEFT,
        at=at,
        values={DEPARTURE: SeatDeparture.DECLINED.value},
    )


# -- the grace -------------------------------------------------------------


def test_the_grace_is_forty_eight_hours():
    """``docs/adr/0153`` §4 — ADR-0151's rule, second application: the default
    here is destruction, and 24 h *equals* the gap it has to outlast."""

    assert CONVERSATION_GRACE == timedelta(hours=48)


def test_the_grace_is_this_context_s_own_and_not_a_games_window():
    """``docs/adr/0153`` §4 — there is no interlock with ``ENTRY_GRACE`` here, so
    unlike ``PLAN_HORIZON`` the number lives with the room rather than beside the
    window it has nothing to do with."""

    assert CONVERSATION_GRACE != ENTRY_GRACE


# -- the game anchor -------------------------------------------------------


def test_a_room_whose_line_up_completed_ends_when_entry_closes():
    """``docs/adr/0153`` §2 — the instant *we played* stops being sayable."""

    room = _opened()
    room.note_game(game_id=uuid4(), occurred_at=_later(hours=1))

    assert game_ends_it_at(room) == entry_closes_at(_later(hours=1))


def test_the_anchor_is_the_moment_the_game_was_planned_and_never_the_room_s_own():
    """``docs/adr/0153`` §2 — ``Game.planned_at`` **is** ``GamePlanned.occurred_at``,
    and the room is already told it. A room opened on a first acceptance days
    before the line-up completed must not date its end from the opening."""

    room = _opened()
    planned = _later(days=3)
    room.note_game(game_id=uuid4(), occurred_at=planned)

    assert game_ends_it_at(room) == instant(planned + PLAN_HORIZON + ENTRY_GRACE)


def test_the_end_never_moves_later_once_the_game_is_known():
    """``docs/adr/0153`` §2 — ADR-0145 §5's refusal, put to a second job: the end
    is fixed at birth, and messages and slot lines afterwards do not move it."""

    room = _opened()
    planned = _later(hours=1)
    room.note_game(game_id=uuid4(), occurred_at=planned)
    fixed = game_ends_it_at(room)

    _line(room, SystemLineCode.DAY_RECORDED, at=_later(days=2), values={"value": "x"})
    room.say(
        author_id=uuid4(),
        client_message_id=uuid4(),
        text="still on?",
        occurred_at=_later(days=4),
    )

    assert game_ends_it_at(room) == fixed


# -- the played anchor -----------------------------------------------------


def test_a_game_played_on_day_one_ends_its_room_on_day_three():
    """``docs/adr/0153`` §5 — the instant moves as the room is told things, which
    is why it is derived and never stored."""

    room = _opened()
    room.note_game(game_id=uuid4(), occurred_at=NOW)
    played = _later(days=1)
    _line(room, SystemLineCode.GAME_PLAYED, at=played)

    assert game_ends_it_at(room) == instant(played + CONVERSATION_GRACE)
    assert game_ends_it_at(room) < entry_closes_at(NOW)


def test_the_earliest_anchor_wins_and_entry_closing_can_be_it():
    """A game played on the very last day it could be leaves less than a grace
    before entry closes, and the room goes then."""

    room = _opened()
    room.note_game(game_id=uuid4(), occurred_at=NOW)
    _line(room, SystemLineCode.GAME_PLAYED, at=_later(days=7, hours=23))

    assert game_ends_it_at(room) == entry_closes_at(NOW)


# -- the room without a game ------------------------------------------------


def test_a_room_without_a_game_has_no_end_here_whatever_it_was_told():
    """``docs/adr/0164`` §6 — there is no departure anchor. A room without a
    game lives exactly as long as its challenge, which is a fact about somebody
    else's record and not this stream's; so a departure line, a year on, is not
    an end."""

    room = _opened()
    _departure(room, at=_later(hours=2))

    assert game_ends_it_at(room) is None
    assert not ended_by_its_game(room, now=_later(days=365))


@pytest.mark.parametrize(
    "order",
    [
        pytest.param(
            (SystemLineCode.SEAT_ACCEPTED, SystemLineCode.SEAT_LEFT), id="yes-then-no"
        ),
        pytest.param(
            (SystemLineCode.SEAT_LEFT, SystemLineCode.SEAT_ACCEPTED), id="no-then-yes"
        ),
    ],
)
def test_the_order_the_answers_arrived_in_decides_nothing(order):
    """The shelf read the **last** membership line, so *B yes → D yes → C no*
    closed a room two days later while three people were still in it, and
    *B yes → C no → D yes* never did. Neither order is an anchor now."""

    room = _opened()
    for hours, code in enumerate(order, start=1):
        if code is SystemLineCode.SEAT_LEFT:
            _departure(room, at=_later(hours=hours))
        else:
            _line(room, code, at=_later(hours=hours))

    assert game_ends_it_at(room) is None


def test_a_fill_after_a_departure_is_the_same_room_with_no_clock_either():
    """A fill seats somebody new into the room that was already there
    (``docs/adr/0150``, ``docs/adr/0164`` §6) — and the room it continues has
    no end of its own to move."""

    room = _opened()
    _departure(room, at=_later(hours=2))
    _line(room, SystemLineCode.SEATS_INVITED, at=_later(hours=3), values={COUNT: "1"})

    assert game_ends_it_at(room) is None


def test_a_game_is_the_first_anchor_a_room_gets_and_a_departure_before_it_is_not_one():
    """A departure reopens one seat and disturbs nothing else, so a line-up that
    completed afterwards is the arrangement having concluded **into a game** —
    and the game's own anchor is the one that answers."""

    room = _opened()
    _departure(room, at=_later(hours=2))
    room.note_game(game_id=uuid4(), occurred_at=_later(hours=5))

    assert game_ends_it_at(room) == entry_closes_at(_later(hours=5))


def test_a_room_still_arranging_has_no_end_and_is_not_given_a_clock_of_its_own():
    """Its end is its challenge's end, read one seam out — and a withdrawal
    destroys the room in the same act rather than dating it."""

    room = _opened()
    _line(room, SystemLineCode.SEAT_ACCEPTED, at=_later(hours=1))

    assert game_ends_it_at(room) is None
    assert not ended_by_its_game(room, now=_later(days=365))


# -- the boundary ----------------------------------------------------------


def test_a_room_is_over_at_its_end_and_not_a_moment_after():
    """The same ``now >= closes_at`` boundary every window in this repository
    uses, so a reader does not have to remember which way one of them leans."""

    room = _opened()
    played = _later(hours=1)
    room.note_game(game_id=uuid4(), occurred_at=NOW)
    _line(room, SystemLineCode.GAME_PLAYED, at=played)

    end = instant(played + CONVERSATION_GRACE)
    assert not ended_by_its_game(room, now=instant(end - timedelta(seconds=1)))
    assert ended_by_its_game(room, now=end)


def test_the_end_survives_a_replay_because_it_is_derived_from_the_stream():
    """``docs/adr/0153`` §5 — there is no ``ends_at`` column, so a room folded
    back from its own events answers identically."""

    room = _opened()
    room.note_game(game_id=uuid4(), occurred_at=_later(hours=1))
    _line(room, SystemLineCode.GAME_PLAYED, at=_later(days=1))
    replayed = Conversation.from_history(room.pull_events())

    assert game_ends_it_at(replayed) == game_ends_it_at(room)
