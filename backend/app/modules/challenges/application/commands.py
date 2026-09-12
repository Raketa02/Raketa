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
class WithdrawChallengeCommand:
    """*End this challenge, for everybody on it.*

    **Not an ``AnswerSeatCommand`` with a third value**, and the two fields being
    identical is not a reason to make it one: an answer is about the seat the
    caller holds and this is about the arrangement everybody holds one in. A
    command they shared would be a caller that could withdraw where it meant to
    decline, and a reader who had to look at the use case to find out which.

    The player is named for the reason every command here names one — a use case
    that read the caller from an ambient current user is a use case a seed run
    cannot drive — and the aggregate is what decides that this player is the
    organiser.
    """

    challenge_id: UUID
    player_id: UUID


@dataclass(frozen=True, slots=True)
class LeaveGameCommand:
    """*I am out of this game.* From the person holding one accepted seat.

    **Not an ``AnswerSeatCommand`` under a third name**, for the reason the
    withdraw is not: an answer is about an invitation and this is about a game
    the caller had already agreed to. The two fields being the same is not a
    reason to share the type — a caller that could leave where it meant to
    decline is exactly the caller the split refuses.
    """

    challenge_id: UUID
    player_id: UUID


@dataclass(frozen=True, slots=True)
class FillSeatsCommand:
    """*Ask these people to take the open seats on this court.*

    **The send's shape minus the mint** (``docs/adr/0150`` §6): the challenge
    already exists and its id is in the path, so what is left is the court and
    the search it was built on.

    ``court`` is the **whole** arrangement, not the new seats: an acceptance is
    to the game and not to the side, so the people already in may be moved across
    the net and may not be taken out — and an arrangement that named only the
    newcomers could not say which way round the four ended up sitting.

    ``player`` is whoever pressed it, and **any live member may**. Growing a court
    and ending one are different acts: the withdraw is the organiser's, and a
    challenge born of two mutual yeses has an organiser who is only whoever said
    yes second.

    **No sport, no mode and no window.** All three are the challenge's, and the
    window is never re-stamped — a re-stamp would move a fact other people have
    already answered against.
    """

    challenge_id: UUID
    player_id: UUID
    search_id: UUID
    court: tuple[SeatChoice, ...]


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
