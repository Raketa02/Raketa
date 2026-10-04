import uuid
from datetime import datetime
from typing import Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class RefreshTokenORM(Base):
    """One issued refresh token, and **whose it is** (``docs/adr/0185`` §6).

    A token belongs to a User or to a Club account, never both and never
    neither, and the row says which by filling **one of two columns**, each a
    real foreign key. One ``account_id`` column with a kind beside it was the
    alternative, and it gives up the reference: a token could then name an
    account that does not exist, and deleting one would leave its sessions
    behind. The check constraint is what makes *exactly one* a fact about the
    table rather than about every writer.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("jti", name="uq_refresh_tokens_jti"),
        CheckConstraint(
            "(user_id IS NULL) <> (club_account_id IS NULL)",
            name="ck_refresh_tokens_one_holder",
        ),
    )

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    club_account_id: Mapped[Optional[UUID]] = mapped_column(
        UUIDType(binary=False),
        ForeignKey("club_accounts.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    token_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    jti: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    refresh_expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    is_valid: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    revoked_at: Mapped[Optional[datetime]] = mapped_column(
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
