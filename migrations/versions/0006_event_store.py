"""create append-only event store

Revision ID: 0006_event_store
Revises: 0005_event_delivery_queue
Create Date: 2026-06-01
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0006_event_store"
down_revision = "0005_event_delivery_queue"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "event_store",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("aggregate_type", sa.String(length=100), nullable=False),
        sa.Column("aggregate_id", UUIDType(binary=False), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(length=255), nullable=False),
        sa.Column("schema_version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("payload", JSONB, nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint(
            "aggregate_type",
            "aggregate_id",
            "version",
            name="uq_event_store_stream_version",
        ),
        if_not_exists=True,
    )
    op.create_index(
        "ix_event_store_stream",
        "event_store",
        ["aggregate_type", "aggregate_id", "version"],
        unique=False,
        if_not_exists=True,
    )
    op.create_index(
        "ix_event_store_event_type",
        "event_store",
        ["event_type"],
        unique=False,
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_event_store_event_type", table_name="event_store", if_exists=True
    )
    op.drop_index("ix_event_store_stream", table_name="event_store", if_exists=True)
    op.drop_table("event_store", if_exists=True)
