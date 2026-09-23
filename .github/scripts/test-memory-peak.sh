#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for memory-peak.sh.
#
#   bash .github/scripts/test-memory-peak.sh     # or: make test-memory-peak
#
# memory-peak.sh is not a gate, but it stands between every test job's command
# and that job's result: the Jest shards, the deck and the backend suite all run
# through it. A wrapper there that lost an exit status would turn a red test
# into a green job, and ci-ok would sum the green jobs into a green run. So its
# one promise — the command's exit status is its exit status — is driven here,
# failing statuses first. ci-ok runs it before rendering a verdict.
#
# On Linux it also asserts the measurement is written down; elsewhere there is no
# /proc/meminfo, and the wrapper only runs the command.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
WRAPPER="$ROOT/.github/scripts/memory-peak.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"

pass=0
fail=0

ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

for f in "$WRAPPER" "$CI_YML"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d) || exit 2
trap 'rm -rf "$TMP"' EXIT INT TERM

# The probes' measurements go to a scratch summary, and never become annotations
# on the run that is testing them.
wrap() { # <command...> — sets $got and $out
  out=$(GITHUB_ACTIONS='' GITHUB_STEP_SUMMARY="$TMP/summary.md" bash "$WRAPPER" probe "$@" 2>&1)
  got=$?
}

expect_status() { # <want> <name> <command...>
  local want="$1" name="$2"
  shift 2
  wrap "$@"
  [ "$got" = "$want" ] && ok "$name" || bad "$name" "want exit $want, got $got"
}

# ---------------------------------------------------------------------------
echo
echo "memory-peak.sh — the command's exit status is its exit status"

expect_status 1 "a failing command fails" false
expect_status 3 "any other status comes through unchanged" bash -c 'exit 3'
expect_status 127 "a command that does not exist fails as the shell says" "$TMP/no-such-command"
expect_status 0 "a passing command passes" true

wrap bash -c 'echo said-on-stdout; echo said-on-stderr >&2'
if printf '%s' "$out" | grep -q said-on-stdout && printf '%s' "$out" | grep -q said-on-stderr; then
  ok "the command's own output still reaches the log"
else
  bad "the command's own output still reaches the log" "got: $out"
fi

out=$(bash "$WRAPPER" probe 2>&1)
got=$?
[ "$got" = 2 ] && ok "no command is a usage error, not a pass" \
  || bad "no command is a usage error, not a pass" "want exit 2, got $got"

# ---------------------------------------------------------------------------
echo
if [ -r /proc/meminfo ]; then
  echo "memory-peak.sh — the measurement is written down"
  rm -f "$TMP/summary.md"
  wrap bash -c 'sleep 2; exit 5'
  [ "$got" = 5 ] && ok "a measured command still keeps its status" \
    || bad "a measured command still keeps its status" "want exit 5, got $got"
  printf '%s' "$out" | grep -q 'memory — probe: peak [0-9]* MB used of [0-9]* MB' \
    && ok "the peak is printed in the log" \
    || bad "the peak is printed in the log" "got: $out"
  grep -q 'Memory — probe:\*\* peak' "$TMP/summary.md" 2>/dev/null \
    && ok "and written to the step summary" \
    || bad "and written to the step summary"
else
  echo "memory-peak.sh — no /proc/meminfo here, so nothing is measured (Linux only)"
fi

# ---------------------------------------------------------------------------
echo
echo "CI wiring"

grep -q 'test-memory-peak.sh' "$CI_YML" \
  && ok "ci.yml runs this suite" \
  || bad "ci.yml runs this suite" "no step invokes test-memory-peak.sh"

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
