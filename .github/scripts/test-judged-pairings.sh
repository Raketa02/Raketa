#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the judged-pairings check.
#
#   bash .github/scripts/test-judged-pairings.sh     # or: make test-judged-pairings
#
# check-judged-pairings.sh was added to a tree that already satisfied it, so it
# has never been seen to fail — the same reason test-contract-drift.sh,
# test-poetry-pin-drift.sh and .claude/hooks/test-hooks.sh exist. This drives it
# against each shape of failure it claims to catch and asserts it goes red, and
# against the committed tree and asserts it goes green.
#
# The two halves are tested apart, because they fail for different reasons and a
# suite that only ever broke the fixture would leave the floor's re-derivation —
# the half a diff cannot do — unexercised:
#
#   · DRIFT      a generated table, or an input the tables are derived from,
#                no longer reproduces
#   · THE FLOOR  QUALITY_FLOOR has left max(Fit | not shown) < floor <=
#                min(Fit | shown), from either side
#
# Every case perturbs a real file in place and restores the original bytes on
# exit — including on failure or interrupt — so it is safe to run on a dirty
# tree and preserves whatever was there. It needs no git: the check compares a
# file against what regenerating it produces, never against HEAD.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-judged-pairings.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"
SPECS="$ROOT/docs/specs/matchmaking"
FIXTURE="$SPECS/judged-pairings.json"
JUDGED="$SPECS/the-judged-pairings.md"
WEIGHTS="$SPECS/ranking-weights.md"

pass=0
fail=0

ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

# The check is run ONCE per perturbation and its output and exit code are held
# here, because the check REPAIRS what it finds: a second invocation would see a
# regenerated tree, exit 0 and say nothing, and every assertion about the
# failure message would miss for the wrong reason.
OUT=""
CODE=0

run_check() {
  # Captured rather than piped into grep: `set -o pipefail` above makes a
  # pipeline take the check's exit 1, so `check | grep -q` would report a miss
  # on every case that correctly went red.
  OUT=$(bash "$CHECK" 2>&1)
  CODE=$?
}

had_exit() { # <want> <name>
  [ "$CODE" = "$1" ] && ok "$2" || bad "$2" "want exit $1, got $CODE"
}

said() { # <needle> <name>
  if printf '%s' "$OUT" | grep -qF "$1"; then
    ok "$2"
  else
    bad "$2" "output never mentioned '$1'"
  fi
}

expect_exit() { # <want> <name>
  run_check
  had_exit "$1" "$2"
}

# `jq` is not assumed — CI's backend job has Python and nothing else guaranteed.
edit_fixture() { # <python expression over `data`>
  python3 - "$FIXTURE" "$1" <<'PY'
import json, sys
path, program = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding="utf-8"))
exec(program)
with open(path, "w", encoding="utf-8") as out:
    json.dump(data, out, indent=2, ensure_ascii=False)
    out.write("\n")
PY
}

for f in "$CHECK" "$CI_YML" "$FIXTURE" "$JUDGED" "$WEIGHTS"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d)
cp "$FIXTURE" "$TMP/judged-pairings.json"
cp "$JUDGED" "$TMP/the-judged-pairings.md"
cp "$WEIGHTS" "$TMP/ranking-weights.md"
restore() {
  cp "$TMP/judged-pairings.json" "$FIXTURE"
  cp "$TMP/the-judged-pairings.md" "$JUDGED"
  cp "$TMP/ranking-weights.md" "$WEIGHTS"
}
trap 'restore; rm -rf "$TMP"' EXIT INT TERM

by_id() { printf 'next(c for c in data["cases"] if c["id"] == "%s")' "$1"; }

# ---------------------------------------------------------------------------
echo
echo "check-judged-pairings.sh — the committed tree"

expect_exit 0 "the six reproduce from the fixture"

# ---------------------------------------------------------------------------
echo
echo "a hand-edited generated table"

# The case the generate-commit-diff idiom exists for: somebody corrects a number
# in the document instead of in the ruleset. Nothing about the engine changed,
# so only regeneration catches it.
sed -i.bak 's/\*\*82\.0\*\*/**83.0**/' "$JUDGED" && rm -f "$JUDGED.bak"
run_check
had_exit 1 "a table edited by hand is drift"
said "JUDGED-PAIRINGS DRIFT" "the failure names the drift"
said "the-judged-pairings.md" "the failure names the file that did not reproduce"
said "git add" "the failure says what to run"
said "argued for in the pull request" "the failure says a diff here is a design change"
restore

# `ranking-weights.md` §10 is generated from the same fixture and is the table
# the floor's integer is read off. It has its own marker, so it has its own case.
sed -i.bak 's/| 44\.5 | 47\.8 |/| 45.5 | 47.8 |/' "$WEIGHTS" && rm -f "$WEIGHTS.bak"
expect_exit 1 "ranking-weights.md §10 edited by hand is drift"
restore

# ---------------------------------------------------------------------------
echo
echo "a deliberately broken fixture"

# An INPUT moved — the median stranger is suddenly half a point away. Every
# derived half of the fixture and both documents must move with it, and this is
# the shape a real ruleset or formula change takes.
edit_fixture "$(by_id 5)['candidate']['mu'] = 3.4"
expect_exit 1 "an input nobody regenerated is drift"
restore

# A DERIVED half hand-typed to a number the ruleset does not produce. This is
# the failure ADR-0122 is about: fitting readings to a remembered total.
edit_fixture "$(by_id 1)['readings']['comp']['fit'] = 78.4"
expect_exit 1 "a reading fitted to a remembered total is drift"
restore

# ---------------------------------------------------------------------------
echo
echo "the floor's re-derivation, from both sides"

# `ranking-weights.md` §11: turning a term on is a ruleset release that re-runs
# the six cases and may move the floor. Both directions are failures and they
# are different failures, so both are named.
edit_fixture "$(by_id "3′-fun")['verdict'] = 'shown'"
run_check
had_exit 1 "a floor that now hides a case judged shown fails"
said "hides a case judged shown" "the failure names which side broke"
said "QUALITY FLOOR" "the failure says it is the floor and not a table"
said "land as an ADR" "the failure says what moving a verdict costs"
restore

edit_fixture "$(by_id 5)['verdict'] = 'not_shown'"
run_check
had_exit 1 "a floor that now shows a case judged hidden fails"
said "shows a case judged hidden" "the failure names the other side"
restore

# The bound is read across a split, and a fixture with nothing on one side of it
# bounds nothing at all. Reporting that as a pass is the exact shape of failure
# this whole machine exists to refuse.
edit_fixture "[c.__setitem__('verdict', 'shown') for c in data['cases']]"
expect_exit 2 "a fixture with nothing hidden refuses rather than passing"
restore

# ---------------------------------------------------------------------------
echo
echo "the check refuses rather than passing when it cannot run"

# A generated region whose marker somebody deleted is a region that silently
# stops being regenerated — which reads as a table that always reproduces.
sed -i.bak 's/<!-- generated: judged-readings/<!-- judged-readings/' "$JUDGED" && rm -f "$JUDGED.bak"
expect_exit 2 "a document with no marker is a usage error, not a pass"
restore

mv "$FIXTURE" "$TMP/moved.json"
expect_exit 2 "a fixture that has moved is a usage error, not a pass"
mv "$TMP/moved.json" "$FIXTURE"

expect_exit 0 "the tree is restored between cases"

# ---------------------------------------------------------------------------
echo
echo "CI wiring"

# The reason this suite exists at all: a check CI does not run is not a gate.
if grep -q 'check-judged-pairings.sh' "$CI_YML"; then
  ok "ci.yml runs the check"
else
  bad "ci.yml runs the check" "no step invokes check-judged-pairings.sh"
fi

# The backend filter has to watch the specs the tables live in, or the check is
# dormant in precisely the pull request that hand-edits one.
if grep -q "'docs/specs/matchmaking/\*\*'" "$CI_YML"; then
  ok "the backend filter watches the matchmaking specs"
else
  bad "the backend filter watches the matchmaking specs"
fi

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
