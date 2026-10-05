"""proposals: the pools, and the games still filling in them

A **Proposal** is a game still filling — a pool, a sport, a kind, a court hour
at a club, the share fixed on it, the versions it was dealt in, the yeses and
the book-by ([#538](https://github.com/Raketa02/Raketa/issues/538),
[ADR-0189](../../docs/adr/0189-a-yes-books-a-court-and-the-club-is-the-seller.md)
§2, §5). The stream is in ``event_store``; three tables sit beside it:

- **``pools``** — the pool is first-class and a table of its own (the screens
  C5). A group's pool is filed under the group's id and opened by the first
  proposal made in it; its kind decides what it is made of.
- **``proposals``** — a projection: one row per proposed game, read by the live
  lists and the book-by sweep, indexed by club and start and by pool and start.
- **``proposal_people``** — a projection: one row per person a game is anything
  to — dealt a version, In, or gone — with their answer.

Revision ID: 0037_pools_and_proposals
Revises: 0036_payment_customers_and_notices
Create Date: 2026-09-30
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0037_pools_and_proposals"
down_revision = "0036_payment_customers_and_notices"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "pools",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column("kind", sa.String(16), nullable=False),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("kind IN ('GROUP')", name="ck_pools_kind"),
    )
    op.create_table(
        "proposals",
        sa.Column("id", UUIDType(binary=False), primary_key=True),
        sa.Column(
            "pool_id",
            UUIDType(binary=False),
            sa.ForeignKey("pools.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("origin", sa.String(16), nullable=False),
        sa.Column("poster_id", UUIDType(binary=False), nullable=True),
        sa.Column("sport", sa.String(32), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("club_id", UUIDType(binary=False), nullable=False),
        sa.Column("start", sa.DateTime(timezone=True), nullable=False),
        sa.Column("share_grosze", sa.Integer(), nullable=False),
        sa.Column("book_by", sa.DateTime(timezone=True), nullable=False),
        sa.Column("made_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ended", sa.String(16), nullable=True),
        sa.CheckConstraint(
            "ended IS NULL OR ended IN ('EXPIRED', 'WITHDRAWN')",
            name="ck_proposals_ended",
        ),
    )
    op.create_index("ix_proposals_ended_book_by", "proposals", ["ended", "book_by"])
    op.create_index("ix_proposals_club_id_start", "proposals", ["club_id", "start"])
    op.create_index("ix_proposals_pool_id_start", "proposals", ["pool_id", "start"])
    op.create_table(
        "proposal_people",
        sa.Column(
            "proposal_id",
            UUIDType(binary=False),
            sa.ForeignKey("proposals.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("player_id", UUIDType(binary=False), primary_key=True),
        sa.Column("version", sa.Integer(), nullable=True),
        sa.Column("answer", sa.String(16), nullable=True),
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "answer IS NULL OR answer IN ('YES', 'NO', 'WITHDRAWN')",
            name="ck_proposal_people_answer",
        ),
    )
    op.create_index(
        "ix_proposal_people_player_id_answer",
        "proposal_people",
        ["player_id", "answer"],
    )


def downgrade() -> None:
    op.drop_index("ix_proposal_people_player_id_answer", table_name="proposal_people")
    op.drop_table("proposal_people")
    op.drop_index("ix_proposals_pool_id_start", table_name="proposals")
    op.drop_index("ix_proposals_club_id_start", table_name="proposals")
    op.drop_index("ix_proposals_ended_book_by", table_name="proposals")
    op.drop_table("proposals")
    op.drop_table("pools")
