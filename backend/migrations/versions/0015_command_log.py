"""a destructive command remembers what it did, for twenty-four hours

ADR-0030: *"We will give destructive commands a command log keyed `(command,
idempotency key)`** with a 24-hour expiry, rather than keeping an idempotency key
on an emptied seat or answering a replay from the departure record."* Both
alternatives it names fail in the same place — an emptied seat has nothing left
to hold a key on, and the departure record answers *whose money is this* rather
than *did I already do this*.

The departure route (`Raketa02/Raketa#80`) is the first command to carry one, and
the table is cross-cutting rather than Matches' because the second one will not
be Matches'.

**The key is the primary key.** A surrogate id would be a second identity for a
row whose entire content is its key, and a unique constraint beside one would be
the same index written twice. It also makes the collision ADR-0030 cares about a
database refusal rather than a read-then-write race.

**No expiry column and no scheduled prune.** Twenty-four hours is applied on the
**read** — a row past the window is not a replay whether or not anything has
deleted it — so correctness never waits on a sweep. The sweep runs on the next
write of the same command, which is what the second index is for, and it keeps
the table bounded by *how many of these were sent in the last day*.

Revision ID: 0015_command_log
Revises: 0014_match_closed_at
Create Date: 2026-08-23
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0015_command_log"
down_revision = "0014_match_closed_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "command_log",
        sa.Column("command", sa.String(length=64), nullable=False),
        sa.Column("key", sa.String(length=128), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("result", sa.String(length=64), nullable=False),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("command", "key", name="pk_command_log"),
    )
    op.create_index("ix_command_log_expiry", "command_log", ["command", "recorded_at"])


def downgrade() -> None:
    op.drop_index("ix_command_log_expiry", table_name="command_log")
    op.drop_table("command_log")
