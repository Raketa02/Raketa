"""**A hold stops you writing anywhere another player sees it, and never stops
you reading** (``docs/adr/0148`` §9).

The hold's own argument is about **reach** — *a hold that stops you searching but
lets you send invitations is the same hole with the blast radius pointed at other
people* — and a message is reach. But a hold must not erase an arrangement other
people are already inside: they still need to read what was said and see who is
in the room.

Asserted here rather than at the HTTP seam because the provider is ``cases``,
which does not exist: every route in the suite runs against a hold query whose
true answer is *nobody*, so a test that went through the app would be asserting
the null object. What is under test is the rule, and the rule lives in the use
cases.

**It refuses the send and all three slot writes**, and this file covers all four
— because ADR-0148 §9 states them in one breath and the way that sentence goes
wrong is by half of it being implemented. A slot change writes a system line into
a room other people are in, so it is reach in exactly the sense a message is; the
plan **read** is ungated for exactly the reason the conversation reads are.
"""

from __future__ import annotations

from datetime import date, datetime, time, timezone
from typing import Collection
from uuid import UUID, uuid4

import pytest

from app.kernel import Sport, instant
from app.modules.conversations.application.commands import (
    ReadConversationCommand,
    ReadEntriesCommand,
    SendMessageCommand,
)
from app.modules.conversations.application.a_room_of_yours import ARoomOfYours
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.application.read_conversation import ReadConversation
from app.modules.conversations.application.read_entries import ReadEntries
from app.modules.conversations.application.send_message import SendMessage
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.errors import ConversationNotFound
from app.modules.conversations.domain.live import Nudge
from app.modules.conversations.domain.ports import MemberFace
from app.modules.games.domain.ports import PlannableGame
from app.modules.plans.application.commands import (
    ReadPlansCommand,
    SetDayCommand,
    SetHourCommand,
    SetPlaceCommand,
)
from app.modules.plans.application.read_plans import ReadPlans
from app.modules.plans.application.record_a_slot import SetDay, SetHour, SetPlace
from app.modules.plans.domain.plan import Plan
from app.shared.domain.errors import AccountHeld

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))
HELD = uuid4()
BESIDE_THEM = uuid4()
A_STRANGER = uuid4()
CHALLENGE = uuid4()
GAME = uuid4()


class _FrozenClock:
    def now(self):
        return NOW


class _OneRoom:
    """The repository, holding one room and remembering what was appended."""

    def __init__(self, room: Conversation) -> None:
        self.room = room
        self.saved: list[Conversation] = []

    async def load(self, conversation_id: UUID) -> Conversation | None:
        return self.room if conversation_id == self.room.conversation_id else None

    async def load_for_append(self, conversation_id: UUID) -> Conversation | None:
        return await self.load(conversation_id)

    async def for_challenge(self, challenge_id: UUID) -> Conversation | None:
        return self.room if challenge_id == self.room.challenge_id else None

    async def save(self, conversation: Conversation) -> None:
        self.saved.append(conversation)


class _TheCourt:
    async def accepted_on(self, challenge_ids: Collection[UUID]):
        return {
            challenge_id: frozenset({HELD, BESIDE_THEM})
            for challenge_id in challenge_ids
        }

    async def accepted_by(self, player_id: UUID):
        return frozenset({CHALLENGE})

    async def sport_of(self, challenge_id: UUID):
        return Sport.PADEL


class _NoGames:
    async def line_ups_of(self, game_ids: Collection[UUID]):
        return {}


class _Faces:
    async def faces_of(self, player_ids: Collection[UUID]):
        return {
            player_id: MemberFace(player_id=player_id, nickname="somebody")
            for player_id in player_ids
        }


class _HoldOn:
    """The provider that does not exist yet, answering about one person."""

    def __init__(self, *held: UUID) -> None:
        self._held = frozenset(held)

    async def held_among(self, player_ids: Collection[UUID]) -> frozenset[UUID]:
        return self._held & frozenset(player_ids)


class _Uow:
    def __init__(self) -> None:
        self.commits = 0

    async def commit(self) -> None:
        self.commits += 1

    async def flush(self) -> None:
        return None

    async def rollback(self) -> None:
        return None


@pytest.fixture
def room() -> Conversation:
    opened = Conversation.opened(
        conversation_id=uuid4(),
        challenge_id=CHALLENGE,
        sport=Sport.PADEL,
        occurred_at=NOW,
    )
    opened.say(
        author_id=BESIDE_THEM,
        client_message_id=uuid4(),
        text="six on Thursday?",
        occurred_at=NOW,
    )
    opened.pull_events()
    return opened


@pytest.fixture
def membership() -> Membership:
    return Membership(arranging=_TheCourt(), played=_NoGames())


class _Nudges:
    """The live channel, recording what the room announced about itself."""

    def __init__(self) -> None:
        self.published: list[Nudge] = []

    async def nudge(self, nudge: Nudge) -> None:
        self.published.append(nudge)


def _send(
    room: Conversation,
    membership: Membership,
    holds,
    *,
    conversations: _OneRoom | None = None,
    uow: _Uow | None = None,
    nudges: _Nudges | None = None,
) -> SendMessage:
    repository = conversations or _OneRoom(room)
    return SendMessage(
        rooms=ARoomOfYours(
            conversations=repository, membership=membership, clock=_FrozenClock()
        ),
        conversations=repository,
        holds=holds,
        # A hold refuses the send **before** anything is recorded, so the live
        # channel is the thing that must stay silent — which is what
        # `test_a_held_member_writes_nothing_at_all` reads off this list.
        nudges=nudges or _Nudges(),
        uow=uow or _Uow(),
        clock=_FrozenClock(),
    )


async def test_a_held_member_cannot_say_anything(room, membership):
    """A message is reach, and reach is what a hold stops."""

    with pytest.raises(AccountHeld) as refused:
        await _send(room, membership, _HoldOn(HELD)).execute(
            SendMessageCommand(
                conversation_id=room.conversation_id,
                author_id=HELD,
                client_message_id=uuid4(),
                text="I'm in",
            )
        )

    assert refused.value.code == "account_held"


async def test_a_held_member_writes_nothing_at_all(room, membership):
    """A refusal records nothing — not a bubble nobody can see."""

    conversations = _OneRoom(room)
    send = _send(room, membership, _HoldOn(HELD), conversations=conversations)

    with pytest.raises(AccountHeld):
        await send.execute(
            SendMessageCommand(
                conversation_id=room.conversation_id,
                author_id=HELD,
                client_message_id=uuid4(),
                text="I'm in",
            )
        )

    assert conversations.saved == []
    assert len(room.entries) == 1


async def test_a_held_member_still_reads_the_room(room, membership):
    """**A hold may not erase an arrangement other people are already inside.**
    They still need to read what was said and reach the people in it."""

    read = ReadConversation(
        rooms=ARoomOfYours(
            conversations=_OneRoom(room), membership=membership, clock=_FrozenClock()
        ),
        faces=_Faces(),
        clock=_FrozenClock(),
    )

    _, opened = await read.execute(
        ReadConversationCommand(conversation_id=room.conversation_id, reader_id=HELD)
    )

    assert len(opened.entries) == 1
    assert {member.player_id for member in opened.members} == {HELD, BESIDE_THEM}


async def test_a_held_member_still_pages_backward(room, membership):
    """Every read on this context is ungated, and that is the whole rule's
    second half."""

    entries = await ReadEntries(
        rooms=ARoomOfYours(
            conversations=_OneRoom(room), membership=membership, clock=_FrozenClock()
        )
    ).execute(
        ReadEntriesCommand(
            conversation_id=room.conversation_id,
            reader_id=HELD,
            before_seq=None,
            limit=50,
        )
    )

    assert [entry.seq for entry in entries] == [1]


async def test_a_non_member_is_refused_before_the_hold_is_ever_asked(room, membership):
    """Membership is the gate, and it answers first: a stranger is told there is
    no such room, never that their account is held — which would be an answer
    about a room they may not know exists."""

    with pytest.raises(ConversationNotFound):
        await _send(room, membership, _HoldOn(A_STRANGER)).execute(
            SendMessageCommand(
                conversation_id=room.conversation_id,
                author_id=A_STRANGER,
                client_message_id=uuid4(),
                text="hello",
            )
        )


async def test_a_member_who_is_not_held_says_what_they_like(room, membership):
    conversations = _OneRoom(room)
    uow = _Uow()
    send = _send(room, membership, _HoldOn(), conversations=conversations, uow=uow)

    message = await send.execute(
        SendMessageCommand(
            conversation_id=room.conversation_id,
            author_id=HELD,
            client_message_id=uuid4(),
            text="seven suits me",
        )
    )

    assert message.seq == 2
    assert conversations.saved == [room]
    assert uow.commits == 1


async def test_a_held_member_reaches_nobodys_phone_either(room, membership):
    """A hold is about **reach**, and the live channel is reach.

    A refusal that recorded nothing but still nudged would tell every other phone
    in the room to go and look — at nothing. The refusal comes before the append,
    so the announcement never happens rather than being suppressed afterwards.
    """

    nudges = _Nudges()
    send = _send(room, membership, _HoldOn(HELD), nudges=nudges)

    with pytest.raises(AccountHeld):
        await send.execute(
            SendMessageCommand(
                conversation_id=room.conversation_id,
                author_id=HELD,
                client_message_id=uuid4(),
                text="I'm in",
            )
        )

    assert nudges.published == []


async def test_a_message_that_lands_announces_the_rooms_new_length(room, membership):
    """**A nudge published on append**, carrying `last_seq` and nothing else."""

    nudges = _Nudges()
    send = _send(room, membership, _HoldOn(), nudges=nudges)

    await send.execute(
        SendMessageCommand(
            conversation_id=room.conversation_id,
            author_id=HELD,
            client_message_id=uuid4(),
            text="seven?",
        )
    )

    assert nudges.published == [
        Nudge(conversation_id=room.conversation_id, last_seq=room.last_seq)
    ]


# ---------------------------------------------------------------------------
# The three slot writes, and the read beside them
# ---------------------------------------------------------------------------


class _ACourtStillArranging:
    """``PlanningCourt``, answering about one game that is open to planning."""

    async def plannable_for(self, player_id: UUID, *, now):
        return {GAME: PlannableGame(planned_at=NOW, open_to_planning=True)}


class _OnePlan:
    """The repository, holding one plan and remembering what was appended."""

    def __init__(self) -> None:
        self.plan = Plan.unwritten(GAME)
        self.saved: list[Plan] = []

    async def load(self, game_id: UUID) -> Plan:
        return self.plan

    async def save(self, plan: Plan) -> None:
        self.saved.append(plan)


class _NoPlans:
    async def for_games(self, game_ids):
        return ()


def _collaborators(holds, plans: _OnePlan, uow: _Uow) -> dict:
    return {
        "plans": plans,
        "court": _ACourtStillArranging(),
        "holds": holds,
        "uow": uow,
        "clock": _FrozenClock(),
    }


async def test_a_held_member_cannot_set_the_place():
    """A slot change writes a line other people read, so it is reach."""

    plans, uow = _OnePlan(), _Uow()
    place = SetPlace(**_collaborators(_HoldOn(HELD), plans, uow))

    with pytest.raises(AccountHeld) as refused:
        await place.execute(
            SetPlaceCommand(game_id=GAME, player_id=HELD, place="Zabłocie Sport")
        )

    assert refused.value.code == "account_held"
    assert plans.saved == []
    assert uow.commits == 0


async def test_a_held_member_cannot_set_the_day():
    plans, uow = _OnePlan(), _Uow()
    day = SetDay(**_collaborators(_HoldOn(HELD), plans, uow))

    with pytest.raises(AccountHeld):
        await day.execute(
            SetDayCommand(game_id=GAME, player_id=HELD, day=date(2026, 9, 12))
        )

    assert plans.saved == []


async def test_a_held_member_cannot_set_the_hour():
    plans, uow = _OnePlan(), _Uow()
    hour = SetHour(**_collaborators(_HoldOn(HELD), plans, uow))

    with pytest.raises(AccountHeld):
        await hour.execute(
            SetHourCommand(game_id=GAME, player_id=HELD, hour=time(18, 0))
        )

    assert plans.saved == []


async def test_a_member_who_is_not_held_writes_the_slot():
    """The other arm, so the refusal above is the hold and not the wiring."""

    plans, uow = _OnePlan(), _Uow()
    place = SetPlace(**_collaborators(_HoldOn(), plans, uow))

    written = await place.execute(
        SetPlaceCommand(game_id=GAME, player_id=HELD, place="Zabłocie Sport")
    )

    assert written.place is not None
    assert written.place.value == "Zabłocie Sport"
    assert uow.commits == 1


async def test_a_held_member_still_reads_their_plans():
    """**A hold must not erase an arrangement other people are already inside.**

    The read takes no hold query at all — there is nowhere for one to be asked —
    which is what makes *never stops you reading* structural here rather than a
    branch somebody remembered not to write.
    """

    read = ReadPlans(
        plans=_NoPlans(), court=_ACourtStillArranging(), clock=_FrozenClock()
    )

    assert await read.execute(ReadPlansCommand(reader_id=HELD)) == ()
    assert "holds" not in ReadPlans.__init__.__code__.co_varnames
