"""The Groups context's three rows: the group, each Group member, and each Join
request waiting.

**All three are projections**, written beside the event in the same transaction
(``docs/adr/0183`` §1) — the stream is the record.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    JSON,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class GroupORM(Base):
    """One group, as the lists, the page and the searches read it.

    ``name_folded`` is **a second spelling stored beside the first**, folded by
    ``clubs/domain/folding.py`` — the function a query is folded by — so join
    search can match a group's name as home-club search matches a club's
    (``docs/adr/0183`` §9). It is written from the first event on, because a
    fold cannot be computed in SQL and a copy added later would need every
    group re-projected.

    ``code`` is unique and never changes (``docs/adr/0183`` §4).

    **The kind decides which columns hold anything**, and a check constraint
    holds the two shapes (``docs/adr/0183`` §1, §3): a player group has an
    ``owner_id`` and nothing in the official columns; an official group has no
    Owner, and its ``administrator_id``, ``whatsapp_size`` and
    ``declared_sports`` — registry codes in the registry's order, as a club's
    sports are held.

    ``created_at`` is the creating event's own instant, so an Administrator's
    groups come newest created first even when the stream was written in the
    past, as a seed writes it.
    """

    __tablename__ = "groups"
    __table_args__ = (
        UniqueConstraint("code", name="uq_groups_code"),
        CheckConstraint(
            "(kind = 'PLAYER' AND owner_id IS NOT NULL AND administrator_id IS NULL"
            " AND whatsapp_size IS NULL AND declared_sports IS NULL)"
            " OR (kind = 'OFFICIAL' AND owner_id IS NULL"
            " AND administrator_id IS NOT NULL AND whatsapp_size IS NOT NULL"
            " AND declared_sports IS NOT NULL)",
            name="ck_groups_kind_shape",
        ),
    )

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    name: Mapped[str] = mapped_column(String(40), nullable=False)
    # Case folding can lengthen a string (``ß`` → ``ss``), so the folded copy
    # is wider than the column it is folded from.
    name_folded: Mapped[str] = mapped_column(String(255), nullable=False)
    home_club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("clubs.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    join_policy: Mapped[str] = mapped_column(String(32), nullable=False)
    kind: Mapped[str] = mapped_column(
        String(16), nullable=False, default="PLAYER", server_default="PLAYER"
    )
    owner_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False), nullable=True
    )
    administrator_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("administrators.id", ondelete="RESTRICT"),
        nullable=True,
        index=True,
    )
    whatsapp_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # ``none_as_null``: a player group's ``None`` is SQL ``NULL``, never the
    # JSON ``null`` the check constraint would read as a value.
    declared_sports: Mapped[Optional[list[str]]] = mapped_column(
        JSON(none_as_null=True), nullable=True
    )
    code: Mapped[str] = mapped_column(String(8), nullable=False)
    #: When the club handed it to whoever runs it now, while they have not been
    #: told; cleared by ``handover_seen`` (``docs/adr/0192`` §1).
    handed_over_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class GroupMemberORM(Base):
    """One Group member of one group.

    ``joined_at`` is the event's own instant — *newest joined first* on a
    player's list reads it. ``joined_version`` is the stream version of the
    event that admitted them, so *the order they joined in* is exact within a
    group even when two joins share an instant.
    """

    __tablename__ = "group_members"

    group_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, index=True
    )
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    joined_version: Mapped[int] = mapped_column(Integer, nullable=False)


class GroupJoinRequestORM(Base):
    """One Join request **while it waits**, and not a moment longer.

    Approved or declined, the row is deleted: the stream remembers every
    answer, and this table answers only *who is waiting*. The key is the
    group and the person, which is *at most one waiting per player per group*
    (``docs/adr/0183`` §7) held by the database as well as by the aggregate.

    ``requested_version`` is the stream version of the ask, so the Owner's
    queue is in the exact order people asked even when two asked in one
    instant.
    """

    __tablename__ = "group_join_requests"

    group_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("groups.id", ondelete="CASCADE"),
        primary_key=True,
    )
    player_id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    requested_version: Mapped[int] = mapped_column(Integer, nullable=False)
