"""The interest ledger: one row per live *Let's play*, with its origin key.

`the-engine.md` §12 makes interest **durable, in the module** — the one thing in
this context a human would miss, since a person reached out to another person.
Exposure and suppression stay Redis keys with TTLs beside it; this is a row.

**The primary key is the idempotency rule.** `(from_player_id, to_player_id,
sport)`, so a second yes cannot become a second row even if two taps race — and
there is no update path, so the expiry a yes was born with is the expiry it dies
with (`docs/adr/0127` §5).

**The origin key is two columns and not a third table** (`search-telemetry.md`
§4). `origin_search_id` is a non-nullable foreign key onto `search` and
`origin_position` is where that person sat in it: an interest citing an unknown
or foreign search is refused rather than linked as null, because a silently
dropped link is a denominator that lies. When `matches` arrives the chain is
`match ← interest ← search`, still foreign keys, still no third table.

**This is the one table in this context that is deleted from.** `docs/adr/0104`'s
*nothing deletes a row* is about the search record; `the-engine.md` §12 draws the
line the other way here — *an interest expires, a pass record does not* — so the
expiry loop removes rows and there is deliberately no `expired_at`, no `state`
and no archive.

Revision ID: 0013_interest_ledger
Revises: 0012_relaxation_offers
Create Date: 2026-08-28

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0013_interest_ledger"
down_revision = "0012_relaxation_offers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "interest",
        sa.Column("from_player_id", UUIDType(binary=False), nullable=False),
        sa.Column("to_player_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=False),
        # Dated at birth, so a later change to `INTEREST_TTL` cannot reach
        # backwards and shorten a yes somebody already sent.
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "origin_search_id",
            UUIDType(binary=False),
            sa.ForeignKey("search.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("origin_position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint(
            "from_player_id",
            "to_player_id",
            "sport",
            name="pk_interest",
        ),
        sa.CheckConstraint(
            "from_player_id <> to_player_id",
            name="ck_interest_not_to_yourself",
        ),
        sa.CheckConstraint(
            "expires_at > sent_at",
            name="ck_interest_expires_after_it_was_sent",
        ),
        sa.CheckConstraint(
            "origin_position >= 1",
            name="ck_interest_origin_position_is_a_rank",
        ),
    )
    # The lift's read and the mutual read both point *towards* somebody, which
    # the primary key's leading column does not serve.
    op.create_index(
        "ix_interest_towards",
        "interest",
        ["to_player_id", "sport", "expires_at"],
    )
    # The expiry loop's sweep, and the only index a background job needs.
    op.create_index("ix_interest_expires_at", "interest", ["expires_at"])


def downgrade() -> None:
    op.drop_index("ix_interest_expires_at", table_name="interest")
    op.drop_index("ix_interest_towards", table_name="interest")
    op.drop_table("interest")
