"""What the room is told, what it writes, and the events that write nothing.

The refusals are the point of this file. ``the-words.md`` §23.1 names them in
prose; ``app/modules/conversations/application/telling.py`` names them as data;
this walks the data so that **a line that quietly reappears turns the build red**
rather than being noticed by whoever next reads the event list.

Membership is here too, because it is a **fold over two other contexts' records**
and there is no seam further out that can see the rule on its own.
"""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from app.kernel import Sport, instant
from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    ChallengeWithdrawn,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatLeft,
    SeatsInvited,
)
from app.modules.conversations.application.membership import Membership
from app.modules.conversations.application.telling import TELLINGS, TOLD_ABOUT
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import SystemLineCode
from app.modules.games.domain.events import (
    GameCalledOff,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
    ResultAccepted,
    ResultCorrected,
    ResultCountered,
    ResultProposed,
    SeatVacated,
)
from app.modules.plans.domain.events import (
    DayRecorded,
    HourRecorded,
    PlaceRecorded,
    PlanLocked,
)

NOW = instant(datetime(2026, 9, 8, 18, 0, tzinfo=timezone.utc))

#: Every event ``challenges``, ``games`` and ``plans`` publish. Spelled out
#: rather than imported from any register, because the thing under test is
#: whether this context has an answer for each of them — and a list derived from
#: the same place the answers come from could not fail.
EVERY_PUBLISHED_EVENT = (
    ChallengeSent,
    ChallengeOpenedFromMutualInterest,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatLeft,
    SeatsInvited,
    ChallengeWithdrawn,
    GamePlanned,
    SeatVacated,
    LineUpReseated,
    GameCalledOff,
    GamePlayed,
    ResultProposed,
    ResultCorrected,
    ResultCountered,
    ResultAccepted,
    PlaceRecorded,
    DayRecorded,
    HourRecorded,
    PlanLocked,
)

WRITES_NOTHING = tuple(
    telling for telling in TELLINGS if telling.line is None
)


def test_every_published_event_has_an_answer_here():
    """A builder reading the event list must not have to guess."""

    assert {telling.event for telling in TELLINGS} == set(EVERY_PUBLISHED_EVENT)


@pytest.mark.parametrize(
    "telling", WRITES_NOTHING, ids=lambda telling: telling.event.__name__
)
def test_each_event_that_publishes_nothing_names_its_reason(telling):
    """``the-words.md`` §23.1 — a refusal with no reason beside it is how a line
    quietly reappears."""

    assert telling.line is None
    assert telling.why_nothing


def test_the_eleven_that_write_nothing_are_the_eleven_the_words_names():
    """``the-words.md`` §23.1 is headed *the six events that publish nothing* and
    its own table names eleven of them, four grouped on one row as *the result
    argument*, two on one row as *the game's line-up moving*, and the call-off
    on a row of its own (``docs/adr/0163``). The discrepancy is in the source;
    this asserts the events."""

    assert {telling.event for telling in WRITES_NOTHING} == {
        ChallengeSent,
        ChallengeOpenedFromMutualInterest,
        ChallengeWithdrawn,
        GamePlanned,
        SeatVacated,
        LineUpReseated,
        GameCalledOff,
        ResultProposed,
        ResultCorrected,
        ResultCountered,
        ResultAccepted,
    }


def test_there_is_no_game_on_line():
    """``docs/adr/0146`` §6 — a folded standing has exactly one place to be true,
    and it is not a sentence in the backlog."""

    assert "GAME_ON" not in {code.value for code in SystemLineCode}
    planned = next(t for t in TELLINGS if t.event is GamePlanned)
    assert planned.line is None


def test_a_refused_line_is_not_a_refused_telling():
    """``the-words.md`` §23.1 — ``GamePlanned`` draws nothing and still arrives,
    because the room's own end is anchored on its moment and ``GamePlayed`` names
    a game and nothing else."""

    planned = next(t for t in TELLINGS if t.event is GamePlanned)
    mutual = next(
        t for t in TELLINGS if t.event is ChallengeOpenedFromMutualInterest
    )

    assert planned.reaches_the_room and planned.line is None
    assert mutual.reaches_the_room and mutual.line is None
    assert GamePlanned in TOLD_ABOUT


def test_the_withdrawal_draws_nothing_and_has_the_largest_effect_of_any_telling():
    """``docs/adr/0153`` §2 — it **destroys** the room in the same act, so there
    is nobody left to read a line and the news is on the challenge screen.

    The telling that draws the least is the one that must not be dropped: a
    refusal read as *do not deliver this* would leave every withdrawn court a
    readable room for ever.
    """

    withdrawn = next(t for t in TELLINGS if t.event is ChallengeWithdrawn)

    assert withdrawn.line is None
    assert withdrawn.reaches_the_room
    assert ChallengeWithdrawn in TOLD_ABOUT


def test_the_result_argument_never_reaches_the_room_at_all():
    """Refused on **scope** — ``games`` has its own conversation for it — so
    unlike the two above, it is not even delivered."""

    for event in (ResultProposed, ResultCorrected, ResultCountered, ResultAccepted):
        assert event not in TOLD_ABOUT


def test_the_send_reaches_nothing_because_no_room_exists_yet():
    assert ChallengeSent not in TOLD_ABOUT


def test_a_seat_leaving_is_one_code_told_by_three_events():
    """``docs/adr/0162`` §5 — a no, a silence, and somebody leaving a game they
    had agreed to. The two events ``games`` writes for the same departure reach
    the room not at all: a room told twice would write a second line."""

    declined = next(t for t in TELLINGS if t.event is SeatDeclined)
    lapsed = next(t for t in TELLINGS if t.event is SeatLapsed)
    left = next(t for t in TELLINGS if t.event is SeatLeft)

    assert declined.line is lapsed.line is left.line is SystemLineCode.SEAT_LEFT
    assert SeatLeft in TOLD_ABOUT
    for event in (SeatVacated, LineUpReseated):
        assert event not in TOLD_ABOUT


def test_a_call_off_reaches_the_room_not_at_all_because_the_withdrawal_already_did():
    """``docs/adr/0163`` §5 — the withdrawal destroys the room in the same
    transaction, so the game's own end has nobody left to tell. It is refused
    with a reason rather than dropped, and the withdrawal is still told."""

    called_off = next(t for t in TELLINGS if t.event is GameCalledOff)
    withdrawn = next(t for t in TELLINGS if t.event is ChallengeWithdrawn)

    assert called_off.line is None and not called_off.reaches_the_room
    assert "destroys" in called_off.why_nothing
    assert GameCalledOff not in TOLD_ABOUT
    assert withdrawn.reaches_the_room and ChallengeWithdrawn in TOLD_ABOUT


def test_every_plan_event_writes_a_line_and_each_writes_its_own():
    """``the-words.md`` §23 — four codes, and the Plan is the one context on
    this table where every event it publishes draws a line.

    The inverse of the seat-leaving rule above, and deliberately: a lapse and a
    decline do the same thing to a line-up and *are* two facts, so they share a
    code and differ in a value; three slots are three different facts, so they
    are three codes — and the lock is a fourth fact again.
    """

    lines = {
        telling.event: telling.line
        for telling in TELLINGS
        if telling.event
        in (PlaceRecorded, DayRecorded, HourRecorded, PlanLocked)
    }

    assert lines == {
        PlaceRecorded: SystemLineCode.PLACE_RECORDED,
        DayRecorded: SystemLineCode.DAY_RECORDED,
        HourRecorded: SystemLineCode.HOUR_RECORDED,
        PlanLocked: SystemLineCode.PLAN_LOCKED,
    }
    assert all(event in TOLD_ABOUT for event in lines)


def test_the_lock_draws_a_line_where_the_completed_line_up_draws_none():
    """``docs/adr/0155`` — the two are on opposite sides of ``docs/adr/0142``
    §3's test, and this is where that is asserted.

    ``GamePlanned`` announces a conclusion **the seats already reach**, so it
    writes nothing. A lock is a fact nobody wrote down: no arrangement of the
    three slots says *these people have agreed*, so the event is the only place
    it is true rather than a second one.
    """

    locked = next(t for t in TELLINGS if t.event is PlanLocked)
    planned = next(t for t in TELLINGS if t.event is GamePlanned)

    assert locked.line is SystemLineCode.PLAN_LOCKED
    assert locked.reaches_the_room
    assert planned.line is None


def test_there_is_no_code_for_a_slot_being_changed():
    """``docs/adr/0144`` — *setting a slot and moving one are the same event told
    with two sentences*, separated by the fold rather than by a second class.

    A fourth code, or a value distinguishing the two, would be this context
    deciding that a change is different news from a first fill — which is the one
    thing the record says it is not.
    """

    codes = {code.value for code in SystemLineCode}

    assert not any("CHANGED" in code or "MOVED" in code for code in codes)
    assert len(codes) == 8


def test_there_is_no_code_for_a_plan_being_unlocked():
    """``docs/adr/0155`` — there is no unlock and no ``PlanUnlocked``, for the
    same reason there is no clearing event: the lock is a thing that happened.

    A later slot move keeps the lock and writes its **own** line, so the room
    already has a truthful record of the re-agreeing without a code that would
    have to mean *never mind*.
    """

    codes = {code.value for code in SystemLineCode}

    assert not any("UNLOCK" in code for code in codes)


# -- membership ------------------------------------------------------------


class _Court:
    def __init__(self, accepted=None, sports=None) -> None:
        self._accepted = accepted or {}
        self._sports = sports or {}

    async def accepted_on(self, challenge_ids):
        return {
            challenge_id: self._accepted[challenge_id]
            for challenge_id in challenge_ids
            if challenge_id in self._accepted
        }

    async def accepted_by(self, player_id):
        return frozenset(
            challenge_id
            for challenge_id, players in self._accepted.items()
            if player_id in players
        )

    async def sport_of(self, challenge_id):
        return self._sports.get(challenge_id)


class _LineUps:
    def __init__(self, line_ups=None) -> None:
        self._line_ups = line_ups or {}

    async def line_ups_of(self, game_ids):
        return {
            game_id: self._line_ups[game_id]
            for game_id in game_ids
            if game_id in self._line_ups
        }


def _room(challenge_id, *, game_id=None) -> Conversation:
    room = Conversation.opened(
        conversation_id=uuid4(),
        challenge_id=challenge_id,
        sport=Sport.PADEL,
        occurred_at=NOW,
    )
    if game_id is not None:
        room.note_game(game_id=game_id, occurred_at=NOW)
    room.pull_events()
    return room


async def test_membership_reads_the_challenge_while_the_line_up_is_incomplete():
    """``docs/adr/0146`` §7 — whichever record is *currently arranging*."""

    challenge_id, ana, bo = uuid4(), uuid4(), uuid4()
    room = _room(challenge_id)
    membership = Membership(
        arranging=_Court(accepted={challenge_id: frozenset({ana, bo})}),
        played=_LineUps(),
    )

    assert await membership.of_one(room) == frozenset({ana, bo})


async def test_membership_reads_the_game_once_the_line_up_has_completed():
    """One rule, two records — and the game's line-up is frozen, so it stops
    growing."""

    challenge_id, game_id = uuid4(), uuid4()
    four = frozenset(uuid4() for _ in range(4))
    room = _room(challenge_id, game_id=game_id)
    membership = Membership(
        # The challenge would answer with two; the game answers with four, and
        # the game is the record this room is now about.
        arranging=_Court(accepted={challenge_id: frozenset(list(four)[:2])}),
        played=_LineUps(line_ups={game_id: four}),
    )

    assert await membership.of_one(room) == four


async def test_a_room_whose_record_answers_about_nobody_has_no_members():
    """The one way this fold is allowed to fail, and it fails **closed**: an
    empty membership lets nobody in rather than everybody."""

    room = _room(uuid4())
    membership = Membership(arranging=_Court(), played=_LineUps())

    assert await membership.of_one(room) == frozenset()


async def test_a_whole_list_costs_one_read_per_record_and_never_one_per_room():
    first, second, game_id = uuid4(), uuid4(), uuid4()
    ana = uuid4()
    rooms = (_room(first), _room(second, game_id=game_id))
    membership = Membership(
        arranging=_Court(accepted={first: frozenset({ana})}),
        played=_LineUps(line_ups={game_id: frozenset({ana})}),
    )

    found = await membership.of(rooms)

    assert set(found.values()) == {frozenset({ana})}
    assert len(found) == 2
