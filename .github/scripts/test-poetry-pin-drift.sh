#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the Poetry pin drift check.
#
#   bash .github/scripts/test-poetry-pin-drift.sh     # or: make test-poetry-pin
#
# check-poetry-pin-drift.sh was added to a tree that already satisfied it, so
# it has never been seen to fail — the same reason test-contract-drift.sh and
# .claude/hooks/test-hooks.sh exist. This drives it against each shape of drift
# it claims to catch and asserts it goes red, and against the committed tree and
# asserts it goes green.
#
# Every case perturbs a real file in place and restores the original bytes on
# exit — including on failure or interrupt — so it is safe to run on a dirty
# tree and preserves whatever was there.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-poetry-pin-drift.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"
LOCK="$ROOT/backend/poetry.lock"
DEV="$ROOT/backend/docker/api/Dockerfile.dev"
PROD="$ROOT/backend/docker/api/Dockerfile.prod"

pass=0
fail=0

ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

expect_exit() { # <want> <name>
  local want="$1" name="$2" got
  bash "$CHECK" >/dev/null 2>&1
  got=$?
  [ "$got" = "$want" ] && ok "$name" || bad "$name" "want exit $want, got $got"
}

expect_says() { # <needle> <name>
  # The check's output is captured before it is searched rather than piped into
  # grep: `set -o pipefail` above makes a pipeline take the check's exit 1, so
  # `check | grep -q` reports a miss on every case that correctly went red.
  local needle="$1" name="$2" out
  out=$(bash "$CHECK" 2>&1)
  if printf '%s' "$out" | grep -qF "$needle"; then
    ok "$name"
  else
    bad "$name" "output never mentioned '$needle'"
  fi
}

for f in "$CHECK" "$CI_YML" "$LOCK" "$DEV" "$PROD"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d)
cp "$LOCK" "$TMP/poetry.lock"
cp "$DEV" "$TMP/Dockerfile.dev"
cp "$PROD" "$TMP/Dockerfile.prod"
restore() {
  cp "$TMP/poetry.lock" "$LOCK"
  cp "$TMP/Dockerfile.dev" "$DEV"
  cp "$TMP/Dockerfile.prod" "$PROD"
}
trap 'restore; rm -rf "$TMP"' EXIT INT TERM

# ---------------------------------------------------------------------------
echo
echo "check-poetry-pin-drift.sh — the committed tree"

expect_exit 0 "pins that match the lock's writer pass"

# ---------------------------------------------------------------------------
echo
echo "a pin older than the Poetry that wrote the lock"

# Exactly the #153 shape: the lock is written by 2.1.3 and a build pins 1.8.3.
# Poetry itself only warns here and exits 0, so the build stays green — this is
# the case the check exists for.
sed -i.bak 's/poetry==2\.1\.3/poetry==1.8.3/' "$DEV" && rm -f "$DEV.bak"
expect_exit 1 "a pin two majors behind the lock is drift"
expect_says "Dockerfile.dev" "the failure names the file that is behind"
restore

# ---------------------------------------------------------------------------
echo
echo "pins that disagree with each other"

# The half-fix: one site bumped, the rest forgotten. Both pins here can read the
# lock, so only the agreement rule catches it.
sed -i.bak 's/poetry==2\.1\.3/poetry==2.2.0/' "$PROD" && rm -f "$PROD.bak"
expect_exit 1 "one site bumped and the others left behind is drift"
expect_says "Dockerfile.prod" "the failure names the file that disagrees"
restore

# ---------------------------------------------------------------------------
echo
echo "poetry export without the plugin on Poetry 2.x"

# Poetry 2.x unbundled `poetry export`. A pin that reads the lock fine still
# builds a stage that dies on "The command \"export\" does not exist".
sed -i.bak 's/ poetry-plugin-export==1\.10\.0//' "$DEV" && rm -f "$DEV.bak"
expect_exit 1 "2.x running 'poetry export' without the plugin is drift"
expect_says "poetry-plugin-export" "the failure names the missing plugin"
restore

# A file that does NOT run `poetry export` needs no plugin — the workflows
# install from the lock instead. If this ever goes red the rule has widened into
# a false failure, which is the kind that teaches people to ignore the check.
expect_exit 0 "a site that never exports is not asked for the plugin"

# ---------------------------------------------------------------------------
echo
echo "the check refuses rather than passing when it cannot run"

# A check that cannot find its subject must not report success. Both of these
# would silently "pass" if the script treated an empty read as agreement.
sed -i.bak '1s/.*/# nothing useful here/' "$LOCK" && rm -f "$LOCK.bak"
expect_exit 2 "an unreadable lock header is a usage error, not a pass"
restore

expect_exit 0 "the tree is restored between cases"

# ---------------------------------------------------------------------------
echo
echo "CI wiring"

# The reason this suite exists at all: a check CI does not run is not a gate.
if grep -q 'check-poetry-pin-drift.sh' "$CI_YML"; then
  ok "ci.yml runs the check"
else
  bad "ci.yml runs the check" "no step invokes check-poetry-pin-drift.sh"
fi

# The backend filter has to watch the lock and the workflows, or the check is
# dormant in precisely the pull request that moves a pin.
if grep -q "'.github/workflows/ci.yml'" "$CI_YML"; then
  ok "the backend filter watches the workflow itself"
else
  bad "the backend filter watches the workflow itself"
fi

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
