"""The sweep that makes a room's destruction real.

**What is asserted here is that the sweep decides nothing.** The end is derived
(``docs/adr/0153`` §5) and every route already answers ``conversation_not_found``
past it, so this loop exists to make the destruction real rather than to make the
answer right — which means the only interesting claims are *it destroys exactly
what has ended*, *it leaves what has not*, and *it can run beside itself*.

**Ended is read off each room's own stream, through the one fold the reads use**
(``domain/lifetime.py``): a booked game's room is over on the game's clock, and a
room with no game is over already — so what the sweep deletes is exactly what
the list has already dropped.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from app.kernel import Sport, instant
from app.modules.conversations.application.destroy_ended_conversations import (
    DestroyEndedConversations,
)
from app.modules.conversations.domain.conversation import Conversation
from tests.unit.fake_event_store import FrozenClock

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))


def _later(**kwargs):
    return instant(NOW + timedelta(**kwargs))


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
        booking_id=uuid4(),
        sport=Sport.PADEL,
        occurred_at=NOW,
    )
    room.pull_events()
    return room


def _booked(*, days: int) -> Conversation:
    """A room born about a game booked for ``days`` from now. Its end is entry
    closing: the game's hour, plus the hour, plus a day."""

    room = _room()
    room.note_game(game_id=uuid4(), occurred_at=NOW, starts_at=_later(days=days))
    room.pull_events()
    return room


def _sweep(rooms: _Rooms, uow: _Uow, *, at) -> DestroyEndedConversations:
    return DestroyEndedConversations(
        directory=rooms,
        conversations=rooms,
        unit_of_work=uow,
        clock=FrozenClock(at=at),
    )


async def test_it_destroys_a_room_whose_game_is_over():
    over = _booked(days=1)
    rooms, uow = _Rooms(over), _Uow()

    swept = await _sweep(rooms, uow, at=_later(days=3)).execute()

    assert rooms.by_id == {}
    assert (swept.walked, swept.destroyed) == (1, 1)
    assert uow.commits == 1


async def test_it_leaves_a_room_whose_game_has_not_ended():
    standing = _booked(days=1)
    rooms, uow = _Rooms(standing), _Uow()

    swept = await _sweep(rooms, uow, at=_later(days=2)).execute()

    assert list(rooms.by_id) == [standing.conversation_id]
    assert (swept.walked, swept.destroyed) == (1, 0)


async def test_it_destroys_a_room_with_no_game_at_once():
    """Only a booked game opens a room (#575), so a room with no game is over —
    and the sweep is what makes that real."""

    gameless = _room()
    rooms, uow = _Rooms(gameless), _Uow()

    swept = await _sweep(rooms, uow, at=NOW).execute()

    assert rooms.by_id == {}
    assert (swept.walked, swept.destroyed) == (1, 1)


async def test_it_walks_every_room_and_destroys_only_the_ended_ones():
    over, standing, gameless = _booked(days=1), _booked(days=3), _room()
    rooms, uow = _Rooms(over, standing, gameless), _Uow()

    swept = await _sweep(rooms, uow, at=_later(days=3)).execute()

    assert set(rooms.by_id) == {standing.conversation_id}
    assert (swept.walked, swept.destroyed) == (3, 2)


async def test_a_second_run_destroys_nothing_and_still_commits():
    """``docs/adr/0092`` — with N API processes it runs N times per interval, and
    for a delete keyed on a fold that is exactly nothing."""

    rooms, uow = _Rooms(_booked(days=1)), _Uow()
    sweep = _sweep(rooms, uow, at=_later(days=3))

    await sweep.execute()
    again = await sweep.execute()

    assert (again.walked, again.destroyed) == (0, 0)
    assert uow.commits == 2


async def test_a_run_that_finds_nothing_is_not_a_failure():
    rooms, uow = _Rooms(), _Uow()

    swept = await _sweep(rooms, uow, at=NOW).execute()

    assert (swept.walked, swept.destroyed) == (0, 0)
