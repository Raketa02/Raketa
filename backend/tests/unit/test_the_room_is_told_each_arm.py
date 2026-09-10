"""``TellTheRoom``, arm by arm — **including the two no API test can reach.**

The API suite drives most of the tellings through real requests: the first
acceptance, a later one, a decline, a completed line-up, *we played*, the three
slot writes and the lock. Two are left, and they are the two most worth a test —
a **fill** (``SeatsInvited``) and a **mutual-born opening**, each of which is the
only place its rule is expressed.

The lock is driven here as well, on top of its API test, for the one thing that
is a property of the arm rather than of the route: it is the **only** plan line
with no values at all, and a value invented for it would be the second place the
slots are true (``docs/adr/0155``).

And one thing no request can exercise at all: **the order the outbox delivers a
transaction's own events in.** ``created_at`` is ``func.now()`` — transaction-start
time, identical across a transaction (``docs/adr/0097``) — so the queue's
``(created_at, id)`` tie-break is a minted uuid, and the accept that fills the
last seat can deliver ``GamePlanned`` before or after the ``SeatAccepted`` beside
it. Both orders are driven here, and they are required to reach the same room.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Collection, Mapping
from uuid import UUID, uuid4

import pytest

from app.application.events import DeliveryContext
from app.kernel import Sport
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    ChallengeWithdrawn,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatsInvited,
)
from app.modules.conversations.application.tell_the_room import TellTheRoom
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.live import Nudge
from app.modules.conversations.domain.entries import (
    COUNT,
    DEPARTURE,
    SystemLine,
    SystemLineCode,
)
from app.modules.games.domain.events import GamePlanned, GamePlayed, ResultProposed
from app.modules.plans.domain.events import PlanLocked

NOW = datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc)
CHALLENGE = uuid4()
GAME = uuid4()
ORGANISER = uuid4()
ANA = uuid4()
BO = uuid4()


def _at(minutes: int) -> datetime:
    return NOW + timedelta(minutes=minutes)


def _delivery() -> DeliveryContext:
    """One outbox row. A fresh id per call, because that is what a fresh row is."""

    return DeliveryContext(event_id=uuid4(), attempt=1, occurred_at=NOW)


class _Rooms:
    """The repository and the directory, over a dict. **One object for both**,
    because the real pair share a repository so their stream versions agree."""

    def __init__(self) -> None:
        self.by_id: dict[UUID, Conversation] = {}

    async def load(self, conversation_id: UUID) -> Conversation | None:
        return self.by_id.get(conversation_id)

    async def load_for_append(self, conversation_id: UUID) -> Conversation | None:
        return await self.load(conversation_id)

    async def for_challenge(self, challenge_id: UUID) -> Conversation | None:
        for room in self.by_id.values():
            if room.challenge_id == challenge_id:
                return room
        return None

    async def for_game(self, game_id: UUID) -> Conversation | None:
        for room in self.by_id.values():
            if room.game_id == game_id:
                return room
        return None

    async def save(self, conversation: Conversation) -> None:
        conversation.pull_events()
        self.by_id[conversation.conversation_id] = conversation

    async def destroy(self, conversation_id: UUID) -> None:
        self.by_id.pop(conversation_id, None)

    async def every_room(self) -> tuple[Conversation, ...]:
        return tuple(self.by_id.values())

    # -- what a test asks it ------------------------------------------------

    @property
    def only(self) -> Conversation:
        assert len(self.by_id) == 1, f"{len(self.by_id)} rooms, expected one"
        return next(iter(self.by_id.values()))

    @property
    def lines(self) -> list[SystemLine]:
        return [entry for entry in self.only.entries if isinstance(entry, SystemLine)]


class _Court:
    async def accepted_on(
        self, challenge_ids: Collection[UUID]
    ) -> Mapping[UUID, frozenset[UUID]]:
        return {challenge_id: frozenset({ORGANISER}) for challenge_id in challenge_ids}

    async def accepted_by(self, player_id: UUID) -> frozenset[UUID]:
        return frozenset({CHALLENGE})

    async def sport_of(self, challenge_id: UUID) -> Sport | None:
        return Sport.PADEL if challenge_id == CHALLENGE else None


class _Games:
    """``games``, which may or may not have opened one yet."""

    def __init__(self, *, game_for: UUID | None = None) -> None:
        self._game_for = game_for

    async def line_ups_of(
        self, game_ids: Collection[UUID]
    ) -> Mapping[UUID, frozenset[UUID]]:
        return {}

    async def game_of(self, challenge_id: UUID) -> UUID | None:
        return GAME if self._game_for == challenge_id else None


class _Nudges:
    """The live channel, recording what the room announced about itself.

    A hand-written stub over the port, like every other collaborator here — what
    is asserted is *which* tellings announce anything, and a room's own
    ``last_seq`` is the only thing they announce.
    """

    def __init__(self) -> None:
        self.published: list[Nudge] = []

    async def nudge(self, nudge: Nudge) -> None:
        self.published.append(nudge)


def _teller(
    rooms: _Rooms,
    games: _Games | None = None,
    nudges: _Nudges | None = None,
) -> TellTheRoom:
    return TellTheRoom(
        conversations=rooms,
        directory=rooms,
        arranging=_Court(),
        played=games or _Games(),
        nudges=nudges or _Nudges(),
    )


@pytest.fixture
def rooms() -> _Rooms:
    return _Rooms()


@pytest.fixture
def nudges() -> _Nudges:
    return _Nudges()


# -- the openings ----------------------------------------------------------


async def test_a_mutual_born_challenge_opens_the_room_and_writes_no_line(rooms):
    """``the-words.md`` §23.1 — it **is** the opening. Both seats are accepted
    from birth, so there was never a moment with one person in the room."""

    await _teller(rooms)(
        ChallengeOpenedFromMutualInterest(
            challenge_id=CHALLENGE,
            sport=Sport.PADEL.value,
            organiser_id=ORGANISER,
            other_player_id=ANA,
            seats=(),
            occurred_at=NOW,
        ),
        _delivery(),
    )

    assert rooms.only.challenge_id == CHALLENGE
    assert rooms.only.entries == ()


async def test_a_mutual_delivered_twice_opens_one_room(rooms):
    tell = _teller(rooms)
    event = ChallengeOpenedFromMutualInterest(
        challenge_id=CHALLENGE,
        sport=Sport.PADEL.value,
        organiser_id=ORGANISER,
        other_player_id=ANA,
        seats=(),
        occurred_at=NOW,
    )

    await tell(event, _delivery())
    await tell(event, _delivery())

    assert len(rooms.by_id) == 1


async def test_a_challenge_this_context_cannot_be_told_about_opens_nothing(rooms):
    """A room with no sport is a row no client can draw, so nothing is opened."""

    await _teller(rooms)(
        SeatAccepted(challenge_id=uuid4(), player_id=ANA, occurred_at=NOW),
        _delivery(),
    )

    assert rooms.by_id == {}


# -- the fill --------------------------------------------------------------


async def test_seats_invited_writes_one_line_carrying_the_count_and_the_filler(
    rooms,
):
    """``the-words.md`` §23 — `{name} asked {n} more`. The name is the **filler**
    and not the organiser: ADR-0150 lets any live member fill."""

    tell = _teller(rooms)
    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )

    await tell(
        SeatsInvited(
            challenge_id=CHALLENGE,
            seats=(),
            newly_invited=(str(uuid4()), str(uuid4())),
            occurred_at=_at(1),
            invited_by=ANA,
        ),
        _delivery(),
    )

    (line,) = rooms.lines
    assert line.code is SystemLineCode.SEATS_INVITED
    assert line.actor_id == ANA
    assert line.values == {COUNT: "2"}


async def test_a_fill_before_any_room_exists_writes_nothing(rooms):
    """**Only when there was already a room to write it in** — the one rule all
    three membership codes share."""

    await _teller(rooms)(
        SeatsInvited(
            challenge_id=CHALLENGE,
            seats=(),
            newly_invited=(str(uuid4()),),
            occurred_at=NOW,
            invited_by=ANA,
        ),
        _delivery(),
    )

    assert rooms.by_id == {}


# -- leaving ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("event_cls", "departure"),
    [(SeatDeclined, "DECLINED"), (SeatLapsed, "LAPSED")],
    ids=["declined", "lapsed"],
)
async def test_a_seat_leaving_is_one_code_with_the_answer_as_a_value(
    rooms, event_cls, departure
):
    tell = _teller(rooms)
    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )

    await tell(
        event_cls(challenge_id=CHALLENGE, player_id=BO, occurred_at=_at(1)),
        _delivery(),
    )

    (line,) = rooms.lines
    assert line.code is SystemLineCode.SEAT_LEFT
    assert line.values == {DEPARTURE: departure}
    assert line.actor_id == BO


# -- the events that reach the room and draw nothing -----------------------


async def test_the_send_and_the_argument_reach_nothing(rooms):
    """Two of the refusals, driven rather than read off the table: the handler
    has no arm for either, so a room is neither opened nor written."""

    tell = _teller(rooms)
    for event in (
        ChallengeSent(
            challenge_id=CHALLENGE,
            sport=Sport.PADEL.value,
            mode=None,
            window="ANY",
            organiser_id=ORGANISER,
            seats=(),
            occurred_at=NOW,
        ),
        ResultProposed(
            game_id=GAME, player_id=ANA, side="A", score="6-4", occurred_at=NOW
        ),
    ):
        await tell(event, _delivery())

    assert rooms.by_id == {}


# -- the withdrawal --------------------------------------------------------


async def test_a_withdrawal_destroys_the_room_and_writes_no_line(rooms, nudges):
    """``docs/adr/0153`` §2 — destroyed in the same act, and there is nobody left
    to read a line."""

    tell = _teller(rooms, nudges=nudges)
    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )
    assert len(rooms.by_id) == 1

    await tell(
        ChallengeWithdrawn(challenge_id=CHALLENGE, occurred_at=_at(5)), _delivery()
    )

    assert rooms.by_id == {}
    # **No nudge**: a nudge says *the room is now this long*, and there is no
    # room to be a length.
    assert nudges.published == []


async def test_a_withdrawal_of_a_challenge_with_no_room_does_nothing(rooms):
    """A redelivery, a court withdrawn before anybody accepted, and a challenge
    this context cannot be told about all want exactly nothing done."""

    await _teller(rooms)(
        ChallengeWithdrawn(challenge_id=CHALLENGE, occurred_at=NOW), _delivery()
    )

    assert rooms.by_id == {}


async def test_a_redelivered_withdrawal_is_a_no_op(rooms):
    """The outbox is at-least-once, and destroying a room that is already gone is
    the state this asks for."""

    tell = _teller(rooms)
    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )
    withdrawn = ChallengeWithdrawn(challenge_id=CHALLENGE, occurred_at=_at(5))

    await tell(withdrawn, _delivery())
    await tell(withdrawn, _delivery())

    assert rooms.by_id == {}


# -- the coin flip ---------------------------------------------------------


async def test_the_accept_first_order_leaves_the_room_knowing_its_game(rooms):
    tell = _teller(rooms, _Games(game_for=CHALLENGE))

    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )
    await tell(
        GamePlanned(
            game_id=GAME,
            challenge_id=CHALLENGE,
            sport=Sport.PADEL.value,
            kind="COUNTED",
            window=None,
            seatings=(),
            occurred_at=NOW,
        ),
        _delivery(),
    )

    assert rooms.only.game_id == GAME
    assert rooms.only.entries == ()


async def test_both_orders_anchor_the_room_on_the_same_instant(rooms):
    """``docs/adr/0153`` §2 — the room's end is dated from ``Game.planned_at``,
    and the coin flip must not decide what that is.

    The two orders reach ``planned_at`` by different routes: the accept-first one
    reads the game off ``PlayedCourt.game_of`` and stamps it with the
    **acceptance's** moment, the planned-first one takes ``GamePlanned``'s own.
    They agree because every path that completes a line-up stamps both from one
    ``now`` — which is a fact about ``challenges``, and therefore one this suite
    has to assert rather than assume.
    """

    accept = SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW)
    planned = GamePlanned(
        game_id=GAME,
        challenge_id=CHALLENGE,
        sport=Sport.PADEL.value,
        kind="COUNTED",
        window=None,
        seatings=(),
        occurred_at=NOW,
    )

    accept_first = _Rooms()
    await _teller(accept_first, _Games(game_for=CHALLENGE))(accept, _delivery())
    await _teller(accept_first, _Games(game_for=CHALLENGE))(planned, _delivery())

    planned_first = _Rooms()
    await _teller(planned_first, _Games(game_for=CHALLENGE))(planned, _delivery())
    await _teller(planned_first, _Games(game_for=CHALLENGE))(accept, _delivery())

    assert accept_first.only.planned_at == planned_first.only.planned_at == NOW


async def test_the_planned_first_order_reaches_exactly_the_same_room(rooms):
    """**The order is a coin flip and the room may not be.** ``created_at`` is
    transaction-start time, identical for both events, so the queue tie-breaks on
    a minted uuid — and without the opening reading the game for itself, this
    order would leave ``game_id`` null for ever."""

    tell = _teller(rooms, _Games(game_for=CHALLENGE))

    await tell(
        GamePlanned(
            game_id=GAME,
            challenge_id=CHALLENGE,
            sport=Sport.PADEL.value,
            kind="COUNTED",
            window=None,
            seatings=(),
            occurred_at=NOW,
        ),
        _delivery(),
    )
    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )

    assert rooms.only.game_id == GAME
    assert rooms.only.entries == (), "the founding acceptance writes no line"


async def test_we_played_finds_the_room_through_the_game_it_was_told_about(rooms):
    tell = _teller(rooms, _Games(game_for=CHALLENGE))
    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )

    await tell(
        GamePlayed(game_id=GAME, said_by=ANA, occurred_at=_at(1)),
        _delivery(),
    )

    (line,) = rooms.lines
    assert line.code is SystemLineCode.GAME_PLAYED
    assert line.actor_id == ANA


# -- the plan --------------------------------------------------------------


async def test_the_lock_writes_the_one_plan_line_that_carries_no_value(rooms):
    """``docs/adr/0155`` — the value is the three slots and they are already
    recorded, so this line carries **who and when** and nothing else.

    Found through the game like the three slot lines, and for the same reason:
    a plan exists only for a game, so the room is the one whose line-up
    completed into it.
    """

    tell = _teller(rooms, _Games(game_for=CHALLENGE))
    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )

    await tell(
        PlanLocked(game_id=GAME, locked_by=BO, occurred_at=_at(1)),
        _delivery(),
    )

    (line,) = rooms.lines
    assert line.code is SystemLineCode.PLAN_LOCKED
    assert line.actor_id == BO
    assert line.values == {}


async def test_a_lock_with_no_room_to_write_it_in_is_a_safe_drop(rooms):
    """The slot arm's reasoning exactly: a plan cannot be written before its game
    exists, so by the time this arrives the room either knows its game or was
    never opened at all. There is nothing to hang the line on and nothing to
    retry."""

    tell = _teller(rooms)

    await tell(
        PlanLocked(game_id=GAME, locked_by=BO, occurred_at=NOW),
        _delivery(),
    )

    assert rooms.by_id == {}


# -- redelivery ------------------------------------------------------------


async def test_the_same_outbox_row_delivered_twice_writes_one_line(rooms):
    """The outbox is at-least-once, so a subscriber that writes is idempotent on
    the **row** rather than on the event's contents."""

    tell = _teller(rooms)
    await tell(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )
    accepted = SeatAccepted(challenge_id=CHALLENGE, player_id=BO, occurred_at=_at(1))
    row = _delivery()

    await tell(accepted, row)
    await tell(accepted, row)

    assert len(rooms.lines) == 1


# ---------------------------------------------------------------------------
# What the room announces about itself
# ---------------------------------------------------------------------------


async def test_a_line_nudges_the_room_and_carries_its_new_length(rooms, nudges):
    """**One mechanism carries messages and system lines alike** (ADR-0147 §3).

    There is no separate live-plan feature to build and none to defer: a telling
    that writes a line announces the room's new length on the same channel a
    message does, and it announces nothing else.
    """

    teller = _teller(rooms, nudges=nudges)
    await teller(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )
    await teller(
        SeatAccepted(challenge_id=CHALLENGE, player_id=BO, occurred_at=_at(1)),
        _delivery(),
    )

    assert nudges.published == [
        Nudge(conversation_id=rooms.only.conversation_id, last_seq=1)
    ]


async def test_the_opening_announces_nothing_because_it_moved_no_seq(rooms, nudges):
    """A frame says *the room is now this long*, and an opening changes no length.

    Nudging here would send every phone to the read path to be told what it
    already holds. The room's existence reaches a client on the ordinary list
    read, not on this channel.
    """

    await _teller(rooms, nudges=nudges)(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )

    assert nudges.published == []


async def test_the_game_being_noted_announces_nothing_either(rooms, nudges):
    """``GamePlanned`` reaches the room, draws nothing, and moves no ``seq``.

    It is where the room learns its game — a *Details* door the detail read
    draws — and there is deliberately no *Game on* line for it to announce.
    """

    teller = _teller(rooms, games=_Games(game_for=CHALLENGE), nudges=nudges)
    await teller(
        SeatAccepted(challenge_id=CHALLENGE, player_id=ANA, occurred_at=NOW),
        _delivery(),
    )
    nudges.published.clear()

    await teller(
        GamePlanned(
            game_id=GAME,
            challenge_id=CHALLENGE,
            sport=Sport.PADEL.value,
            kind="COUNTED",
            window=None,
            seatings=(),
            occurred_at=_at(1),
        ),
        _delivery(),
    )

    assert rooms.only.game_id == GAME
    assert nudges.published == []
