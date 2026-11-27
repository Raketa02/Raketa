"""Request-scoped declarations for the Discovery context.

*When* each read is built, never *what* — every concrete class comes from
``app.bootstrap.composition``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import ClockDep, DbSession, SettingsDep
from app.bootstrap.composition import (
    build_read_new_in_rakieta,
    build_read_new_in_rakieta_page,
    build_read_same_level,
    build_read_same_level_page,
    build_read_same_vibe,
    build_read_same_vibe_page,
    build_report_on_screen,
)
from app.modules.discovery.application.new_in_rakieta import (
    ReadNewInRakietaPage,
    ReadNewInRakieta,
)
from app.modules.discovery.application.on_screen import ReportOnScreen
from app.modules.discovery.application.same_level import (
    ReadSameLevel,
    ReadSameLevelPage,
)
from app.modules.discovery.application.same_vibe import (
    ReadSameVibe,
    ReadSameVibePage,
)


def get_read_new_in_rakieta(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> ReadNewInRakieta:
    return build_read_new_in_rakieta(db, settings=settings, clock=clock)


ReadNewInRakietaDep = Annotated[ReadNewInRakieta, Depends(get_read_new_in_rakieta)]


def get_read_new_in_rakieta_page(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> ReadNewInRakietaPage:
    return build_read_new_in_rakieta_page(db, settings=settings, clock=clock)


ReadNewInRakietaPageDep = Annotated[
    ReadNewInRakietaPage, Depends(get_read_new_in_rakieta_page)
]


def get_read_same_level(db: DbSession, settings: SettingsDep) -> ReadSameLevel:
    return build_read_same_level(db, settings=settings)


ReadSameLevelDep = Annotated[ReadSameLevel, Depends(get_read_same_level)]


def get_read_same_level_page(db: DbSession, settings: SettingsDep) -> ReadSameLevelPage:
    return build_read_same_level_page(db, settings=settings)


ReadSameLevelPageDep = Annotated[ReadSameLevelPage, Depends(get_read_same_level_page)]


def get_read_same_vibe(db: DbSession, settings: SettingsDep) -> ReadSameVibe:
    return build_read_same_vibe(db, settings=settings)


ReadSameVibeDep = Annotated[ReadSameVibe, Depends(get_read_same_vibe)]


def get_read_same_vibe_page(db: DbSession, settings: SettingsDep) -> ReadSameVibePage:
    return build_read_same_vibe_page(db, settings=settings)


ReadSameVibePageDep = Annotated[ReadSameVibePage, Depends(get_read_same_vibe_page)]


def get_report_on_screen(db: DbSession, clock: ClockDep) -> ReportOnScreen:
    return build_report_on_screen(db, clock=clock)


ReportOnScreenDep = Annotated[ReportOnScreen, Depends(get_report_on_screen)]
