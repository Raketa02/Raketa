"""``discovery_rest_counts`` — the rest count (``docs/adr/0204`` §10; migration
0075, #796).

**The phone's on-screen reports, which no stream holds**: one row per viewer,
row and player seen, with how many different Warsaw days the card came on
screen while the two were unconnected (``days``) and the last of them
(``last_day``) — the days come in the clock's order, so a report for a day no
later than the last counts nothing, and the count is of different days without
keeping each. Written by the report in its own transaction; a gone account's
rows go on either side. **No rebuild**: there is nothing to fold it from.

Keyed ``(viewer_id, row, player_id)``, so a row's read asks about a batch of
its cards by the key, and the viewer's own rows go by its prefix;
``ix_discovery_rest_counts_player_id`` serves forgetting the player seen. **No
foreign key to the directory**, as the levels have none.
"""

from __future__ import annotations

from datetime import date
from uuid import UUID

from sqlalchemy import Date, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class DiscoveryRestCountORM(Base):
    __tablename__ = "discovery_rest_counts"
    __table_args__ = (Index("ix_discovery_rest_counts_player_id", "player_id"),)

    viewer_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    #: ``SAME_LEVEL`` or ``SAME_VIBE`` — each row keeps its own count.
    row: Mapped[str] = mapped_column(String(16), primary_key=True)
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    #: Different Warsaw days on screen while unconnected.
    days: Mapped[int] = mapped_column(Integer, nullable=False)
    #: The last of them.
    last_day: Mapped[date] = mapped_column(Date, nullable=False)
