"""notifications: push, the recent list and the three choices

**Players are told** ([#549](https://github.com/Rakieta02/Rakieta/issues/549);
the mechanics §17.2; the screens A7.2, A9; ADR-0189 §5). Two new streams — a
player's **Notification preferences**, and **what they were told on a day** —
and three projections beside them:

- **``notification_preferences``** — each player's three choices, one row per
  player who ever chose; no row is the defaults.
- **``push_devices``** — which player each phone is pushed to as, and the one
  place its push token is kept: the stream names a phone by the token's
  SHA-256, since the token itself may not enter the event store (ADR-0184 §4).
- **``notices``** — the recent list: one row per notice given, and how many of
  its kind the day gathered into it.

Revision ID: 0045_notifications
Revises: 0044_club_money_and_payouts
Create Date: 2026-10-02
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0045_notifications"
down_revision = "0044_club_money_and_payouts"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notification_preferences",
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("you_complete_it", sa.Boolean(), nullable=False),
        sa.Column("challenges_for_you", sa.Boolean(), nullable=False),
        sa.Column("fill_in_alerts", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "push_devices",
        sa.Column("device", sa.String(64), primary_key=True),
        sa.Column("token", sa.String(255), nullable=False),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("registered_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_push_devices_player_id", "push_devices", ["player_id"])
    op.create_table(
        "notices",
        sa.Column("notice_id", UUIDType(binary=False), primary_key=True),
        sa.Column("player_id", UUIDType(binary=False), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("game_id", UUIDType(binary=False), nullable=False),
        sa.Column("pool_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(16), nullable=False),
        sa.Column("game_kind", sa.String(16), nullable=False),
        sa.Column("club_id", UUIDType(binary=False), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("opens", sa.String(16), nullable=False),
        sa.Column("amount_grosze", sa.Integer(), nullable=True),
        sa.Column("people", sa.Text(), nullable=False, server_default=""),
        sa.Column("reason", sa.String(32), nullable=True),
        sa.Column("given_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sequence_no", sa.BigInteger(), nullable=False),
        sa.Column("gathered", sa.Integer(), nullable=False, server_default="0"),
    )
    op.create_index(
        "ix_notices_player_id_given_at",
        "notices",
        ["player_id", "given_at", "sequence_no"],
    )


def downgrade() -> None:
    # The streams still say what each player chose and was told; the
    # projections are gone.
    op.drop_index("ix_notices_player_id_given_at", table_name="notices")
    op.drop_table("notices")
    op.drop_index("ix_push_devices_player_id", table_name="push_devices")
    op.drop_table("push_devices")
    op.drop_table("notification_preferences")
