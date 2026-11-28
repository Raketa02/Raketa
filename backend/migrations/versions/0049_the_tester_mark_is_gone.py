"""the tester mark is gone, and its column with it

**The feature flags and the Tester mark that fed them were removed**
([#581](https://github.com/Rakieta02/Rakieta/issues/581), PRD #569). A Tester was
a real player who could be given a feature before anyone else, and the player
app handed the mark to flag evaluation (``0028``). The flag machinery went with
Classic play, there will never be an old build to switch, and nothing reads the
mark — so ``users.is_tester`` goes, with ``is_tester`` on ``/users/me`` and on
the sign-up response, the two events that set it and ``make tester``.

**Dropped, not emptied**: nothing will write it again. Only ``local`` runs, and
its store is reset with this change (``make down-v && make up && make seed``),
because a stored ``users.user_marked_as_tester`` no longer decodes.

**The downgrade restores the column as ``0028`` added it**, ``false`` for every
row through the server default. That is what every stream written since this
revision folds to, and an older checkout's seed marks its own Testers again.

Revision ID: 0049_the_tester_mark_is_gone
Revises: 0048_the_candidate_index_is_gone
Create Date: 2026-10-06
"""

import sqlalchemy as sa
from alembic import op

revision = "0049_the_tester_mark_is_gone"
down_revision = "0048_the_candidate_index_is_gone"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column("users", "is_tester")


def downgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "is_tester", sa.Boolean(), nullable=False, server_default=sa.text("false")
        ),
    )
