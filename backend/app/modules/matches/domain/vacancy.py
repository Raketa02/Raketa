"""A hole a departure left, for as long as it is unfilled.

**A vacancy and the departure that caused it are independent facts** (ADR-0033).
The ladder asks *is there a hole in this match*; what the leaver recovered is her
departure's answer and moves on its own axis. So a vacancy carries no amount, no
outcome and no player — only which seat, when it was emptied, and whether it has
since been filled. The departure record itself is ``Raketa02/Raketa#67``'s, and
it is deliberately not here: a settlement stored beside a hole would be the two
axes welded back together.

**Filled, never deleted**, for the same reason a reservation is released rather
than dropped: *when did this match lose a player, and when did it get one back*
is a question a support agent asks, and a row that vanishes cannot answer it.
Only the open ones reach the ladder, which is what stops a refilled match being
pinned in a recovery state for ever — the defect the prototype shipped by setting
a flag it never cleared.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.kernel import Instant
from app.kernel import Vacancy as RecordVacancy

from app.modules.matches.domain.errors import VacancyAlreadyFilled


@final
@dataclass
class Vacancy:
    """One hole: which seat, when it opened, and when it closed if it has."""

    id: UUID
    seat_index: int
    vacated_at: Instant
    filled_at: Instant | None = None

    @property
    def is_open(self) -> bool:
        return self.filled_at is None

    def fill(self, *, at: Instant) -> None:
        """Somebody took the seat back.

        Refused rather than ignored when it has already closed: filling a hole
        twice would move the instant it closed, which is history rewritten
        rather than recorded — the same argument that makes a second release of
        a reservation an error.
        """

        if self.filled_at is not None:
            raise VacancyAlreadyFilled()
        self.filled_at = at

    def as_record(self) -> RecordVacancy:
        """The one field the ladder reads."""

        return RecordVacancy(vacated_at=self.vacated_at)
