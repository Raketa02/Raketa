"""The Games context's domain events — **eleven written, one retired, and every
one of them an act**.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a sport, a kind and a window as their codes, a
player as a ``str`` uuid, a whole seating as one string (``lineup.py``) and a
whole score as another (``results.py``).

**No event announces a standing the record already implies.** There is no
``ResultConfirmed``, no ``GameUnscored`` and no ``GameNeverPlayed``: a derived
standing has exactly one place to be true, and an event saying otherwise would
become the second — and it would be the one a subscriber believed. Silence
confirming is a fact about a clock, and a clock has nothing to publish.

**One event announces an end, and it is the rule's one exemption here**
(``docs/adr/0163``). ``GameCalledOff`` is a decision taken while a seat was
open, or by the club over the whole court, and there is nothing on the record to
fold it out of — no played moment, no window closing — so it passes
``docs/adr/0142`` §3's test: *an event may announce a conclusion only when no
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
and ``LineUpReseated`` is a rescue taking a seat that was open (#545); each is
written in the transaction of the act on the booking that caused it. Neither
announces a standing — a court with an open seat is still ``AWAITING_ENTRY`` —
and each passes ``docs/adr/0142`` §3's test: a departure, and the arrangement
that replaces it, are decisions no arrangement of this record could reach.

**Two events are about somebody who did not come** (#547): ``NoShowReported``
is a player who came saying so of another, and ``NoShowDisputed`` is that other
saying they did. Neither announces a standing — a report stands only by its day
passing in silence, which is a clock, and a clock has nothing to publish.

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
    """A line-up was booked, so there is now a game to have played.

    Opened by ``bookings`` in the transaction of the fill that booked the court
    (#541), through games' own use case. The arrangement travels whole: **a
    game's line-up is frozen until somebody leaves it** (``docs/adr/0162``), and
    nothing in this context moves anybody on its own.

    ``challenge_id`` is the booking's id, under the name the field was born
    with when a challenge's completed line-up opened games; ``window`` is
    ``None`` on every booked game, which has an hour instead. Both stay on the
    payload so the wire format of a stored row never moves.
    """

    game_id: UUID
    challenge_id: UUID
    sport: str
    kind: str
    window: str | None
    #: The whole court, in the order the booking handed it over: one
    #: ``A|<uuid>`` per person. See ``lineup.py`` for the code.
    seatings: tuple[str, ...]
    occurred_at: datetime
    #: The hour it is booked for, on a game **a booking** opened (#541).
    #: ``None`` on a row written before bookings, which had no hour: a default
    #: rather than a version 2, since every row written without it is exactly
    #: such a game.
    starts_at: datetime | None = None

    def __post_init__(self) -> None:
        _retuple(self, "seatings")


@dataclass(frozen=True)
class SeatVacated:
    """Somebody on the court left the game before it happened.

    Told by ``bookings``, in the transaction of the departure it recorded
    (#544), so the seat opens on both records or on neither. The game's
    ``planned_at`` does not move: it keeps meaning *when it became a game*.
    """

    game_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class LineUpReseated:
    """A rescue took a seat that was open (#545), and this is the court now.

    **The whole arrangement travels**, as ``GamePlanned.seatings`` carries it,
    so a reader never folds a half-applied court nobody built. Same field name
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
    """The game was ended while a seat was open — or, by its club, whole.

    Told by ``bookings`` in the transaction of what ended it: the cut-off that
    found a seat still open (#544), or the club taking the court back (#547).
    It carries **who** (``docs/adr/0172`` §4), and that name crosses the wire as
    ``called_off_by`` — **nobody**, for both. A payload written while a leaver
    could still be named decodes, at version 1, with the field nullable.

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
    """**Retired** (#578): one player cleared a called-off game's card from
    their own rail (``docs/adr/0172`` §5), from the old game card the
    challenges' loop drew.

    Nothing writes it any more. It stays because stored history outlives the
    code that wrote it: a booked game called off at its cut-off could be
    dismissed, and every read of a game walks its whole stream — so a stored
    row still decodes, and the fold reads it and changes nothing.
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

    It settles the result at once and closes the game (#654; ``docs/adr/0195``
    §5) — which no fold has to announce, because the standing reads it: no
    ``ResultConfirmed`` follows it. ``side`` is the accepter's; the proposal it
    accepts is the other one, by construction. A row written while an agreement
    still ran out a six-hour grace may be followed by a counter, which voided it
    (``standing.live_acceptance``).
    """

    game_id: UUID
    player_id: UUID
    side: str
    occurred_at: datetime


@dataclass(frozen=True)
class NoShowReported:
    """Somebody who came to a **booked** game says ``player_id`` did not (#547;
    the mechanics §15.3) — *Kuba didn't come*, where they would have entered the
    result. **Not a standing**: the player has a day to dispute it, and only the
    day passing in silence makes it stand, which nothing announces.
    """

    game_id: UUID
    player_id: UUID
    reported_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class NoShowDisputed:
    """The player reported as not turning up says they did, inside their day
    (#547). **Nobody arbitrates**: the report falls, and nothing goes on their
    record."""

    game_id: UUID
    player_id: UUID
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
