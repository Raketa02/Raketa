"""The Games context's domain events — **six, and every one of them an act**.

Events carry **primitive** fields, so their wire format survives any later
refactor of the Python types: a sport, a kind and a window as their codes, a
player as a ``str`` uuid, a whole seating as one string (``lineup.py``) and a
whole score as another (``results.py``).

**No event announces a standing.** There is no ``ResultConfirmed``, no
``GameUnscored`` and no ``GameNeverPlayed``, for the reason ``challenges`` has no
``GameOn``: a derived standing has exactly one place to be true, and an event
saying otherwise would become the second — and it would be the one a subscriber
believed. Silence confirming is a fact about a clock, and a clock has nothing to
publish.

**Two events for one act, at the entry.** *We played, here is the score* is one
tap and two facts, read by different people: ``GamePlayed`` is what
``counted_games``, the pairwise history and *shows up* are built from, and it
stays true whatever happens to the score afterwards; ``ResultProposed`` is the
first move in a negotiation that may end in no score at all. One event carrying
both would make every reader of the first depend on the shape of the second.

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
    arrangement travels whole: **a game's line-up is frozen at the plan**, and
    nothing in this context can move anybody.

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

    def __post_init__(self) -> None:
        _retuple(self, "seatings")


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
