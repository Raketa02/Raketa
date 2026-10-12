"""What the room is told, what it writes, and the events that write nothing.

The refusals are the point of this file. ``the-words.md`` §23.1 names them in
prose; ``app/modules/conversations/application/telling.py`` names them as data;
this walks the data so that **a line that quietly reappears turns the build red**
rather than being noticed by whoever next reads the event list.

**One context tells the room** (#575): a room is opened only by a booked game, so
the table is ``games``' events and nothing else's.

Membership is here too, because it is a **fold over another context's record**
and there is no seam further out that can see the rule on its own.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.kernel import InvariantViolated, Sport, instant
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.application.telling import (
    TELLINGS,
    TOLD_ABOUT,
    line_for,
)
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import SystemLineCode
from app.modules.games.domain.events import (
    AbsenceNoted,
    ArrivalNoted,
    GameCalledOff,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
    NoShowDisputed,
    NoShowReported,
    PresenceClaimed,
    PresenceConfirmed,
    ResultAccepted,
    ResultCorrected,
    ResultCountered,
    ResultProposed,
    SeatVacated,
)

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))

#: Every event ``games`` publishes about a game's court and its result. Spelled
#: out rather than imported from any register, because the thing under test is
#: whether this context has an answer for each of them — and a list derived from
#: the same place the answers come from could not fail.
EVERY_PUBLISHED_EVENT = (
    GamePlanned,
    SeatVacated,
    LineUpReseated,
    GameCalledOff,
    GamePlayed,
    ResultProposed,
    ResultCorrected,
    ResultCountered,
    ResultAccepted,
    NoShowReported,
    NoShowDisputed,
    AbsenceNoted,
    ArrivalNoted,
    PresenceClaimed,
    PresenceConfirmed,
)

WRITES_NOTHING = tuple(telling for telling in TELLINGS if telling.line is None)


def _row(event: type):
    return next(t for t in TELLINGS if t.event is event)


def test_every_published_event_has_an_answer_here():
    """A builder reading the event list must not have to guess."""

    assert {telling.event for telling in TELLINGS} == set(EVERY_PUBLISHED_EVENT)
    assert len(TELLINGS) == len(EVERY_PUBLISHED_EVENT), "one row per event"


@pytest.mark.parametrize(
    "telling", WRITES_NOTHING, ids=lambda telling: telling.event.__name__
)
def test_each_event_that_publishes_nothing_names_its_reason(telling):
    """``the-words.md`` §23.1 — a refusal with no reason beside it is how a line
    quietly reappears."""

    assert telling.line is None
    assert telling.why_nothing


def test_the_played_line_is_the_only_line_written():
    """Everything else a booked game publishes writes nothing into its room."""

    writes = {t.event: t.line for t in TELLINGS if t.line is not None}

    assert writes == {GamePlayed: SystemLineCode.GAME_PLAYED}
    assert {t.event for t in WRITES_NOTHING} == set(EVERY_PUBLISHED_EVENT) - {
        GamePlayed
    }


def test_every_code_a_stored_line_carries_is_still_a_code():
    """Nine codes and one written: the other eight stay so a stored line still
    folds, and a room whose stream will not fold is one the sweep cannot
    destroy."""

    assert len(SystemLineCode) == 9


def test_there_is_no_game_on_line():
    """``docs/adr/0146`` §6 — a folded standing has exactly one place to be true,
    and it is not a sentence in the backlog."""

    assert "GAME_ON" not in {code.value for code in SystemLineCode}
    assert _row(GamePlanned).line is None


def test_a_refused_line_is_not_a_refused_telling():
    """``the-words.md`` §23.1 — ``GamePlanned`` draws nothing and still arrives,
    because it is what opens a booked game's room, and the room's own end is
    anchored on it."""

    planned = _row(GamePlanned)

    assert planned.reaches_the_room and planned.line is None
    assert GamePlanned in TOLD_ABOUT


def test_the_room_is_told_exactly_the_rows_that_reach_it():
    """``TOLD_ABOUT`` is what the teller subscribes to, derived from the table:
    the booking that opens the room, the line it writes, and the call-off that
    destroys it."""

    assert TOLD_ABOUT == tuple(t.event for t in TELLINGS if t.reaches_the_room)
    assert set(TOLD_ABOUT) == {GamePlanned, GamePlayed, GameCalledOff}


def test_a_call_off_draws_nothing_and_has_the_largest_effect_of_any_telling():
    """``docs/adr/0165`` §3 — it **destroys** the room in the same act, so there
    is nobody left to read a line.

    The telling that draws the least is the one that must not be dropped: a
    refusal read as *do not deliver this* would leave every called-off game a
    readable room for ever.
    """

    called_off = _row(GameCalledOff)

    assert called_off.line is None and called_off.reaches_the_room
    assert "destroys" in called_off.why_nothing
    assert GameCalledOff in TOLD_ABOUT


def test_the_line_up_moving_reaches_the_room_not_at_all():
    """Membership reads the game's line-up live, so a departure and a re-seat
    move the roster the moment they commit, with no telling."""

    for event in (SeatVacated, LineUpReseated):
        assert _row(event).line is None
        assert event not in TOLD_ABOUT


def test_the_result_argument_never_reaches_the_room_at_all():
    """Refused on **scope** — ``games`` has its own conversation for it — so
    unlike the booking and the call-off, it is not even delivered."""

    for event in (ResultProposed, ResultCorrected, ResultCountered, ResultAccepted):
        assert event not in TOLD_ABOUT


def test_the_handler_asks_the_table_for_the_line_it_writes():
    """``line_for`` reads the code off the row, so a row edited to refuse the
    line cannot ship with the handler still writing one."""

    played = GamePlayed(game_id=uuid4(), said_by=uuid4(), occurred_at=NOW)

    assert line_for(played) is SystemLineCode.GAME_PLAYED


def test_an_event_that_writes_nothing_cannot_be_asked_for_a_line():
    """The handler asks only on the arms that write, so asking about a refusal is
    a caller bug and not a state."""

    called_off = GameCalledOff(game_id=uuid4(), called_by=None, occurred_at=NOW)

    with pytest.raises(InvariantViolated):
        line_for(called_off)


# -- membership ------------------------------------------------------------


class _LineUps:
    def __init__(self, line_ups=None) -> None:
        self._line_ups = line_ups or {}
        self.asked: list[tuple] = []

    async def line_ups_of(self, game_ids):
        self.asked.append(tuple(game_ids))
        return {
            game_id: self._line_ups[game_id]
            for game_id in game_ids
            if game_id in self._line_ups
        }

    async def bookings_played_by(self, player_id):
        return frozenset()


def _room(*, game_id=None) -> Conversation:
    room = Conversation.opened(
        conversation_id=uuid4(),
        booking_id=uuid4(),
        sport=Sport.PADEL,
        occurred_at=NOW,
    )
    if game_id is not None:
        room.note_game(game_id=game_id, occurred_at=NOW, starts_at=NOW)
    room.pull_events()
    return room


async def test_membership_is_the_game_s_current_line_up():
    """``docs/adr/0146`` §7, as ``docs/adr/0162`` amended it — read live, so a
    seat left and re-seated moves the room with it."""

    game_id = uuid4()
    four = frozenset(uuid4() for _ in range(4))
    room = _room(game_id=game_id)

    assert await Membership(played=_LineUps({game_id: four})).of_one(room) == four


async def test_a_room_whose_game_answers_about_nobody_has_no_members():
    """The one way this fold is allowed to fail, and it fails **closed**: an
    empty membership lets nobody in rather than everybody."""

    room = _room(game_id=uuid4())

    assert await Membership(played=_LineUps()).of_one(room) == frozenset()


async def test_a_room_with_no_game_has_no_members():
    room = _room()

    assert await Membership(played=_LineUps()).of((room,)) == {}


async def test_a_whole_list_costs_one_question_and_never_one_per_room():
    first, second, ana = uuid4(), uuid4(), uuid4()
    rooms = (_room(game_id=first), _room(game_id=second), _room())
    played = _LineUps({first: frozenset({ana}), second: frozenset({ana})})

    found = await Membership(played=played).of(rooms)

    assert found == {
        rooms[0].conversation_id: frozenset({ana}),
        rooms[1].conversation_id: frozenset({ana}),
    }
    assert len(played.asked) == 1
    assert set(played.asked[0]) == {first, second}
