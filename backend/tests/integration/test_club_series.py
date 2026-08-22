"""One open row per club series — asserted against PostgreSQL, on the real tables.

The sibling `test_partial_unique_index.py` asserts the *shape* against a
throwaway table, because when #62 landed there was no club-policy series to point
at. #64 brings the real ones, and this file points at those: the tables are
created from `Base.metadata` — the same declarations the application maps to and
`tests/unit/test_clubs_migration.py` pins the migration against — inside a
throwaway schema that is dropped afterwards.

**Why here as well as on SQLite.** SQLite has partial indexes, so the guarantee is
not impossible there the way the interval exclusion is, and `tests/unit/
test_club_repository.py` does exercise it. What SQLite cannot speak for is what
production runs: uuid comparison, `timestamptz`, index-level locking under
concurrent inserts, and the actual DDL these declarations compile to on
PostgreSQL — which is not the DDL they compile to on SQLite, because the
predicate is a dialect-scoped keyword argument and a typo in one of the two is
invisible on the other.

**Every case is paired with the same insert against the same table with the index
dropped**, as next door. The negative control here is stronger than a copied
table: it is the real index, removed by name, so the positive case can no longer
pass because the row was refused for an unrelated reason.
"""

import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.infrastructure.database.base import Base
from app.infrastructure.database import models as _models  # noqa: F401  (registers)

pytestmark = pytest.mark.postgres

UNIQUE_VIOLATION = "23505"

MONDAY = datetime(2026, 8, 31, 9, 0, tzinfo=timezone.utc)
FRIDAY_1600 = datetime(2026, 9, 4, 16, 0, tzinfo=timezone.utc)

CLUB_TABLES = (
    "clubs",
    "club_card_offsets",
    "club_policies",
    "club_payout_destinations",
    "club_court_categories",
    "club_court_catalogue",
)

#: index name -> the series it guards, as `(table, insert, keys)`. Written out so
#: an index quietly renamed fails here rather than being dropped from the sweep.
SERIES = {
    "uq_club_policies_open_row": "club_policies",
    "uq_club_payout_destinations_open_row": "club_payout_destinations",
    "uq_club_court_catalogue_open_row": "club_court_catalogue",
}


@pytest.fixture
async def clubs_schema(pg_engine):
    """The Clubs tables, from the application's own declarations, in a scratch
    schema that is dropped on the way out — failure included."""

    schema = f"clubs_guarantee_{uuid.uuid4().hex[:12]}"
    tables = [Base.metadata.tables[name] for name in CLUB_TABLES]
    async with pg_engine.begin() as connection:
        await connection.execute(text(f'CREATE SCHEMA "{schema}"'))
        await connection.execute(text(f'SET search_path TO "{schema}"'))
        await connection.run_sync(Base.metadata.create_all, tables=tables)
    try:
        yield schema
    finally:
        async with pg_engine.begin() as connection:
            await connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))


async def _run(pg_engine, schema, statement, **params):
    async with pg_engine.begin() as connection:
        await connection.execute(text(f'SET search_path TO "{schema}"'))
        return await connection.execute(text(statement), params)


async def _scalar(pg_engine, schema, statement, **params):
    return (await _run(pg_engine, schema, statement, **params)).scalar_one()


async def _a_club(pg_engine, schema, name: str = "Zabłocie Sport") -> uuid.UUID:
    club_id = uuid.uuid4()
    await _run(
        pg_engine,
        schema,
        "INSERT INTO clubs (id, name, address_line, address_city, "
        "address_postal_code, address_country, latitude, longitude, timezone, "
        "price_multiplier_num, price_multiplier_den, slot_discount_num, "
        "slot_discount_den, version) VALUES (:i, :n, 'ul. Zabłocie 25', "
        "'Kraków', '30-701', 'PL', 50.048100, 19.958500, 'Europe/Warsaw', "
        "100, 100, 100, 100, 0)",
        i=club_id,
        n=name,
    )
    return club_id


async def _open_policy(pg_engine, schema, club_id, cap, valid_from=MONDAY):
    row_id = uuid.uuid4()
    await _run(
        pg_engine,
        schema,
        "INSERT INTO club_policies (id, club_id, window_minutes, "
        "join_cut_minutes, max_hold_age_minutes, prob_hold, rebooking_credit, "
        "free_cancel_hours, turnaround_minutes, counts_cash, valid_from, "
        "valid_to, changed_by) VALUES (:i, :c, 1440, 30, :m, false, false, "
        "NULL, 0, true, :f, NULL, 'system')",
        i=row_id,
        c=club_id,
        m=cap,
        f=valid_from,
    )
    return row_id


async def _open_payout(pg_engine, schema, club_id, iban):
    row_id = uuid.uuid4()
    await _run(
        pg_engine,
        schema,
        "INSERT INTO club_payout_destinations (id, club_id, account_holder, "
        "iban, valid_from, valid_to, changed_by) "
        "VALUES (:i, :c, 'Zabłocie Sport', :b, :f, NULL, 'system')",
        i=row_id,
        c=club_id,
        b=iban,
        f=MONDAY,
    )
    return row_id


async def _a_category(pg_engine, schema, club_id, name="Padel · Mondo, indoor"):
    category_id = uuid.uuid4()
    await _run(
        pg_engine,
        schema,
        "INSERT INTO club_court_categories (id, club_id, name, sport, "
        "rate_grosze, retired_at) VALUES (:i, :c, :n, 'PADEL', 12000, NULL)",
        i=category_id,
        c=club_id,
        n=name,
    )
    return category_id


async def _open_catalogue(pg_engine, schema, club_id, category_id, court_id, label):
    row_id = uuid.uuid4()
    await _run(
        pg_engine,
        schema,
        "INSERT INTO club_court_catalogue (id, club_id, court_id, category_id, "
        "label, valid_from, valid_to, changed_by) "
        "VALUES (:i, :c, :ct, :g, :l, :f, NULL, 'system')",
        i=row_id,
        c=club_id,
        ct=court_id,
        g=category_id,
        l=label,
        f=MONDAY,
    )
    return row_id


async def _close(pg_engine, schema, table, row_id, at=FRIDAY_1600):
    await _run(
        pg_engine,
        schema,
        f"UPDATE {table} SET valid_to = :t WHERE id = :i",
        t=at,
        i=row_id,
    )


async def _open_rows(pg_engine, schema, table, column, key):
    return await _scalar(
        pg_engine,
        schema,
        f"SELECT count(*) FROM {table} WHERE {column} = :k AND valid_to IS NULL",
        k=key,
    )


async def _drop_index(pg_engine, schema, name):
    """The negative control: the real index, removed by name."""

    await _run(pg_engine, schema, f'DROP INDEX "{name}"')


# --- the schema itself ------------------------------------------------------


async def test_every_declared_index_exists_on_postgresql(pg_engine, clubs_schema):
    """The declarations compile to real PostgreSQL DDL — which is not the same
    DDL they compile to on SQLite, and is what a migration will run."""

    found = set(
        (
            await _run(
                pg_engine,
                clubs_schema,
                "SELECT indexname FROM pg_indexes WHERE schemaname = :s",
                s=clubs_schema,
            )
        )
        .scalars()
        .all()
    )
    assert set(SERIES) <= found
    assert "uq_club_court_categories_live_name" in found


@pytest.mark.parametrize("name", sorted(SERIES))
async def test_each_series_index_is_unique_and_partial(pg_engine, clubs_schema, name):
    """Read back from the catalog, so *partial* is what PostgreSQL believes and
    not what the declaration said."""

    definition = await _scalar(
        pg_engine,
        clubs_schema,
        "SELECT indexdef FROM pg_indexes WHERE schemaname = :s AND indexname = :n",
        s=clubs_schema,
        n=name,
    )
    assert "CREATE UNIQUE INDEX" in definition, definition
    assert "WHERE (valid_to IS NULL)" in definition, definition


# --- series 1: the policy ---------------------------------------------------


async def test_a_second_open_policy_row_is_refused(pg_engine, clubs_schema):
    club = await _a_club(pg_engine, clubs_schema)
    await _open_policy(pg_engine, clubs_schema, club, 2880)

    with pytest.raises(IntegrityError) as exc:
        await _open_policy(pg_engine, clubs_schema, club, 360)

    assert getattr(exc.value.orig, "sqlstate", None) == UNIQUE_VIOLATION, (
        "the second open row was refused, but not by the partial unique index"
    )
    assert (
        await _open_rows(pg_engine, clubs_schema, "club_policies", "club_id", club)
        == 1
    )


async def test_without_the_index_a_second_open_policy_row_is_accepted(
    pg_engine, clubs_schema
):
    """The negative control. Without it, the case above would still pass if the
    predicate were wrong and no row ever qualified."""

    club = await _a_club(pg_engine, clubs_schema)
    await _drop_index(pg_engine, clubs_schema, "uq_club_policies_open_row")

    await _open_policy(pg_engine, clubs_schema, club, 2880)
    await _open_policy(pg_engine, clubs_schema, club, 360)

    assert (
        await _open_rows(pg_engine, clubs_schema, "club_policies", "club_id", club)
        == 2
    )


async def test_closing_the_open_policy_lets_the_next_version_open(
    pg_engine, clubs_schema
):
    """ADR-0077's scenario: 48 h on Monday, 6 h from Friday at 16:00, and the
    Monday answer still there."""

    club = await _a_club(pg_engine, clubs_schema)
    first = await _open_policy(pg_engine, clubs_schema, club, 2880)
    await _close(pg_engine, clubs_schema, "club_policies", first)
    await _open_policy(pg_engine, clubs_schema, club, 360, valid_from=FRIDAY_1600)

    assert (
        await _open_rows(pg_engine, clubs_schema, "club_policies", "club_id", club)
        == 1
    )
    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_policies WHERE club_id = :c",
            c=club,
        )
        == 2
    )
    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT max_hold_age_minutes FROM club_policies WHERE club_id = :c "
            "AND valid_from <= :t AND (valid_to IS NULL OR valid_to > :t)",
            c=club,
            t=MONDAY,
        )
        == 2880
    )


async def test_four_changes_leave_four_closed_rows_and_one_open(
    pg_engine, clubs_schema
):
    """The whole reason the index is partial: a club that has changed its hold
    cap four times has five rows carrying its id."""

    club = await _a_club(pg_engine, clubs_schema)
    opened = MONDAY
    for offset, cap in enumerate((2880, 1440, 360, 60)):
        row = await _open_policy(pg_engine, clubs_schema, club, cap, valid_from=opened)
        opened = FRIDAY_1600 + timedelta(days=offset)
        await _close(pg_engine, clubs_schema, "club_policies", row, at=opened)
    await _open_policy(pg_engine, clubs_schema, club, 0, valid_from=opened)

    assert (
        await _open_rows(pg_engine, clubs_schema, "club_policies", "club_id", club)
        == 1
    )
    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_policies WHERE club_id = :c",
            c=club,
        )
        == 5
    )


async def test_two_clubs_may_each_hold_an_open_policy(pg_engine, clubs_schema):
    first = await _a_club(pg_engine, clubs_schema, "Zabłocie Sport")
    second = await _a_club(pg_engine, clubs_schema, "Kortowo")

    await _open_policy(pg_engine, clubs_schema, first, 2880)
    await _open_policy(pg_engine, clubs_schema, second, 0)

    assert (
        await _open_rows(pg_engine, clubs_schema, "club_policies", "club_id", first)
        == 1
    )
    assert (
        await _open_rows(pg_engine, clubs_schema, "club_policies", "club_id", second)
        == 1
    )


async def test_a_zero_hold_cap_is_stored_apart_from_a_null_one(
    pg_engine, clubs_schema
):
    """*"`maxHoldAge = 0` means the club does not hold speculatively at all"* —
    which only means something if the column can tell it from *never stale*."""

    never_stale = await _a_club(pg_engine, clubs_schema, "Never stale")
    never_holds = await _a_club(pg_engine, clubs_schema, "Never holds")
    await _open_policy(pg_engine, clubs_schema, never_stale, None)
    await _open_policy(pg_engine, clubs_schema, never_holds, 0)

    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_policies WHERE max_hold_age_minutes IS NULL",
        )
        == 1
    )
    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_policies WHERE max_hold_age_minutes = 0",
        )
        == 1
    )


# --- series 2: the payout destination ---------------------------------------


async def test_a_second_open_payout_row_is_refused(pg_engine, clubs_schema):
    club = await _a_club(pg_engine, clubs_schema)
    await _open_payout(pg_engine, clubs_schema, club, "PL61109010140000071219812874")

    with pytest.raises(IntegrityError) as exc:
        await _open_payout(
            pg_engine, clubs_schema, club, "PL27114020040000300201355387"
        )

    assert getattr(exc.value.orig, "sqlstate", None) == UNIQUE_VIOLATION


async def test_without_the_index_a_second_open_payout_row_is_accepted(
    pg_engine, clubs_schema
):
    club = await _a_club(pg_engine, clubs_schema)
    await _drop_index(pg_engine, clubs_schema, "uq_club_payout_destinations_open_row")

    await _open_payout(pg_engine, clubs_schema, club, "PL61109010140000071219812874")
    await _open_payout(pg_engine, clubs_schema, club, "PL27114020040000300201355387")

    assert (
        await _open_rows(
            pg_engine, clubs_schema, "club_payout_destinations", "club_id", club
        )
        == 2
    )


async def test_the_payout_series_is_independent_of_the_policy_series(
    pg_engine, clubs_schema
):
    """A bank change is not buried under routine tuning, and vice versa."""

    club = await _a_club(pg_engine, clubs_schema)
    policy = await _open_policy(pg_engine, clubs_schema, club, 2880)
    await _open_payout(pg_engine, clubs_schema, club, "PL61109010140000071219812874")

    await _close(pg_engine, clubs_schema, "club_policies", policy)
    await _open_policy(pg_engine, clubs_schema, club, 360)

    assert (
        await _open_rows(
            pg_engine, clubs_schema, "club_payout_destinations", "club_id", club
        )
        == 1
    )
    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_payout_destinations WHERE club_id = :c",
            c=club,
        )
        == 1
    )


# --- series 3: the court catalogue ------------------------------------------


async def test_a_second_open_row_for_one_court_is_refused(pg_engine, clubs_schema):
    club = await _a_club(pg_engine, clubs_schema)
    category = await _a_category(pg_engine, clubs_schema, club)
    court = uuid.uuid4()
    await _open_catalogue(pg_engine, clubs_schema, club, category, court, "Court 1")

    with pytest.raises(IntegrityError) as exc:
        await _open_catalogue(
            pg_engine, clubs_schema, club, category, court, "Court 1"
        )

    assert getattr(exc.value.orig, "sqlstate", None) == UNIQUE_VIOLATION


async def test_without_the_index_a_second_open_court_row_is_accepted(
    pg_engine, clubs_schema
):
    club = await _a_club(pg_engine, clubs_schema)
    category = await _a_category(pg_engine, clubs_schema, club)
    court = uuid.uuid4()
    await _drop_index(pg_engine, clubs_schema, "uq_club_court_catalogue_open_row")

    await _open_catalogue(pg_engine, clubs_schema, club, category, court, "Court 1")
    await _open_catalogue(pg_engine, clubs_schema, club, category, court, "Court 1")

    assert (
        await _open_rows(
            pg_engine, clubs_schema, "club_court_catalogue", "court_id", court
        )
        == 2
    )


async def test_the_catalogue_index_is_keyed_on_the_court_not_the_club(
    pg_engine, clubs_schema
):
    """A club has many courts and each has its own series. Keyed on the club, one
    club could publish exactly one court — which is the mistake the other two
    indexes' shape invites."""

    club = await _a_club(pg_engine, clubs_schema)
    category = await _a_category(pg_engine, clubs_schema, club)

    for label in ("Court 1", "Court 2", "Court 3"):
        await _open_catalogue(
            pg_engine, clubs_schema, club, category, uuid.uuid4(), label
        )

    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_court_catalogue WHERE club_id = :c "
            "AND valid_to IS NULL",
            c=club,
        )
        == 3
    )


async def test_a_retired_court_frees_its_key_and_keeps_its_history(
    pg_engine, clubs_schema
):
    """Retired, never deleted — and the same court may come back."""

    club = await _a_club(pg_engine, clubs_schema)
    category = await _a_category(pg_engine, clubs_schema, club)
    court = uuid.uuid4()
    row = await _open_catalogue(
        pg_engine, clubs_schema, club, category, court, "Court 3"
    )

    await _close(pg_engine, clubs_schema, "club_court_catalogue", row)
    await _open_catalogue(pg_engine, clubs_schema, club, category, court, "Court 3")

    assert (
        await _open_rows(
            pg_engine, clubs_schema, "club_court_catalogue", "court_id", court
        )
        == 1
    )
    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_court_catalogue WHERE court_id = :c",
            c=court,
        )
        == 2
    )


# --- the category catalogue's own liveness ----------------------------------


async def test_two_live_categories_may_not_share_a_name(pg_engine, clubs_schema):
    club = await _a_club(pg_engine, clubs_schema)
    await _a_category(pg_engine, clubs_schema, club)

    with pytest.raises(IntegrityError) as exc:
        await _a_category(pg_engine, clubs_schema, club)

    assert getattr(exc.value.orig, "sqlstate", None) == UNIQUE_VIOLATION


async def test_a_retired_category_frees_its_name(pg_engine, clubs_schema):
    club = await _a_club(pg_engine, clubs_schema)
    category = await _a_category(pg_engine, clubs_schema, club)
    await _run(
        pg_engine,
        clubs_schema,
        "UPDATE club_court_categories SET retired_at = :t WHERE id = :i",
        t=FRIDAY_1600,
        i=category,
    )

    await _a_category(pg_engine, clubs_schema, club)

    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_court_categories WHERE club_id = :c",
            c=club,
        )
        == 2
    )


async def test_without_the_index_two_live_categories_may_share_a_name(
    pg_engine, clubs_schema
):
    club = await _a_club(pg_engine, clubs_schema)
    await _drop_index(pg_engine, clubs_schema, "uq_club_court_categories_live_name")

    await _a_category(pg_engine, clubs_schema, club)
    await _a_category(pg_engine, clubs_schema, club)

    assert (
        await _scalar(
            pg_engine,
            clubs_schema,
            "SELECT count(*) FROM club_court_categories WHERE club_id = :c",
            c=club,
        )
        == 2
    )
