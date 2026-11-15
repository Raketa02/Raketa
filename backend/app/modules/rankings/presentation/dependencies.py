"""Request-scoped declarations for the Rankings context.

*When* each read is built, never *what* — every concrete class comes from
``app.bootstrap.composition``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import ClockDep, DbSession, SettingsDep, StoreOrNothingDep
from app.bootstrap.composition import (
    build_general_orders,
    build_read_general_page,
    build_read_ranking,
    build_read_top_ten,
)
from app.modules.rankings.application.reads import (
    ReadGeneralPage,
    ReadRanking,
    ReadTopTen,
)
from app.modules.rankings.domain.ports import GeneralOrders


def get_general_orders(store: StoreOrNothingDep) -> GeneralOrders:
    """Each sport's kept General order, over the process's ephemeral store —
    **per request**, so the fail-soft wrapper complains once a request at
    most. A ``Depends`` so a test reads through the in-memory equivalent."""
    return build_general_orders(store)


GeneralOrdersDep = Annotated[GeneralOrders, Depends(get_general_orders)]


def get_read_ranking(
    db: DbSession, settings: SettingsDep, clock: ClockDep, orders: GeneralOrdersDep
) -> ReadRanking:
    return build_read_ranking(db, settings=settings, clock=clock, orders=orders)


ReadRankingDep = Annotated[ReadRanking, Depends(get_read_ranking)]


def get_read_general_page(
    db: DbSession, settings: SettingsDep, clock: ClockDep, orders: GeneralOrdersDep
) -> ReadGeneralPage:
    return build_read_general_page(db, settings=settings, clock=clock, orders=orders)


ReadGeneralPageDep = Annotated[ReadGeneralPage, Depends(get_read_general_page)]


def get_read_top_ten(
    db: DbSession, settings: SettingsDep, clock: ClockDep, orders: GeneralOrdersDep
) -> ReadTopTen:
    return build_read_top_ten(db, settings=settings, clock=clock, orders=orders)


ReadTopTenDep = Annotated[ReadTopTen, Depends(get_read_top_ten)]
