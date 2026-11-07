"""Request-scoped declarations for the Rankings context.

*When* each read is built, never *what* — every concrete class comes from
``app.bootstrap.composition``.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends

from app.api.dependencies import ClockDep, DbSession, SettingsDep
from app.bootstrap.composition import build_read_ranking
from app.modules.rankings.application.reads import ReadRanking


def get_read_ranking(
    db: DbSession, settings: SettingsDep, clock: ClockDep
) -> ReadRanking:
    return build_read_ranking(db, settings=settings, clock=clock)


ReadRankingDep = Annotated[ReadRanking, Depends(get_read_ranking)]
