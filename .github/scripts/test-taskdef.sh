#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the task-definition check.
#
#   bash .github/scripts/test-taskdef.sh     # or: make test-taskdef
#
# Each of check-taskdef.sh's rules was added in the same commit that made the
# task definition satisfy it, so on the committed tree neither has been seen to
# fail — the same reason test-poetry-pin-drift.sh, test-contract-drift.sh and
# .claude/hooks/test-hooks.sh exist. This drives it against each shape of
# disagreement it claims to catch and asserts it goes red.
#
# Two cases matter more than the rest, and both perturb the **application**
# rather than the task definition — a check that had copied out its own list or
# its own number would stay green through either:
#
#   * a new refusal in config.py that the task definition does not satisfy (#341)
#   * a --graceful-timeout in startup.prod.sh raised past the kill deadline (#345)
#
# That is the claim the whole design rests on: both rules are derived by
# executing the application, not restated from it.
#
# Every case perturbs a real file in place and restores the original bytes on
# exit — including on failure or interrupt — so it is safe to run on a dirty
# tree and preserves whatever was there.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-taskdef.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"
TASKDEF="$ROOT/backend/deploy/ecs/taskdef.json"
CONFIG="$ROOT/backend/app/core/config.py"
STARTUP="$ROOT/backend/docker/api/startup.prod.sh"

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

for f in "$CHECK" "$CI_YML" "$TASKDEF" "$CONFIG" "$STARTUP"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d) || exit 2
cp "$TASKDEF" "$TMP/taskdef.json"
cp "$CONFIG" "$TMP/config.py"
cp "$STARTUP" "$TMP/startup.prod.sh"
restore() {
  cp "$TMP/taskdef.json" "$TASKDEF"
  cp "$TMP/config.py" "$CONFIG"
  cp "$TMP/startup.prod.sh" "$STARTUP"
}
trap 'restore; rm -rf "$TMP"' EXIT INT TERM

# `secrets` and `environment` entries are one per line in the committed file, so
# a variable is dropped by deleting its line. Asserted rather than assumed: a
# reformatted task definition would otherwise silently stop being perturbed, and
# every case below would "pass" by testing nothing.
# Deleting a line from a JSON array leaves a trailing comma behind whatever was
# last. Written once because both perturbations below delete a line, and a second
# copy is a second thing to keep in step.
reflow() {
  python3 - "$TASKDEF" <<'PY'
import json, re, sys
path = sys.argv[1]
text = open(path, encoding="utf-8").read()
open(path, "w", encoding="utf-8").write(re.sub(r",(\s*[\]}])", r"\1", text))
json.load(open(path, encoding="utf-8"))
PY
}

# A fixture miss stops the run rather than counting one failure and going on:
# every case after it would test an unperturbed tree and report green.
require_line() { # <needle>
  grep -q "$1" "$TASKDEF" && return 0
  printf '  FAIL  fixture: %s no longer contains %s\n' "$TASKDEF" "$1"
  printf '        every case below would run against an unperturbed tree.\n'
  exit 2
}

drop() { # <variable>
  require_line "\"$1\""
  sed -i.bak "/\"$1\"/d" "$TASKDEF" && rm -f "$TASKDEF.bak"
  reflow
}

# ---------------------------------------------------------------------------
echo
echo "check-taskdef.sh — the committed tree"

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
echo "the container's kill deadline against the application's drain"

# The #345 shape. `stopTimeout` unset does not mean "no deadline": Fargate
# supplies 30, which is exactly gunicorn's graceful timeout, so the agent's
# SIGKILL lands on the same second the master would have force-killed its
# stragglers. Removing the key must read as the dead heat it is.
drop stopTimeout
expect_exit 1 "an unset stopTimeout is a dead heat, not an absent deadline"
expect_says "stopTimeout" "the failure names the setting"
expect_says "30" "the failure names the default it would inherit"
restore

# The half the ticket argues against: raising the graceful timeout to meet a
# drain window rather than moving the deadline. Nothing in the task definition
# is touched here — a check that only read that file would sail through it.
sed -i.bak 's/--graceful-timeout 30/--graceful-timeout 60/' "$STARTUP" && rm -f "$STARTUP.bak"
expect_exit 1 "a graceful timeout raised past the kill deadline is caught"
expect_says "60" "the failure names the application's own number"
restore

# Fargate's documented ceiling. RegisterTaskDefinition rejects this at deploy
# time, which is a slow way to find out.
sed -i.bak 's/"stopTimeout": [0-9]*/"stopTimeout": 200/' "$TASKDEF" && rm -f "$TASKDEF.bak"
expect_exit 1 "a stopTimeout past Fargate's 120-second ceiling is caught"
expect_says "120" "the failure names the ceiling"
restore

# The entrypoint documents this flag in a paragraph directly above it, so the
# number is read from live lines only. A false red here would be the check
# quoting its own documentation back as configuration.
printf '%s\n' '# --graceful-timeout 90 would be wrong, and this line is not configuration' >> "$STARTUP"
expect_exit 0 "a comment mentioning the flag is not read as the flag"
restore

expect_exit 0 "the tree is restored between cases"

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

# The half that reads the *application*. If the flag moves or the entrypoint is
# rewritten, the check has lost the number it compares against — and the one
# thing it must not do then is report that the deadline is fine.
sed -i.bak 's/--graceful-timeout 30 \\//' "$STARTUP" && rm -f "$STARTUP.bak"
expect_exit 2 "an entrypoint with no --graceful-timeout is a usage error, not a pass"
expect_says "graceful-timeout" "the failure says which number it could not find"
restore

# Two live invocations with different numbers: which one the container gets
# depends on which gunicorn runs, and the check must not pick one.
printf '%s\n' 'exec gunicorn app.main:app --graceful-timeout 45' >> "$STARTUP"
expect_exit 2 "two different --graceful-timeout values are a usage error, not a pass"
expect_says "more than once" "the failure says why it will not guess"
restore

# The drain rule is about the process this repository builds. A task definition
# whose containers all carry somebody else's image gives the check nothing to
# hold to gunicorn's number, and it says so rather than asserting anyway.
sed -i.bak 's|"image": "__IMAGE__"|"image": "public.ecr.aws/somebody/else:1"|' "$TASKDEF" && rm -f "$TASKDEF.bak"
expect_exit 2 "a task definition this repository does not build is a usage error, not a pass"
expect_says "__IMAGE__" "the failure names the marker it looked for"
restore

expect_exit 0 "the tree is restored between cases"

# ---------------------------------------------------------------------------
echo
echo "CI wiring"

# The reason this suite exists at all: a check CI does not run is not a gate.
if grep -q 'check-taskdef.sh' "$CI_YML"; then
  ok "ci.yml runs the check"
else
  bad "ci.yml runs the check" "no step invokes check-taskdef.sh"
fi

if grep -q 'test-taskdef.sh' "$CI_YML"; then
  ok "ci.yml runs this suite"
else
  bad "ci.yml runs this suite" "no step invokes test-taskdef.sh"
fi

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
