"""Request-scoped declarations for the Notifications context — when each is
built; **what** is built is the composition root's."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import ClockDep, DbSession, UnitOfWorkDep
from app.bootstrap.composition import (
    build_notice_directory,
    build_notice_words,
    build_notification_preferences_repository,
)
from app.modules.notifications.application.preferences import (
    ReadNotificationPreferences,
    RegisterAPhone,
    RemoveAPhone,
    SetNotificationChoices,
)
from app.modules.notifications.application.reading import ReadRecentNotices
from app.modules.notifications.domain.ports import NotificationPreferencesRepository


def get_notification_preferences_repository(
    db: DbSession,
) -> NotificationPreferencesRepository:
    return build_notification_preferences_repository(db)


NotificationPreferencesRepositoryDep = Annotated[
    NotificationPreferencesRepository,
    Depends(get_notification_preferences_repository),
]


def get_read_notification_preferences(
    preferences: NotificationPreferencesRepositoryDep,
) -> ReadNotificationPreferences:
    return ReadNotificationPreferences(preferences=preferences)


ReadNotificationPreferencesDep = Annotated[
    ReadNotificationPreferences, Depends(get_read_notification_preferences)
]


def get_set_notification_choices(
    preferences: NotificationPreferencesRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> SetNotificationChoices:
    return SetNotificationChoices(preferences=preferences, uow=uow, clock=clock)


SetNotificationChoicesDep = Annotated[
    SetNotificationChoices, Depends(get_set_notification_choices)
]


def get_register_a_phone(
    preferences: NotificationPreferencesRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> RegisterAPhone:
    return RegisterAPhone(preferences=preferences, uow=uow, clock=clock)


RegisterAPhoneDep = Annotated[RegisterAPhone, Depends(get_register_a_phone)]


def get_remove_a_phone(
    preferences: NotificationPreferencesRepositoryDep,
    uow: UnitOfWorkDep,
    clock: ClockDep,
) -> RemoveAPhone:
    return RemoveAPhone(preferences=preferences, uow=uow, clock=clock)


RemoveAPhoneDep = Annotated[RemoveAPhone, Depends(get_remove_a_phone)]


def get_read_recent_notices(db: DbSession) -> ReadRecentNotices:
    return ReadRecentNotices(
        notices=build_notice_directory(db), words=build_notice_words(db)
    )


ReadRecentNoticesDep = Annotated[ReadRecentNotices, Depends(get_read_recent_notices)]
