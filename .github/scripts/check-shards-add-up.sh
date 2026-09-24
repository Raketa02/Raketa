#!/bin/bash
# ---------------------------------------------------------------------------
# The backend's test groups add up to the suite.
#
#   bash .github/scripts/check-shards-add-up.sh <directory of group reports>
#   make shards-add-up REPORTS=<directory>
#
# CI's backend tests are a matrix of groups (ADR-0181 §5, #489): each runner runs
# one group of `make test-group` and writes a JUnit report of the tests it ran.
# Splitting is how the suite stays fast as it grows, and it is also the one
# change to the gate that could make a green run test less — a group layout that
# drops a test, or deals one to two groups, is green for the tests it did run.
# So the union of the reports is held against the suite, collected once:
#
#   exit 0  every collected test ran, in exactly one group
#   exit 1  one did not — each test missing, run twice or never collected is named
#   exit 2  the check could not run: no reports, an unreadable one, or no
#           collection — never a pass
#
# The reading and the arithmetic are backend/scripts/shards_add_up.py, which
# collects through `make test` and splits nothing itself: the ids are compared
# on pytest's own terms, and a test that ran is whatever a group's report says.
# `make split-partition` from backend/ is the collection half of the same claim,
# and runs without a CI run to read.
#
# Tested by .github/scripts/test-shards-add-up.sh (`make test-shards-add-up`),
# which builds real group reports and deletes a test from one. A check that has
# never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

dir="${1:-}"
if [ -z "$dir" ] || [ $# -ne 1 ]; then
  echo "usage: check-shards-add-up.sh <directory of group reports>" >&2
  exit 2
fi
if [ ! -d "$dir" ]; then
  echo "No such directory: $dir — no reports, so no verdict." >&2
  exit 2
fi
dir=$(cd "$dir" && pwd)

shopt -s nullglob
reports=("$dir"/*.xml)
if [ ${#reports[@]} -eq 0 ]; then
  # Every group's artifact failed to arrive, or the directory is the wrong one.
  # Zero reports add up to nothing, and nothing is not the suite.
  echo "No group reports (*.xml) in $dir — nothing to add up, so no verdict." >&2
  exit 2
fi

cd "$ROOT/backend" || exit 2
poetry run python -m scripts.shards_add_up "${reports[@]}"
