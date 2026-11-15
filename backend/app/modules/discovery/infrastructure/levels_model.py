"""``discovery_levels`` — every player's current level per sport
(``docs/adr/0204`` §10; migration 0074, #794).

**A copy of what the rating streams stand at**: the Level, its Uncertainty and
the band the rating published with it, and how many results have moved it —
written by the follower on every delivered ``rating.rating_initialised`` and
``rating.moved_on_result``, and by the rebuild, in the caller's transaction.

**One row per player and sport**, the questionnaire's alone included.
``ix_discovery_levels_sport_mu`` serves *Same competitive level*'s windows:
everybody within a gap of the reader's level, one sport at a time; and
``ix_discovery_levels_sport_sigma`` the least Uncertainty in a sport, which
bounds how even anybody beyond a window could read. **No foreign
key to the directory**: a level may be delivered before its account's entry,
and the reads join the two.
"""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import Float, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class DiscoveryLevelORM(Base):
    __tablename__ = "discovery_levels"
    __table_args__ = (
        Index("ix_discovery_levels_sport_mu", "sport", "mu", "player_id"),
        Index("ix_discovery_levels_sport_sigma", "sport", "sigma"),
    )

    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    sport: Mapped[str] = mapped_column(String(16), primary_key=True)
    mu: Mapped[float] = mapped_column(Float, nullable=False)
    sigma: Mapped[float] = mapped_column(Float, nullable=False)
    band_name: Mapped[str] = mapped_column(String(32), nullable=False)
    band_lower: Mapped[float] = mapped_column(Float, nullable=False)
    band_upper: Mapped[float] = mapped_column(Float, nullable=False)
    #: Results that have moved it: the upsert keeps the fold with the most.
    results: Mapped[int] = mapped_column(Integer, nullable=False)
