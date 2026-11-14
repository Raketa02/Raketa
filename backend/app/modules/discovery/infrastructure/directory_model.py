"""``discovery_players`` and ``discovery_player_tags`` — the player directory
(``docs/adr/0204`` §10; migration 0073).

**A copy of what the owners hold**, written whole by the follower on every
delivered user or Player profile event that changes it, and by the rebuild, in
the caller's transaction. The owners' streams are the record.

**One row per account**, ``plays`` true once it holds a Player profile; a
non-player's profile columns are ``NULL``. **One row per tag**
(``discovery_player_tags``), so the tags two players share are counted in SQL,
portably, by a join (#795's Same vibe). ``ix_discovery_players_joined_at``
serves New in Raketa's *who joined after*, newest first.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class DirectoryPlayerORM(Base):
    __tablename__ = "discovery_players"
    __table_args__ = (
        Index("ix_discovery_players_joined_at", "joined_at", "player_id"),
    )

    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    nickname: Mapped[str | None] = mapped_column(String(64), nullable=True)
    #: Holds a Player profile: every column below is that profile's.
    plays: Mapped[bool] = mapped_column(Boolean, nullable=False)
    #: When sign-up finished: the profile commit.
    joined_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    photo_id: Mapped[UUID | None] = mapped_column(UUIDType(binary=False), nullable=True)
    area_latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    area_longitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    #: *Show me to new people*.
    open_to_new_people: Mapped[bool] = mapped_column(Boolean, nullable=False)


class DirectoryTagORM(Base):
    __tablename__ = "discovery_player_tags"
    __table_args__ = (Index("ix_discovery_player_tags_tag", "tag", "player_id"),)

    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("discovery_players.player_id", ondelete="CASCADE"),
        primary_key=True,
    )
    tag: Mapped[str] = mapped_column(String(64), primary_key=True)
