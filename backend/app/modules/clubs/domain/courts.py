"""A court: one physical court at a club, as the club lists it for Raketa.

A **name** the club uses (*Court 2*, *Kort centralny*), **one sport**, and
indoor or outdoor — shown on a card, because it matters to players (the
mechanics §16.4). It is **offered** to Raketa or switched off, and switching it
off keeps it, its hours and its name. Players never pick one: a card promises a
court at a club at an hour, and the number is given at booking.

**Its Raketa hours are the player's own grid** — ``WeeklyHours``, seven days by
sixteen hours from 07:00 (``docs/adr/0189`` §3, the screens B3) — reused rather
than respelled, because *an hour outside it could never match a player* is the
whole reason for the grid's edges, and a second spelling is how the two would
drift apart. A court's week has **no floor**: a court offering nothing is a
court the club has not painted yet, and ``WeeklyHours.edited`` is the
constructor that says so.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final, final
from uuid import UUID

from app.kernel import Sport
from app.modules.clubs.domain.errors import CourtNameInvalid
from app.modules.player_profile.domain.weekly_hours import WeeklyHours

#: The longest court name, in characters. **Domain, never configuration**: it is
#: a label on a table row and on a booked card, and its falsifier is the first
#: club whose own name for a court does not fit.
COURT_NAME_LONGEST: Final = 40


@final
@dataclass(frozen=True, slots=True)
class CourtName:
    """What the club calls the court: trimmed, runs of whitespace collapsed,
    1–40 characters. Unique among the club's courts, which the aggregate — the
    one place all of them are known — refuses."""

    value: str

    def __post_init__(self) -> None:
        collapsed = " ".join(self.value.split())
        if not 1 <= len(collapsed) <= COURT_NAME_LONGEST:
            raise CourtNameInvalid()
        object.__setattr__(self, "value", collapsed)

    @property
    def folded(self) -> str:
        """The name as two names are compared: *Court 2* and *court 2* are one
        court to a desk reading its own table."""

        return self.value.casefold()


@final
@dataclass(frozen=True, slots=True)
class Court:
    """One court, as the club's stream leaves it."""

    id: UUID
    name: CourtName
    sport: Sport
    indoor: bool
    offered: bool = True
    hours: WeeklyHours = field(default_factory=WeeklyHours.blank)
