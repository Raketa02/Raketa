"""a club and its account, and a refresh token that says whose it is

Rakieta gets clubs ([#503](https://github.com/Raketa02/Raketa/issues/503),
[ADR-0182](../../docs/adr/0182-a-club-is-a-place-players-search-and-its-account-signs-in-only-on-the-club-surface.md)).
Both new tables are **projections**, written beside their events in the same
transaction; the streams live in ``event_store`` beside everybody else's.

- **``clubs``** is the search projection: a club's name, district and city, the
  sports it offers (registry codes, in the registry's order) and its point, as
  the desk dropped it — plus **folded copies of the name and the district**, the
  second spelling search matches on (``clubs/domain/folding.py``).
- **``club_accounts``** is the club's sign-in. Its email is unique **among club
  accounts** and nowhere else: the same address may belong to an unrelated User,
  so nothing here reaches across to ``users``.

**``refresh_tokens`` records whose a token is**
([ADR-0185](../../docs/adr/0185-one-account-holds-several-profiles-and-a-password-change-signs-out-everywhere.md)
§6). A token now belongs to a User *or* a Club account, so ``user_id`` stops
being required and ``club_account_id`` joins it, each a real foreign key, with a
check that exactly one is filled. Every row that exists names a User, so every
row already satisfies it — which is also why the tokens issued before this
revision survive it.

Revision ID: 0029_clubs
Revises: 0028_the_tester_mark
Create Date: 2026-09-25

The revision id fits ``alembic_version.version_num``'s ``VARCHAR(32)``; the
filename carries the sentence.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0029_clubs"
down_revision = "0028_the_tester_mark"
branch_labels = None
depends_on = None


def _timestamps() -> list[sa.Column]:
    return [
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
    ]


def upgrade() -> None:
    op.create_table(
        "clubs",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("district", sa.String(length=64), nullable=False),
        sa.Column("city", sa.String(length=64), nullable=False),
        sa.Column("sports", sa.JSON(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("name_folded", sa.String(length=255), nullable=False),
        sa.Column("district_folded", sa.String(length=255), nullable=False),
        *_timestamps(),
    )
    op.create_table(
        "club_accounts",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "club_id",
            UUIDType(binary=False),
            sa.ForeignKey("clubs.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        *_timestamps(),
        sa.UniqueConstraint("email", name="uq_club_accounts_email"),
    )
    op.create_index("ix_club_accounts_club_id", "club_accounts", ["club_id"])
    op.create_index("ix_club_accounts_email", "club_accounts", ["email"])

    op.add_column(
        "refresh_tokens",
        sa.Column(
            "club_account_id",
            UUIDType(binary=False),
            sa.ForeignKey(
                "club_accounts.id",
                ondelete="CASCADE",
                name="fk_refresh_tokens_club_account_id",
            ),
            nullable=True,
        ),
    )
    op.create_index(
        "ix_refresh_tokens_club_account_id", "refresh_tokens", ["club_account_id"]
    )
    op.alter_column(
        "refresh_tokens", "user_id", existing_type=UUIDType(binary=False), nullable=True
    )
    op.create_check_constraint(
        "ck_refresh_tokens_one_holder",
        "refresh_tokens",
        "(user_id IS NULL) <> (club_account_id IS NULL)",
    )


def downgrade() -> None:
    # A club's sessions cannot survive a table that only knows Users, and they
    # are sessions rather than records: dropping them signs the desk out.
    op.execute("DELETE FROM refresh_tokens WHERE club_account_id IS NOT NULL")
    op.drop_constraint("ck_refresh_tokens_one_holder", "refresh_tokens", type_="check")
    op.alter_column(
        "refresh_tokens",
        "user_id",
        existing_type=UUIDType(binary=False),
        nullable=False,
    )
    op.drop_index("ix_refresh_tokens_club_account_id", table_name="refresh_tokens")
    op.drop_constraint(
        "fk_refresh_tokens_club_account_id", "refresh_tokens", type_="foreignkey"
    )
    op.drop_column("refresh_tokens", "club_account_id")
    op.drop_index("ix_club_accounts_email", table_name="club_accounts")
    op.drop_index("ix_club_accounts_club_id", table_name="club_accounts")
    op.drop_table("club_accounts")
    op.drop_table("clubs")
