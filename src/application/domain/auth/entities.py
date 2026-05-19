import uuid

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, String, func
from sqlalchemy_utils.types.uuid import UUIDType

from application.core.database import Base


class RefreshToken(Base):
    __tablename__ = "refresh_tokens"

    id = Column(UUIDType(binary=False), primary_key=True, default=uuid.uuid4)
    user_id = Column(
        UUIDType(binary=False),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # bcrypt hash of the issued refresh JWT — never store the token itself
    token_hash = Column(String(255), nullable=False)
    jti = Column(String(64), nullable=False, unique=True, index=True)
    refresh_expires_at = Column(DateTime(timezone=True), nullable=False)
    is_valid = Column(Boolean, nullable=False, default=True, server_default="true")
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
