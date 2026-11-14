"""``ranking_rows`` — the ranking projection: one row per player per sport — and
``ranking_level_history``, a point per event that put a Level where it stood
(``docs/adr/0203`` §10).

**A fold of one rating stream**, written by the move on every delivered
``rating.moved_on_result`` and by the rebuild, in the caller's transaction.
The stream is the record; this is a copy that pages and orders.

**The order's index** is General's order exactly — sport, Level descending,
results descending, Level reached ascending, player id — so a sport's listed
rows are read in place order off the index.

**The level history is keyed by the stored event** (``event_store.id``): the
rating's opening, and every ``rating.moved_on_result``. Each is written once,
so a redelivery changes nothing; ``ix_ranking_level_history_points`` serves
*each player's point in a sport at an instant* (#769).
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


class LevelPointORM(Base):
    __tablename__ = "ranking_level_history"

    #: The stored event that put the Level here — ``event_store.id``.
    event_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    sport: Mapped[str] = mapped_column(String(16), nullable=False)
    #: The rating's opening, or when the result settled.
    at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    hundredths: Mapped[int] = mapped_column(Integer, nullable=False)
    #: How many results had moved the Level by then — ``0`` at the opening.
    results: Mapped[int] = mapped_column(Integer, nullable=False)
    level_reached_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )


Index(
    "ix_ranking_level_history_points",
    LevelPointORM.sport,
    LevelPointORM.player_id,
    LevelPointORM.at,
)
