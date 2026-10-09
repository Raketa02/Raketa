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
    #: Who a post is for — ``ANYONE``, ``MEN``, ``WOMEN`` or ``MIXED_PAIRS`` —
    #: and the range the others' Levels are in (#546). ``None`` on a pick, and
    #: on a post made before posts had either, which is for anybody.
    who: str | None = None
    level_low: float | None = None
    level_high: float | None = None


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
    Silent, free, and it holds nothing (the mechanics §6.1). On a post it may
    come from a member it was never dealt to, joining it from the slot sheet
    (#546)."""

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
class ProposalFilled:
    """**The last yes booked the game** (the mechanics §11; #541): every seat's
    share was held and taken, and a Booking opened under this proposal's own
    id. Every version disappears with it.

    ``first_side`` and ``second_side`` are the people whose yeses filled it,
    **drawn for the most even game** — which is what a yes means: E said yes to
    a card showing Marek, E, F and G, and plays with Marek, B and C (§7).

    ``filled_by`` is the player whose own act filled it — the last yes, a join
    or a confirmed payment — so what it booked is never told back to them as
    news (the mechanics Q102); ``None`` when no player's act did: the club's
    yes, a paused yes coming back. Defaulted for the rows recorded before it
    was asked, which name nobody."""

    proposal_id: UUID
    first_side: tuple[UUID, ...]
    second_side: tuple[UUID, ...]
    occurred_at: datetime
    filled_by: UUID | None = None

    def __post_init__(self) -> None:
        for side in ("first_side", "second_side"):
            object.__setattr__(
                self,
                side,
                tuple(UUID(str(player_id)) for player_id in getattr(self, side)),
            )


@dataclass(frozen=True)
class SeatReopened:
    """The last yes came and **this player's yes could not be counted**, so
    nothing was booked and their seat is open again — *your seat reopens* (the
    mechanics §12.2). Not their act: their share could not be held — the bank
    wanted them present, or refused, or their method cannot be charged — or
    they and somebody In may no longer share a court (§7). ``reason`` is the
    ``ReopenReason`` code.

    ``seat_charge_id`` is the refused payment, which they confirm in the app —
    *confirming is your yes again*; ``None`` where nothing was asked of the
    provider. Like a withdrawn yes, it is no verdict on the card: they may say
    yes again while the game fills."""

    proposal_id: UUID
    player_id: UUID
    seat_charge_id: UUID | None
    reason: str
    occurred_at: datetime


@dataclass(frozen=True)
class YesPaused:
    """Another game of this player's filled, and **their games per week are
    booked** for the week this one is in: the yes stops counting, and they are
    never booked more games than they asked for (the mechanics §6.6). It comes
    back if one of those games is called off (#544)."""

    proposal_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class YesResumed:
    """A yes another game's booking paused **comes back** (#544; the mechanics
    §19): one of the games that filled the player's week was called off, or
    they left it, so their week has room again and the yes counts once more —
    as theirs, said before, not said again."""

    proposal_id: UUID
    player_id: UUID
    occurred_at: datetime


@dataclass(frozen=True)
class TurnedDown:
    """**The club did not take it** (#543; the mechanics §16.8): every seat was
    In and the game waited for its On request club, which refused it or did not
    answer by its deadline. Nobody paid; *Called off · refused / no answer* is
    the booking's to say. ``answer`` is ``REFUSED`` or ``NO_ANSWER``.

    **The people who were In stay on the record** and are dealt a new card
    first — never at this club and hour, which the club turned down."""

    proposal_id: UUID
    answer: str
    occurred_at: datetime


@dataclass(frozen=True)
class ClubCancelled:
    """**The club cancelled the booked game** (#547; the mechanics §16.9): the
    booking says why, and refunds everybody still in in full. ``player_ids``
    — everybody still in when it did — are **dealt a new card first**, never at
    this club and hour. The proposal still filled; this is what it owes."""

    proposal_id: UUID
    player_ids: tuple[UUID, ...]
    occurred_at: datetime

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "player_ids", tuple(UUID(str(one)) for one in self.player_ids)
        )


@dataclass(frozen=True)
class Redealt:
    """The proposer has dealt the people In on a game its club turned down — or
    still in on one it cancelled (#547) — a new card first. What makes such a
    game owe nothing more; until it, every proposer run looks for an hour again,
    while the game's own hour is still ahead."""

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
