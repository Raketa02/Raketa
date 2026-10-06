"""When a room stops existing. **Derived, never stored** (``docs/adr/0153``).

A conversation exists for the whole **episode** it was opened for — the booked
game, played, and finding out what happened — and not a moment longer. It is
then **destroyed, not delisted**.

Five things about this file are load-bearing and none is obvious from the code.

**This module is the game's clock, and it is the whole of the lifetime** (#575).
A room ends on the earliest of two anchors, both facts the room is already told:
the game's entry window closing, measured from its booked hour, and *we played*
plus a grace. ``Game.planned_at`` **is** ``GamePlanned.occurred_at``, which
arrives on the telling that opens the room, and *we played* is a system line. So
the end costs **no new event, no new field and no new telling**, and it reads
**booking and game events only** — a room is opened by a booked game and by
nothing else.

**A room without a game has ended.** Nothing opens one any more: a booked game's
room is born already about it, in one save. A room with no game is one a
challenge's first acceptance opened before #575, and the challenge it lived as
long as is not something this context reads any longer — so it is over, every
route answers ``conversation_not_found`` about it, and the sweep destroys it.

**Nothing is stored.** The instant moves as the room is told things — a game
played on day 1 ends its room on day 3, days before entry closes — so a stored
``ends_at`` would have to be rewritten on every telling, which is
``docs/adr/0146`` §7's second-copy problem in the column that decides whether a
room exists at all. **Past its end a room answers ``conversation_not_found``
whether or not the sweep has run**: the sweep exists to make the destruction
real, not to make the answer right, which is what ``entry_closes_at``'s own
docstring already says.

**This is a module and not a method on the aggregate, and the import is why.**
The end is read off ``entries``, ``game_id``, ``planned_at`` and ``starts_at``
and nothing else, so ``Conversation.ends_at()`` would be the natural home —
except that it needs ``games``' ``entry_closes_at``, and the aggregate is folded
by a repository that knows nothing about entry windows. ``conversations`` may
read ``games``, and ``.importlinter`` holds the reverse shut.

**A call-off is not on this list, and its absence is the decision.** It
destroys the room **in the same act** and writes no line, because there is
nobody left to read one — so there is no room left to derive an instant for.
"""

from __future__ import annotations

from datetime import timedelta
from typing import Final, Iterable
from uuid import UUID

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
#: **It runs from *we played* and from nothing else.**
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
      stops being sayable, measured from the game's booked hour;
    - the moment somebody said they played, plus :data:`CONVERSATION_GRACE`.
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


def has_ended(room: Conversation, *, now: Instant) -> bool:
    """Whether this room is over at this instant. **The one seam that decides.**

    The list drops what this names, ``ARoomOfYours`` refuses it, and the sweep
    destroys it — one function, so the three cannot come to two answers about
    one room. ``now >= end``, the same boundary every window in this repository
    leans. A room with no game is over (the module docstring).
    """

    if room.game_id is None:
        return True
    end = game_ends_it_at(room)
    return end is not None and now >= end


def ended_among(rooms: Iterable[Conversation], *, now: Instant) -> frozenset[UUID]:
    """The conversation ids of every room here that is over at this instant.

    Folded off each room's own stream, so a whole list costs no read at all.
    """

    return frozenset(
        room.conversation_id for room in rooms if has_ended(room, now=now)
    )


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
