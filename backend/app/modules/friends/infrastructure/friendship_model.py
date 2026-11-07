"""The Friendship's two projections: ``friend_relations`` and, since #749,
``friend_level_asks``.

**Two rows per pair while something stands between them**, one from each side —
``FRIEND`` and ``FRIEND``, or ``SENT`` for the requester and ``ASKED_YOU`` for the
person asked — and **none** once nothing does. Written by the repository's
``save`` from the aggregate as it stands, in the caller's transaction; the stream
is the record.

**Keyed on the reader first**, so every read is the reader's side alone: *my
relation to these people* is one indexed question, and nothing on this table is
read about two other people. That is what makes the reads as cheap as a face
needs them — every deck tile, Home card and Members row asks — and it is why a
projection is kept rather than folding streams per read, as Blocks does.

**``friend_level_asks``** holds every **Ask for a level** ever made, one row per
asker, friend and sport — kept after the friendship ends, as the stream keeps
it — and when the friend's first level in it answered it. Read from the asker's
side by the picker (*Asked*), and by friend and sport by the one subscriber that
answers the asks when that level arrives (``FriendLevelAskORM``).
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class FriendRelationORM(Base):
    __tablename__ = "friend_relations"
    __table_args__ = (
        CheckConstraint(
            "relation IN ('SENT', 'ASKED_YOU', 'FRIEND')",
            name="ck_friend_relations_relation",
        ),
    )

    #: Whose side of the pair this row is.
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    other_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    relation: Mapped[str] = mapped_column(String(16), nullable=False)
    #: When they became friends, or when the request was made.
    since: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: On ``ASKED_YOU``: *Not now*.
    set_aside: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    #: On a request: where it was made.
    made_from: Mapped[str | None] = mapped_column(String(16), nullable=True)
    group_id: Mapped[UUID | None] = mapped_column(UUIDType(binary=False), nullable=True)
    sport: Mapped[str | None] = mapped_column(String(16), nullable=True)


class FriendLevelAskORM(Base):
    """One **Ask for a level** (#749): the asker, the friend asked, the sport —
    the primary key, since each is asked once, ever — the group whose picker it
    was asked from, and when the friend's first level in the sport answered it.

    **Keyed on the asker first**, so the picker's *Asked* is one question on the
    primary key's prefix; ``(friend_id, sport)`` is what the answer is looked
    up by when the rating records a first level."""

    __tablename__ = "friend_level_asks"
    __table_args__ = (
        Index("ix_friend_level_asks_friend_id_sport", "friend_id", "sport"),
    )

    asker_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    friend_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    sport: Mapped[str] = mapped_column(String(16), primary_key=True)
    group_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    #: When the friend's first level in the sport answered it; ``None`` until.
    got_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
