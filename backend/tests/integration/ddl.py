"""The two Postgres-only guarantees, as DDL, each with a switch that removes it.

Nothing in the racket-sport domain is written yet — there is no `reservations`
table and no club-policy series to point at. #62 lands the harness and a
self-check that proves it fires, not the constraints themselves; #64 and #65
bring the real tables, and their migrations will carry these two shapes.

**The `constrained` flag is the point of this module.** "Proven to fire" is an
acceptance criterion, and the honest way to discharge it is not a paragraph
claiming the assertion would fail if the constraint went away — it is running
the same insert against the same table with the constraint removed and asserting
it is *accepted*. That makes the pair a discriminator: the positive case can no
longer pass because the row was refused for some unrelated reason, and the
negative case can no longer pass because the two intervals never overlapped. So
the mutation runs on every CI run rather than living in a script somebody
remembers to invoke.

The tables are created per test under generated names and dropped afterwards.
They are not migrations and not models; `Base.metadata` never learns about them.
"""

# `court_id WITH =` needs an equality operator class GiST does not have for uuid
# out of the box, which is what btree_gist adds. The extension is therefore part
# of the guarantee rather than an implementation detail of the test: a migration
# in #65 has to create it too, and a Postgres image that lacks contrib would
# break that migration. Asserting it is installable here is the cheapest place to
# find that out.
BTREE_GIST = "CREATE EXTENSION IF NOT EXISTS btree_gist"


def reservation_table(name: str, *, constrained: bool = True) -> str:
    """One court, one time range, no two overlapping — or the same table without
    the constraint, which is what makes the assertion above it mean something.

    `tstzrange` rather than two timestamp columns, and `&&` rather than a
    hand-written pair of comparisons, because the overlap test then belongs to
    the database and cannot be got wrong differently in two call sites. The
    ranges the tests build are half-open `[)`, so a court freed at 18:00 and
    taken at 18:00 do not overlap — which is what lets `turnaroundMin` widen a
    claimed interval by padding rather than by arithmetic on somebody else's row.
    """
    exclusion = (
        ",\n    EXCLUDE USING gist (court_id WITH =, during WITH &&)"
        if constrained
        else ""
    )
    return (
        f"CREATE TABLE {name} (\n"
        "    id uuid PRIMARY KEY,\n"
        "    court_id uuid NOT NULL,\n"
        f"    during tstzrange NOT NULL{exclusion}\n"
        ")"
    )


def club_policy_table(name: str) -> str:
    """A versioned series: many closed rows, at most one open one.

    `closed_at IS NULL` is the open row. The uniqueness is partial because the
    closed rows are history and history repeats — a club that has changed its
    hold cap four times has four rows whose `club_id` is identical, and a plain
    unique index would refuse the second change.
    """
    return (
        f"CREATE TABLE {name} (\n"
        "    id uuid PRIMARY KEY,\n"
        "    club_id uuid NOT NULL,\n"
        "    max_hold_age integer NOT NULL,\n"
        "    changed_by text NOT NULL DEFAULT 'system',\n"
        "    closed_at timestamptz\n"
        ")"
    )


def one_open_row_per_series(table: str, index: str, *, constrained: bool = True) -> str:
    """The partial unique index, or a plain non-unique one standing in its place.

    The unconstrained arm is an index rather than nothing at all, so the negative
    control differs from the positive one in exactly the property under test —
    uniqueness — and not also in whether an index exists.
    """
    unique = "UNIQUE " if constrained else ""
    return f"CREATE {unique}INDEX {index} ON {table} (club_id) WHERE closed_at IS NULL"
