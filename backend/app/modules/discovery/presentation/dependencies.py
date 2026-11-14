"""Request-scoped declarations for the Discovery context.

*When* each read is built, never *what* — every concrete class comes from
``app.bootstrap.composition``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import ClockDep, DbSession, SettingsDep
from app.bootstrap.composition import (
    build_read_new_in_raketa,
    build_read_new_in_raketa_page,
)
from app.modules.discovery.application.new_in_raketa import (
    ReadNewInRaketaPage,
    ReadNewInRaketa,
)


def get_read_new_in_raketa(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> ReadNewInRaketa:
    return build_read_new_in_raketa(db, settings=settings, clock=clock)


ReadNewInRaketaDep = Annotated[ReadNewInRaketa, Depends(get_read_new_in_raketa)]


def get_read_new_in_raketa_page(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> ReadNewInRaketaPage:
    return build_read_new_in_raketa_page(db, settings=settings, clock=clock)


ReadNewInRaketaPageDep = Annotated[
    ReadNewInRaketaPage, Depends(get_read_new_in_raketa_page)
]
