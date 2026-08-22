#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the two Postgres-only guarantees' gates.
#
#   bash scripts/test-postgres-gates.sh        # or: make test-pg-gates
#
# `tests/integration/` asserts things SQLite cannot express: a reservation's
# overlapping-interval exclusion, and the partial unique indexes that keep exactly
# one open row per club series. Each assertion was written against a schema that
# already satisfied it — so on the day it landed it had never been observed to
# fail, which is indistinguishable from not working.
#
# This drives each one against a schema with its constraint removed or subtly
# wrong and asserts the suite goes RED, then restores and asserts it goes GREEN
# again. It also drives the harness's own guard: a pipeline with no database must
# fail rather than skip, which is the failure mode #62 exists to remove.
#
# **Three files are mutated**, and the difference matters. `tests/integration/ddl.py`
# is the shape harness #62 landed — throwaway tables, with no application code
# behind them. `app/modules/clubs/infrastructure/sqlalchemy_club_models.py` and
# `app/modules/courts/infrastructure/sqlalchemy_court_models.py` are the real
# declarations the Clubs and Courts tables are created from, so a mutation against
# either breaks the schema the application maps to, which is the stronger
# statement (#64, #65).
#
# All three are edited in place and restored on exit — including on failure or
# interrupt — so it is safe on a dirty tree.
#
# Not part of `make check`, for the same reason `make test-gates`,
# `make test-hooks` and `make test-drift` are not: it shells out to the very
# tools `check` runs, and a gate suite belongs where a gate suite is looked at —
# CI, and after a change to a gate. The backend CI job runs it.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
cd "$ROOT" || exit 2

DDL="tests/integration/ddl.py"
CLUB_MODELS="app/modules/clubs/infrastructure/sqlalchemy_club_models.py"
COURT_MODELS="app/modules/courts/infrastructure/sqlalchemy_court_models.py"
EXCLUSION_TESTS="tests/integration/test_interval_exclusion.py"
UNIQUE_TESTS="tests/integration/test_partial_unique_index.py"
CLUB_TESTS="tests/integration/test_club_series.py"
COURT_TESTS="tests/integration/test_reservation_exclusion.py"
DRIFT_TESTS="tests/unit/test_clubs_migration.py"
COURT_DRIFT_TESTS="tests/unit/test_courts_migration.py"
GUARD_TESTS="tests/integration/test_harness_guard.py"
OUT=$(mktemp)
DDL_BACKUP=$(mktemp)
CLUB_BACKUP=$(mktemp)
COURT_BACKUP=$(mktemp)

restore() {
  [ -s "$DDL_BACKUP" ] && cp "$DDL_BACKUP" "$DDL"
  [ -s "$CLUB_BACKUP" ] && cp "$CLUB_BACKUP" "$CLUB_MODELS"
  [ -s "$COURT_BACKUP" ] && cp "$COURT_BACKUP" "$COURT_MODELS"
  rm -f "$DDL_BACKUP" "$CLUB_BACKUP" "$COURT_BACKUP" "$OUT"
}
trap restore EXIT INT TERM

for f in "$DDL" "$CLUB_MODELS" "$COURT_MODELS" "$EXCLUSION_TESTS" "$UNIQUE_TESTS" \
         "$CLUB_TESTS" "$COURT_TESTS" "$DRIFT_TESTS" "$COURT_DRIFT_TESTS" \
         "$GUARD_TESTS"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done
cp "$DDL" "$DDL_BACKUP"
cp "$CLUB_MODELS" "$CLUB_BACKUP"
cp "$COURT_MODELS" "$COURT_BACKUP"

pass=0
fail=0

# A gate suite that ran against no database would itself be the silent skip it
# exists to catch, so it refuses to pretend. Same rule as the harness: loud in
# CI, quiet on a laptop.
poetry run python -c "
import sys
sys.path.insert(0, '.')
from tests.integration.postgres import resolve_url, running_in_ci
sys.exit(0 if resolve_url() else (2 if running_in_ci() else 1))
"
case $? in
  0) ;;
  2) echo "FAIL  CI is set but no Postgres URL is resolvable — cannot prove these gates fire"
     exit 1 ;;
  *) echo "SKIP  no Postgres reachable; set POSTGRES_TEST_URL to run these gates, e.g."
     echo "      POSTGRES_TEST_URL=postgresql+asyncpg://raketa_user:raketa_pwd@localhost:5432/raketa"
     exit 0 ;;
esac

# --- helpers ---------------------------------------------------------------

run_pytest() { poetry run pytest -q --no-cov -p no:cacheprovider "$@" >"$OUT" 2>&1; }

expect_red() {
  local label="$1"; shift
  if run_pytest "$@"; then
    echo "FAIL  $label — stayed GREEN with the constraint broken"
    tail -3 "$OUT"
    fail=$((fail + 1))
  else
    echo "ok    $label — RED, as it must be"
    pass=$((pass + 1))
  fi
}

expect_green() {
  local label="$1"; shift
  if run_pytest "$@"; then
    echo "ok    $label"
    pass=$((pass + 1))
  else
    echo "FAIL  $label — expected GREEN"
    tail -15 "$OUT"
    fail=$((fail + 1))
  fi
}

# mutate <old> <new> — always from the pristine backup, so mutations never stack.
mutate() { edit "$DDL" "$DDL_BACKUP" "$1" "$2"; }

# mutate_club <old> <new> — the same, against the real Clubs declarations.
mutate_club() { edit "$CLUB_MODELS" "$CLUB_BACKUP" "$1" "$2"; }

# mutate_court <old> <new> — the same, against the real Courts declarations.
mutate_court() { edit "$COURT_MODELS" "$COURT_BACKUP" "$1" "$2"; }

edit() {
  cp "$2" "$1"
  poetry run python - "$1" "$3" "$4" <<'PY'
import pathlib, sys
path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path)
s = p.read_text()
if old not in s:
    sys.exit(f"mutation did not match — {path} has been rewritten: {old!r}")
p.write_text(s.replace(old, new, 1))
PY
  return $?
}

# --- 0. the control --------------------------------------------------------

expect_green "control: the integration suite is green unmutated" tests/integration

# --- 1. the interval exclusion ---------------------------------------------

# Gone entirely: `constrained=True` now builds the table the negative control
# builds, so the two arms of every pair are the same table.
mutate $'        if constrained\n' $'        if False\n' &&
  expect_red "the exclusion constraint removed" "$EXCLUSION_TESTS"

# Present but meaning something else, which is the likelier defect: `-|-` is
# *adjacent*, not *overlapping*, so back-to-back reservations collide and
# overlapping ones do not.
mutate 'during WITH &&' 'during WITH -|-' &&
  expect_red "the exclusion testing adjacency instead of overlap" "$EXCLUSION_TESTS"

# No longer keyed on the court, so one club sells one hour a day.
mutate 'court_id WITH =, during WITH &&' 'during WITH &&' &&
  expect_red "the exclusion no longer keyed on the court" "$EXCLUSION_TESTS"

# --- 2. the partial unique index -------------------------------------------

mutate '"UNIQUE " if constrained else ""' '"" if constrained else ""' &&
  expect_red "the partial unique index made non-unique" "$UNIQUE_TESTS"

# Unique but not partial: the closed rows are history and history repeats, so a
# club that has changed its policy twice cannot open a third version.
mutate ' WHERE closed_at IS NULL' '' &&
  expect_red "the unique index no longer partial" "$UNIQUE_TESTS"

# Partial on the wrong side: it covers the closed rows instead of the open one,
# so two open rows are accepted and history is refused.
mutate 'WHERE closed_at IS NULL' 'WHERE closed_at IS NOT NULL' &&
  expect_red "the partial index covering the closed rows, not the open one" \
    "$UNIQUE_TESTS"

# --- 3. the Clubs series, on the real declarations -------------------------
# These edit `sqlalchemy_club_models.py`, which is what `Base.metadata` builds the
# Clubs tables from — so a mutation here is the application's own schema being
# wrong, not a copy of it. Each also reddens the migration-drift test, which is
# that test's point: the two descriptions of one schema cannot move apart
# silently, in either direction.

mutate_club 'unique=True,' 'unique=False,' &&
  expect_red "the club series index made non-unique" "$CLUB_TESTS" "$DRIFT_TESTS"

# Unique but not partial: history repeats, so a club that has changed its policy
# twice cannot open a third version.
mutate_club $'        postgresql_where=sa.text(where),\n        sqlite_where=sa.text(where),\n' '' &&
  expect_red "the club series index no longer partial" "$CLUB_TESTS" "$DRIFT_TESTS"

# Partial on the wrong side: it covers the closed rows instead of the open one.
mutate_club 'OPEN_ROW = "valid_to IS NULL"' 'OPEN_ROW = "valid_to IS NOT NULL"' &&
  expect_red "the club series index covering the closed rows" "$CLUB_TESTS" \
    "$DRIFT_TESTS"

# The catalogue keyed on the club rather than the court, so a club could publish
# exactly one court.
mutate_club $'    ClubCourtCatalogueORM.court_id,\n' $'    ClubCourtCatalogueORM.club_id,\n' &&
  expect_red "the catalogue index keyed on the club, not the court" "$CLUB_TESTS" \
    "$DRIFT_TESTS"

# The category's liveness index made whole-table, so a retired name can never be
# used again.
mutate_club 'LIVE_CATEGORY = "retired_at IS NULL"' 'LIVE_CATEGORY = "1 = 1"' &&
  expect_red "the category name index no longer keyed on liveness" "$CLUB_TESTS" \
    "$DRIFT_TESTS"

# --- 4. the reservation exclusion, on the real declarations ----------------
# ADR-0035's constraint, and the reason `sqlalchemy_court_models.py` assembles it
# from four named constants rather than writing one literal: four separate
# properties are load-bearing, and each has to be breakable **on its own** for
# these to mean anything. Each also reddens the Courts migration-drift test,
# which compares the two copies of the string and then asserts what the string
# *says* — two files agreeing on the wrong constraint is the one thing a
# comparison between them cannot catch.

# Gone entirely. The table is created and nothing stops a court being sold twice
# — C1's defect, restored: expensive, silent and terminal.
mutate_court $'sa.event.listen(\n    ReservationORM.__table__,\n    "after_create",\n    sa.DDL(RESERVATION_EXCLUSION_DDL).execute_if(dialect="postgresql"),\n)' '' &&
  expect_red "the reservation exclusion constraint removed" "$COURT_TESTS"

# Testing adjacency rather than overlap, which is the same constraint meaning the
# opposite thing: back-to-back claims would collide and overlapping ones would
# not.
mutate_court 'OVERLAPS = "WITH &&"' 'OVERLAPS = "WITH -|-"' &&
  expect_red "the reservation exclusion testing adjacency instead of overlap" \
    "$COURT_TESTS" "$COURT_DRIFT_TESTS"

# No longer keyed on the court, so one club sells one hour a day site-wide.
mutate_court 'ONE_COURT = "court_id WITH ="' 'ONE_COURT = "TRUE WITH ="' &&
  expect_red "the reservation exclusion no longer keyed on the court" \
    "$COURT_TESTS" "$COURT_DRIFT_TESTS"

# Closed at both ends: a court freed at 19:00 could no longer be taken at 19:00,
# so every back-to-back booking in the product would be refused — and
# `turnaroundMin` would stop being expressible as padding.
mutate_court 'RANGE_BOUNDS = "[)"' 'RANGE_BOUNDS = "[]"' &&
  expect_red "the claimed range closed at both ends" "$COURT_TESTS" \
    "$COURT_DRIFT_TESTS"

# No longer partial: a released claim keeps blocking the court for ever, so a
# withdrawn hold takes the slot out of inventory permanently.
mutate_court 'LIVE_CLAIM = "released_at IS NULL"' 'LIVE_CLAIM = "1 = 1"' &&
  expect_red "the reservation exclusion no longer partial over live claims" \
    "$COURT_TESTS" "$COURT_DRIFT_TESTS"

# The `btree_gist` extension not created: `court_id WITH =` has no operator class
# without it, so the constraint cannot be built at all on a fresh database.
mutate_court 'BTREE_GIST_DDL = "CREATE EXTENSION IF NOT EXISTS btree_gist"' \
  'BTREE_GIST_DDL = "SELECT 1"' &&
  expect_red "btree_gist no longer created with the table" "$COURT_DRIFT_TESTS"

# --- 5. restored -----------------------------------------------------------

cp "$DDL_BACKUP" "$DDL"
cp "$CLUB_BACKUP" "$CLUB_MODELS"
cp "$COURT_BACKUP" "$COURT_MODELS"
expect_green "restored: the integration suite is green again" tests/integration \
  "$DRIFT_TESTS" "$COURT_DRIFT_TESTS"

# --- 6. the harness's own guard --------------------------------------------
# The rule is: a pipeline with no database fails, a laptop with no database
# skips. `test_harness_guard.py` asserts the *inputs* to that decision; this
# drives the decision itself, as real pytest runs with every URL variable
# unset.

blind() { env -u POSTGRES_TEST_URL -u WRITER_DB_URL -u EVENT_TEST_DATABASE_URL "$@"; }

if blind CI=true poetry run pytest -q --no-cov -p no:cacheprovider \
     "$EXCLUSION_TESTS" >"$OUT" 2>&1; then
  echo "FAIL  CI with no database stayed GREEN — the guarantee would go unenforced"
  fail=$((fail + 1))
elif grep -q "no Postgres URL was resolvable" "$OUT"; then
  echo "ok    CI with no database FAILS, naming the reason"
  pass=$((pass + 1))
else
  echo "FAIL  CI with no database went red, but not for the guard's reason"
  tail -15 "$OUT"
  fail=$((fail + 1))
fi

if blind -u CI poetry run pytest -q --no-cov -p no:cacheprovider \
     "$EXCLUSION_TESTS" >"$OUT" 2>&1 && grep -q "skipped" "$OUT"; then
  echo "ok    a laptop with no database SKIPS rather than stopping the run"
  pass=$((pass + 1))
else
  echo "FAIL  a laptop with no database should skip, not stop the run"
  tail -15 "$OUT"
  fail=$((fail + 1))
fi

# The guard's own cases need no database and must run everywhere — on a laptop
# with no Docker, on every `make check`. If they ever start needing one, the
# guard has stopped being checkable in the place it is meant to protect.
if blind -u CI poetry run pytest -q --no-cov -p no:cacheprovider \
     "$GUARD_TESTS" >"$OUT" 2>&1 && ! grep -q "skipped" "$OUT"; then
  echo "ok    the guard's own cases run with no database and skip nothing"
  pass=$((pass + 1))
else
  echo "FAIL  the guard's own cases did not run without a database"
  tail -15 "$OUT"
  fail=$((fail + 1))
fi

# ---------------------------------------------------------------------------

echo
echo "$pass passed, $fail failed"
[ "$fail" -eq 0 ] || exit 1
