"""The Friends context's one projection: ``friend_relations``.

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
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, CheckConstraint, DateTime, String
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
