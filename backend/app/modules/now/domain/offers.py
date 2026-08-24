"""What Now needs about a seat somebody has been offered, in Now's words.

The offers region is the one region on the screen a player is neither committed
to nor being suggested: she has been **told a seat freed**, and the card exists
to let her race for it. Two contexts meet in this shape — the match with its club
and court, and the offer the cascade wrote — and everything a card prints comes
from one of the two.

**The port answers facts and the composer applies rules**, exactly as
``enrolled.py`` splits them. Whether the seat is still there, what it costs at
this instant, which situation the ladder answers and what order the region is in
are all the composer's; what a row carries is what four tables say.

**An offer is a fact about the past and a seat is not.** ``Offers.held_by``
answers *what was put in front of her*, so every row here is a claim about a
dispatch that happened — and the region asks ``cascade.seat_exclusions`` on every
compose to find out which of those seats a player could still take. That is why
there is no ``live`` flag on the row: a boolean written by the adapter would be
true for exactly as long as it took to reach the composer.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant, MatchRecord, OfferKind

from app.modules.now.domain.cascade import Rung
from app.modules.now.domain.screen import Money, Place


@final
@dataclass(frozen=True)
class OfferedSeat:
    """One seat the cascade put in front of this viewer, and what its card needs.

    ``record`` is the kernel's, on ``Enrolment``'s rule: it is the vocabulary
    Matches publishes to be resolved, and anything narrower would be a second
    answer to *what is this match doing*.

    ``kind`` is the offer's own — ``OPEN`` for everything v1 writes, ``EXCLUSIVE``
    for the shape ADR-0061 retired and the kernel kept a name for. It rides here
    rather than being assumed because it is what makes ``seatOffered`` and
    ``seatOpened`` two situations on the wire rather than one with a comment.
    """

    match_id: UUID
    vacancy_id: UUID
    record: MatchRecord
    where: Place
    kind: OfferKind

    #: Which rung of the ladder she stood on when this seat reached her. The
    #: region ignores it — a card is a card whoever it came to — and the **push**
    #: is what reads it: ADR-0065 ranks a seat she asked for above one we chose
    #: for her, and words the line differently for each, so this is the only
    #: place that difference shows. It is the offer's own stored rung rather
    #: than a second reading of the row (``offer_of``).
    rung: Rung

    #: What one seat is sold for, before the rescue tier. The **card** prints
    #: ``kernel.seat_price`` of this at the composing instant rather than the
    #: amount stored on the offer: the two differ exactly when the rescue
    #: deadline passed between the telling and the tap, and ADR-0061 makes that a
    #: real change she is entitled to see rather than a disagreement to hide.
    share: Money

    #: What the whole court costs — ``{price} settled to the club``, which is the
    #: court's total and has no audience of its own.
    court_total: Money

    #: When she was told. Not drawn anywhere: it is the region's tie-break, so
    #: that two seats dying at the same instant are ordered by which she heard
    #: about first rather than by the query plan.
    offered_at: Instant

    #: Whether this match is already hers in any of the three senses the pool
    #: means — a seat, a live seat claim, or a departure she made herself. It is
    #: the one ``seat_exclusions`` rule that is a fact about the pair, so it is
    #: read by the adapter and judged by the composer.
    already_mine: bool = False

    #: The court the reservation names, if one has been assigned at all. Whether
    #: it may be **printed** is ``kernel.court_named_at``, applied in the
    #: composer, exactly as it is for the strip.
    court: str | None = None
