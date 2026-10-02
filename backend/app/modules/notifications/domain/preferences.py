"""**Notification preferences** — the three choices a player makes, and the
phones a push reaches (#549; the mechanics §17.2; the screens A7.2, A9).

**Seven notices are always on** and are no choice of anybody's: money, a game
booked or called off, somebody leaving it, the club's answer, a post that did
not fill. **Three are the player's**: *You complete it* and *Challenges for
you*, on until switched off, and *Fill in alerts*, off until switched on.

**Event-sourced, one stream per player, filed under the player's own id and
born by being used**, as Games & money is: a player who never opened the screen
is at the defaults and has written nothing. **A preference, so the same answer
records nothing.**

**A phone is an Expo push token**, registered by the phone signed in as the
player and removed when it signs out. **The stream names it by its SHA-256**
(``device_of``) and never by the token, which would let anybody holding it push
to the phone (ADR-0184 §4): the token is handed to the repository in the act
that registers it and kept in ``push_devices`` alone. A player keeps at most
``DEVICES_KEPT``: a phone signing in past them lets the one registered longest
ago go, which is how a token nobody removed — a phone wiped, an app deleted —
stops costing a push for ever. Which player a phone belongs to is one at a
time; moving it is the use case's, since it is two players' streams.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final, Iterable
from uuid import UUID

from app.kernel import Instant, invariant
from app.modules.notifications.domain.errors import PushTokenInvalid
from app.modules.notifications.domain.events import (
    NotificationChoiceSwitched,
    PushDeviceRegistered,
    PushDeviceRemoved,
)
from app.shared.domain import DomainEvent
from app.shared.domain.events import EventRecorder


class NotificationChoice(StrEnum):
    """The three notices a player may switch (the screens A7.2, *YOUR CHOICE*)."""

    #: A card needs only you — at most once a day, bundled.
    YOU_COMPLETE_IT = "YOU_COMPLETE_IT"
    #: A member's post names you — at most three a day, bundled.
    CHALLENGES_FOR_YOU = "CHALLENGES_FOR_YOU"
    #: A booked game you fit needs one more — at most three a day.
    FILL_IN_ALERTS = "FILL_IN_ALERTS"


#: Where a player starts, until they say otherwise.
DEFAULT_CHOICES: Final[dict[NotificationChoice, bool]] = {
    NotificationChoice.YOU_COMPLETE_IT: True,
    NotificationChoice.CHALLENGES_FOR_YOU: True,
    NotificationChoice.FILL_IN_ALERTS: False,
}

#: The phones one player is pushed on at most — a phone, a tablet, a new phone
#: before the old one signed out, and room to spare.
DEVICES_KEPT: Final = 10

#: What the phone's notifications library hands out: ``ExponentPushToken[…]``,
#: or the newer ``ExpoPushToken[…]``.
_EXPO_TOKEN: Final = re.compile(r"Expo(nent)?PushToken\[[^\[\]\s]{1,200}\]")


def push_token(value: str) -> str:
    """``value`` as a push token, or refused."""

    if not _EXPO_TOKEN.fullmatch(value):
        raise PushTokenInvalid()
    return value


def device_of(token: str) -> str:
    """The name a phone goes by on the stream: its push token's SHA-256."""

    return hashlib.sha256(token.encode()).hexdigest()


@dataclass
class NotificationPreferences:
    """One player's choices and phones, rebuilt by folding their stream."""

    player_id: UUID
    choices: dict[NotificationChoice, bool] = field(
        default_factory=lambda: dict(DEFAULT_CHOICES)
    )
    #: The phones pushed to, by ``device_of``, the one registered longest ago
    #: first.
    devices: tuple[str, ...] = ()
    version: int = 0
    _events: EventRecorder = field(
        default_factory=EventRecorder, init=False, repr=False, compare=False
    )
    #: The token of each phone registered since the load — what the repository
    #: keeps where the stream may not.
    _tokens: dict[str, str] = field(
        default_factory=dict, init=False, repr=False, compare=False
    )

    @classmethod
    def from_history(
        cls, player_id: UUID, events: Iterable[DomainEvent]
    ) -> "NotificationPreferences":
        """The player's preferences — **the defaults, for a stream never
        written**."""

        preferences = cls(player_id=player_id)
        for event in events:
            preferences._apply(event)
        return preferences

    def pull_events(self) -> list[DomainEvent]:
        return self._events.pull()

    def wants(self, choice: NotificationChoice) -> bool:
        return self.choices[choice]

    def switch(self, choice: NotificationChoice, *, on: bool, at: Instant) -> None:
        """One choice on or off; the same answer records nothing."""

        if self.choices[choice] is on:
            return
        self._record_that(
            NotificationChoiceSwitched(
                player_id=self.player_id, choice=choice.value, on=on, occurred_at=at
            )
        )

    def register(self, token: str, *, at: Instant) -> None:
        """Push to this phone too — once, however often it asks. Past
        ``DEVICES_KEPT`` the phone registered longest ago is let go."""

        device = device_of(push_token(token))
        if device in self.devices:
            return
        if len(self.devices) >= DEVICES_KEPT:
            self.remove(self.devices[0], at=at)
        self._tokens[device] = token
        self._record_that(
            PushDeviceRegistered(
                player_id=self.player_id, device=device, occurred_at=at
            )
        )

    def remove(self, device: str, *, at: Instant) -> bool:
        """Push to this phone no more. Answers whether it was pushed to."""

        if device not in self.devices:
            return False
        self._tokens.pop(device, None)
        self._record_that(
            PushDeviceRemoved(player_id=self.player_id, device=device, occurred_at=at)
        )
        return True

    def token_of(self, device: str) -> str:
        """The token of a phone registered since the load."""

        token = self._tokens.get(device)
        invariant(token is not None, f"{device} was not registered in this act")
        assert token is not None
        return token

    def _record_that(self, event: DomainEvent) -> None:
        self._apply(event)
        self._events.record(event)

    def _apply(self, event: DomainEvent) -> None:
        if isinstance(event, NotificationChoiceSwitched):
            self.choices = {**self.choices, NotificationChoice(event.choice): event.on}
        elif isinstance(event, PushDeviceRegistered):
            self.devices = (*self.devices, event.device)
        elif isinstance(event, PushDeviceRemoved):
            self.devices = tuple(one for one in self.devices if one != event.device)
        else:
            invariant(False, f"a Notification preferences stream holds {event!r}")
        self.version += 1
