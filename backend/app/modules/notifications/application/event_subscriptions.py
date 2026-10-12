"""The Notifications context's durable event names, and who hears them.

A name here is a **published contract** and outlives every Python class it maps
to.

**Three subscriptions, of two kinds.** The log handler is registered once for
the process, like every other context's. The **teller** — the handler that turns
``proposals``', ``bookings``' and ``payments``' events into notices — and the
**pusher**, which pushes a notice given, write, so each is registered per
delivery batch over that batch's session in ``app/bootstrap/events.py``; the
pusher holds the run's push service, as the room teller holds its live channel.

**Three notice kinds left with On request** (#669; ``docs/adr/0196`` §1):
``WAITING_FOR_THE_CLUB``, ``CLUB_CONFIRMED`` and ``CLUB_COULD_NOT_TAKE_IT``, with
the ``AT_THE_CLUBS_YES``, ``REFUSED``, ``NO_ANSWER`` and ``LEFT_AFTER_THE_BOOK_BY``
reasons. ``notifications.notice_given`` keeps its name and version — its shape did
not change — and a stored row naming a retired kind no longer folds: the local
store is reset with the removal and only ``local`` has ever run.

**One kind joined with the club's Move** (#671; Q122): ``GAME_MOVED``, which
names the court the game is on now and its kind — two facts added to
``notifications.notice_given`` **defaulted**, as ``own``, ``until`` and
``rescue`` were, so a row given before names no court and the version stays.
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
    RecentNoticesOpened,
)

_CONTRACTS = (
    (NotificationChoiceSwitched, "notifications.choice_switched"),
    (PushDeviceRegistered, "notifications.push_device_registered"),
    (PushDeviceRemoved, "notifications.push_device_removed"),
    (NoticeGiven, "notifications.notice_given"),
    (NoticeBundled, "notifications.notice_bundled"),
    (RecentNoticesOpened, "notifications.recent_notices_opened"),
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
    dispatcher.subscribe(RecentNoticesOpened, LogNotificationEvent())


def subscribe_the_teller(dispatcher: EventDispatcher, teller: TellThePlayers) -> None:
    """One teller for everything a player is told about — ``telling.py``'s
    table, and the only place the list is written."""

    for event_class in TOLD_ABOUT:
        dispatcher.subscribe(event_class, teller)


def subscribe_the_pusher(dispatcher: EventDispatcher, pusher: PushTheNotice) -> None:
    """A notice given is pushed to the player's phones, over the run's push
    service — the API's is Expo, a seed's records and pushes nothing."""

    dispatcher.subscribe(NoticeGiven, pusher)
