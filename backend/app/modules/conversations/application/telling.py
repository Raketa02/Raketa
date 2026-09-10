"""**What each published event writes into a room, including the ones that
write nothing.**

``the-words.md`` §23 and §23.1, and ``the-loop-screens.md`` §3.4, as a table
rather than as prose. A builder reading only the event list would write a line
for each; most of them are refused, and this is where the refusal and its reason
live so that ``tests/unit/test_the_room_is_told.py`` can name every one.

**Three contexts publish into this table and none of them knows it exists.**
``challenges``, ``games`` and now ``plans``, and the Plan's rows are the only
ones on the list where **every** event of a context draws a line: it has exactly
four events and every one of them is somebody doing something the other people on
the court would want to know, which is what a system line is for. Three of them
are somebody writing something down; the fourth is somebody agreeing what was
written (``docs/adr/0155``).

**Three different rules do the refusing.**

1. **There was no room to write it in.** ``ChallengeSent`` happens before any
   room exists; ``ChallengeOpenedFromMutualInterest`` and the first
   ``SeatAccepted`` *are* the opening, and ``seq`` 1 is whatever happens next.
   One rule gives all three membership codes one shape: an acceptance, an
   invitation and a departure each write a line **only when there was already a
   room to write it in**.
2. **No system line announces a conclusion the record already implies.**
   ``GamePlanned`` is refused on ``docs/adr/0142`` §3's own test — *an event may
   announce a conclusion only when no arrangement of the seats could reach it* —
   and everybody having accepted is exactly such an arrangement. **So there is no
   *Game on* line.** ``ChallengeWithdrawn`` is refused because the withdrawal
   destroys the room in the same act and there is nobody left to read it. That
   reason is now true: the destruction is ``docs/adr/0153``'s and is built, and
   the withdrawal is the one telling here whose whole effect is that the room
   stops existing.

   **``PlanLocked`` is what that test looks like from the other side.** No
   arrangement of the three slots reaches *these people have agreed* — nobody
   wrote it down — so the event is the only place the fact is true rather than a
   second one, and it draws a line. There is still no *plan complete* line, and
   the two are not the same news: a complete plan is one everybody *could* agree
   (``docs/adr/0155``).
3. **The argument belongs to somebody else.** The four result events are
   ``games``' and ``games`` has its own eight-arm conversation for them. One fact
   in one place.

**A refused line is not a refused telling**, and here that is load-bearing
twice. ``GamePlanned`` still reaches the room and draws nothing, because
``GamePlayed`` names a game and nothing else and the room's own end is derived
from ``GamePlanned``'s moment (``docs/adr/0153`` §2); dropping the delivery
because nothing renders would drop the anchor with it. ``ChallengeWithdrawn``
draws nothing and arrives for a stronger reason still — it is what **destroys**
the room, so a refusal read as *do not deliver this* would leave every withdrawn
court a readable room for ever.

**On the count.** ``the-words.md`` §23.1 is headed *the six events that publish
nothing* and its own table names **eight** of them, four of which it groups on
one row as *the result argument*. The table below is the events, one row each, so
it is eight; the discrepancy is in the source and is left visible rather than
resolved by dropping rows to make a number come out.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.modules.challenges.domain.events import (
    ChallengeOpenedFromMutualInterest,
    ChallengeSent,
    ChallengeWithdrawn,
    SeatAccepted,
    SeatDeclined,
    SeatLapsed,
    SeatsInvited,
)
from app.kernel import invariant
from app.modules.conversations.domain.entries import SystemLineCode
from app.modules.games.domain.events import (
    GamePlanned,
    GamePlayed,
    ResultAccepted,
    ResultCorrected,
    ResultCountered,
    ResultProposed,
)
from app.modules.plans.domain.events import (
    DayRecorded,
    HourRecorded,
    PlaceRecorded,
    PlanLocked,
)


@final
@dataclass(frozen=True, slots=True)
class Telling:
    """One published event, and what this context does about it.

    ``line`` is the code it writes, or ``None``. ``why_nothing`` is required
    exactly when ``line`` is ``None``: a refusal with no reason beside it is how
    a line quietly reappears the next time somebody reads the event list.

    ``reaches_the_room`` is a **third** state and not a synonym for either. An
    event may write no line and still have to arrive — see the module docstring
    on ``GamePlanned``.
    """

    event: type
    line: SystemLineCode | None
    reaches_the_room: bool
    why_nothing: str | None = None


#: Every event either half of the loop publishes, and this room's answer to it.
TELLINGS: tuple[Telling, ...] = (
    Telling(
        event=SeatAccepted,
        line=SystemLineCode.SEAT_ACCEPTED,
        reaches_the_room=True,
    ),
    Telling(
        event=SeatsInvited,
        line=SystemLineCode.SEATS_INVITED,
        reaches_the_room=True,
    ),
    Telling(
        event=SeatDeclined,
        line=SystemLineCode.SEAT_LEFT,
        reaches_the_room=True,
    ),
    Telling(
        event=SeatLapsed,
        line=SystemLineCode.SEAT_LEFT,
        reaches_the_room=True,
    ),
    Telling(
        event=GamePlayed,
        line=SystemLineCode.GAME_PLAYED,
        reaches_the_room=True,
    ),
    Telling(
        event=PlaceRecorded,
        line=SystemLineCode.PLACE_RECORDED,
        reaches_the_room=True,
    ),
    Telling(
        event=DayRecorded,
        line=SystemLineCode.DAY_RECORDED,
        reaches_the_room=True,
    ),
    Telling(
        event=HourRecorded,
        line=SystemLineCode.HOUR_RECORDED,
        reaches_the_room=True,
    ),
    Telling(
        event=PlanLocked,
        line=SystemLineCode.PLAN_LOCKED,
        reaches_the_room=True,
    ),
    Telling(
        event=ChallengeSent,
        line=None,
        reaches_the_room=False,
        why_nothing="no conversation exists yet — there is nowhere to write",
    ),
    Telling(
        event=ChallengeOpenedFromMutualInterest,
        line=None,
        reaches_the_room=True,
        why_nothing="it **is** the opening; `seq` 1 is whatever happens next",
    ),
    Telling(
        event=GamePlanned,
        line=None,
        reaches_the_room=True,
        why_nothing=(
            "the seats already imply it, so there is no *Game on* line — but the "
            "room is told, because this is where it learns its game and where "
            "its own end is anchored"
        ),
    ),
    Telling(
        event=ChallengeWithdrawn,
        line=None,
        reaches_the_room=True,
        why_nothing=(
            "the withdrawal **destroys** the room in the same act, so there is "
            "nobody left to read a line and the news is on the challenge screen "
            "instead. It is the one telling here whose whole effect is that the "
            "room stops existing, which is why it reaches the room while drawing "
            "nothing"
        ),
    ),
    Telling(
        event=ResultProposed,
        line=None,
        reaches_the_room=False,
        why_nothing="`games` has its own conversation for the result argument",
    ),
    Telling(
        event=ResultCorrected,
        line=None,
        reaches_the_room=False,
        why_nothing="`games` has its own conversation for the result argument",
    ),
    Telling(
        event=ResultCountered,
        line=None,
        reaches_the_room=False,
        why_nothing="`games` has its own conversation for the result argument",
    ),
    Telling(
        event=ResultAccepted,
        line=None,
        reaches_the_room=False,
        why_nothing="`games` has its own conversation for the result argument",
    ),
)


#: The events this context subscribes to. Everything the room is **told**, which
#: is not the same list as everything that draws a line.
TOLD_ABOUT: tuple[type, ...] = tuple(
    telling.event for telling in TELLINGS if telling.reaches_the_room
)

_BY_EVENT: dict[type, Telling] = {telling.event: telling for telling in TELLINGS}


def line_for(event: object) -> SystemLineCode:
    """The code this event writes. **Read from the table, never respelled.**

    The handler needs the code and the table already holds it, so this is what
    stops the two parting company — a row edited to refuse a line while the
    handler went on writing one would otherwise be a green build with a table
    that lies about what ships.

    It raises rather than answering ``None`` for an event that writes nothing:
    the handler asks only on the arms that write, so a lookup that came back
    empty would be a caller bug and not a state.
    """

    telling = _BY_EVENT[type(event)]
    invariant(
        telling.line is not None,
        f"{type(event).__name__} writes no line: {telling.why_nothing}",
    )
    return telling.line  # type: ignore[return-value]
