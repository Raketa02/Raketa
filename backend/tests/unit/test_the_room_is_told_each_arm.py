"""``TellTheRoom``, arm by arm.

Three arms, all ``games``' (#575): a booked ``GamePlanned`` **opens** the room,
already about its game; ``GamePlayed`` writes the one line a room is told; and
``GameCalledOff`` **destroys** it. Each is driven here with the outbox's own
habit of delivering twice, because every write here has to be idempotent.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.application.events import DeliveryContext
from app.kernel import Sport
from app.modules.conversations.application.tell_the_room import TellTheRoom
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import SystemLine, SystemLineCode
from app.modules.conversations.domain.live import Nudge
from app.modules.games.domain.events import (
    GameCalledOff,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
    ResultProposed,
    SeatVacated,
)

NOW = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)
BOOKING = uuid4()
GAME = uuid4()
ANA = uuid4()
BO = uuid4()


def _at(minutes: int) -> datetime:
    return NOW + timedelta(minutes=minutes)


#: The hour the game is booked for — two days on, so the room stands.
HOUR = _at(2 * 24 * 60)


def _delivery() -> DeliveryContext:
    """One outbox row. A fresh id per call, because that is what a fresh row is."""

    return DeliveryContext(event_id=uuid4(), attempt=1, occurred_at=NOW)


def _booked(*, starts_at: datetime | None = HOUR, at: datetime = NOW) -> GamePlanned:
    """The game a booking opened: filed under the booking, with its hour."""

    return GamePlanned(
        game_id=GAME,
        challenge_id=BOOKING,
        sport=Sport.PADEL.value,
        kind="COUNTED",
        window=None,
        seatings=(),
        occurred_at=at,
        starts_at=starts_at,
    )


class _Rooms:
    """The repository and the directory, over a dict. **One object for both**,
    because the real pair share a repository so their stream versions agree."""

    def __init__(self) -> None:
        self.by_id: dict[UUID, Conversation] = {}
        self.saves = 0

    async def load(self, conversation_id: UUID) -> Conversation | None:
        return self.by_id.get(conversation_id)

    async def load_for_append(self, conversation_id: UUID) -> Conversation | None:
        return await self.load(conversation_id)

    async def for_booking(self, booking_id: UUID) -> Conversation | None:
        for room in self.by_id.values():
            if room.booking_id == booking_id:
                return room
        return None

    async def for_game(self, game_id: UUID) -> Conversation | None:
        for room in self.by_id.values():
            if room.game_id == game_id:
                return room
        return None

    async def save(self, conversation: Conversation) -> None:
        self.saves += 1
        conversation.pull_events()
        self.by_id[conversation.conversation_id] = conversation

    async def destroy(self, conversation_id: UUID) -> None:
        self.by_id.pop(conversation_id, None)

    async def every_room(self) -> tuple[Conversation, ...]:
        return tuple(self.by_id.values())

    async def for_bookings(self, booking_ids) -> tuple[Conversation, ...]:
        return tuple(r for r in self.by_id.values() if r.booking_id in booking_ids)

    # -- what a test asks it ------------------------------------------------

    @property
    def only(self) -> Conversation:
        assert len(self.by_id) == 1, f"{len(self.by_id)} rooms, expected one"
        return next(iter(self.by_id.values()))

    @property
    def lines(self) -> list[SystemLine]:
        return [entry for entry in self.only.entries if isinstance(entry, SystemLine)]


class _Nudges:
    """The live channel, recording what the room announced about itself."""

    def __init__(self) -> None:
        self.published: list[Nudge] = []

    async def nudge(self, nudge: Nudge) -> None:
        self.published.append(nudge)


def _teller(rooms: _Rooms, nudges: _Nudges | None = None) -> TellTheRoom:
    return TellTheRoom(conversations=rooms, directory=rooms, nudges=nudges or _Nudges())


@pytest.fixture
def rooms() -> _Rooms:
    return _Rooms()


@pytest.fixture
def nudges() -> _Nudges:
    return _Nudges()


# -- the opening -----------------------------------------------------------


async def test_a_booked_game_opens_its_room_already_about_it(rooms):
    """The mechanics §14.3 — *the chat opens when the game is booked*. Filed
    under the booking, born knowing the game, its moment and its hour, in one
    save — and the opening writes no line."""

    await _teller(rooms)(_booked(), _delivery())

    room = rooms.only
    assert room.booking_id == BOOKING
    assert room.game_id == GAME
    assert (room.planned_at, room.starts_at) == (NOW, HOUR)
    assert room.sport is Sport.PADEL
    assert room.opened_at == NOW
    assert room.entries == ()
    assert rooms.saves == 1


async def test_a_game_with_no_hour_opens_nothing(rooms):
    """A game with no hour is one a challenge's line-up completed into, and
    nothing opens a room for that any more (#575)."""

    await _teller(rooms)(_booked(starts_at=None), _delivery())

    assert rooms.by_id == {}


@pytest.mark.parametrize("same_row", [True, False], ids=["same-row", "fresh-row"])
async def test_a_redelivered_booking_opens_one_room(rooms, same_row):
    """The outbox is at-least-once: the second delivery finds the room filed
    under the booking, and the game it already knows does not move."""

    tell = _teller(rooms)
    row = _delivery()

    await tell(_booked(), row)
    opened = rooms.only.conversation_id
    await tell(_booked(at=_at(30)), row if same_row else _delivery())

    assert rooms.only.conversation_id == opened
    assert rooms.only.planned_at == NOW


async def test_the_opening_announces_nothing_because_it_moved_no_seq(rooms, nudges):
    """A frame says *the room is now this long*, and an opening changes no length.

    Nudging here would send every phone to the read path to be told what it
    already holds. The room's existence reaches a client on the ordinary list
    read, not on this channel.
    """

    await _teller(rooms, nudges)(_booked(), _delivery())

    assert nudges.published == []


# -- we played -------------------------------------------------------------


async def test_we_played_writes_one_line_into_the_game_s_room_and_nudges_it(
    rooms, nudges
):
    tell = _teller(rooms, nudges)
    await tell(_booked(), _delivery())

    await tell(GamePlayed(game_id=GAME, said_by=ANA, occurred_at=_at(1)), _delivery())

    (line,) = rooms.lines
    assert line.seq == 1
    assert line.code is SystemLineCode.GAME_PLAYED
    assert line.actor_id == ANA
    assert line.values == {}
    assert line.occurred_at == _at(1)
    assert nudges.published == [
        Nudge(conversation_id=rooms.only.conversation_id, last_seq=1)
    ]


async def test_the_same_outbox_row_delivered_twice_writes_one_line(rooms, nudges):
    """Idempotent on the **row** rather than on the event's contents. The
    redelivery nudges too, with the length the room already had — true, and a
    no-op to every phone already holding it."""

    tell = _teller(rooms, nudges)
    await tell(_booked(), _delivery())
    played = GamePlayed(game_id=GAME, said_by=ANA, occurred_at=_at(1))
    row = _delivery()

    await tell(played, row)
    await tell(played, row)

    assert len(rooms.lines) == 1
    assert [nudge.last_seq for nudge in nudges.published] == [1, 1]


async def test_we_played_with_no_room_to_write_it_in_is_a_safe_drop(rooms, nudges):
    """``GamePlayed`` is written strictly after the booking that opened the room,
    so a game with no room is one that never had one: nothing to hang the line
    on and nothing to retry."""

    await _teller(rooms, nudges)(
        GamePlayed(game_id=GAME, said_by=ANA, occurred_at=NOW), _delivery()
    )

    assert rooms.by_id == {}
    assert nudges.published == []


# -- the call-off ----------------------------------------------------------


async def test_a_call_off_destroys_the_room_and_writes_no_line(rooms, nudges):
    """``docs/adr/0165`` §3 — found through the game it was born about, destroyed
    in the same act, no line and no nudge: there is no room left to be a
    length."""

    tell = _teller(rooms, nudges)
    await tell(_booked(), _delivery())

    await tell(
        GameCalledOff(game_id=GAME, called_by=None, occurred_at=_at(5)), _delivery()
    )

    assert rooms.by_id == {}
    assert nudges.published == []


async def test_a_redelivered_call_off_is_a_no_op(rooms):
    """Destroying a room that is already gone is the state this asks for."""

    tell = _teller(rooms)
    await tell(_booked(), _delivery())
    called_off = GameCalledOff(game_id=GAME, called_by=ANA, occurred_at=_at(5))

    await tell(called_off, _delivery())
    await tell(called_off, _delivery())

    assert rooms.by_id == {}


async def test_a_call_off_for_a_game_with_no_room_does_nothing(rooms):
    await _teller(rooms)(
        GameCalledOff(game_id=GAME, called_by=ANA, occurred_at=NOW), _delivery()
    )

    assert rooms.by_id == {}


async def test_a_call_off_takes_only_its_own_game_s_room(rooms):
    tell = _teller(rooms)
    await tell(_booked(), _delivery())
    other_game, other_booking = uuid4(), uuid4()
    await tell(
        GamePlanned(
            game_id=other_game,
            challenge_id=other_booking,
            sport=Sport.TENNIS.value,
            kind="COUNTED",
            window=None,
            seatings=(),
            occurred_at=NOW,
            starts_at=HOUR,
        ),
        _delivery(),
    )

    await tell(
        GameCalledOff(game_id=GAME, called_by=None, occurred_at=_at(5)), _delivery()
    )

    assert rooms.only.booking_id == other_booking


# -- the events that reach no room -----------------------------------------


async def test_what_the_room_is_not_told_changes_nothing_even_if_handed_it(
    rooms, nudges
):
    """The teller is not subscribed to these (``telling.py``), and it has no arm
    for them either: a room handed one is left exactly as it was."""

    tell = _teller(rooms, nudges)
    await tell(_booked(), _delivery())

    for event in (
        SeatVacated(game_id=GAME, player_id=BO, occurred_at=_at(1)),
        LineUpReseated(game_id=GAME, seatings=(), occurred_at=_at(2)),
        ResultProposed(
            game_id=GAME, player_id=ANA, side="A", score="6-4", occurred_at=_at(4)
        ),
    ):
        await tell(event, _delivery())

    assert rooms.only.entries == ()
    assert nudges.published == []
