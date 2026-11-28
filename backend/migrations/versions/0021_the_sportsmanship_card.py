"""the sportsmanship card, and one standing answer per pair of people

The first part of the player record that **stores** anything
([#376](https://github.com/Rakieta02/Rakieta/issues/376),
[ADR-0158](../../docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)).
Everything else on that sheet derives; this is a new bounded context with an
aggregate, and it is the first aggregate on this platform that is stored rather
than replayed — a card is born answered, nothing amends it, and nothing
subscribes to one being written.

**Two tables, and the second one cannot be derived from the first.** A card
answered with everybody left blank has no ratings at all, and it still has to
close: an explicit *I am not rating anyone* is an answer, and one that left no
trace would be an invitation to come back a day later and fill somebody in. So
`sportsmanship_card` records **that a court was answered for** and
`sportsmanship_rating` records **what somebody currently thinks of somebody
else**, and the two have different keys because they are different facts.

**`sportsmanship_rating` is keyed on the pair, and that key is the product
rule.** *Only a rater's most recent rating of a given person counts* — two friends
who partner every week would otherwise supply ten of each other's twelve ratings
and the published average would drift towards what one regular partner thinks,
which is the opposite of what the row claims to measure. Keyed on
`(rater_id, subject_id)` a later card **replaces** the earlier answer, so the
collapse is a fact about the schema rather than a discipline every future reader
has to remember, and the count printed beside the figure keeps meaning *how many
different people have an opinion*. It is the same shape `0013` gives interest —
*the primary key is the idempotency rule* — pointed at a different problem.

The earlier answer is **not archived**. Individual ratings reach nobody on any
route, there is no appeal route behind the published figure, and a history kept
for nobody to read is a history somebody eventually reads.

**No blank is stored.** Somebody left blank is absent from `sportsmanship_rating`
entirely, which is what makes *not rating produces no record of the omission*
structural rather than a promise.

**No event stream and no outbox**, and this is a departure the ADR argues for
rather than inherits: every other aggregate here is event-sourced. A card has one
act in its life and nothing reacts to it — the published figure is a fold over
these rows at the moment somebody opens a record, and the matcher never reads any
of it in either the floor or the term.

Revision ID: 0021_sportsmanship
Revises: 0020_conversation
Create Date: 2026-09-08

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy_utils.types.uuid import UUIDType

revision = "0021_sportsmanship"
down_revision = "0020_conversation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sportsmanship_card",
        sa.Column("game_id", UUIDType(binary=False), nullable=False),
        sa.Column("rater_id", UUIDType(binary=False), nullable=False),
        # When the card was closed. There is no `updated_at` and no `state`
        # column: a card is answered or it does not exist.
        sa.Column("answered_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("game_id", "rater_id", name="pk_sportsmanship_card"),
    )
    op.create_table(
        "sportsmanship_rating",
        sa.Column("rater_id", UUIDType(binary=False), nullable=False),
        sa.Column("subject_id", UUIDType(binary=False), nullable=False),
        # Which card the standing answer came from — a column and not a key. The
        # answer belongs to the pair; the game says which evening produced the
        # one that stands.
        sa.Column("game_id", UUIDType(binary=False), nullable=False),
        sa.Column("stars", sa.SmallInteger(), nullable=False),
        sa.Column("rated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint(
            "rater_id", "subject_id", name="pk_sportsmanship_rating"
        ),
        sa.ForeignKeyConstraint(
            ["game_id", "rater_id"],
            ["sportsmanship_card.game_id", "sportsmanship_card.rater_id"],
            name="fk_sportsmanship_rating_card",
            ondelete="RESTRICT",
        ),
        # A rating that came from no answered card cannot exist, and neither can
        # one about yourself: you rate everybody else on the court, and the
        # write path cannot produce a self-rating because the rater is not among
        # the others a court offers.
        sa.CheckConstraint(
            "rater_id <> subject_id",
            name="ck_sportsmanship_rating_not_about_yourself",
        ),
        # One to five whole stars. The rule's home is the domain; this refuses a
        # value that rule would never have produced.
        sa.CheckConstraint(
            "stars BETWEEN 1 AND 5",
            name="ck_sportsmanship_rating_is_one_to_five_stars",
        ),
    )
    # The published fold's only read: *who has an opinion about this person,
    # most recent first*. The date is in the index because the window is always
    # applied — it is fifty raters, and taking the fifty most recent of them is
    # an ordering before it is a limit.
    op.create_index(
        "ix_sportsmanship_rating_about",
        "sportsmanship_rating",
        ["subject_id", "rated_at"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_sportsmanship_rating_about", table_name="sportsmanship_rating"
    )
    op.drop_table("sportsmanship_rating")
    op.drop_table("sportsmanship_card")
