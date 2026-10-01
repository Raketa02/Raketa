"""What a caller asks the Proposals context for, in the primitives it asked in.

Plain values rather than value objects, for the reason ``RegisterUserCommand``
gives: a command is what a caller *asked for*, and the boundary must be able to
express the answer that gets refused.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from uuid import UUID

from app.engines.matchfit.core import SearchMode
from app.kernel import Instant, Sport
from app.modules.proposals.domain.proposal import Origin


@dataclass(frozen=True)
class MakeProposalCommand:
    """A game proposed at a court hour, and the versions it is dealt in.

    ``poster_id`` is the member who posted it, and ``None`` for a pick.
    ``versions`` are the names for the open seats, one tuple per version —
    none at all is a proposal nobody has been dealt yet. ``proposal_id`` is the
    stream to make it in — the proposer's ``pick_id``, so two processes cannot
    make one game twice — and a fresh one when ``None``."""

    pool_id: UUID
    origin: Origin
    poster_id: UUID | None
    sport: Sport
    kind: SearchMode
    club_id: UUID
    start: Instant
    versions: Sequence[Sequence[UUID]] = ()
    proposal_id: UUID | None = None


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
