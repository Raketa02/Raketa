#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the task-definition boot check.
#
#   bash .github/scripts/test-taskdef-boots.sh     # or: make test-taskdef
#
# check-taskdef-boots.sh was added in the same commit that made the task
# definition satisfy it, so on the committed tree it has never been seen to
# fail — the same reason test-poetry-pin-drift.sh, test-contract-drift.sh and
# .claude/hooks/test-hooks.sh exist. This drives it against each shape of
# disagreement it claims to catch and asserts it goes red.
#
# The case that matters most is `a new refusal the task definition has not caught
# up with`: it perturbs config.py rather than the task definition, and a check
# that had hard-coded its list of required variables would stay green through it.
# That is the claim the whole design rests on — the required set is derived by
# executing the authority, not copied out of it (#341).
#
# Every case perturbs a real file in place and restores the original bytes on
# exit — including on failure or interrupt — so it is safe to run on a dirty
# tree and preserves whatever was there.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-taskdef-boots.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"
TASKDEF="$ROOT/backend/deploy/ecs/taskdef.json"
CONFIG="$ROOT/backend/app/core/config.py"

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
  # The output is captured before it is searched rather than piped into grep:
  # `set -o pipefail` above makes a pipeline take the check's exit 1, so
  # `check | grep -q` would report a miss on every case that correctly went red.
  local needle="$1" name="$2" out
  out=$(bash "$CHECK" 2>&1)
  if printf '%s' "$out" | grep -qF "$needle"; then
    ok "$name"
  else
    bad "$name" "output never mentioned '$needle'"
  fi
}

for f in "$CHECK" "$CI_YML" "$TASKDEF" "$CONFIG"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d) || exit 2
cp "$TASKDEF" "$TMP/taskdef.json"
cp "$CONFIG" "$TMP/config.py"
restore() {
  cp "$TMP/taskdef.json" "$TASKDEF"
  cp "$TMP/config.py" "$CONFIG"
}
trap 'restore; rm -rf "$TMP"' EXIT INT TERM

# `secrets` and `environment` entries are one per line in the committed file, so
# a variable is dropped by deleting its line. Asserted rather than assumed: a
# reformatted task definition would otherwise silently stop being perturbed, and
# every case below would "pass" by testing nothing.
drop() { # <variable>
  if ! grep -q "\"$1\"" "$TASKDEF"; then
    printf '  FAIL  fixture: %s no longer names %s\n' "$TASKDEF" "$1"
    printf '        every case below would run against an unperturbed tree.\n'
    exit 2
  fi
  sed -i.bak "/\"$1\"/d" "$TASKDEF" && rm -f "$TASKDEF.bak"
  # Deleting the last entry of an array leaves a trailing comma behind it.
  python3 - "$TASKDEF" <<'PY'
import json, re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
text = re.sub(r",(\s*[\]}])", r"\1", text)
open(path, "w", encoding="utf-8").write(text)
json.load(open(path, encoding="utf-8"))
PY
}

# ---------------------------------------------------------------------------
echo
echo "check-taskdef-boots.sh — the committed tree"

expect_exit 0 "the task definition as committed boots"

# ---------------------------------------------------------------------------
echo
echo "a variable the application demands and the file does not supply"

# Exactly the #341 shape. The task definition selects production and supplies no
# REDIS_URL, so the container inherits docker-compose-local.yml's service name —
# a Redis that resolves on a laptop and nowhere else.
drop REDIS_URL
expect_exit 1 "a missing REDIS_URL is caught"
expect_says "REDIS_URL" "the failure names the missing variable"
expect_says "supplies no REDIS_URL" "the failure says the file supplies it nowhere"
restore

# The other two the same commit found. Both were as unbootable as the first and
# neither was in the ticket, which is the argument for booting the artifact
# rather than comparing two lists of names.
drop PHOTO_STORAGE_SECRET_KEY
expect_exit 1 "a missing PHOTO_STORAGE_SECRET_KEY is caught"
expect_says "PHOTO_STORAGE_SECRET_KEY" "the failure names it"
restore

drop ALLOW_ORIGINS
expect_exit 1 "an ALLOW_ORIGINS left to default to the wildcard is caught"
expect_says "ALLOW_ORIGINS" "the failure names it"
restore

# ---------------------------------------------------------------------------
echo
echo "a value the file supplies and the application rejects"

# Not a missing variable — a wrong one. The two need different edits, so the
# report has to tell them apart rather than saying 'add it' to somebody who
# already did.
sed -i.bak 's/{ "name": "DB_SSL_MODE", "value": "require" }/{ "name": "DB_SSL_MODE", "value": "disable" }/' "$TASKDEF" && rm -f "$TASKDEF.bak"
expect_exit 1 "an unencrypted DB_SSL_MODE is caught"
expect_says "Change the value" "a supplied-but-wrong variable is not reported as missing"
restore

# ---------------------------------------------------------------------------
echo
echo "a refusal the task definition has not caught up with"

# **The case this check exists for**, and the one that separates it from a list
# of names. config.py starts demanding a variable the task definition does not
# supply; nothing in .github/ or in scripts/ is edited. A check that had written
# its own copy of the required set would sail straight through this.
#
# EVENT_DELIVERY_BATCH_SIZE is chosen because it is a real setting with a real
# default that the task definition genuinely does not supply — so the perturbed
# config is a configuration the application could plausibly have grown.
sed -i.bak 's/if "REDIS_URL" not in provided:/if "EVENT_DELIVERY_BATCH_SIZE" not in provided:/' "$CONFIG" && rm -f "$CONFIG.bak"
sed -i.bak 's/f"REDIS_URL is not set, and APP_ENV selects/f"EVENT_DELIVERY_BATCH_SIZE is not set, and APP_ENV selects/' "$CONFIG" && rm -f "$CONFIG.bak"
expect_exit 1 "a newly required variable fails the build without editing this check"
expect_says "EVENT_DELIVERY_BATCH_SIZE" "the failure names the newly required variable"
restore

# ---------------------------------------------------------------------------
echo
echo "the ambient environment cannot make it pass"

# The failure mode that would make this check worthless on a developer's machine
# and, worse, worthless in a runner that happens to export one of these. What is
# asserted is what the *file* supplies, so a REDIS_URL in the process
# environment must not answer for one the task definition omits.
drop REDIS_URL
out=$(REDIS_URL="redis://someone-elses-shell:6379/0" bash "$CHECK" 2>&1)
got=$?
if [ "$got" = 1 ] && printf '%s' "$out" | grep -qF "REDIS_URL"; then
  ok "a variable in the caller's environment does not stand in for the file"
else
  bad "a variable in the caller's environment does not stand in for the file" \
      "want exit 1 naming REDIS_URL, got exit $got"
fi
restore

# ---------------------------------------------------------------------------
echo
echo "the check refuses rather than passing when it cannot run"

# A check that cannot find or read its subject must not report success.
printf '%s' "{ not json" > "$TASKDEF"
expect_exit 2 "an unparseable task definition is a usage error, not a pass"
restore

printf '%s' '{"containerDefinitions": []}' > "$TASKDEF"
expect_exit 2 "a task definition with no containers is a usage error, not a pass"
restore

expect_exit 0 "the tree is restored between cases"

# ---------------------------------------------------------------------------
echo
echo "CI wiring"

# The reason this suite exists at all: a check CI does not run is not a gate.
if grep -q 'check-taskdef-boots.sh' "$CI_YML"; then
  ok "ci.yml runs the check"
else
  bad "ci.yml runs the check" "no step invokes check-taskdef-boots.sh"
fi

if grep -q 'test-taskdef-boots.sh' "$CI_YML"; then
  ok "ci.yml runs this suite"
else
  bad "ci.yml runs this suite" "no step invokes test-taskdef-boots.sh"
fi

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
