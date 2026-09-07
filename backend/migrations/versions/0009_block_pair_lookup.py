"""index the one block read that is not keyed by stream id

A block's stream id is a `uuid5` of the ordered `(blocker, blocked)` pair
(ADR-0095 §1), so every question this platform asks about *one pair* is a keyed
read that `ix_event_store_stream` already serves. One question is not about a
pair: **whom must this player never be shown**, which is every stream they appear
in on either side, resolved at request time and carried into generation as an
exclusion list (ADR-0095 §4). A `uuid5` cannot be reversed, so that read matches
on the payload — and without an index it is a sequential scan of every block ever
recorded, on the live request path of every search.

ADR-0095 §4 says **"tens of rows, not a scan"**, and this is what makes that
sentence true rather than aspirational.

**Two partial expression indexes, not one composite.** The query is a disjunction
— *this player is the blocker* OR *this player is the blocked* — and PostgreSQL
serves that by scanning both and combining the bitmaps; a composite over the two
keys would serve neither arm. Both are partial on `aggregate_type = 'block'`,
because they exist for one context and every other stream in this table would
otherwise pay for the index on every append.

**Declared here and not on `EventStoreORM`.** `payload->>` is PostgreSQL's
syntax, and the model is created directly from its metadata under the SQLite the
test suite runs on. An index this narrow buys nothing at test volumes and would
have to be spelled twice to be dialect-portable; the model stays portable and the
statement stays in the one place that is already unapologetically PostgreSQL.

Revision ID: 0009_block_pair_lookup
Revises: 0008_candidate_index
Create Date: 2026-08-27
"""

from alembic import op

revision = "0009_block_pair_lookup"
down_revision = "0008_candidate_index"
branch_labels = None
depends_on = None

# The aggregate type is `EventSourcedBlockRepository.BLOCK_AGGREGATE`. It is
# spelled here because a migration is a statement about what the database held on
# the day it ran, and must not change meaning when a constant does.
_BLOCKER = """
    CREATE INDEX ix_event_store_block_blocker
        ON event_store ((payload ->> 'blocker_id'))
     WHERE aggregate_type = 'block'
"""

_BLOCKED = """
    CREATE INDEX ix_event_store_block_blocked
        ON event_store ((payload ->> 'blocked_id'))
     WHERE aggregate_type = 'block'
"""


def upgrade() -> None:
    op.execute(_BLOCKER)
    op.execute(_BLOCKED)


def downgrade() -> None:
    op.execute("DROP INDEX ix_event_store_block_blocked")
    op.execute("DROP INDEX ix_event_store_block_blocker")
