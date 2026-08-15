#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the contract drift check.
#
#   bash .github/scripts/test-contract-drift.sh          # or: make test-drift
#
# Drives check-contract-drift.sh against a deliberately-stale tree and asserts
# it goes red, then against the committed tree and asserts it goes green. The
# point of a drift check is that it is watched, and a check that has never once
# failed is indistinguishable from one that cannot — the same reason
# .claude/hooks/test-hooks.sh exists for the guardrail hooks.
#
# The stale case is built the way the real one arrives: the CONTRACT is changed
# and the client is left alone. The check regenerates and the working tree stops
# matching HEAD, which is exactly the comparison CI makes on a pull request that
# commits a contract change without its client types.
#
# It perturbs backend/openapi.player.json in place and restores the original
# bytes from a temporary copy on exit — including on failure or interrupt — so
# it is safe to run on a dirty tree and preserves whatever was there.
#
# frontend_player is the only client exercised: frontend_club has no lockfile
# and no node_modules until #65, so its generator cannot run. The club's half of
# the check is asserted structurally below instead.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-contract-drift.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"
DOC="$ROOT/backend/openapi.player.json"
GEN="$ROOT/frontend_player/src/generated/schema.d.ts"
NEIGHBOUR="$ROOT/frontend_player/src/generated/README.md"

pass=0
fail=0

ok()   { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad()  { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

expect_exit() { # <want> <name> <command...>
  local want="$1" name="$2" got
  shift 2
  "$@" >/dev/null 2>&1
  got=$?
  [ "$got" = "$want" ] && ok "$name" || bad "$name" "want exit $want, got $got"
}

for f in "$CHECK" "$CI_YML" "$DOC" "$GEN" "$NEIGHBOUR"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d)
cp "$DOC" "$TMP/contract.json"
cp "$GEN" "$TMP/schema.d.ts"
cp "$NEIGHBOUR" "$TMP/README.md"
restore() {
  cp "$TMP/contract.json" "$DOC"
  cp "$TMP/schema.d.ts" "$GEN"
  cp "$TMP/README.md" "$NEIGHBOUR"
}
trap 'restore; rm -rf "$TMP"' EXIT INT TERM

# ---------------------------------------------------------------------------
echo
echo "check-contract-drift.sh — the committed tree"

expect_exit 0 "a contract and a client that agree pass" \
  bash "$CHECK" frontend_player
restore

expect_exit 2 "an app the check does not know is a usage error" \
  bash "$CHECK" frontend_nonesuch

# src/generated/ holds a hand-maintained README.md beside the generator's output.
# Scoping the diff to the directory rather than to the file `gen:api` writes
# reported an edit to that README as contract drift — a false failure, and the
# kind that teaches people to ignore the check. Found by this suite, kept here.
printf '\n<!-- drift probe -->\n' >>"$NEIGHBOUR"
expect_exit 0 "an edit beside the generated file is not drift" \
  bash "$CHECK" frontend_player
restore

# ---------------------------------------------------------------------------
echo
echo "check-contract-drift.sh — a contract change with a stale client"

# Add a schema the client has never generated. openapi-typescript emits every
# entry under components.schemas, referenced or not, so this is the smallest
# contract change that is guaranteed to move the generated output — and it
# leaves every existing path and schema untouched.
python3 - "$DOC" <<'PY'
import json, sys
path = sys.argv[1]
with open(path) as fh:
    doc = json.load(fh)
doc["components"]["schemas"]["DriftProbe"] = {
    "type": "object",
    "properties": {"probe": {"type": "string", "title": "Probe"}},
    "title": "DriftProbe",
}
with open(path, "w") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
PY

out=$(bash "$CHECK" frontend_player 2>&1)
got=$?

[ "$got" = 1 ] && ok "a contract change without a regenerated client fails" \
  || bad "a contract change without a regenerated client fails" "want exit 1, got $got"

grep -q 'frontend_player' <<<"$out" && ok "the failure names the app" \
  || bad "the failure names the app"

grep -q 'backend/openapi.player.json' <<<"$out" && ok "the failure names the contract document" \
  || bad "the failure names the contract document"

grep -q 'make gen-api' <<<"$out" && ok "the failure prints the command that fixes it" \
  || bad "the failure prints the command that fixes it"

grep -q 'DriftProbe' <<<"$out" && ok "the failure prints the diff it found" \
  || bad "the failure prints the diff it found"

restore

# The check must not leave the stale state behind as a pass on a second run.
expect_exit 0 "the restored tree passes again" \
  bash "$CHECK" frontend_player
restore

# ---------------------------------------------------------------------------
# The check firing is only half of it. It has to be REACHED — a drift step in a
# job that a backend-only pull request never runs is dormant in precisely the
# case it exists to catch.
# ---------------------------------------------------------------------------
echo
echo "ci.yml — the change that must trigger it"

filter_has() { # <filter> <pattern>
  python3 - "$CI_YML" "$1" "$2" <<'PY'
import re, sys
yml, want_filter, want_pattern = sys.argv[1], sys.argv[2], sys.argv[3]
lines = open(yml).read().splitlines()
start = next((i for i, l in enumerate(lines) if l.strip() == "filters: |"), None)
if start is None:
    sys.exit(1)
indent = len(lines[start]) - len(lines[start].lstrip())
block = []
for line in lines[start + 1:]:
    if line.strip() and (len(line) - len(line.lstrip())) <= indent:
        break
    block.append(line)
body = [l for l in block if l.strip()]
base = min(len(l) - len(l.lstrip()) for l in body) if body else 0
filters, current = {}, None
for line in body:
    text = line[base:]
    key = re.fullmatch(r"(\w+):", text.strip())
    if key and not text.lstrip().startswith("-"):
        current = key.group(1)
        filters[current] = []
    elif text.lstrip().startswith("-") and current:
        filters[current].append(text.lstrip()[1:].strip().strip("'\""))
sys.exit(0 if want_pattern in filters.get(want_filter, []) else 1)
PY
}

filter_has player 'backend/openapi.player.json' \
  && ok "the player filter watches the player contract document" \
  || bad "the player filter watches the player contract document" \
         "a backend-only pull request would not run the player job"

filter_has club 'backend/openapi.club.json' \
  && ok "the club filter watches the club contract document" \
  || bad "the club filter watches the club contract document" \
         "a backend-only pull request would not run the club job"

filter_has player 'frontend_player/**' \
  && ok "the player filter still watches the player app" \
  || bad "the player filter still watches the player app"

filter_has club 'frontend_club/**' \
  && ok "the club filter still watches the club app" \
  || bad "the club filter still watches the club app"

# ---------------------------------------------------------------------------
echo
echo "ci.yml — both jobs run it, and the club's stays behind its gate"

grep -q 'check-contract-drift.sh frontend_player' "$CI_YML" \
  && ok "the player job runs the check" \
  || bad "the player job runs the check"

grep -q 'check-contract-drift.sh frontend_club' "$CI_YML" \
  && ok "the club job runs the check" \
  || bad "the club job runs the check"

# The club app has never been installed (#65). Its drift step must live inside
# the job that already skips itself until a lockfile exists, not in a second job
# that would install it.
grep -q "needs.changes.outputs.club_ready == 'true'" "$CI_YML" \
  && ok "the club job is still gated on being bootstrapped" \
  || bad "the club job is still gated on being bootstrapped" \
         "this issue must not switch the club job on — that is #65"

# ---------------------------------------------------------------------------
echo
printf '\n  %s passed, %s failed\n\n' "$pass" "$fail"
[ "$fail" = 0 ]
