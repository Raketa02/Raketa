"""The club's Bookings page — the rules that need no I/O (#547; the mechanics
§16.7–§16.9, §16.14; the screens B4, B6).

**One day at a time**, every Raketa booking at the club, each with one status
**folded on every read** from the booking and the clock — never stored:

- *waiting for you* — an On request club's full game, until its answer is due;
- *accepted · waiting for one player's payment* — the club said yes and a
  share could not be held: its yes and the court are kept until the player's
  time to pay ends (#626; Q112) — never in *waiting for you*, since the club
  has answered;
- *booked* — full and paid, its hour still to come;
- *seat open* — a player left and the seat is offered;
- *called off* — refused, unanswered, short at the cut-off, cancelled by the
  club, or a player's payment that did not come in time after its yes — each
  read off the clock from the moment it is true, whether or not anything has
  recorded it yet;
- *played* — a booked game whose hour has passed. The club is owed the court
  whatever happened on it, so a game that went ahead short, or one somebody
  did not come to, is *played* here.

**What the club may still do to a game** is read here too: a booked game — whole
or with a seat open — may be moved or cancelled **until it starts**, and never
once it is called off.

**What the club sees of a player is their name, and whether they paid or their
share is only held** (§16.14) — nothing about their level, their record or the
game's chat, and since desk check-in was removed (#651), nothing about whether
they came.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from collections.abc import Iterable
from typing import Final, final
from uuid import UUID

from app.kernel import SPORT_SPECS, Instant
from app.modules.proposals.domain.deck import GAME_LENGTH
from app.modules.proposals.domain.home import (
    BookedGame,
    BookingStage,
    CalledOffReason,
)


class ClubStatus(StrEnum):
    """What a booking is to its club, right now (the mechanics §16.7)."""

    WAITING_FOR_YOU = "WAITING_FOR_YOU"
    #: The club said yes, and one player's payment is still to come (#626).
    WAITING_FOR_A_PAYMENT = "WAITING_FOR_A_PAYMENT"
    BOOKED = "BOOKED"
    SEAT_OPEN = "SEAT_OPEN"
    CALLED_OFF = "CALLED_OFF"
    PLAYED = "PLAYED"


class ClubFilter(StrEnum):
    """The page's filters (the screens B4)."""

    ALL = "ALL"
    WAITING_FOR_YOU = "WAITING_FOR_YOU"
    SEAT_OPEN = "SEAT_OPEN"
    CALLED_OFF = "CALLED_OFF"


def called_off_for_the_club(
    game: BookedGame, *, now: Instant
) -> CalledOffReason | None:
    """Why the game will not be played, at ``now`` — the players' reasons, a
    request whose answer came due unanswered, which is *no answer* from that
    moment whether or not the timeout has recorded it, and a payment the
    club's yes waited on, which did not come by its time (#626)."""

    if (
        game.stage is BookingStage.WAITING_FOR_THE_CLUB
        and game.answer_by is not None
        and now >= game.answer_by
    ):
        return CalledOffReason.NO_ANSWER
    if (
        game.stage is BookingStage.WAITING_FOR_A_PAYMENT
        and game.pay_by is not None
        and now >= game.pay_by
    ):
        return CalledOffReason.PAYMENT_NOT_IN_TIME
    return game.called_off_reason(now)


def club_status(game: BookedGame, *, now: Instant) -> ClubStatus:
    if called_off_for_the_club(game, now=now) is not None:
        return ClubStatus.CALLED_OFF
    if game.stage is BookingStage.WAITING_FOR_THE_CLUB:
        return ClubStatus.WAITING_FOR_YOU
    if game.stage is BookingStage.WAITING_FOR_A_PAYMENT:
        return ClubStatus.WAITING_FOR_A_PAYMENT
    if now >= game.start + GAME_LENGTH:
        return ClubStatus.PLAYED
    if game.stage is BookingStage.SEAT_OPEN:
        return ClubStatus.SEAT_OPEN
    return ClubStatus.BOOKED


def shown_under(status: ClubStatus, chosen: ClubFilter) -> bool:
    """Whether a booking of this status is on the page under this filter."""

    return chosen is ClubFilter.ALL or status.value == chosen.value


def still_to_be_played(game: BookedGame, *, now: Instant) -> bool:
    """Whether the club may still move or cancel it: booked — whole or with a
    seat open — not called off, and its hour still ahead."""

    return (
        game.stage in (BookingStage.BOOKED, BookingStage.SEAT_OPEN)
        and game.called_off_reason(now) is None
        and now < game.start
    )


def price_of(game: BookedGame) -> int:
    """The court's price for the hour — every seat's share."""

    return game.share_grosze * SPORT_SPECS[game.sport].players


@final
@dataclass(frozen=True, slots=True)
class Takings:
    """A booking's money as its club reads it (the mechanics §16.7, §16.11):
    who paid and whose share is only held, what was collected — taken shares
    only (#637) — what was given back — and, on the Money page
    (#548), the card fees the club pays on it, what is the club's, and whether
    a payout has carried that to its bank."""

    #: Everybody whose share was taken.
    paid: frozenset[UUID]
    collected_grosze: int
    #: ``None`` while a refund less the fee kept waits for a fee not yet known
    #: (#641).
    refunded_grosze: int | None
    #: The provider's card fee on every share taken — never returned; the real
    #: one, or ``None`` while any is not yet known (#641). Never an estimate.
    card_fees_grosze: int | None = 0
    #: Whether a payout carried it to the club's bank; until then it waits on
    #: the club's account, where a refund before the start can come out of it.
    paid_out: bool = False
    #: Everybody whose share is held on their card for the game until the
    #: club's cut-off, which takes it (#637) — not paid, and not collected.
    held: frozenset[UUID] = frozenset()

    @property
    def net_grosze(self) -> int | None:
        """What is the club's: collected, less refunded, less the card fees —
        below nought on a game everybody was given back whole; ``None`` while
        either is not yet known."""

        if self.refunded_grosze is None or self.card_fees_grosze is None:
            return None
        return self.collected_grosze - self.refunded_grosze - self.card_fees_grosze


def known_sum(figures: Iterable[int | None]) -> int | None:
    """The sum of figures each real or not yet known: not yet known if any of
    them is — never a total that leaves one out (#641)."""

    total = 0
    for figure in figures:
        if figure is None:
            return None
        total += figure
    return total


NOTHING_TAKEN: Final = Takings(paid=frozenset(), collected_grosze=0, refunded_grosze=0)


@final
@dataclass(frozen=True, slots=True)
class BookedFrom:
    """The group a booking came from, as the club's page names it."""

    name: str
    #: One of the club's own official groups, or a player group.
    official: bool


@final
@dataclass(frozen=True, slots=True)
class CourtToMoveTo:
    """A free court of the game's sport at its hour, as the club calls it."""

    court_id: UUID
    name: str


@final
@dataclass(frozen=True, slots=True)
class ClubCancellation:
    """What the club's cancel owes: everybody still in — refunded in full and
    dealt a new card first — and everybody given money back, which adds a
    leaver whose seat it left open and paid."""

    still_in: tuple[UUID, ...]
    refunded: tuple[UUID, ...]
