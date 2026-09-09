"""The sweep that makes a room's destruction real.

**What is asserted here is that the sweep decides nothing.** The end is derived
(``docs/adr/0153`` §5) and every route already answers ``conversation_not_found``
past it, so this loop exists to make the destruction real rather than to make the
answer right — which means the only interesting claims are *it destroys exactly
what has ended*, *it leaves what has not*, and *it can run beside itself*.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.kernel import Sport, instant
from app.modules.conversations.application.destroy_ended_conversations import (
    DestroyEndedConversations,
)
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import (
    DEPARTURE,
    SeatDeparture,
    SystemLineCode,
)
from tests.unit.fake_event_store import FrozenClock

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))


class _Rooms:
    """The repository and the directory over one dict, as the real pair share a
    repository."""

    def __init__(self, *rooms: Conversation) -> None:
        self.by_id: dict[UUID, Conversation] = {
            room.conversation_id: room for room in rooms
        }

    async def every_room(self) -> tuple[Conversation, ...]:
        return tuple(self.by_id.values())

    async def destroy(self, conversation_id: UUID) -> None:
        self.by_id.pop(conversation_id, None)


class _Uow:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def rollback(self) -> None:  # pragma: no cover - never reached here
        raise AssertionError("the sweep does not roll back")


def _room() -> Conversation:
    room = Conversation.opened(
        conversation_id=uuid4(),
        challenge_id=uuid4(),
        sport=Sport.PADEL,
        occurred_at=NOW,
    )
    room.pull_events()
    return room


def _played(room: Conversation, *, days: int) -> Conversation:
    room.note_game(game_id=uuid4(), occurred_at=NOW)
    room.record_line(
        code=SystemLineCode.GAME_PLAYED,
        actor_id=uuid4(),
        values={},
        source_event_id=uuid4(),
        occurred_at=instant(NOW + timedelta(days=days)),
    )
    room.pull_events()
    return room


def _abandoned(room: Conversation) -> Conversation:
    room.record_line(
        code=SystemLineCode.SEAT_LEFT,
        actor_id=uuid4(),
        values={DEPARTURE: SeatDeparture.LAPSED.value},
        source_event_id=uuid4(),
        occurred_at=NOW,
    )
    room.pull_events()
    return room


def _sweep(rooms: _Rooms, uow: _Uow, *, at) -> DestroyEndedConversations:
    return DestroyEndedConversations(
        directory=rooms,
        conversations=rooms,
        unit_of_work=uow,
        clock=FrozenClock(at=at),
    )


async def test_it_destroys_a_room_whose_episode_is_over():
    over = _played(_room(), days=1)
    rooms, uow = _Rooms(over), _Uow()

    swept = await _sweep(rooms, uow, at=instant(NOW + timedelta(days=4))).execute()

    assert rooms.by_id == {}
    assert (swept.walked, swept.destroyed) == (1, 1)
    assert uow.commits == 1


async def test_it_leaves_a_room_still_inside_its_grace():
    recent = _played(_room(), days=1)
    rooms, uow = _Rooms(recent), _Uow()

    swept = await _sweep(rooms, uow, at=instant(NOW + timedelta(days=2))).execute()

    assert list(rooms.by_id) == [recent.conversation_id]
    assert (swept.walked, swept.destroyed) == (1, 0)


async def test_it_leaves_a_room_that_is_still_arranging_alone_for_ever():
    """``docs/adr/0142`` §1 — a half-built court's end is the organiser's
    withdrawal, and this loop does not invent a clock for it."""

    arranging = _room()
    rooms, uow = _Rooms(arranging), _Uow()

    swept = await _sweep(
        rooms, uow, at=instant(NOW + timedelta(days=3650))
    ).execute()

    assert list(rooms.by_id) == [arranging.conversation_id]
    assert swept.destroyed == 0


async def test_it_walks_every_room_and_destroys_only_the_ended_ones():
    over, live, arranging = (
        _played(_room(), days=1),
        _played(_room(), days=3),
        _abandoned(_room()),
    )
    rooms, uow = _Rooms(over, live, arranging), _Uow()

    swept = await _sweep(rooms, uow, at=instant(NOW + timedelta(days=4))).execute()

    assert set(rooms.by_id) == {live.conversation_id}
    assert (swept.walked, swept.destroyed) == (3, 2)


async def test_a_second_run_destroys_nothing_and_still_commits():
    """``docs/adr/0092`` — with N API processes it runs N times per interval, and
    for a delete keyed on a fold that is exactly nothing."""

    rooms, uow = _Rooms(_played(_room(), days=1)), _Uow()
    sweep = _sweep(rooms, uow, at=instant(NOW + timedelta(days=4)))

    await sweep.execute()
    again = await sweep.execute()

    assert (again.walked, again.destroyed) == (0, 0)
    assert uow.commits == 2


async def test_a_run_that_finds_nothing_is_not_a_failure():
    rooms, uow = _Rooms(), _Uow()

    swept = await _sweep(rooms, uow, at=NOW).execute()

    assert (swept.walked, swept.destroyed) == (0, 0)
