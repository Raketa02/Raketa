"""the deck reads no declaration, and a deal may record that none stood

The Players deal scores every viewer under the fun ruler and reads no Play intent
([#439](https://github.com/Rakieta02/Rakieta/issues/439),
[ADR-0169](../../docs/adr/0169-the-deck-lives-on-players-and-a-swipe-is-an-answer.md)
§2). `play_intent_not_declared` is never raised by the deck any more, so a viewer
who never declared is dealt — and the row still records **the declaration as it
stood**, which for them is nothing.

`0010` wrote `intent_read` as the mirror of `mode`: set exactly when the surface
is the deck, because the deck used to read it to pick a vector. Half of that
sentence survives. `intent_read` is still set on **no other surface** — a
shortlist's mode is the request's, and there is nothing to record — but on the
deck it is now history rather than an input, and history may be empty. So the
constraint loosens from a biconditional to an implication, and `mode`'s is
untouched: a deal still has no mode, and it never will.

No row moves. Every deal recorded so far carries the declaration the deck read at
the time, which the new constraint admits as it did the old.

Revision ID: 0022_deck_no_intent
Revises: 0021_sportsmanship
Create Date: 2026-09-15

The revision id is short because `alembic_version.version_num` is `VARCHAR(32)`:
a longer one applies its DDL and then fails writing the stamp, which leaves the
schema ahead of the version table. The **filename** carries the sentence; the id
only has to be unique.
"""

from alembic import op

revision = "0022_deck_no_intent"
down_revision = "0021_sportsmanship"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_constraint("ck_search_intent_read_set_exactly_on_the_deck", "search")
    op.create_check_constraint(
        "ck_search_intent_read_only_on_the_deck",
        "search",
        "(intent_read IS NULL) OR (surface = 'DECK')",
    )


def downgrade() -> None:
    # A deal recorded for a viewer who never declared has `intent_read` null on
    # a `DECK` row, which the older constraint refuses; there is no value to put
    # there that would not be an invented declaration, so the downgrade refuses
    # rather than lying about what somebody said.
    op.drop_constraint("ck_search_intent_read_only_on_the_deck", "search")
    op.create_check_constraint(
        "ck_search_intent_read_set_exactly_on_the_deck",
        "search",
        "(intent_read IS NOT NULL) = (surface = 'DECK')",
    )
