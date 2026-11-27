"""**What's new in Needs your answer** — the envelope's badge (#815;
``docs/adr/0205`` §3; the decision log §3.2).

**What is new**: an item that arrived since the player last closed the sheet.
Every kind of item waiting there has **an arrival instant**, and only that is
compared — a change of state never moves it:

- a friend request, when it was asked;
- a friends game invitation, when its seat was invited into;
- a payment to confirm, when it was first refused — so a payment going from
  *Fix your card* to *Confirm* is not new;
- an ask for a level, **each asker's own ask** — a second friend asking on a
  card already there is a new person.

**The visit is the bell's pattern, applied to the sheet**
(``notifications/domain/bell.py``). One watermark per player, never a seen
flag per item: closing the sheet records **the newest arrival it showed**, and
only what arrived after it counts — on every phone at once. **Recorded only
when later than the last**, so it is idempotent and never moves back: a phone
closing on an older read, after another closed on a newer one, records
nothing. The bell's visit is ordered by the server's own clock; this one's
watermark comes from the phone, so it is the watermark that is compared, and
one **past the server's clock** — served by no read — is refused.

**Event-sourced, one stream per player under the player's own id**, as their
Games & money is, and born by being used: a player who never closed the sheet
has no stream, and everything waiting on them is new. The stream grows only
when the watermark moves, which only a newer arrival can make it do.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from typing import final
from uuid import UUID

from app.kernel import Instant, instant, invariant
from app.modules.proposals.domain.errors import WatermarkInTheFuture
from app.modules.proposals.domain.events import NeedsYourAnswerClosed
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


@final
@dataclass(frozen=True, slots=True)
class WhatIsNew:
    """The envelope's badge, and the watermark of the read it was counted
    on."""

    #: The items that arrived past the last visit's watermark — everything
    #: waiting, before any visit.
    count: int
    #: **The newest arrival among everything waiting**, seen or not — what the
    #: phone sends back when it closes the sheet drawn from this read.
    #: ``None`` with nothing waiting.
    watermark: Instant | None


def to_the_millisecond(at: Instant) -> Instant:
    """``at`` as a phone's date holds it. **Every arrival and every watermark
    is compared at this precision**, so a phone that turns the watermark into
    its own date and back sends the same instant again — at the microsecond the
    store keeps, it would send one just below the newest arrival, and that one
    would be new for ever. Two arrivals inside one millisecond are one."""

    return instant(at.replace(microsecond=at.microsecond - at.microsecond % 1000))


def what_is_new(
    arrivals: Iterable[Instant], *, seen_through: Instant | None
) -> WhatIsNew:
    """How many of these arrivals are past the last visit's watermark — every
    one of them before any visit — and the newest of them, each to the
    millisecond."""

    arrived = [to_the_millisecond(at) for at in arrivals]
    return WhatIsNew(
        count=sum(1 for at in arrived if seen_through is None or at > seen_through),
        watermark=max(arrived, default=None),
    )


@dataclass
class NeedsYourAnswerVisit:
    """The last time one player closed Needs your answer — the watermark it
    showed — rebuilt by folding its stream."""

    player_id: UUID
    #: The newest arrival the sheet showed when last closed — ``None`` before
    #: the first close.
    watermark: Instant | None = None
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )

    @classmethod
    def from_history(
        cls, player_id: UUID, events: Iterable[DomainEvent]
    ) -> "NeedsYourAnswerVisit":
        visit = cls(player_id=player_id)
        for event in events:
            visit._apply(event)
        return visit

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    def close(self, *, watermark: Instant, at: Instant) -> NeedsYourAnswerClosed | None:
        """The player closed the sheet at ``at``, drawn from a read whose newest
        arrival was ``watermark`` — ``None``, recording nothing, when that is no
        later than the last visit's. ``WatermarkInTheFuture`` for one past
        ``at``, which no read served. Kept to the millisecond."""

        watermark = to_the_millisecond(watermark)
        if watermark > at:
            raise WatermarkInTheFuture()
        if self.watermark is not None and watermark <= self.watermark:
            return None
        closed = NeedsYourAnswerClosed(
            player_id=self.player_id, watermark=watermark, occurred_at=at
        )
        self._apply(closed)
        self._events.record(closed)
        return closed

    def _apply(self, event: DomainEvent) -> None:
        invariant(
            isinstance(event, NeedsYourAnswerClosed),
            f"a Needs your answer stream holds {event!r}",
        )
        assert isinstance(event, NeedsYourAnswerClosed)
        self.watermark = instant(event.watermark)
        self.version += 1
