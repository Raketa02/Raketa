import uuid
from datetime import datetime
from uuid import UUID

from sqlalchemy import Boolean, DateTime, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy_utils.types.uuid import UUIDType

from app.infrastructure.database.base import Base


class UserORM(Base):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", name="uq_users_email"),
        UniqueConstraint("nickname", name="uq_users_nickname"),
    )

    id: Mapped[UUID] = mapped_column(
        UUIDType(binary=False), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(320), nullable=False, index=True)
    # Both null until the naming (``docs/adr/0171`` §2). The unique constraint
    # on the nickname admits any number of nulls, on Postgres and SQLite alike,
    # which is exactly the reading wanted: two unnamed accounts share nothing.
    name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    nickname: Mapped[str | None] = mapped_column(
        String(64), nullable=True, index=True
    )
    # Null only between the club's *Reset password* clearing it and a new one
    # being set (``docs/adr/0184`` §6): nothing signs in to such an account.
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)
    authority: Mapped[str] = mapped_column(
        String(32), nullable=False, default="USER", server_default="USER"
    )
    is_admin: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True, server_default="true"
    )
    # The tester mark (``docs/adr/0180`` §9). A column beside ``authority`` and
    # never a value of it: a Tester is shown features early and holds no power.
    is_tester: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    # When the credentials last changed (``docs/adr/0185`` §7). On the row
    # because every player-surface request already reads it: an access token
    # issued before it is refused at no extra read.
    credentials_changed_at: Mapped[datetime | None] = mapped_column(
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
