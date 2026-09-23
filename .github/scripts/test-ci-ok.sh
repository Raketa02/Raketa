#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the ci-ok check.
#
#   bash .github/scripts/test-ci-ok.sh     # or: make test-ci-ok
#
# ci-ok is the one status a human reads before merging (ADR-0181 §4), so it is
# the one check whose silent failure costs the most: a summary that stayed green
# while a job failed would turn every other gate in the workflow into a
# suggestion. It was added to a workflow that it passed on, so it has never been
# seen to fail — the reason test-taskdef.sh, test-poetry-pin-drift.sh and
# .claude/hooks/test-hooks.sh exist. This drives both of its halves red:
#
#   * the verdict, against the `needs` context of runs that went wrong;
#   * the wiring, against copies of ci.yml where a job no longer reaches ci-ok,
#     or ci-ok no longer runs when something upstream failed.
#
# Nothing in the tree is touched: the verdict reads its input from the
# environment, and the wiring cases perturb a copy of the workflow.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-ci-ok.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"

pass=0
fail=0

ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

# The check's output is captured before it is searched rather than piped into
# grep: `set -o pipefail` above makes a pipeline take the check's exit 1, so
# `check | grep -q` would report a miss on every case that correctly went red.
run() { # <mode> [arg] — sets $got and $out
  out=$(bash "$CHECK" "$@" 2>&1)
  got=$?
}

expect() { # <want exit> <name> <needle, or - for none> <mode> [arg]
  local want="$1" name="$2" needle="$3"
  shift 3
  run "$@"
  if [ "$got" != "$want" ]; then
    bad "$name" "want exit $want, got $got"
  elif [ "$needle" != "-" ] && ! printf '%s' "$out" | grep -qF -- "$needle"; then
    bad "$name" "output never mentioned '$needle'"
  else
    ok "$name"
  fi
}

verdict() { # <json> <want exit> <name> [needle]
  NEEDS="$1" expect "$2" "$3" "${4:--}" verdict
}

# The verdict reads the context from NEEDS, so whatever the caller's environment
# holds must not leak into the case that asserts its absence.
unset NEEDS

for f in "$CHECK" "$CI_YML"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d) || exit 2
trap 'rm -rf "$TMP"' EXIT INT TERM

# ---------------------------------------------------------------------------
echo
echo "the verdict — what GitHub hands ci-ok as \`toJSON(needs)\`"

# The shape of the real context: one key per needed job, its `result`, and its
# outputs, which the verdict must ignore.
green='{"changes":{"result":"success","outputs":{"backend":"true"}},"backend-tests":{"result":"success","outputs":{}}}'
verdict "$green" 0 "every needed job succeeded"

verdict '{"changes":{"result":"success","outputs":{}},"player-tests":{"result":"skipped","outputs":{}}}' \
  0 "a job skipped because its app did not change passes"

verdict '{"changes":{"result":"success","outputs":{}},"backend-tests":{"result":"failure","outputs":{}}}' \
  1 "a failed job fails ci-ok" "backend-tests"

# A matrix job's result is its shards' together — one red shard makes it
# `failure`, which is the case above. Cancelled is the one that reads like
# nobody's fault: a superseded run, a timeout, a runner that went away. None of
# them tested the change, so none of them is green.
verdict '{"changes":{"result":"success","outputs":{}},"player-deck":{"result":"cancelled","outputs":{}}}' \
  1 "a cancelled job fails ci-ok" "player-deck"

verdict '{"a":{"result":"failure","outputs":{}},"b":{"result":"cancelled","outputs":{}},"c":{"result":"success","outputs":{}}}' \
  1 "every job that went wrong is named, not just the first" "b: cancelled"

# Fail closed. A result this check has never heard of is not a pass: the day
# GitHub adds one, the answer should be a red run somebody reads, not a green
# one nobody does.
verdict '{"changes":{"result":"neutral","outputs":{}}}' \
  1 "a result the check does not know fails closed" "neutral"

verdict '{"changes":{"outputs":{}}}' \
  1 "a job with no result at all fails closed" "changes"

# A check that cannot see its subject must not report success.
verdict '{}' 2 "no needed jobs at all is a check that lost its subject"
verdict 'not json' 2 "an unreadable context is a usage error, not a pass"
expect 2 "no context in the environment is a usage error, not a pass" - verdict

# ---------------------------------------------------------------------------
echo
echo "the wiring — ci-ok needs every job, and runs whatever they did"

expect 0 "the committed ci.yml is wired" - wiring "$CI_YML"

# Each perturbation below is a line-level edit of a copy, so each first asserts
# that it changed something — a reformatted ci.yml would otherwise stop being
# perturbed, and every case would "pass" by testing nothing.
perturb() { # <name> <sed expression> — writes $TMP/ci.yml
  sed "$2" "$CI_YML" >"$TMP/ci.yml"
  if cmp -s "$CI_YML" "$TMP/ci.yml"; then
    bad "$1" "the perturbation matched nothing in ci.yml — the case tests nothing"
    return 1
  fi
}

# The needs list is one job per line, so a job is dropped by deleting its line.
# The day somebody adds a job and forgets ci-ok, it runs, fails, and the one
# status anybody reads stays green.
if perturb "a job dropped from ci-ok's needs" '/^  ci-ok:/,/^  [a-z]/{/^      - backend-tests$/d;}'; then
  expect 1 "a job dropped from ci-ok's needs is red" "backend-tests" wiring "$TMP/ci.yml"
fi

# The same mistake from the other side: a new job nobody told ci-ok about.
cp "$CI_YML" "$TMP/ci.yml"
cat >>"$TMP/ci.yml" <<'EOF'

  a-new-check:
    name: A check added after ci-ok was
    runs-on: ubuntu-latest
    steps:
      - run: "false"
EOF
expect 1 "a job added without telling ci-ok is red" "a-new-check" wiring "$TMP/ci.yml"

# Without `always()`, a failed need *skips* ci-ok — and a skipped check reads as
# passing. `success()` is the default GitHub would otherwise apply, and
# `!cancelled()` would skip it on the superseded run, which never tested the push.
if perturb "ci-ok on success() alone" '/^  ci-ok:/,/^  [a-z]/{s/^    if: always()$/    if: success()/;}'; then
  expect 1 "ci-ok gated on success() is red" "always()" wiring "$TMP/ci.yml"
fi
if perturb "ci-ok on !cancelled()" '/^  ci-ok:/,/^  [a-z]/{s/^    if: always()$/    if: ${{ !cancelled() }}/;}'; then
  expect 1 "ci-ok gated on !cancelled() is red" "always()" wiring "$TMP/ci.yml"
fi
if perturb "ci-ok with no condition" '/^  ci-ok:/,/^  [a-z]/{/^    if: always()$/d;}'; then
  expect 1 "ci-ok with no condition is red" "always()" wiring "$TMP/ci.yml"
fi

# The list is read one job per line — the form a diff shows one job at a time, and
# the only form this check parses. A flow list is refused by name rather than read
# as one job called "[changes, …]", which would bury the reason under twelve.
cp "$CI_YML" "$TMP/ci.yml"
python3 - "$TMP/ci.yml" <<'PY'
import re, sys
path = sys.argv[1]
text = open(path).read()
text, n = re.subn(r"(\n  ci-ok:\n(?:    .*\n)*?)    needs:\n((?:      - .*\n)+)",
                  lambda m: m.group(1) + "    needs: [" + ", ".join(
                      l.strip()[2:] for l in m.group(2).splitlines()) + "]\n",
                  text)
open(path, "w").write(text)
sys.exit(0 if n == 1 else 1)
PY
if [ $? -eq 0 ]; then
  expect 1 "ci-ok's needs as a flow list is refused by name" "one job per line" wiring "$TMP/ci.yml"
else
  bad "ci-ok's needs as a flow list" "the perturbation matched nothing in ci.yml — the case tests nothing"
fi

if perturb "no ci-ok job" 's/^  ci-ok:$/  summary:/'; then
  expect 1 "a workflow with no ci-ok job is red" "no ci-ok job" wiring "$TMP/ci.yml"
fi

expect 2 "a workflow that is not there is a usage error, not a pass" - wiring "$TMP/absent.yml"
printf 'name: CI\non: push\n' >"$TMP/ci.yml"
expect 2 "a workflow with no jobs is a usage error, not a pass" - wiring "$TMP/ci.yml"

# ---------------------------------------------------------------------------
echo
echo "CI wiring"

# The reason this suite exists at all: a check CI does not run is not a gate.
grep -q 'check-ci-ok.sh verdict' "$CI_YML" \
  && ok "ci.yml renders the verdict" \
  || bad "ci.yml renders the verdict" "no step invokes check-ci-ok.sh verdict"

grep -q 'check-ci-ok.sh wiring' "$CI_YML" \
  && ok "ci.yml checks its own wiring" \
  || bad "ci.yml checks its own wiring" "no step invokes check-ci-ok.sh wiring"

grep -q 'test-ci-ok.sh' "$CI_YML" \
  && ok "ci.yml runs this suite" \
  || bad "ci.yml runs this suite" "no step invokes test-ci-ok.sh"

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
