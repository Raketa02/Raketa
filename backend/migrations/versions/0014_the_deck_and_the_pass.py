"""The pass record, and the two columns only a deal ever writes.

`docs/adr/0128` gives the pass three boundaries — deck only, one-directional,
never escalating — and `search-telemetry.md` §6 makes the **record durable while
the suppression is not**. That split is this migration: the 30-day suppression
stays a Redis key with a TTL, and the row saying the pass happened is kept, for
one reason. `PASS_SUPPRESS`'s only falsifier is *pass rate on **re-shown**
profiles*, and a lapsed suppression leaves no trace the pair was ever passed — so
at the exact moment a re-show happens, the fact that makes it one has expired.

**The gate is the cache; the evidence is the row.**

**`player_pass` is append-only and never deleted from.** Erasure will be the only
path that removes one, which is `docs/adr/0104` §3's rule for the search record
and is the opposite of `interest`'s — *an interest expires, a pass record does
not*. The primary key is a **surrogate** rather than the pair: a natural key
would collapse a second pass into the first, and a pass never escalates, so
nothing counts them and two passes a month apart are two facts.

**Two nullable columns on the existing tables, and only one of them can carry a
check constraint.** `search.n_excluded_by_suppression` is the only thing that
distinguishes *your own passes emptied your deck* from *the pool is empty* — a
failure nobody can see from any screen, because no route returns a pass — and
`search_candidate.suppression_lapsed` is whether a card is a **re-show**. Both are
**deck deals only**.

For the first that is a constraint, on the same argument as `mode` being null
exactly on the deck: one refuses a row this build could write and the other
refuses a row any writer could. **For the second it cannot be**, and the reason
is worth writing down rather than leaving as an omission somebody later "fixes":
*deck deals only* is a fact about the **search**, and `surface` lives on the other
table. A `CHECK` may not read a second row, so expressing it here would take a
trigger or a denormalised `surface` column — a second copy of the fact the
constraint exists to protect. It is asserted instead on `SearchRecord`, which
holds both halves at once and refuses the record rather than the row.

Both are null for every search recorded before today, and that is what *there is
no backfill* means: the two rates they support start counting now.

Revision ID: 0014_deck_and_pass
Revises: 0013_interest_ledger
Create Date: 2026-08-28

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0014_deck_and_pass"
down_revision = "0013_interest_ledger"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "player_pass",
        # A surrogate: the fact is the *event*, not the pair. See the docstring.
        sa.Column("id", UUIDType(binary=False), nullable=False),
        sa.Column("passer_id", UUIDType(binary=False), nullable=False),
        sa.Column("passed_id", UUIDType(binary=False), nullable=False),
        sa.Column("sport", sa.String(length=50), nullable=False),
        sa.Column("passed_at", sa.DateTime(timezone=True), nullable=False),
        # The Origin key, non-nullable and a foreign key on the interest row's
        # own rule: a pass citing an unknown or foreign search is refused rather
        # than linked as null, because a dropped link makes a denominator lie.
        sa.Column(
            "origin_search_id",
            UUIDType(binary=False),
            sa.ForeignKey("search.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("origin_position", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id", name="pk_player_pass"),
        sa.CheckConstraint(
            "passer_id <> passed_id",
            name="ck_player_pass_not_on_yourself",
        ),
        sa.CheckConstraint(
            "origin_position >= 1",
            name="ck_player_pass_origin_position_is_a_rank",
        ),
    )
    # The deal's read: *which of these has this player ever passed on, in this
    # sport*. One keyed read over a deal of ten.
    op.create_index(
        "ix_player_pass_passer",
        "player_pass",
        ["passer_id", "sport", "passed_id"],
    )

    op.add_column(
        "search",
        sa.Column("n_excluded_by_suppression", sa.Integer(), nullable=True),
    )
    op.add_column(
        "search_candidate",
        sa.Column("suppression_lapsed", sa.Boolean(), nullable=True),
    )
    # Deck deals only, and a check constraint rather than a convention — the
    # third of its kind on this table, beside `mode` and `intent_read`.
    #
    # **It is applicable to the rows already here**, which is not luck: every
    # existing row is a shortlist, and a shortlist with a null in a column that
    # did not exist satisfies the biconditional on both sides. The only row it
    # could refuse is a deal that forgot to count, and there are none — this
    # migration is what makes deals possible.
    op.create_check_constraint(
        "ck_search_suppression_count_only_on_the_deck",
        "search",
        "(n_excluded_by_suppression IS NOT NULL) = (surface = 'DECK')",
    )


def downgrade() -> None:
    op.drop_constraint(
        "ck_search_suppression_count_only_on_the_deck", "search", type_="check"
    )
    op.drop_column("search_candidate", "suppression_lapsed")
    op.drop_column("search", "n_excluded_by_suppression")
    op.drop_index("ix_player_pass_passer", table_name="player_pass")
    op.drop_table("player_pass")
