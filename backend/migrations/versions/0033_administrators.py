"""administrators, and a password a club can clear

A club makes people administrators, and they get in
([#508](https://github.com/Raketa02/Raketa/issues/508),
[ADR-0184](../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md),
[ADR-0185](../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)).

- **``administrators``** is the projection of every Administrator's stream —
  one per (club, email), so the pair is unique and a removed person invited
  again keeps their row. ``last_used_at`` is the one column no event writes:
  the administrator guard moves it at most once an hour.
- **``users.password_hash`` becomes nullable**, because the club's *Reset
  password* of an administrator-only account clears it: nothing signs in until
  a new one is set. Every existing row keeps its hash.

Revision ID: 0033_administrators
Revises: 0032_mail_and_credentials
Create Date: 2026-09-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0033_administrators"
down_revision = "0032_mail_and_credentials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "administrators",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("name", sa.String(64), nullable=False),
        sa.Column("state", sa.String(16), nullable=False),
        sa.Column("account_id", UUIDType(binary=False), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "reset_pending", sa.Boolean(), nullable=False, server_default=sa.false()
        ),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
        sa.UniqueConstraint("club_id", "email", name="uq_administrators_club_email"),
    )
    op.create_index("ix_administrators_club_id", "administrators", ["club_id"])
    op.create_index("ix_administrators_email", "administrators", ["email"])
    op.create_index("ix_administrators_account_id", "administrators", ["account_id"])

    op.alter_column(
        "users", "password_hash", existing_type=sa.String(255), nullable=True
    )


def downgrade() -> None:
    # A cleared password has no value to restore, and an account is never
    # deleted to make a column fit: the downgrade refuses instead.
    cleared = (
        op.get_bind()
        .execute(sa.text("SELECT COUNT(*) FROM users WHERE password_hash IS NULL"))
        .scalar()
    )
    if cleared:
        raise RuntimeError(
            f"{cleared} account(s) have a password a club cleared; set one "
            f"before downgrading past 0033"
        )
    op.alter_column(
        "users", "password_hash", existing_type=sa.String(255), nullable=False
    )
    op.drop_index("ix_administrators_account_id", table_name="administrators")
    op.drop_index("ix_administrators_email", table_name="administrators")
    op.drop_index("ix_administrators_club_id", table_name="administrators")
    op.drop_table("administrators")
