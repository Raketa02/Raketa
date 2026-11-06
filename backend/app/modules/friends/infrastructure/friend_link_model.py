"""The Friend link's projection: ``friend_link_codes``, **every code a link ever
carried** (#748).

**One row per code, kept for ever**: ``current`` while its owner's link carries
it, and no longer once **New link** replaced it — the row stays, so the minter
never hands the code out again and a link pasted a year ago can lead only to the
person who shared it, or nowhere. The code is the primary key, so the index the
minter's check and the opening's lookup ask is the guard behind both. Written by
the repository's ``save`` from the events it appends, in the caller's
transaction; the stream is the record.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class FriendLinkCodeORM(Base):
    __tablename__ = "friend_link_codes"
    __table_args__ = (Index("ix_friend_link_codes_owner_id", "owner_id"),)

    code: Mapped[str] = mapped_column(String(8), primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), nullable=False)
    #: The owner's link carries it now. False once replaced — and never true again.
    current: Mapped[bool] = mapped_column(Boolean, nullable=False)
    made_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
