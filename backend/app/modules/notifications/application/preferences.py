"""You › Account › **Notifications** (the mechanics §17.2; the screens A7.2) —
read the three choices and save them as the player taps — and the phones a push
reaches: registered when a phone signs in, removed when it signs out.

**A phone is one player's at a time.** A phone signed in as somebody else
before is taken off their preferences in the same transaction it is added to
these — otherwise the next player on a shared or handed-down phone would be
pushed the last one's games.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import final
from uuid import UUID

from app.application.ports import UnitOfWork
from app.kernel import Clock, instant
from app.modules.notifications.domain.ports import NotificationPreferencesRepository
from app.modules.notifications.domain.preferences import (
    NotificationChoice,
    NotificationPreferences,
    device_of,
    push_token,
)


@final
class ReadNotificationPreferences:
    def __init__(self, *, preferences: NotificationPreferencesRepository) -> None:
        self._preferences = preferences

    async def execute(self, player_id: UUID) -> NotificationPreferences:
        return await self._preferences.load(player_id)


@dataclass(frozen=True, slots=True)
class SetNotificationChoicesCommand:
    player_id: UUID
    choices: dict[NotificationChoice, bool]


@final
class SetNotificationChoices:
    """The three choices, as the screen saves them on every tap. The same
    answer records nothing."""

    def __init__(
        self,
        *,
        preferences: NotificationPreferencesRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._preferences = preferences
        self._uow = uow
        self._clock = clock

    async def execute(
        self, command: SetNotificationChoicesCommand
    ) -> NotificationPreferences:
        at = instant(self._clock.now())
        preferences = await self._preferences.load(command.player_id)
        for choice in NotificationChoice:
            if choice in command.choices:
                preferences.switch(choice, on=command.choices[choice], at=at)
        await self._preferences.save(preferences)
        await self._uow.commit()
        return preferences


@final
class RegisterAPhone:
    def __init__(
        self,
        *,
        preferences: NotificationPreferencesRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._preferences = preferences
        self._uow = uow
        self._clock = clock

    async def execute(self, player_id: UUID, token: str) -> None:
        at = instant(self._clock.now())
        device = device_of(push_token(token))
        holder = await self._preferences.holder_of(device)
        if holder is not None and holder != player_id:
            before = await self._preferences.load(holder)
            before.remove(device, at=at)
            await self._preferences.save(before)
        preferences = await self._preferences.load(player_id)
        preferences.register(token, at=at)
        await self._preferences.save(preferences)
        await self._uow.commit()


@final
class RemoveAPhone:
    """Push to this phone no more — what a phone asks as it signs out. A phone
    not registered is removed already."""

    def __init__(
        self,
        *,
        preferences: NotificationPreferencesRepository,
        uow: UnitOfWork,
        clock: Clock,
    ) -> None:
        self._preferences = preferences
        self._uow = uow
        self._clock = clock

    async def execute(self, player_id: UUID, token: str) -> None:
        preferences = await self._preferences.load(player_id)
        if preferences.remove(device_of(token), at=instant(self._clock.now())):
            await self._preferences.save(preferences)
            await self._uow.commit()
