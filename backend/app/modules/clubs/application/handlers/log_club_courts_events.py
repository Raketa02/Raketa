"""The Club courts stream's subscriber: a log line per event, and nothing else.

Nothing reacts to a club's courts yet — what a club can sell is derived on every
read, never projected — but **an event nobody subscribes to is an outbox row
that fails every delivery and is fetched again on the next poll**, so each is
logged as the club's own are (``tests/unit/test_every_event_has_a_subscriber.py``).
The line names the club and nothing it painted.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.clubs.domain.club_courts_events import (
    CourtAdded,
    CourtChanged,
    CourtRemoved,
    CourtSwitchedOff,
    CourtSwitchedOn,
    ExceptionAdded,
    ExceptionRemoved,
    PaymentsAccountOpened,
    PaymentsStatusChanged,
    PricesSet,
    RaketaHoursSet,
    RaketaPaused,
    RaketaResumed,
    RaketaSettingsChanged,
)

logger = logging.getLogger(__name__)

ClubCourtsEvent = (
    CourtAdded
    | CourtChanged
    | CourtSwitchedOff
    | CourtSwitchedOn
    | CourtRemoved
    | RaketaHoursSet
    | ExceptionAdded
    | ExceptionRemoved
    | PricesSet
    | RaketaSettingsChanged
    | RaketaPaused
    | RaketaResumed
    | PaymentsAccountOpened
    | PaymentsStatusChanged
)

_LINES: dict[type, str] = {
    CourtAdded: "clubs.court.added",
    CourtChanged: "clubs.court.changed",
    CourtSwitchedOff: "clubs.court.switched_off",
    CourtSwitchedOn: "clubs.court.switched_on",
    CourtRemoved: "clubs.court.removed",
    RaketaHoursSet: "clubs.raketa_hours.set",
    ExceptionAdded: "clubs.exception.added",
    ExceptionRemoved: "clubs.exception.removed",
    PricesSet: "clubs.prices.set",
    RaketaSettingsChanged: "clubs.raketa_settings.changed",
    RaketaPaused: "clubs.raketa.paused",
    RaketaResumed: "clubs.raketa.resumed",
    PaymentsAccountOpened: "clubs.payments_account.opened",
    PaymentsStatusChanged: "clubs.payments_status.changed",
}


class LogClubCourtsEvent:
    async def __call__(self, event: ClubCourtsEvent, context: DeliveryContext) -> None:
        logger.info(
            _LINES[type(event)],
            extra={
                "club_id": str(event.club_id),
                "occurred_at": event.occurred_at.isoformat(),
                "event_id": str(context.event_id),
                "attempt": context.attempt,
            },
        )
