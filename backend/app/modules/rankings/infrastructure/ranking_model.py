"""``ranking_rows`` — the ranking projection: one row per player per sport
(``docs/adr/0203`` §10).

**A fold of one rating stream**, written by the move on every delivered
``rating.moved_on_result`` and by the rebuild, in the caller's transaction.
The stream is the record; this is a copy that pages and orders.

**The order's index** is General's order exactly — sport, Level descending,
results descending, Level reached ascending, player id — so a sport's listed
rows are read in place order off the index.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import DateTime, Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class RankingRowORM(Base):
    __tablename__ = "ranking_rows"

    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    sport: Mapped[str] = mapped_column(String(16), primary_key=True)
    #: The Level in hundredths: ``2,71`` is ``271``.
    hundredths: Mapped[int] = mapped_column(Integer, nullable=False)
    sigma: Mapped[float] = mapped_column(Float, nullable=False)
    results: Mapped[int] = mapped_column(Integer, nullable=False)
    last_result_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    level_reached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    general_entered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    friends_entered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    #: The last results, oldest first: ``W`` a win, ``L`` a loss — at most five.
    form: Mapped[str] = mapped_column(String(5), nullable=False)


#: General's order. Declared after the class, because two of its keys descend
#: and a descending key is an expression over the column.
Index(
    "ix_ranking_rows_order",
    RankingRowORM.sport,
    RankingRowORM.hundredths.desc(),
    RankingRowORM.results.desc(),
    RankingRowORM.level_reached_at,
    RankingRowORM.player_id,
)
