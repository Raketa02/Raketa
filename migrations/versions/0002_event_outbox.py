"""event_outbox table for transactional outbox

Revision ID: 0002_event_outbox
Revises: 0001_initial
Create Date: 2026-05-25
"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0002_event_outbox"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_outbox",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column("published_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "attempts", sa.Integer(), nullable=False, server_default="0"
        ),
        sa.Column("last_error", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_event_outbox_event_type", "event_outbox", ["event_type"], unique=False
    )
    op.create_index(
        "ix_event_outbox_pending",
        "event_outbox",
        ["published_at", "created_at"],
        unique=False,
        postgresql_where=sa.text("published_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_event_outbox_pending", table_name="event_outbox")
    op.drop_index("ix_event_outbox_event_type", table_name="event_outbox")
    op.drop_table("event_outbox")
