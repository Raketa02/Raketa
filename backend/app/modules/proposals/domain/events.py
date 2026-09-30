"""The Proposal stream: one per proposed game, filed under the proposal's id.

**Born made**: ``ProposalMade`` is the first event and carries everything the
card promises — the court hour at a club (never a court number, which is given
at booking), the share fixed on it and the book-by the club's way of working
derived for it. Nothing on it is re-read from the club later: a club changing
its prices or its settings changes only the cards dealt after (the mechanics
§5.2, §16.6).

**Nobody's yes is a message.** ``YesSaid`` and ``NoSaid`` are the silent swipe of
the mechanics §6.1–§6.2 and are delivered to nobody but the log; the only
announcement a later ticket gives them is the one the fill makes.

Every event carries ``proposal_id``, the stream's own key, so a record read
alone still says which game it is about. Sport, kind and origin travel as their
codes, as a challenge's do.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class ProposalMade:
    """A game was proposed — **picked** by the engine, or **posted** by a
    member, whose yes is then the next event on the stream.

    ``club_id`` and ``start`` are the court hour and nothing narrower: any
    court of the sport at that club and hour will do until one is booked.
    """

    proposal_id: UUID
    pool_id: UUID
    #: What the pool is made of — ``GROUP`` — so a record read alone says which
    #: kind of pool the game was dealt in, and the pools projection needs no
    #: second source.
    pool_kind: str
    #: ``PICK`` or ``POST``.
    origin: str
    #: The member who posted it; ``None`` on a pick.
    poster_id: UUID | None
    sport: str
    #: The kind of game — ``COMPETITIVE`` or ``FOR_FUN``.
    kind: str
    club_id: UUID
    start: datetime
    #: The court's price divided by the seats, in grosze — fixed on the card.
    share_grosze: int
    #: The latest moment the game can still fill (the mechanics §5.4).
    book_by: datetime
    occurred_at: datetime


@dataclass(frozen=True)
class VersionDealt:
    """One more view of the game was dealt: ``player_ids`` are named for the
    seats still open, beside everybody already In (the mechanics §7). The
    first version is ``1``; there are at most three."""

    proposal_id: UUID
    number: int
    player_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        # JSON hands a list of strings back; the codec coerces a bare ``UUID``
        # hint and nothing inside a tuple, so the stream's own shape is kept
        # here, as ``clubs``' ``ExceptionAdded`` keeps its courts'.
        object.__setattr__(
            self,
            "player_ids",
            tuple(UUID(str(player_id)) for player_id in self.player_ids),
        )


@dataclass(frozen=True)
class YesSaid:
    """A swipe right: *if everybody is in, book it and charge my share.*
    Silent, free, and it holds nothing (the mechanics §6.1)."""

    proposal_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class NoSaid:
    """A swipe left. Silent, final, and never on anybody's record (§6.2)."""

    proposal_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class YesWithdrawn:
    """A yes taken back before the game filled — free, like the yes (§6.5,
    §9.3). The seat is open again, and unlike a no it is no verdict on the
    card: the player may say yes again while the game fills."""

    proposal_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class ProposalWithdrawn:
    """A post ended by its poster taking their yes back **with nobody else
    In** — *the post disappears* (the mechanics §9.3). Recorded right after
    that ``YesWithdrawn``. A post somebody else is In on carries on instead."""

    proposal_id: UUID
    withdrawn_by: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class ProposalExpired:
    """The book-by passed with the game unfilled: nobody paid and the yeses
    lapse (the mechanics §5.4). **The record, not the fact** — the proposal
    reads as expired from its book-by on, and this is written by whoever
    notices after."""

    proposal_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class CourtHourLost:
    """The last court at the card's club and hour went — booked by another card,
    withdrawn by the club, or the club stopped selling — so the game can no
    longer be played where and when it promised (the mechanics §5.2, §19).
    Nobody paid, and the yeses lapse with it; **the people who were In are dealt
    a new card first** (#540). Recorded by the proposer, which is who reads the
    club's hours.

    Only the **last** court: while any court of the sport is free at that club
    and hour, the card still has one — its number is given at booking — and
    nobody's yes changes."""

    proposal_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class GamesAndMoneySet:
    """A player changed their **Games & money** (the mechanics §6.6, §17.1): how
    many games a week they will play, and the most one may cost them. The only
    event on that stream, filed under the player's own id; both values travel
    together, as the screen saves them, so a record read alone is the whole
    setting. ``None`` is *off* — every card is shown, whatever its share."""

    player_id: UUID
    games_per_week: int
    most_ill_pay_grosze: int | None
    occurred_at: datetime
