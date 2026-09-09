"""When a room stops existing. **Derived, never stored** (``docs/adr/0153``).

A conversation exists for the whole **episode** it was opened for — arrange the
game, play it, find out what happened — and not for the arranging alone. It is
then **destroyed, not delisted**.

Four things about this file are load-bearing and none is obvious from the code.

**Both anchors are facts the room is already told, and that is the windfall.**
``Game.planned_at`` **is** ``GamePlanned.occurred_at``, which arrives on a
telling that draws no line, and *we played* is system-line code 4. So the end
costs **no new event, no new field and no new telling**; being told without
drawing a line is the shape ``ChallengeOpenedFromMutualInterest`` and
``challenges.withdrawn`` already have.

**The anchor is ``planned_at`` and never the plan's agreed point.** A plan is
editable by any member at any time, so dating from the agreed point would let two
people walk their own room forward by tapping a chip — the precise shape
``docs/adr/0145`` §5 refused for the entry window, put to a second job.

*The end never moves later, only earlier*, and the sentence is **about that
anchor**: once a game exists its end is fixed at the instant the line-up
completed, and nothing anybody does in the room afterwards moves it — not a slot,
not a message, not a second telling of the same game. The one instant that does
retract is the departure anchor below, and it retracts for the one reason worth
retracting for: **somebody joined the court**. That is the arrangement resuming
rather than two people extending their own room, and it costs a real search and
a real acceptance rather than a tap.

**Nothing is stored.** The instant moves as the room is told things — a game
played on day 1 ends its room on day 3, six days before entry closes — so a
stored ``ends_at`` would have to be rewritten on every telling, which is
``docs/adr/0146`` §7's second-copy problem in the column that decides whether a
room exists at all. **Past its end a room answers ``conversation_not_found``
whether or not the sweep has run**: the sweep exists to make the destruction
real, not to make the answer right, which is what ``challenges``' ``lapse`` and
``entry_closes_at``'s own docstring both already say.

**This is a module and not a method on the aggregate, and the import is why.**
The end is read off ``entries``, ``game_id`` and ``planned_at`` and nothing else,
so ``Conversation.ends_at()`` would be the natural home — except that it needs
``games``' ``entry_closes_at``, and the aggregate is folded by a repository that
knows nothing about entry windows. Keeping the cross-context import in one file
beside the constant that pairs with it is the trade, and it is the same
direction ``plans`` already runs in (``docs/adr/0148`` §8): ``conversations`` may
read ``games``, and ``.importlinter`` holds the reverse shut.

**A withdrawal is not on this list, and its absence is the decision.** It
destroys the room **in the same act** and writes no line, because there is
nobody left to read one — so there is no room left to derive an instant for. It
is also why a room that is still arranging answers ``None`` here rather than
being given a clock of its own: ``docs/adr/0142`` §1's own answer to a court
nobody will complete is the organiser ending it, and inventing a deadline for
that here would be this context folding somebody else's record.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from app.kernel import Instant, instant
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import SystemLine, SystemLineCode
from app.modules.games.domain.windows import entry_closes_at

#: How long a room outlives the thing it was opened for. **Forty-eight hours**,
#: on ``docs/adr/0151``'s rule — *a window must exceed the gap between app opens,
#: not equal it* — and its second application, the first outside a challenge. The
#: default here is destruction and what it costs is the room, so 24 h, which
#: *equals* the gap it has to outlast, is the boundary condition that record
#: found in ``ANSWER_WINDOW``.
#:
#: **It belongs to this context and not to ``games``.** ``docs/adr/0148`` kept
#: ``PLAN_HORIZON`` in ``games`` because its interlock with ``ENTRY_GRACE`` is
#: the argument; there is no such interlock here. This grace is about **app
#: opens**, which is ``ANSWER_WINDOW``'s argument and not a games window's.
#:
#: **It is stated, not derived, and the obvious derivation does not exist.** A
#: correction re-dates the proposal and correcting is free until the other side
#: responds, so settling has no upper bound and no number can be shown to outlive
#: it. ``docs/adr/0153`` §4 therefore **declines to claim** that the room
#: survives ``games``' own conversation, rather than claiming it and being wrong.
#:
#: **Falsifier, named rather than implied:** messages sent after ``GamePlayed``,
#: against time since it. If nothing is ever said on the second day, the second
#: day is not being used and the number comes back down.
CONVERSATION_GRACE: Final = timedelta(hours=48)

#: The three codes that are facts about **who is on this court**. They are what
#: the conclusion is read off, and a message is deliberately not one of them: two
#: people still typing is not a challenge un-concluding.
_MEMBERSHIP_CODES: Final = frozenset(
    {
        SystemLineCode.SEAT_ACCEPTED,
        SystemLineCode.SEATS_INVITED,
        SystemLineCode.SEAT_LEFT,
    }
)


def ends_at(room: Conversation) -> Instant | None:
    """When this room stops existing, or ``None`` while nothing has ended it.

    The **earliest** of the anchors it actually has:

    - ``entry_closes_at(planned_at)`` — the instant *we played* stops being
      sayable and the game becomes a ghost;
    - the moment somebody said they played, plus :data:`CONVERSATION_GRACE`;
    - the challenge concluding without ever producing a game, plus the same
      grace.

    ``None`` is a real answer and not an omission, and it is **the answer for
    every room whose challenge is still arranging** — which is more shapes than
    it first looks, so they are named rather than left to be rediscovered:

    - a court nobody has left and nobody has withdrawn;
    - a court somebody left and somebody then **filled**, because the fill is the
      arrangement resuming (see :func:`_concluded_at`);
    - a **mutual-born** doubles court, which is window-less for life
      (``docs/adr/0150``), so its empty seats never lapse and no departure is
      ever told.

    All three are the same room: one whose *challenge* has no end either. That is
    not the record-with-no-end ``docs/adr/0142`` was written to prevent — it is
    that record's own answer, which is that a half-built court ends when the
    organiser withdraws, and a withdrawal destroys the room in the same act
    rather than dating it.
    """

    anchors = [
        anchor
        for anchor in (
            None if room.planned_at is None else entry_closes_at(room.planned_at),
            _after(_played_at(room)),
            _after(_concluded_at(room)),
        )
        if anchor is not None
    ]
    return min(anchors) if anchors else None


def has_ended(room: Conversation, *, now: Instant) -> bool:
    """Whether this room is over at this instant.

    ``now >= ends_at`` — the same boundary every window in this repository
    leans, so a reader does not have to remember which way one of them does.
    """

    end = ends_at(room)
    return end is not None and now >= end


def _after(moment: Instant | None) -> Instant | None:
    return None if moment is None else instant(moment + CONVERSATION_GRACE)


def _played_at(room: Conversation) -> Instant | None:
    """When somebody said they played, off the line the room already drew.

    Read backwards, so the newest wins: ``GamePlayed`` is published once per
    game, and reading from the end is what makes a redelivered line — which
    answers the entry that already stands — cost nothing here either.
    """

    for entry in reversed(room.entries):
        if isinstance(entry, SystemLine) and entry.code is SystemLineCode.GAME_PLAYED:
            return entry.occurred_at
    return None


def _concluded_at(room: Conversation) -> Instant | None:
    """When the challenge ended without ever producing a game.

    **The last membership line, and only when it is a departure.** A departure
    reopens one seat and disturbs nothing else, so it is a conclusion exactly
    while nothing has happened to the court since: an acceptance or a fill after
    it is the arrangement moving again, and ``docs/adr/0150`` makes a fill
    reachable for as long as the line-up is incomplete.

    **A room that has a game has no conclusion of this kind**, whatever its
    backlog holds. A line-up that completed after somebody left is an
    arrangement that concluded *into a game*, and the game's own anchor is the
    one that answers.

    **This leans on a coincidence of two numbers, and the coincidence is written
    down rather than tidied away** (``docs/adr/0153`` §7's own instruction). A
    seat still owing an answer when the departure landed was invited **before**
    it, and its window closes at ``invitation + ANSWER_WINDOW`` — so while
    ``ANSWER_WINDOW <= CONVERSATION_GRACE`` (48 h each today) the room always
    outlives every answer anybody could still give, and a seat invited *after* a
    departure writes a ``SEATS_INVITED`` line that clears this anchor anyway.
    Lengthen ``ANSWER_WINDOW`` past the grace and a half-built court could be
    destroyed while somebody is still entitled to accept into it. This context
    cannot check that for itself — reading the seats would be folding
    ``challenges``' record — so the coupling is stated here, where a reader of
    either number can find it.
    """

    if room.game_id is not None:
        return None
    for entry in reversed(room.entries):
        if not isinstance(entry, SystemLine) or entry.code not in _MEMBERSHIP_CODES:
            continue
        return entry.occurred_at if entry.code is SystemLineCode.SEAT_LEFT else None
    return None
