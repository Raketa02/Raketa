"""The conversation room: one row per room, and it exists for the sequence.

The stream lives in `event_store` beside every other aggregate's; this table is
not a projection of it and holds nothing a reader draws. It is here for the
**gapless per-conversation sequence number** `docs/adr/0147` §2 decided:
`last_seq + 1`, read and written **under this row's lock**, inside the appending
transaction.

**Not a Postgres sequence object**, which is explicitly not gapless — aborts and
crashes leave holes — and **not a timestamp**, which `docs/adr/0097` disqualified
when it found `func.now()` is transaction-start time, identical across a
transaction and not unique.

**`challenge_id` is unique**, which is what makes *one arrangement is one room*
an invariant the database holds rather than a race between two acceptances
arriving in one outbox poll. **`game_id` is nullable and unique**: nullable
because a room opens on the first acceptance and a line-up that never completes
has no game at all; unique because one arrangement is one game is already
`games`' invariant, and a second room claiming a game would be this context
contradicting it.

**No member column.** Membership is derived from whichever record is arranging —
the challenge's accepted seats until the line-up completes, the game's frozen
line-up after (`docs/adr/0146` §7) — and a stored roster would be the copy that
decides who may read the messages.

Revision ID: 0020_conversation
Revises: 0019_the_searchers_own_area
Create Date: 2026-09-08

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0020_conversation"
down_revision = "0019_the_searchers_own_area"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "conversation",
        sa.Column("conversation_id", UUIDType(binary=False), nullable=False),
        sa.Column("challenge_id", UUIDType(binary=False), nullable=False),
        sa.Column("game_id", UUIDType(binary=False), nullable=True),
        sa.Column("sport", sa.String(length=50), nullable=False),
        # The allocator. Zero in a room where nothing has landed yet, which is a
        # real state: the opening is not a line, and `seq` 1 is whatever
        # happens next.
        sa.Column("last_seq", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("opened_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("conversation_id", name="pk_conversation"),
        sa.CheckConstraint(
            "last_seq >= 0", name="ck_conversation_last_seq_is_a_count"
        ),
    )
    # **Unique, not merely indexed.** One arrangement is one room, and this is
    # where that is enforced rather than remembered.
    op.create_index(
        "ix_conversation_challenge_id", "conversation", ["challenge_id"], unique=True
    )
    op.create_index(
        "ix_conversation_game_id", "conversation", ["game_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_game_id", table_name="conversation")
    op.drop_index("ix_conversation_challenge_id", table_name="conversation")
    op.drop_table("conversation")
