#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the two Postgres-only guarantees' gates.
#
#   bash scripts/test-postgres-gates.sh        # or: make test-pg-gates
#
# `tests/integration/` asserts two things SQLite cannot express: a reservation's
# overlapping-interval exclusion, and the partial unique index that keeps exactly
# one open row per club-policy series. Both assertions were written against a
# schema that already satisfied them — so on the day they landed, neither had
# ever been observed to fail, which is indistinguishable from not working.
#
# This drives each one against a schema with its constraint removed or subtly
# wrong and asserts the suite goes RED, then restores and asserts it goes GREEN
# again. It also drives the harness's own guard: a pipeline with no database must
# fail rather than skip, which is the failure mode #62 exists to remove.
#
# It edits `tests/integration/ddl.py` in place and restores it on exit —
# including on failure or interrupt — so it is safe on a dirty tree.
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
EXCLUSION_TESTS="tests/integration/test_interval_exclusion.py"
UNIQUE_TESTS="tests/integration/test_partial_unique_index.py"
GUARD_TESTS="tests/integration/test_harness_guard.py"
OUT=$(mktemp)
BACKUP=$(mktemp)

restore() { [ -f "$BACKUP" ] && cp "$BACKUP" "$DDL"; rm -f "$BACKUP" "$OUT"; }
trap restore EXIT INT TERM

for f in "$DDL" "$EXCLUSION_TESTS" "$UNIQUE_TESTS" "$GUARD_TESTS"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done
cp "$DDL" "$BACKUP"

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
mutate() {
  cp "$BACKUP" "$DDL"
  poetry run python - "$DDL" "$1" "$2" <<'PY'
import pathlib, sys
path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
p = pathlib.Path(path)
s = p.read_text()
if old not in s:
    sys.exit(f"mutation did not match — ddl.py has been rewritten: {old!r}")
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

# --- 3. restored -----------------------------------------------------------

cp "$BACKUP" "$DDL"
expect_green "restored: the integration suite is green again" tests/integration

# --- 4. the harness's own guard --------------------------------------------
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
