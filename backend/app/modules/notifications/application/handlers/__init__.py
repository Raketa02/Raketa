"""The Notifications context's log line, one per event.

A delivered event with no handler is a delivery failure, so each is logged as
every context's are — **by whose it is, and never by what it says**: no phone, and
nothing a notice tells.
"""

from __future__ import annotations

import logging

from app.application.events import DeliveryContext
from app.modules.notifications.domain.events import (
    PushDeviceRegistered,
    PushDeviceRemoved,
    NoticeBundled,
    NoticeGiven,
    NotificationChoiceSwitched,
    RecentNoticesOpened,
)

logger = logging.getLogger(__name__)

NotificationEvent = (
    NotificationChoiceSwitched
    | PushDeviceRegistered
    | PushDeviceRemoved
    | NoticeGiven
    | NoticeBundled
    | RecentNoticesOpened
)

_LINES: dict[type, str] = {
    NotificationChoiceSwitched: "notifications.choice.switched",
    PushDeviceRegistered: "notifications.device.registered",
    PushDeviceRemoved: "notifications.device.removed",
    NoticeGiven: "notifications.notice.given",
    NoticeBundled: "notifications.notice.bundled",
    RecentNoticesOpened: "notifications.notices.opened",
}


class LogNotificationEvent:
    async def __call__(
        self, event: NotificationEvent, context: DeliveryContext
    ) -> None:
        extra = {
            "player_id": str(event.player_id),
            "occurred_at": event.occurred_at.isoformat(),
            "event_id": str(context.event_id),
            "attempt": context.attempt,
        }
        if isinstance(event, (NoticeGiven, NoticeBundled)):
            extra["notice_id"] = str(event.notice_id)
            extra["notice_kind"] = event.kind
        logger.info(_LINES[type(event)], extra=extra)


__all__ = ["LogNotificationEvent"]
