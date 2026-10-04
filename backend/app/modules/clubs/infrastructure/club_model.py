"""The Club context's two rows: the search projection and the account.

**Both are projections**, written beside the event in the same transaction
(``docs/adr/0182`` §2) — the streams are the record. ``clubs`` is what search
reads and nothing else; ``club_accounts`` is what sign-in and every club
request read.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    JSON,
    DateTime,
    Float,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class ClubORM(Base):
    """One club, as search reads it.

    ``name_folded`` and ``district_folded`` are **a second spelling stored
    beside the first**, folded by ``clubs/domain/folding.py`` — the function a
    query is folded by — so a match is a substring test on two columns. Changing
    the fold means re-projecting every club (``docs/adr/0182``, *Harder*).

    ``sports`` holds registry codes in the registry's order. The point is two
    floats as the desk dropped it, never coarsened.
    """

    __tablename__ = "clubs"

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    name: Mapped[str] = mapped_column(String(80), nullable=False)
    district: Mapped[str] = mapped_column(String(64), nullable=False)
    city: Mapped[str] = mapped_column(String(64), nullable=False)
    sports: Mapped[list[str]] = mapped_column(JSON, nullable=False)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    # Case folding can lengthen a string (``ß`` → ``ss``), so the folded copies
    # are wider than the columns they are folded from.
    name_folded: Mapped[str] = mapped_column(String(255), nullable=False)
    district_folded: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class ClubAccountORM(Base):
    """One club's sign-in.

    The email is unique **among club accounts** and nowhere else: the same
    address may be an unrelated User's (``docs/adr/0182`` §3), so there is
    deliberately no constraint reaching across to ``users``.
    """

    __tablename__ = "club_accounts"
    __table_args__ = (UniqueConstraint("email", name="uq_club_accounts_email"),)

    id: Mapped[UUID] = mapped_column(UUIDType(binary=False), primary_key=True)
    club_id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("clubs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    # When the password last changed (``docs/adr/0185`` §7), read on every club
    # request beside the account itself.
    credentials_changed_at: Mapped[Optional[datetime]] = mapped_column(
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
