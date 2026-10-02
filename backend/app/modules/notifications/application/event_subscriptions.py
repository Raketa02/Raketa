"""The Notifications context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to.

**Three subscriptions, of two kinds.** The log handler is registered once for
the process, like every other context's. The **teller** — the handler that turns
``proposals``', ``bookings``' and ``payments``' events into notices — and the
**pusher**, which pushes a notice given, write, so each is registered per
delivery batch over that batch's session in ``app/bootstrap/events.py``; the
pusher holds the run's push service, as the room teller holds its live channel.
"""

from __future__ import annotations

from app.application.events import EventCatalog, EventDispatcher
from app.modules.notifications.application.handlers import LogNotificationEvent
from app.modules.notifications.application.pushing import PushTheNotice
from app.modules.notifications.application.telling import TOLD_ABOUT, TellThePlayers
from app.modules.notifications.domain.events import (
    PushDeviceRegistered,
    PushDeviceRemoved,
    NoticeBundled,
    NoticeGiven,
    NotificationChoiceSwitched,
)

_CONTRACTS = (
    (NotificationChoiceSwitched, "notifications.choice_switched"),
    (PushDeviceRegistered, "notifications.push_device_registered"),
    (PushDeviceRemoved, "notifications.push_device_removed"),
    (NoticeGiven, "notifications.notice_given"),
    (NoticeBundled, "notifications.notice_bundled"),
)


def register_notification_events(catalog: EventCatalog) -> None:
    for event_class, name in _CONTRACTS:
        catalog.register(event_class, name=name, version=1)


def subscribe_notification_handlers(dispatcher: EventDispatcher) -> None:
    dispatcher.subscribe(NotificationChoiceSwitched, LogNotificationEvent())
    dispatcher.subscribe(PushDeviceRegistered, LogNotificationEvent())
    dispatcher.subscribe(PushDeviceRemoved, LogNotificationEvent())
    dispatcher.subscribe(NoticeGiven, LogNotificationEvent())
    dispatcher.subscribe(NoticeBundled, LogNotificationEvent())


def subscribe_the_teller(dispatcher: EventDispatcher, teller: TellThePlayers) -> None:
    """One teller for everything a player is told about — ``telling.py``'s
    table, and the only place the list is written."""

    for event_class in TOLD_ABOUT:
        dispatcher.subscribe(event_class, teller)


def subscribe_the_pusher(dispatcher: EventDispatcher, pusher: PushTheNotice) -> None:
    """A notice given is pushed to the player's phones, over the run's push
    service — the API's is Expo, a seed's records and pushes nothing."""

    dispatcher.subscribe(NoticeGiven, pusher)
