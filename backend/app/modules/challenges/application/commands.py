"""What a caller asks this context to do.

The organiser is named explicitly rather than taken from an ambient *current
user*, for the reason every command in this codebase is: a use case that read the
caller from somewhere would be a use case a seed run or a management command
could not drive, and the boundary is where an identity comes from a token.

**The arrangement travels whole.** It is the sides the organiser built, in the
court's own order, and it is what the invitee will be answering — never a better
one worked out afterwards.

**What the caller does not say is as load-bearing as what it does.** A send
carries the court and the search it was built on, and nothing else: the sport,
the kind of evening and the **window** are read off that search's own record, and
each invitee's position in it is looked up rather than sent. A window a client
stated would be a window somebody was asked for, which ``docs/adr/0100`` has no
picker for anywhere; a position a client stated would be true only while the
client was honest about where it had scrolled to.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from app.kernel import Sport
from app.modules.challenges.domain.seats import Side


@dataclass(frozen=True, slots=True)
class SeatChoice:
    """One position on the court as the organiser left it: a side, and who.

    ``player_id`` is ``None`` for a seat nobody was put in — **an empty seat is a
    seat**, because an A-side full with a B-side short is a different court from
    the reverse and the next invitee's side is not a free choice.

    It carries no origin, which is what separates it from ``SeatPlan``: where an
    invitation came from is resolved server-side against the cited search, and a
    caller has nothing to say about it.
    """

    side: Side
    player_id: UUID | None = None


@dataclass(frozen=True, slots=True)
class SendChallengeCommand:
    """*Ask everybody on this court to play.*

    ``search_id`` is the court's origin. It is one search and not one per seat:
    the arrangement was built and forecast against a single answer, and a court
    assembled out of two searches is a court no forecast was ever computed for.
    """

    organiser_id: UUID
    search_id: UUID
    court: tuple[SeatChoice, ...]


@dataclass(frozen=True, slots=True)
class AnswerSeatCommand:
    """*Yes* or *no*, from the person holding one seat.

    The challenge is named and the seat is not: a player holds at most one seat
    in a challenge, so an id for it would be a second way to say the same thing
    and a way for a caller to answer somebody else's.
    """

    challenge_id: UUID
    player_id: UUID


@dataclass(frozen=True, slots=True)
class OpenFromMutualInterestCommand:
    """*These two just said yes to each other.*

    No window and no mode: nothing was proposed from a grid and nobody picked a
    kind of evening. No deadline either — each of them has already said yes to
    the other, and asking either to answer again would make *you now have an open
    game together* not yet true.
    """

    sport: Sport
    #: The player whose yes arrived second, and who therefore holds seat one.
    #: They are the organiser in the sense the aggregate means it — the seat the
    #: court is built out from — and in no other: neither of them proposed
    #: anything to the other.
    player_id: UUID
    other_player_id: UUID
