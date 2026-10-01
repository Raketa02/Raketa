"""When a room stops existing. **Derived, never stored** (``docs/adr/0153``).

A conversation exists for the whole **episode** it was opened for — arrange the
game, play it, find out what happened — and not for the arranging alone. It is
then **destroyed, not delisted**.

Six things about this file are load-bearing and none is obvious from the code.

**This module is the game's clock, and only that.** A room with a game ends on
the earliest of two anchors, both facts the room is already told — and that is
the windfall. ``Game.planned_at`` **is** ``GamePlanned.occurred_at``, which
arrives on a telling that draws no line, and *we played* is system-line code 4.
So the end costs **no new event, no new field and no new telling**; being told
without drawing a line is the shape ``ChallengeOpenedFromMutualInterest`` and
``challenges.withdrawn`` already have.

**A room without a game has no clock here, and that absence is the decision**
(``docs/adr/0164`` §6). It has ended exactly when its challenge is over —
``DECLINED``, ``LAPSED``, ``WITHDRAWN``, ``CALLED_OFF`` — which is a fact about
somebody else's record, read on every read through the port the room already reads its
membership from (``application/lifetime.py``), and never folded off this stream.
There used to be a third anchor here: the last membership line, when it was a
departure, plus the grace — a 48 h *departure shelf* that closed a room while
the people in it were still talking, and read the **order** the answers arrived
in (*B yes → D yes → C no* closed it; *B yes → C no → D yes* never did). It is
gone, and with it the coupling this file used to state between ``ANSWER_WINDOW``
and ``CONVERSATION_GRACE``: that coupling existed so the shelf could not destroy
a court somebody was still entitled to accept into, and a room that lives as
long as its challenge cannot be destroyed under an open seat by any number.

**The anchor is ``planned_at`` and never the plan's agreed point.** A plan is
editable by any member at any time, so dating from the agreed point would let two
people walk their own room forward by tapping a chip — the precise shape
``docs/adr/0145`` §5 refused for the entry window, put to a second job. *The end
never moves later, only earlier*: once a game exists its end is fixed at the
instant the line-up completed, and nothing anybody does in the room afterwards
moves it — not a slot, not a message, not a second telling of the same game.

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
nobody left to read one — so there is no room left to derive an instant for.
**A withdrawal now reaches a room that already holds its game**
(``docs/adr/0163``) — a reopened court is called off through it — **and so does
a call-off on its own** (``docs/adr/0165`` §3), told by the departure that left
one player on the court; nothing here reads ``game_id`` on either path: the
destruction is the teller's, in the act, and the anchors below are only ever
consulted on a read of a room that still exists.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final

from app.kernel import Instant, instant
from app.modules.conversations.domain.conversation import Conversation
from app.modules.conversations.domain.entries import SystemLine, SystemLineCode
from app.modules.games.domain.windows import entry_closes_at

#: How long a room outlives the game it was opened for. **Forty-eight hours**,
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
#: **It runs from *we played* and from nothing else** — a room without a game
#: has no grace, because it has no clock of its own (the module docstring).
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


def game_ends_it_at(room: Conversation) -> Instant | None:
    """When this room's **game** ends it, or ``None`` because there is no game.

    The **earliest** of the anchors it actually has:

    - ``entry_closes_at(planned_at, starts_at=…)`` — the instant *we played*
      stops being sayable and the game becomes a ghost, measured from a booked
      game's hour when it has one;
    - the moment somebody said they played, plus :data:`CONVERSATION_GRACE`.

    ``None`` is a real answer and not an omission, and it is **the answer for
    every room without a game** — whatever its backlog holds. A departure line,
    a fill, a mutual-born court whose empty seats never lapse: none of them is
    an anchor, because a room without a game ends with its challenge and not on
    a clock of its own (``docs/adr/0164`` §6). Whether that challenge is over is
    not this stream's to say, so a caller that needs *has this room ended* asks
    ``application/lifetime.py``, which asks ``challenges``.
    """

    anchors = [
        anchor
        for anchor in (
            None
            if room.planned_at is None
            else entry_closes_at(room.planned_at, starts_at=room.starts_at),
            _after(_played_at(room)),
        )
        if anchor is not None
    ]
    return min(anchors) if anchors else None


def ended_by_its_game(room: Conversation, *, now: Instant) -> bool:
    """Whether this room's game is over at this instant.

    ``now >= game_ends_it_at`` — the same boundary every window in this
    repository leans, so a reader does not have to remember which way one of
    them does. ``False`` for every room without a game, for the reason
    :func:`game_ends_it_at` gives; that room's end is the application seam's to
    read — which is what the name is for: a caller that wants *has this room
    ended* and reaches for this has the half-answer spelled out in the import.
    """

    end = game_ends_it_at(room)
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
