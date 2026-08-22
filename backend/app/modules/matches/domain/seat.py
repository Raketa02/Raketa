"""A seat, and the relationship a player has to it.

**Enrolment is a relationship, not an object** (ADR-0034). There is no
``Enrolment`` aggregate, no enrolment row with a lifecycle of its own, and
nothing that can be enrolled without a seat to be enrolled in: a seat either
names a player or it does not. ``3.1`` §0.1 puts it as *"the state is a property
of the match and the wording is a property of your relationship to it"*, and
encoding that relationship as its own object would be the third instance of the
mistake ADR-0030 named — a fact about a player's relationship stored as a fact
about the match.

**Taken and paid are two facts, never one.** A seat somebody holds and nobody
has paid for is the whole of ``formingHeld``; folding it into *filled* tells
four people a match is complete while a seat may still lapse
(``Raketa02/Raketa#74``). The kernel refuses the degenerate combination — paid
with nobody on it — and so does this, at the door rather than downstream.

**A vacancy is not stored here.** A seat that was left is simply free again; the
*hole* a departure left, and when it was left, is its own fact with its own life
(``vacancy.py``), because a seat can be refilled without changing anything about
the departure that emptied it (ADR-0033).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.kernel import Seat as RecordSeat

from app.modules.matches.domain.errors import (
    SeatAlreadyPaid,
    SeatAlreadyTaken,
    SeatNotTaken,
)


@final
@dataclass
class Seat:
    """One of the court's seats: whether somebody holds it, and whether it is paid.

    ``index`` is the seat's position in the match's fixed order and is its
    identity: the sport decides how many seats there are, so a seat is never
    created or destroyed, only occupied and emptied. That is what lets the
    record carry *exactly as many seats as the sport is sold for, in a fixed
    order* without a count stored anywhere.
    """

    index: int
    player_id: UUID | None = None
    paid: bool = False
    taken_at: Instant | None = None

    def __post_init__(self) -> None:
        if self.paid and self.player_id is None:
            raise ValueError(f"seat {self.index} is paid with nobody on it")

    @property
    def is_taken(self) -> bool:
        return self.player_id is not None

    @property
    def is_free(self) -> bool:
        return self.player_id is None

    def take(self, player_id: UUID, *, at: Instant) -> None:
        """A player takes the seat, holding it and owing for it."""

        if self.is_taken:
            raise SeatAlreadyTaken()
        self.player_id = player_id
        self.taken_at = at
        self.paid = False

    def pay(self) -> None:
        """The seat's money landed.

        Separate from taking it, because *held* and *paid* are two states the
        card says two different things about — not because there is a grace
        period, which ADR-0034 considered and rejected.
        """

        if not self.is_taken:
            raise SeatNotTaken()
        if self.paid:
            raise SeatAlreadyPaid()
        self.paid = True

    def vacate(self) -> None:
        """The seat is empty again. Whose it was is the departure's to remember."""

        if not self.is_taken:
            raise SeatNotTaken()
        self.player_id = None
        self.taken_at = None
        self.paid = False

    def as_record(self) -> RecordSeat:
        """The two bits the ladder reads. **No player identity crosses.**"""

        return RecordSeat(taken=self.is_taken, paid=self.paid)
