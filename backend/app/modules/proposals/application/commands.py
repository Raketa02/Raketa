"""What a caller asks the Proposals context for, in the primitives it asked in.

Plain values rather than value objects, for the reason ``RegisterUserCommand``
gives: a command is what a caller *asked for*, and the boundary must be able to
express the answer that gets refused.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport
from app.modules.proposals.domain.overlap import DayRange
from app.modules.proposals.domain.post import PostedFor, Who
from app.modules.proposals.domain.proposal import Origin


@dataclass(frozen=True)
class MakeProposalCommand:
    """A game proposed at a court hour, and the versions it is dealt in.

    ``poster_id`` is the member who posted it, and ``None`` for a pick.
    ``versions`` are the names for the open seats, one tuple per version —
    none at all is a proposal nobody has been dealt yet. ``proposal_id`` is the
    stream to make it in — the proposer's ``pick_id``, so two processes cannot
    make one game twice — and a fresh one when ``None``. ``posted_for`` is who
    a post is for (#546); ``None`` on a pick, and on a post for anybody.
    ``owed_card_for`` makes a pick the owed card for those people (#673)."""

    pool_id: UUID
    origin: Origin
    poster_id: UUID | None
    sport: Sport
    kind: SearchMode
    club_id: UUID
    start: Instant
    versions: Sequence[Sequence[UUID]] = ()
    proposal_id: UUID | None = None
    posted_for: PostedFor | None = None
    owed_card_for: Sequence[UUID] = ()


@dataclass(frozen=True)
class DealVersionCommand:
    """One more version, or — ``into_version`` — the next best fits for the
    seats a no left on an existing one."""

    proposal_id: UUID
    player_ids: Sequence[UUID]
    into_version: int | None = None


@dataclass(frozen=True)
class AnswerProposalCommand:
    """A yes, a no, or a yes taken back. ``player_id`` comes from the session,
    never from the body."""

    proposal_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class ConfirmPaymentCommand:
    """*I confirmed this refused payment in the app* — the yes again.
    ``player_id`` comes from the session."""

    seat_charge_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class ReadGroupDeckCommand:
    """One reader's deck in one pool, sport and segment. ``player_id`` comes
    from the session."""

    player_id: UUID
    pool_id: UUID
    sport: Sport
    kind: SearchMode


@dataclass(frozen=True)
class SetGamesAndMoneyCommand:
    """Both values, as the screen sends them on every tap — ``None`` is *off*."""

    player_id: UUID
    games_per_week: int
    most_ill_pay_grosze: int | None


@dataclass(frozen=True)
class LeaveTheGameCommand:
    """*Leave the game* on a booked game's details (#544)."""

    booking_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class RescueCommand:
    """*I'm in* — or *not this time* — on a rescue: an open seat on a booked
    game (#545). ``player_id`` comes from the session."""

    booking_id: UUID
    player_id: UUID


@dataclass(frozen=True)
class ReadFillInCommand:
    """One reader's *Fill in* tab in one pool and sport (#545)."""

    player_id: UUID
    pool_id: UUID
    sport: Sport


@dataclass(frozen=True)
class PostingCommand:
    """What every step of posting a game is asked in (#546; the screens A5.1):
    the poster — from the session — the group, and the four controls. A level
    bound left out is the engine's own."""

    player_id: UUID
    pool_id: UUID
    sport: Sport
    kind: SearchMode
    who: Who
    level_low: float | None = None
    level_high: float | None = None


@dataclass(frozen=True)
class ReadPostingGridCommand:
    """One week of the posting grid — ``1`` starts today, ``2`` the week after."""

    posting: PostingCommand
    week: int


@dataclass(frozen=True)
class ReadPostingSlotCommand:
    """One cell's sheet: a day on the club's clock and a third of it."""

    posting: PostingCommand
    day: date
    day_range: DayRange


@dataclass(frozen=True)
class PostAGameCommand:
    """*Post — you're In*: the court hour picked on a sheet."""

    posting: PostingCommand
    club_id: UUID
    start: Instant
