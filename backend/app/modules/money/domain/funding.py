"""What Money is told when it asks whether a seat can still be bought.

The vocabulary of one question — *money has arrived for this player's seat; is
the seat still hers to have, and what is behind it?* — stated in **Money's**
words rather than in the answering context's. ``Seats`` in ``ports.py`` is the
question; this is the answer, and ``money/infrastructure/seats_through_matches.py``
is the one file that knows whose question it really is.

**Two forms, never one with a sometimes-absent half.** *Hers* carries a
reservation, a club and a custody regime; *gone* carries none of them and could
not, because none of them exists. A single dataclass covering both would carry
three fields that are meaningless in one of the two cases — and typecheck in
both, which is the shape ``commands.py`` refuses one file over.

**Both name a seat, and neither may name none.** A ``shareOnline`` movement
without a seat is refused by ``Movement`` itself (``CAUSE_RULES``), so a payment
that cannot be attributed to a seat is refused at the door rather than recorded
against nothing — see ``PaymentNamesNoSeat``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TypeAlias, final
from uuid import UUID

from app.modules.money.domain.movement import SeatRef


class Custody(str, Enum):
    """Who is holding a seat's money the instant it arrives (ADR-0056).

    **It follows what was sold, never how it was paid.** The same 38 zł buys a
    held share on one path and a passed-through one on the other, and the
    difference is invisible on the screen — which is exactly why the answer has
    to come from the match rather than from the payer or from whoever is
    reporting the landing.

    Cash across a counter is **not** a third member. It is a *channel* and not a
    custody: Raketa is never a party to it (ADR-0059), so there is no position
    for us to be holding or to have passed on. The channel is the caller's fact
    and lives on the command; this is the match's.
    """

    #: An open match: nothing is booked yet, so the money is genuinely Raketa's
    #: to hold until the match commits. This is what ``cancelledIncomplete``
    #: gives back whole.
    HELD = "held"
    #: A private court: it is already bought, so the share is paid through to the
    #: club on arrival and Raketa's position on that seat is zero from the same
    #: instant.
    PASSED_THROUGH = "passedThrough"


@final
@dataclass(frozen=True)
class SeatIsHers:
    """The seat is taken **and** paid, and this is what that write left behind.

    ``reservation`` is the court the payment earned, when it earned one. It is
    ``None`` in two different situations and deliberately does not distinguish
    them, because the movement does not either: a match that has not reached a
    hold tier has no court to name, and a match whose grant found nothing free
    has lost its inventory and never will. Both are *this share funded no
    reservation*, which is the only thing a statement can say about it.
    """

    seat: SeatRef
    club_id: UUID
    custody: Custody
    reservation: UUID | None


@final
@dataclass(frozen=True)
class SeatIsGone:
    """Nothing was written. The money still arrived, and it goes back.

    The late bank confirmation: her five minutes ran out while the money was in
    flight, so the seat went back to the race and somebody else may already have
    it. Holding the claim open until the bank answered would make five minutes
    mean *five minutes, or longer if your bank is slow* (ADR-0081).

    It still names the seat, because the share and its reversal are both about
    the seat she was buying — a refund filed against no seat is one the nightly
    invariant cannot pair with anything.
    """

    seat: SeatRef


#: What ``Seats.pay_for`` answers. See the module docstring.
SeatFunding: TypeAlias = SeatIsHers | SeatIsGone
