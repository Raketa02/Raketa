"""**The bell** — when a player last opened their recent notices (#621; the
mechanics Q101, §17.2; the screens A9).

**One moment per player, never a read flag per notice.** The bell's number is
the notices given since it — counted by the recent list, not here — so opening
the list on one phone clears the number on every phone, and nothing is marked
read row by row.

**Idempotent, and never back**: opening it again at the same moment records
nothing, and neither does an earlier one, which a second process whose clock is
behind the first could send.

**Event-sourced, one stream per player under the player's own id**, as their
Notification preferences are, and born by being used: a player who never opened
the list has no stream, and every notice they hold is new.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable
from uuid import UUID

from app.kernel import Instant, instant, invariant
from app.modules.notifications.domain.events import RecentNoticesOpened
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@dataclass
class Bell:
    """When one player last opened their recent notices, rebuilt by folding its
    stream."""

    player_id: UUID
    #: The last time they opened the list — ``None`` before the first.
    last_opened_at: Instant | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def from_history(cls, player_id: UUID, events: Iterable[DomainEvent]) -> "Bell":
        bell = cls(player_id=player_id)
        for event in events:
            bell._apply(event)
        return bell

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    def open(self, *, at: Instant) -> RecentNoticesOpened | None:
        """The player opened the list at ``at`` — ``None``, recording nothing,
        when that is no later than the last time."""

        if self.last_opened_at is not None and at <= self.last_opened_at:
            return None
        opened = RecentNoticesOpened(player_id=self.player_id, occurred_at=at)
        self._apply(opened)
        self._events.record(opened)
        return opened

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, RecentNoticesOpened):
            self.last_opened_at = instant(event.occurred_at)
        else:
            invariant(False, f"a bell holds {event!r}")
        self.version += 1
