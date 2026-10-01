"""The Games context's domain events — **ten, and every one of them an act**.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a sport, a kind and a window as their codes, a
player as a ``str`` uuid, a whole seating as one string (``lineup.py``) and a
whole score as another (``results.py``).

**No event announces a standing the record already implies.** There is no
``ResultConfirmed``, no ``GameUnscored`` and no ``GameNeverPlayed``, for the
reason ``challenges`` has no ``GameOn``: a derived standing has exactly one place
to be true, and an event saying otherwise would become the second — and it would
be the one a subscriber believed. Silence confirming is a fact about a clock, and
a clock has nothing to publish.

**One event announces an end, and it is the rule's one exemption here**
(``docs/adr/0163``). ``GameCalledOff`` is a decision a person took while a seat
was open, and there is nothing on the record to fold it out of — no played
moment, no window closing — so it passes ``docs/adr/0142`` §3's test the way
``ChallengeWithdrawn`` does: *an event may announce a conclusion only when no
arrangement of the record could reach it*. It is the first event here about the
game as a whole rather than about a seat, a score or a moment, and the next one
has to pass the same test in writing.

**Two events for one act, at the entry.** *We played, here is the score* is one
tap and two facts, read by different people: ``GamePlayed`` is what
``counted_games``, the pairwise history and *shows up* are built from, and it
stays true whatever happens to the score afterwards; ``ResultProposed`` is the
first move in a negotiation that may end in no score at all. One event carrying
both would make every reader of the first depend on the shape of the second.

**Two events move the line-up, and both are told rather than decided here**
(``docs/adr/0162``). ``SeatVacated`` is somebody leaving a game they agreed to,
and ``LineUpReseated`` is the next completed line-up arriving for a game that
has a seat open; each is written in the transaction of the act on the challenge
that caused it. Neither announces a standing — a court with an open seat is still
``AWAITING_ENTRY`` — and each passes ``docs/adr/0142`` §3's test the way a
withdrawal does: a departure, and the arrangement that replaces it, are decisions
no arrangement of this record could reach.

**One event is a player's own and moves nothing on the game**
(``docs/adr/0172`` §5). ``GameDismissed`` is somebody clearing a called-off
game's card from their own rail: recorded once per player on the game's stream
because the card must be gone on their other phone and after a reinstall, and
read by the rail's fold alone — not by the tallies, not by the settled query,
not by the room, which is gone before a card can be dismissed. It announces no
standing and changes nobody else's read.

**Three proposals events and not one with a kind field.** A first score, a
revision of your own side's score and a disagreement with the other side's are
three different things to explain to a player, and ADR-0034's surviving
obligation is that *every change a support agent would one day need to explain is
announced as its own named event.* A ``kind`` field would be that obligation
answered with a string.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class GamePlanned:
    """A line-up completed, so there is now a game to have played.

    Opened by ``challenges`` in the transaction of the accept that filled the
    last seat, through a port it declares and this context signs. The
    arrangement travels whole: **a game's line-up is frozen until somebody
    leaves it** (``docs/adr/0162``), and nothing in this context moves anybody on
    its own.

    ``window`` is the code the challenge was sent under, carried through and
    never re-derived — ``None`` exactly when the challenge had none, which is a
    mutual-born one. It is recorded rather than read because it is what the
    people who accepted were agreeing to.
    """

    game_id: UUID
    challenge_id: UUID
    sport: str
    kind: str
    window: str | None
    #: The whole court, in the order ``challenges`` handed it over: one
    #: ``A|<uuid>`` per person. See ``lineup.py`` for the code.
    seatings: tuple[str, ...]
    occurred_at: datetime
    #: The hour it is booked for, on a game **a booking** opened (#541) — and
    #: then ``challenge_id`` is the booking's id, the arrangement it came from.
    #: ``None`` on a game a completed line-up opened, which has no hour: a
    #: default rather than a version 2, since every row written without it is
    #: exactly such a game.
    starts_at: datetime | None = None

    def __post_init__(self) -> None:
        _retuple(self, "seatings")


@dataclass(frozen=True)
class SeatVacated:
    """Somebody on the court left the game before it happened.

    Told by ``challenges``, in the transaction of the departure it recorded, so
    the seat opens on both records or on neither. The game's ``planned_at`` does
    not move: it keeps meaning *when it became a game*.
    """

    game_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class LineUpReseated:
    """A completed line-up arrived for a game with a seat open, and this is the
    court now.

    **The whole arrangement travels**, as ``GamePlanned.seatings`` and
    ``challenges``' ``SeatsInvited`` carry theirs, because a re-seat may move an
    accepted player across the net as well as fill the seat, and two events
    would let a reader fold a half-applied court nobody built. Same field name
    as the opening's on purpose: the stream reads match on it, so a newcomer is
    found on the court they joined.
    """

    game_id: UUID
    seatings: tuple[str, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        _retuple(self, "seatings")


@dataclass(frozen=True)
class GameCalledOff:
    """The game was ended while a seat was open.

    Told by ``challenges`` in the transaction of what ended the court
    (``docs/adr/0163`` §2, ``docs/adr/0172`` §1, ``docs/adr/0175``) — the
    departure that left at most one player on it, or the hour that found it
    still short of a player — so the ``CALLED_OFF`` on the challenge and the
    end on the game commit together or neither does. It carries **who**: the
    leaver whose departure emptied the court, and since ``docs/adr/0172`` §4
    that name crosses the wire as ``called_off_by`` — the leaver's seat is
    vacated by then, so the court cannot supply it — or **nobody**, when the
    hour called it off (``0175`` §3). Nobody presses it any more; a payload
    written while somebody could still decodes, at version 1, with the field
    widened to nullable.

    **It is the fourth end and the only one an event reaches.** The standing
    reads it first, before the clock; a game already ended by its clock is never
    told this, because un-ghosting a game the platform has already drawn as
    *Never played* would contradict the card.
    """

    game_id: UUID
    called_by: UUID | None
    occurred_at: datetime


@dataclass(frozen=True)
class GameDismissed:
    """One player cleared this called-off game's card from their own rail
    (``docs/adr/0172`` §5).

    The reader's own act and nobody else's fact: recorded once per player, so a
    second dismissal by the same player writes nothing, and read by the rail's
    fold alone — ``GET /games`` omits a game its reader has dismissed, derived
    on every read and never a stored list. It removes a card, not a fact: the
    game, its record and the challenge's row are untouched, and there is no
    undo.
    """

    game_id: UUID
    dismissed_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class GamePlayed:
    """Somebody who was on the court says it happened. **The moment is this one.**

    There is no date field, and that is the decision rather than an omission: the
    entry carries the moment, because a booking, a calendar and a court
    reservation are exactly the three things this platform does not have, and a
    date asked for is a date nothing can check.
    """

    game_id: UUID
    said_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class ResultProposed:
    """The first score put on the table, by the side that entered it."""

    game_id: UUID
    player_id: UUID
    side: str
    score: str
    occurred_at: datetime


@dataclass(frozen=True)
class ResultCorrected:
    """The proposing side fixing its own score before anybody answered it.

    **Not a second proposal**, and the cap of one per side is untouched by it.
    It may come from **any** member of the proposing side, not only the author:
    the rule that makes a teammate's agreement worthless is the same rule that
    makes a teammate's objection credible, and this is where that survives after
    the cap took countering-from-your-own-side away (``docs/adr/0137``).

    It **re-dates the proposal**, because the other side is answering a score,
    and a score they have not seen has not started their day.
    """

    game_id: UUID
    player_id: UUID
    side: str
    score: str
    occurred_at: datetime


@dataclass(frozen=True)
class ResultCountered:
    """The other side's disagreement. **It carries a score, always.**

    There is no bare rejection in this context. A rejection carrying no score
    would be free and always optimal for the loser: suspend the result, protect
    your Level, and nothing was ever said in front of the people who were there.
    """

    game_id: UUID
    player_id: UUID
    side: str
    score: str
    occurred_at: datetime


@dataclass(frozen=True)
class ResultAccepted:
    """Somebody on the opposing side agreed. **One opponent suffices.**

    It settles nothing on its own: the grace runs from the proposal, and inside
    it a counter still wins. ``side`` is the accepter's; the proposal it accepts
    is the other one, by construction.
    """

    game_id: UUID
    player_id: UUID
    side: str
    occurred_at: datetime


def _retuple(event: object, *fields: str) -> None:
    """Force a collection field to a tuple, on the way in and out of storage.

    The codec encodes a tuple as a JSON array and decodes it back as a ``list``,
    so without this an event that has been through the store is unequal to the
    event that was appended — and a replay would fold lists where the first pass
    folded tuples.
    """

    for field in fields:
        object.__setattr__(event, field, tuple(getattr(event, field)))
