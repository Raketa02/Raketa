"""**What each published event writes into a room, including the ones that
write nothing.**

``the-words.md`` §23 and §23.1 as a table rather than as prose. A builder
reading only the event list would write a line for each; most of them are
refused, and this is where the refusal and its reason live so that
``tests/unit/test_the_room_is_told.py`` can name every one.

**One context publishes into this table, and it does not know it exists**
(#575). A room is opened by a booked game and by nothing else, so its lifetime
and its telling read ``games``' events and **booking and game events only** —
there used to be a challenge's and a plan's rows here too, from when a
challenge's first acceptance opened rooms, and nothing opens a room that way
any more.

**Two different rules do the refusing.**

1. **No system line announces a conclusion the record already implies.**
   ``GamePlanned`` is the booked game itself: Home and its details announce it,
   and the room is born about it — so there is no *Game on* line. And
   ``GameCalledOff`` is refused because the call-off **destroys** the room in
   the same act (``docs/adr/0165`` §3): there is nobody left to read a line.
2. **The argument belongs to somebody else.** The four result events are
   ``games``' and ``games`` has its own conversation for them, and the four
   attendance events (#657) are the game's record, drawn on its details — as
   the two retired no-show events were. One fact in one place.

**A refused line is not a refused telling**, and here that is load-bearing
twice. ``GamePlanned`` still reaches the room and draws nothing, because it is
what **opens** a booked game's room and where the room's own end is anchored
(``docs/adr/0153`` §2); dropping the delivery because nothing renders would
drop the room with it. ``GameCalledOff`` draws nothing and arrives for a
stronger reason still — it is what **destroys** the room, so a refusal read as
*do not deliver this* would leave every called-off game a readable room for
ever.

**A departure and a re-seat reach this room not at all**: membership is read
off the game's current line-up live rather than told, so the roster moves the
moment either commits, and a line for them is not drawn yet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final

from app.kernel import invariant
from app.modules.conversations.domain.entries import SystemLineCode
from app.modules.games.domain.events import (
    AbsenceNoted,
    ArrivalNoted,
    GameCalledOff,
    GamePlanned,
    GamePlayed,
    LineUpReseated,
    NoShowDisputed,
    NoShowReported,
    PresenceClaimed,
    PresenceConfirmed,
    ResultAccepted,
    ResultCorrected,
    ResultCountered,
    ResultProposed,
    SeatVacated,
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


#: Every event a booked game's court publishes, and this room's answer to it.
TELLINGS: tuple[Telling, ...] = (
    Telling(
        event=GamePlayed,
        line=SystemLineCode.GAME_PLAYED,
        reaches_the_room=True,
    ),
    Telling(
        event=GamePlanned,
        line=None,
        reaches_the_room=True,
        why_nothing=(
            "the booked game is announced on Home and its details, so there is "
            "no *Game on* line — but the room is told, because a booked game's "
            "room is **opened** by it, born about the game, and its own end is "
            "anchored on it"
        ),
    ),
    Telling(
        event=GameCalledOff,
        line=None,
        reaches_the_room=True,
        why_nothing=(
            "the call-off **destroys** the room, so there is nobody left to "
            "read a line and no room to be a length — the news is on Home and "
            "the game's details. It reaches the room because this is the "
            "telling that destroys (`docs/adr/0165` §3)"
        ),
    ),
    Telling(
        event=SeatVacated,
        line=None,
        reaches_the_room=False,
        why_nothing=(
            "membership reads the game's line-up live rather than being told, "
            "so the roster drops whoever left the moment it commits; a line "
            "for the departure is not drawn"
        ),
    ),
    Telling(
        event=LineUpReseated,
        line=None,
        reaches_the_room=False,
        why_nothing=(
            "membership reads the game's line-up live rather than being told — "
            "a rescue taking a seat (#545) joins the room the moment it "
            "commits, and its line, *Ola took the seat*, is not drawn yet"
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
    *(
        Telling(
            event=event,
            line=None,
            reaches_the_room=False,
            why_nothing=(
                "retired with the no-show report (#657): nothing writes it, and "
                "a stored row folds to nothing"
            ),
        )
        for event in (NoShowReported, NoShowDisputed)
    ),
    *(
        Telling(
            event=event,
            line=None,
            reaches_the_room=False,
            why_nothing=(
                "who turned up is the game's record and is drawn on its details "
                "(#657); the people it concerns are told by Notifications, and "
                "a line in the room is not ruled"
            ),
        )
        for event in (AbsenceNoted, ArrivalNoted, PresenceClaimed, PresenceConfirmed)
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
    return invariant(
        telling.line,
        f"{type(event).__name__} writes no line: {telling.why_nothing}",
    )
