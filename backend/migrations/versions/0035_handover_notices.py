"""handover notices: an official group remembers whether its new administrator
has been told

When the club hands an official group to another Administrator, the app tells
them once, on a sheet ([ADR-0192](../../docs/adr/0192-a-handover-is-told-to-whom-it-was-handed-and-the-app-follows-the-account.md)
§1). Whether they have been told is recorded on the group's stream
(``groups.handover_seen``), and the projection gains the column the account's
read asks:

- **``handed_over_at``** — when the club handed it to whoever runs it now,
  **while they have not been told**; ``NULL`` once they have, and for every
  group its Administrator created. Rows written before this were handed, if at
  all, before anybody could be told, so ``NULL`` is what they are.

**Parallel branch:** ``feature/games_fillin_club`` also chains its own 0035 onto
0034. Whichever branch lands second re-points its first migration onto the
other's head.

Revision ID: 0035_handover_notices
Revises: 0034_official_groups
Create Date: 2026-10-04
"""

import sqlalchemy as sa
from alembic import op

revision = "0035_handover_notices"
down_revision = "0034_official_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "groups",
        sa.Column("handed_over_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("groups", "handed_over_at")
