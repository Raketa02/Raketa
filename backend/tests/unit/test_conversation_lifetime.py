"""When a room stops existing, and what it is anchored on.

``docs/adr/0153``. Every test here names the anchor it is defending, because the
whole record is about *which fact the instant is read off* rather than about the
number: an end stored in a column would be a second copy of the fact that decides
whether a room exists at all.

**A room is about a booked game, and a room without one has ended** (#575). Only
a booked game opens a room, and it is born knowing the game; a room with no game
is one a challenge opened, and nothing it could still be waiting for is read.

**Nothing here reads a clock.** ``game_ends_it_at`` takes the room and answers an
instant; ``has_ended`` and ``ended_among`` take the instant as well. That is what
lets a test say *the room goes a day after the game's hour* without moving
anything.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from app.kernel import Sport, instant
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import SystemLineCode
from app.modules.conversations.domain.lifetime import (
    CONVERSATION_GRACE,
    ended_among,
    game_ends_it_at,
    has_ended,
)
from app.modules.games.domain.windows import (
    A_BOOKED_GAME,
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
        booking_id=uuid4(),
        sport=Sport.PADEL,
        occurred_at=NOW,
    )


def _booked(*, hour, booked_at=NOW) -> Conversation:
    """A room as a booked game opens it: born about the game and its hour."""

    room = _opened()
    room.note_game(game_id=uuid4(), occurred_at=booked_at, starts_at=hour)
    return room


def _played(room: Conversation, *, at) -> None:
    room.record_line(
        code=SystemLineCode.GAME_PLAYED,
        actor_id=uuid4(),
        values={},
        source_event_id=uuid4(),
        occurred_at=at,
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


def test_a_booked_game_s_room_ends_when_entry_closes_measured_from_its_hour():
    """``docs/adr/0153`` §2 — the instant *we played* stops being sayable, and a
    booked game is played at its hour (#541)."""

    hour = _later(days=2)
    room = _booked(hour=hour)

    assert game_ends_it_at(room) == entry_closes_at(NOW, starts_at=hour)
    assert game_ends_it_at(room) == instant(hour + A_BOOKED_GAME + ENTRY_GRACE)


def test_a_booking_a_fortnight_ahead_does_not_end_its_room_before_the_game():
    """A week from the booking would end the room before anybody played."""

    hour = _later(days=14)
    room = _booked(hour=hour)

    assert not has_ended(room, now=instant(NOW + PLAN_HORIZON + ENTRY_GRACE))
    assert not has_ended(room, now=hour)
    assert has_ended(room, now=instant(hour + A_BOOKED_GAME + ENTRY_GRACE))


def test_a_game_with_no_hour_has_its_week_from_the_moment_it_was_planned():
    """A room told its game without an hour is one stored before #541; its end
    is still the game's entry window, a week from ``planned_at``."""

    room = _opened()
    planned = _later(days=3)
    room.note_game(game_id=uuid4(), occurred_at=planned)

    assert game_ends_it_at(room) == instant(planned + PLAN_HORIZON + ENTRY_GRACE)


def test_the_end_never_moves_later_once_the_game_is_known():
    """``docs/adr/0153`` §2 — the end is fixed at birth, and what is said in the
    room afterwards does not move it."""

    room = _booked(hour=_later(days=1))
    fixed = game_ends_it_at(room)

    room.say(
        author_id=uuid4(),
        client_message_id=uuid4(),
        text="still on?",
        occurred_at=_later(days=1, hours=2),
    )

    assert game_ends_it_at(room) == fixed


# -- the played anchor -----------------------------------------------------


def test_a_game_played_on_day_one_ends_its_room_on_day_three():
    """``docs/adr/0153`` §5 — the instant moves as the room is told things, which
    is why it is derived and never stored. Shown on a game with no hour, whose
    week leaves room for the grace to come first."""

    room = _opened()
    room.note_game(game_id=uuid4(), occurred_at=NOW)
    played = _later(days=1)
    _played(room, at=played)

    assert game_ends_it_at(room) == instant(played + CONVERSATION_GRACE)
    assert game_ends_it_at(room) < entry_closes_at(NOW)


def test_the_earliest_anchor_wins_and_entry_closing_can_be_it():
    """A booked game played at its hour leaves less than a grace before entry
    closes, and the room goes then."""

    hour = _later(days=1)
    room = _booked(hour=hour)
    _played(room, at=instant(hour + A_BOOKED_GAME))

    assert game_ends_it_at(room) == entry_closes_at(NOW, starts_at=hour)


# -- the room without a game -----------------------------------------------


def test_a_room_with_no_game_has_ended():
    """Only a booked game opens a room, and it is born about it. A room with no
    game is over from the moment it is read — every route answers
    ``conversation_not_found`` and the sweep destroys it."""

    room = _opened()

    assert game_ends_it_at(room) is None
    assert has_ended(room, now=NOW)
    assert has_ended(room, now=room.opened_at)


# -- the boundary ----------------------------------------------------------


def test_a_room_is_over_at_its_end_and_not_a_moment_before():
    """The same ``now >= closes_at`` boundary every window in this repository
    uses, so a reader does not have to remember which way one of them leans."""

    room = _booked(hour=_later(days=1))
    end = game_ends_it_at(room)

    assert not has_ended(room, now=instant(end - timedelta(seconds=1)))
    assert has_ended(room, now=end)


def test_the_end_survives_a_replay_because_it_is_derived_from_the_stream():
    """``docs/adr/0153`` §5 — there is no ``ends_at`` column, so a room folded
    back from its own events answers identically."""

    room = _booked(hour=_later(days=1))
    _played(room, at=_later(days=1, hours=1))
    replayed = Conversation.from_history(room.pull_events())

    assert game_ends_it_at(replayed) == game_ends_it_at(room)


# -- a whole list ------------------------------------------------------------


def test_ended_among_names_exactly_the_rooms_that_are_over():
    """The list drops, and the sweep destroys, what this names — one fold, so the
    two cannot come to two answers about one room."""

    over = _booked(hour=_later(days=1))
    standing = _booked(hour=_later(days=3))
    gameless = _opened()
    now = _later(days=2, hours=2)

    assert ended_among((over, standing, gameless), now=now) == frozenset(
        {over.conversation_id, gameless.conversation_id}
    )
    assert ended_among((), now=now) == frozenset()
