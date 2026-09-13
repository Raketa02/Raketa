"""A room without a game has ended exactly when its challenge is over.

``docs/adr/0164`` §6. The game's clock is a fold over the room's own stream
(``test_conversation_lifetime.py``); this is the other half — a fact about
**somebody else's record**, read through the port the room already reads its
membership from, on every read, and never stored. What is asserted here is the
seam: which rooms the port is asked about, what its answer does to them, and
that the one place every act on a room passes through refuses an ended one.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import pytest

from app.kernel import Sport, instant
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.lifetime import Lifetime
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import (
    DEPARTURE,
    SeatDeparture,
    SystemLineCode,
)
from app.modules.conversations.domain.errors import ConversationNotFound
from app.modules.conversations.domain.lifetime import CONVERSATION_GRACE
from tests.unit.fake_event_store import FrozenClock

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))


class _Court:
    """``ArrangingCourt``, answering from two dicts and remembering what it was
    asked — so a test can say the port was asked once, about these and not
    those."""

    def __init__(self, *, over=(), accepted=None) -> None:
        self._over = frozenset(over)
        self._accepted = accepted or {}
        self.asked: list[tuple[UUID, ...]] = []

    async def over_among(self, challenge_ids, *, now):
        self.asked.append(tuple(sorted(challenge_ids)))
        return self._over & frozenset(challenge_ids)

    async def accepted_on(self, challenge_ids):
        return {
            challenge_id: self._accepted[challenge_id]
            for challenge_id in challenge_ids
            if challenge_id in self._accepted
        }

    async def accepted_by(self, player_id):  # pragma: no cover - not asked here
        raise AssertionError("the lifetime never asks who accepted what")

    async def sport_of(self, challenge_id):  # pragma: no cover - not asked here
        raise AssertionError("the lifetime never asks for a sport")


class _NoGames:
    async def line_ups_of(self, game_ids):
        return {}

    async def game_of(self, challenge_id):  # pragma: no cover - not asked here
        return None


class _OneRoom:
    def __init__(self, room: Conversation) -> None:
        self._room = room

    async def load(self, conversation_id):
        return self._room if conversation_id == self._room.conversation_id else None

    async def load_for_append(self, conversation_id):
        return await self.load(conversation_id)


def _room(*, game_id: UUID | None = None) -> Conversation:
    room = Conversation.opened(
        conversation_id=uuid4(),
        challenge_id=uuid4(),
        sport=Sport.PADEL,
        occurred_at=NOW,
    )
    if game_id is not None:
        room.note_game(game_id=game_id, occurred_at=NOW)
    room.pull_events()
    return room


def _told_of_a_departure(room: Conversation) -> Conversation:
    room.record_line(
        code=SystemLineCode.SEAT_LEFT,
        actor_id=uuid4(),
        values={DEPARTURE: SeatDeparture.DECLINED.value},
        source_event_id=uuid4(),
        occurred_at=NOW,
    )
    return room


def _played(room: Conversation, *, at) -> Conversation:
    room.record_line(
        code=SystemLineCode.GAME_PLAYED,
        actor_id=uuid4(),
        values={},
        source_event_id=uuid4(),
        occurred_at=at,
    )
    return room


# -- which rooms have ended -------------------------------------------------


async def test_a_room_without_a_game_has_ended_when_its_challenge_is_over():
    room = _room()
    lifetime = Lifetime(arranging=_Court(over={room.challenge_id}))

    assert await lifetime.ended_among((room,), now=NOW) == {room.conversation_id}
    assert await lifetime.has_ended(room, now=NOW)


async def test_a_room_without_a_game_stands_while_its_challenge_does():
    """A departure line is not an end (``docs/adr/0164`` §6): the room was told
    somebody said no, and three people are still in it a year later."""

    room = _told_of_a_departure(_room())
    lifetime = Lifetime(arranging=_Court(over=()))

    a_year_on = instant(NOW + timedelta(days=365))
    assert await lifetime.ended_among((room,), now=a_year_on) == frozenset()
    assert not await lifetime.has_ended(room, now=a_year_on)


async def test_a_room_with_a_game_keeps_the_games_clock_and_the_port_is_not_asked():
    """``docs/adr/0153`` §2, untouched: 48 h after *we played*. The challenge is
    not consulted about a room that has a game — its end is the game's."""

    room = _played(_room(game_id=uuid4()), at=NOW)
    court = _Court(over={room.challenge_id})
    lifetime = Lifetime(arranging=court)

    just_before = instant(NOW + CONVERSATION_GRACE - timedelta(seconds=1))
    assert await lifetime.ended_among((room,), now=just_before) == frozenset()
    assert await lifetime.ended_among(
        (room,), now=instant(NOW + CONVERSATION_GRACE)
    ) == {room.conversation_id}
    assert court.asked == [], "the port is not asked about a room with a game"


async def test_a_whole_list_asks_once_about_the_rooms_without_a_game():
    arranging, over, played = _room(), _room(), _played(_room(game_id=uuid4()), at=NOW)
    court = _Court(over={over.challenge_id})
    lifetime = Lifetime(arranging=court)

    ended = await lifetime.ended_among(
        (arranging, over, played), now=instant(NOW + CONVERSATION_GRACE)
    )

    assert ended == {over.conversation_id, played.conversation_id}
    assert court.asked == [
        tuple(sorted((arranging.challenge_id, over.challenge_id)))
    ], "one question, about the two rooms whose end is the challenge's"


# -- the one seam every act on a room passes through -----------------------


@pytest.mark.parametrize("door", ["to_read", "to_append"])
async def test_every_act_on_a_room_whose_challenge_is_over_is_told_no_such_room(door):
    """``docs/adr/0153`` §5 — one code for *never existed*, *destroyed* and
    *past its end but not yet swept*, and the challenge being over is the third
    of those for a room without a game."""

    reader = uuid4()
    room = _room()
    court = _Court(
        over={room.challenge_id}, accepted={room.challenge_id: frozenset({reader})}
    )
    rooms = ARoomOfYours(
        conversations=_OneRoom(room),
        membership=Membership(arranging=court, played=_NoGames()),
        lifetime=Lifetime(arranging=court),
        clock=FrozenClock(at=NOW),
    )

    with pytest.raises(ConversationNotFound):
        await getattr(rooms, door)(room.conversation_id, reader)


async def test_a_member_of_a_room_whose_challenge_stands_is_let_in():
    reader = uuid4()
    room = _told_of_a_departure(_room())
    court = _Court(over=(), accepted={room.challenge_id: frozenset({reader})})
    rooms = ARoomOfYours(
        conversations=_OneRoom(room),
        membership=Membership(arranging=court, played=_NoGames()),
        lifetime=Lifetime(arranging=court),
        clock=FrozenClock(at=instant(NOW + timedelta(days=3))),
    )

    found = await rooms.to_read(room.conversation_id, reader)

    assert found.conversation is room
    assert found.members == frozenset({reader})
