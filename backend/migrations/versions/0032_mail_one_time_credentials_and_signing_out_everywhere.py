"""email, one-time credentials, and signing out everywhere

Rakieta can send email and anybody can recover a forgotten password
([#507](https://github.com/Raketa02/Raketa/issues/507),
[ADR-0184](../../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md),
[ADR-0185](../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md),
[ADR-0186](../../docs/adr/0186-email-goes-through-a-port-and-a-purged-queue.md)).

- **``mail_queue``** is where a use case leaves a rendered email in its own
  transaction, and the one place a link and a code sit — until the worker sends
  the message and clears ``text_body`` and ``html_body``. What stays is the
  kind, the recipient, the subject and the delivery record.
- **``one_time_credentials``** holds every link-and-code as **hashes**, in a
  plain table and never in an event: a row expires and can be purged, where an
  event is kept for ever. ``issued_at`` comes from the application's clock,
  because the request throttle and a claim's look-back count from it.
- **``users.credentials_changed_at``** and
  **``club_accounts.credentials_changed_at``** are the instant an account last
  signed out everywhere: an access token issued before it is refused. Null for
  every existing account, which refuses nothing.

Revision ID: 0032_mail_and_credentials
Revises: 0031_group_join_requests
Create Date: 2026-09-25
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0032_mail_and_credentials"
down_revision = "0031_group_join_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "mail_queue",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("kind", sa.String(64), nullable=False),
        sa.Column("recipient", sa.String(320), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("text_body", sa.Text(), nullable=True),
        sa.Column("html_body", sa.Text(), nullable=True),
        sa.Column("queued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("next_attempt_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("given_up_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_mail_queue_pending",
        "mail_queue",
        ["sent_at", "given_up_at", "queued_at"],
        postgresql_where=sa.text("sent_at IS NULL AND given_up_at IS NULL"),
    )

    op.create_table(
        "one_time_credentials",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("purpose", sa.String(32), nullable=False),
        sa.Column("audience", sa.String(16), nullable=False),
        sa.Column("subject_id", UUIDType(binary=False), nullable=False),
        sa.Column("email", sa.String(320), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("code_hash", sa.String(255), nullable=False),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("wrong_codes", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("ticket_hash", sa.String(64), nullable=True),
        sa.Column("ticket_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("token_hash", name="uq_one_time_credentials_token_hash"),
        sa.UniqueConstraint("ticket_hash", name="uq_one_time_credentials_ticket_hash"),
    )
    op.create_index(
        "ix_one_time_credentials_email",
        "one_time_credentials",
        ["email", "purpose", "audience", "issued_at"],
    )
    op.create_index(
        "ix_one_time_credentials_subject",
        "one_time_credentials",
        ["subject_id", "purpose", "audience"],
    )

    op.add_column(
        "users",
        sa.Column("credentials_changed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "club_accounts",
        sa.Column("credentials_changed_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("club_accounts", "credentials_changed_at")
    op.drop_column("users", "credentials_changed_at")
    op.drop_index("ix_one_time_credentials_subject", table_name="one_time_credentials")
    op.drop_index("ix_one_time_credentials_email", table_name="one_time_credentials")
    op.drop_table("one_time_credentials")
    op.drop_index("ix_mail_queue_pending", table_name="mail_queue")
    op.drop_table("mail_queue")
