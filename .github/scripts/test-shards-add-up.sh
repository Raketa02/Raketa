#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the shards-add-up check.
#
#   bash .github/scripts/test-shards-add-up.sh     # or: make test-shards-add-up
#
# check-shards-add-up.sh reads the JUnit reports CI's backend groups write, and
# a real run's reports always add up — so it has never been seen to fail, the
# reason test-contract-drift.sh, test-ci-ok.sh and the rest exist. This builds
# the reports the groups write and drives the check against each way they can
# fail to add up, and against the reports as written.
#
# **The reports are real.** Each group runs through the same `make test-group`
# a CI runner runs, xdist and pytest-split included, with pytest's own
# `--junitxml` — and `--setup-plan`, which walks every test's setup and teardown
# without running a fixture or a test body, so a group's report names every
# test it would have run, in pytest's own shape, in seconds rather than minutes.
# Two groups, because CI started at two; the check does not know how many there
# are, and a layout at N is `make split-partition`'s question, not this one's.
#
# Every case perturbs a copy of the reports in a scratch directory, so nothing
# in the tree is written and the suite is safe on a dirty one.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-shards-add-up.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"
SPLITS=2

pass=0
fail=0

ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

OUT=""
CODE=0

run_check() { # <directory>
  # Captured rather than piped into grep: `set -o pipefail` above makes a
  # pipeline take the check's exit 1, so `check | grep -q` would report a miss
  # on every case that correctly went red.
  OUT=$(bash "$CHECK" "$1" 2>&1)
  CODE=$?
}

had_exit() { # <want> <name>
  [ "$CODE" = "$1" ] && ok "$2" || bad "$2" "want exit $1, got $CODE"$'\n'"$OUT"
}

said() { # <needle> <name>
  if printf '%s' "$OUT" | grep -qF -- "$1"; then
    ok "$2"
  else
    bad "$2" "output never mentioned '$1'"
  fi
}

for f in "$CHECK" "$CI_YML"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d) || exit 2
trap 'rm -rf "$TMP"' EXIT INT TERM

# ---------------------------------------------------------------------------
echo
echo "building each group's report through make test-group"

mkdir "$TMP/written"
for group in $(seq 1 "$SPLITS"); do
  report="$TMP/written/group-$group-of-$SPLITS.xml"
  if make -s -C "$ROOT/backend" test-group GROUP="$group" SPLITS="$SPLITS" \
       PYTEST_ARGS="--setup-plan --junitxml=$report" >"$TMP/group-$group.log" 2>&1 \
     && [ -s "$report" ]; then
    echo "  group $group of $SPLITS written"
  else
    echo "Could not build group $group's report — no case below would mean anything:" >&2
    tail -20 "$TMP/group-$group.log" >&2
    exit 2
  fi
done

# A fresh copy of the reports as the groups wrote them, for one case to perturb.
fresh() { # <case name> — prints the copy's directory
  rm -rf "${TMP:?}/$1"
  cp -R "$TMP/written" "$TMP/$1"
  printf '%s' "$TMP/$1"
}

# The first test in a report, taken out of it (or copied into another), with
# ElementTree so the rest of the report is left as pytest wrote it. Prints the
# test's name, which ends the id the check will print.
move_first_test() { # <from report> <to report | ""> <keep in the source: 0|1>
  python3 - "$1" "$2" "$3" <<'PY'
import sys
import xml.etree.ElementTree as ET

source, target, keep = sys.argv[1], sys.argv[2], sys.argv[3] == "1"
tree = ET.parse(source)
suite = tree.getroot().find("testsuite")
case = suite.find("testcase")
if case is None:
    sys.exit("no testcase in " + source)
if not keep:
    suite.remove(case)
    tree.write(source, encoding="utf-8", xml_declaration=True)
if target:
    other = ET.parse(target)
    other.getroot().find("testsuite").append(case)
    other.write(target, encoding="utf-8", xml_declaration=True)
print(case.get("name"))
PY
}

G1="group-1-of-$SPLITS.xml"
G2="group-2-of-$SPLITS.xml"

# ---------------------------------------------------------------------------
echo
echo "check-shards-add-up.sh — the reports as the groups wrote them"

run_check "$TMP/written"
had_exit 0 "the groups add up to the suite"
said "every collected test ran in exactly one group" "and it says so"

# ---------------------------------------------------------------------------
echo
echo "a group layout that does not add up"

# The case the check exists for: a test the suite collects and no group ran.
dir=$(fresh dropped)
name=$(move_first_test "$dir/$G1" "" 0)
run_check "$dir"
had_exit 1 "a test dropped from one group is missing"
said "$name" "the failure names the test"
said "in no group" "and says no group ran it"
said "THE GROUPS DO NOT ADD UP" "and says the groups do not add up"

# Dealt to both groups: twice the minutes, and a sign the layout is not the one
# the durations describe.
dir=$(fresh doubled)
name=$(move_first_test "$dir/$G2" "$dir/$G1" 1)
run_check "$dir"
had_exit 1 "a test in two groups ran twice"
said "$name" "the failure names the test"
said "in more than one group" "and says it ran in more than one"

# A runner that died before its artifact was uploaded is a group of tests that
# did not run — all of them, named.
dir=$(fresh lost)
rm "$dir/$G2"
run_check "$dir"
had_exit 1 "a group whose report never arrived leaves its tests missing"
said "in no group" "and names them as missing"

# ---------------------------------------------------------------------------
echo
echo "what is not a second run"

# pytest writes a failure in the call and an error in the teardown as two
# <testcase> elements with one address. One report is one session, so that is
# one run — reading it as two would turn a red test into a red sharding check.
dir=$(fresh written-twice)
move_first_test "$dir/$G1" "$dir/$G1" 1 >/dev/null
run_check "$dir"
had_exit 0 "a test one report writes twice ran once"

# ---------------------------------------------------------------------------
echo
echo "the check refuses rather than passing when it cannot run"

dir=$(fresh unreadable)
printf '<testsuites><testsuite>' >"$dir/$G1"
run_check "$dir"
had_exit 2 "a report that is not XML is a usage error, not a pass"
said "$G1" "and names the report"

mkdir "$TMP/none"
run_check "$TMP/none"
had_exit 2 "a directory with no reports is a usage error, not a pass"

run_check "$TMP/nonesuch"
had_exit 2 "a directory that does not exist is a usage error, not a pass"

# ---------------------------------------------------------------------------
echo
echo "ci.yml — the groups, their reports and the check"

grep -q 'make test-group' "$CI_YML" \
  && ok "the backend tests job runs one group per runner" \
  || bad "the backend tests job runs one group per runner"

grep -q -- '--junitxml' "$CI_YML" \
  && ok "each group writes a report of the tests it ran" \
  || bad "each group writes a report of the tests it ran"

grep -q 'check-shards-add-up.sh' "$CI_YML" \
  && ok "a job adds the reports up against the suite" \
  || bad "a job adds the reports up against the suite"

grep -q 'test-shards-add-up.sh' "$CI_YML" \
  && ok "and this suite drives it against broken reports" \
  || bad "and this suite drives it against broken reports"

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
