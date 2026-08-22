"""The court catalogue: what courts a club has, and which group each is in.

The third of ADR-0077's history-bearing series, and the one that is not about
money. A retirement shrinks availability, and ``inventoryLost`` is terminal — it
cancels the match and refunds everybody — so *nothing was free* has to be
explicable on the day it mattered: whether because everything was booked, or
because the club retired the court.

**A category is club-authored and it is the priced unit** (ADR-0079).
Interchangeability is a fact only the venue knows: a platform enum would be
either too coarse to be true — swapping a player from an indoor Mondo court onto
an outdoor wall court because both say *Padel* — or so fine that it is the
surface list under another name. The platform constrains exactly one thing: a
category belongs to **one sport**, because a sport's player count is read from
one place everywhere and a category spanning two would make a seat share
undefined.

**The price attaches to the category, and there is no per-court multiplier.**
v37's ``court.pm`` is deleted: a court that costs differently is, by definition,
a different category. That is what makes ADR-0035's *"the court is assigned,
never chosen"* honest rather than something we say while the price moves under
the player — the quote is safe precisely because every court that could satisfy
it costs the same.

**Retired, never deleted**, for both a court and a category. A past reservation
names the court it claimed, and the price quoted is copied onto the match at
booking, so nothing has to query a category as of a past instant. What retirement
buys is that the record still parses.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import final
from uuid import UUID

from app.kernel import Grosze, Instant, Sport

from app.modules.clubs.domain.series import Series
from app.modules.clubs.domain.value_objects import (
    SYSTEM,
    CategoryName,
    ChangedBy,
    CourtLabel,
    base_rate,
)


@final
@dataclass(frozen=True)
class CatalogueEntry:
    """What one court *is*, for as long as it is that.

    The value carried on a court's catalogue series. Moving a court between
    categories closes the row and opens a new one; retiring it closes the row
    and opens none.
    """

    category_id: UUID
    label: CourtLabel


@final
@dataclass
class CourtCategory:
    """A club-scoped named group of interchangeable courts, and its rate.

    ``rate`` is what one booked block of this category costs **before** the
    club's own multipliers, in grosze. It is deliberately not a ``CourtPrice``:
    that brand means *after every multiplier, rounded once to whole złoty*, and
    this is the input to that rounding.
    """

    id: UUID
    name: CategoryName
    sport: Sport
    rate: Grosze
    retired_at: Instant | None = None

    def __post_init__(self) -> None:
        base_rate(self.rate)

    @property
    def is_retired(self) -> bool:
        return self.retired_at is not None

    def retire(self, *, at: Instant) -> None:
        self.retired_at = at


@final
@dataclass
class Court:
    """One court, and the history of what it was.

    A court *exists* exactly while its catalogue series has an open row. There
    is no separate deleted flag: ``catalogue.current`` is ``None`` for a retired
    court, and the closed rows say what it was and when.
    """

    id: UUID
    catalogue: Series[CatalogueEntry] = field(default_factory=Series)

    @property
    def is_retired(self) -> bool:
        return self.catalogue.open_version is None

    @property
    def entry(self) -> CatalogueEntry | None:
        return self.catalogue.current

    @property
    def category_id(self) -> UUID | None:
        entry = self.entry
        return None if entry is None else entry.category_id

    @property
    def label(self) -> CourtLabel | None:
        entry = self.entry
        return None if entry is None else entry.label

    def move_to(
        self,
        *,
        category_id: UUID,
        label: CourtLabel,
        at: Instant,
        changed_by: ChangedBy = SYSTEM,
    ) -> None:
        self.catalogue = self.catalogue.opened(
            CatalogueEntry(category_id=category_id, label=label),
            at=at,
            changed_by=changed_by,
        )

    def retire(self, *, at: Instant) -> None:
        self.catalogue = self.catalogue.closed(at=at)
