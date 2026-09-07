#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the ruleset diff check.
#
#   bash .github/scripts/test-ruleset-diff.sh        # or: make test-ruleset-diff
#
# Drives check-ruleset-diff.sh against a deliberately broken tree and asserts it
# goes red, then against the committed tree and asserts it goes green. **A
# guardrail that silently stops matching is worse than none, because you stop
# watching for it** — the same argument `make test-hooks`, `make test-drift`,
# `make test-poetry-pin` and `make test-judged-pairings` are each built on.
#
# Three broken trees, because the check has three ways to be wrong and they fail
# for different reasons:
#
#   · a hand-edited artifact       — somebody edited a generated file
#   · a moved ruleset constant     — the release this gate exists for
#   · a missing artifact           — the check cannot run and must say so
#
# It perturbs the artifacts and the live ruleset in place and restores every
# byte on exit — including on failure or interrupt — so it is safe to run on a
# dirty tree and preserves whatever was there.
#
# The structural assertions at the end keep the CI wiring honest: a check whose
# job never runs on the pull request that changes a ruleset is dormant in
# precisely the case it exists to catch.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-ruleset-diff.sh"
BLOCK="$ROOT/.github/scripts/check-release-report-block.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"
ANSWERS="$ROOT/docs/specs/matchmaking/ruleset-diff/answers.thin.json"
POPULATION="$ROOT/docs/specs/matchmaking/ruleset-diff/population.thin.json"
# **The live ruleset's own file, resolved rather than typed.** A released dataset
# is never edited and the next release is a new module, so a filename here would
# make this suite exit 2 on the day somebody ships a ruleset — which is exactly
# the day it most needs to run.
RULESET=$(cd "$ROOT/backend" && poetry run python -c "
import inspect
from app.modules.matchmaking.infrastructure import rulesets
from app.modules.matchmaking.infrastructure.rulesets import LIVE_RULESET_VERSION
for name, module in vars(rulesets).items():
    if inspect.ismodule(module) and getattr(module, 'VERSION', None) == LIVE_RULESET_VERSION:
        print(inspect.getsourcefile(module))
        break
" 2>/dev/null)

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

for f in "$CHECK" "$BLOCK" "$CI_YML" "$ANSWERS" "$POPULATION" "$RULESET"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

TMP=$(mktemp -d)
cp "$ANSWERS" "$TMP/answers.json"
cp "$POPULATION" "$TMP/population.json"
cp "$RULESET" "$TMP/ruleset.py"
restore() {
  cp "$TMP/answers.json" "$ANSWERS"
  cp "$TMP/population.json" "$POPULATION"
  cp "$TMP/ruleset.py" "$RULESET"
}
trap 'restore; rm -rf "$TMP"' EXIT INT TERM

# ---------------------------------------------------------------------------
echo
echo "check-ruleset-diff.sh — the committed tree"

expect_exit 0 "the committed artifacts reproduce under both hash seeds" \
  bash "$CHECK"
restore

# ---------------------------------------------------------------------------
echo
echo "check-ruleset-diff.sh — a hand-edited artifact"

# One Fit, moved by a point. A generated file is never hand-edited, and the
# smallest possible edit is the one most likely to slip past a reader.
python3 - "$ANSWERS" <<'HANDEDIT'
import json, sys
path = sys.argv[1]
with open(path) as fh:
    doc = json.load(fh)
for record in doc["records"]:
    if record["returned"]:
        record["returned"][0]["fit"] = round(record["returned"][0]["fit"] + 1.0, 6)
        break
else:
    raise SystemExit("the corpus returned nobody at all — the probe proves nothing")
with open(path, "w") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
HANDEDIT

out=$(bash "$CHECK" 2>&1)
got=$?
[ "$got" = 1 ] && ok "a hand-edited answer fails" \
  || bad "a hand-edited answer fails" "want exit 1, got $got"
grep -q 'RULESET DIFF DRIFT' <<<"$out" && ok "the failure names itself" \
  || bad "the failure names itself"
grep -q 'make gen-ruleset-diff' <<<"$out" && ok "the failure prints the command that fixes it" \
  || bad "the failure prints the command that fixes it"
restore

echo
echo "check-ruleset-diff.sh — a hand-edited population"

python3 - "$POPULATION" <<'HANDEDIT'
import json, sys
path = sys.argv[1]
with open(path) as fh:
    doc = json.load(fh)
doc["members"][0]["mu"] = round(doc["members"][0]["mu"] + 0.5, 2)
with open(path, "w") as fh:
    json.dump(doc, fh, indent=2)
    fh.write("\n")
HANDEDIT

expect_exit 1 "a hand-edited population fails" bash "$CHECK"
restore

# ---------------------------------------------------------------------------
echo
echo "check-ruleset-diff.sh — the release this gate exists for"

# The quality floor, moved by one point, and **inside its own judged bound** so
# that what fails is this check rather than the ruleset refusing to load. It is
# the single most consequential change a ruleset makes: it decides when the
# product says nothing rather than something.
python3 - "$RULESET" <<'RELEASE'
import re, sys
path = sys.argv[1]
source = open(path).read()
# The floor as this ruleset spells it, whatever integer that is — one point
# lower is inside its judged bound (`max(Fit | not shown) < floor`), so what
# fails is this check rather than the ruleset refusing to load.
found = re.search(r"quality_floor=(\d+),", source)
if found is None:
    raise SystemExit(f"{path} does not spell a quality_floor")
lowered = f"quality_floor={int(found.group(1)) - 1},"
open(path, "w").write(source.replace(found.group(0), lowered, 1))
RELEASE

out=$(bash "$CHECK" 2>&1)
got=$?
[ "$got" = 1 ] && ok "a moved ruleset constant fails" \
  || bad "a moved ruleset constant fails" "want exit 1, got $got"

# The report is the point of the failure, not a decoration on it: what the
# release argument needs is what moved, and a floor change moves people across
# the floor in both directions.
grep -q 'crossed the floor' <<<"$out" && ok "the report classifies the searches it moved" \
  || bad "the report classifies the searches it moved"
grep -q 'weight-only' <<<"$out" \
  && ok "a floor change is weight-only — no term value moved" \
  || bad "a floor change is weight-only — no term value moved" \
         "a floor moves who is shown, never what a term reports; classifying it \
shape-class would send its owner to shadow scoring for nothing"
grep -qE 'crossed the floor +[1-9]' <<<"$out" \
  && ok "the report counts the crossings rather than only naming them" \
  || bad "the report counts the crossings rather than only naming them"
restore

# The check must leave the tree holding the fix rather than the snapshot.
expect_exit 0 "the restored tree passes again" bash "$CHECK"
restore

# ---------------------------------------------------------------------------
echo
echo "check-ruleset-diff.sh — a tree it cannot run against"

mv "$ANSWERS" "$TMP/moved-away.json"
expect_exit 2 "a missing artifact is not drift — it is a check that cannot run" \
  bash "$CHECK"
mv "$TMP/moved-away.json" "$ANSWERS"
restore

# ---------------------------------------------------------------------------
# The determinism half. ADR-0105 §4 sanctions setting a hash seed deliberately
# in exactly one place — the test that sets two and compares — and this is the
# second instance of it. A check that regenerated under one seed would assert
# reproducibility against an unknown, because the committed file was produced
# under whatever seed its author's shell handed them.
# ---------------------------------------------------------------------------
echo
echo "check-ruleset-diff.sh — the seeds it varies"

seeds=$(grep -oE 'SEEDS=\([0-9 ]+\)' "$CHECK" | grep -oE '[0-9]+')
[ "$(wc -w <<<"$seeds")" -ge 2 ] && ok "the check pins at least two hash seeds" \
  || bad "the check pins at least two hash seeds" "found: $seeds"
[ "$(sort -u <<<"$seeds" | wc -w)" = "$(wc -w <<<"$seeds")" ] \
  && ok "the pinned seeds differ from each other" \
  || bad "the pinned seeds differ from each other" "found: $seeds"
grep -q 'PYTHONHASHSEED="\$seed"' "$CHECK" \
  && ok "each run is made under one of them" \
  || bad "each run is made under one of them"

# ---------------------------------------------------------------------------
# The other half of the gate, which is a signature (docs/adr/0119 §4). The
# recorded-corpus diff needs a restore and cannot run in CI, so what is asserted
# is that the pull request wrote its corpus window and coverage down. **Presence,
# not truth** — and a check that cannot tell truth still has to be able to tell
# absence, which is what this drives.
# ---------------------------------------------------------------------------
echo
echo "check-release-report-block.sh — presence, and never truth"

BODY="$TMP/pr-body.txt"

cat >"$BODY" <<'REPORT'
Moves the vibe weight from 24 to 20.

## Recorded corpus
corpus window   2026-08-26 → 2026-09-30
replayed        12 402  (coverage 99.4%)
excluded            79  redacted by erasure
REPORT
expect_exit 0 "a release carrying its report block passes" \
  bash "$BLOCK" "$BODY"

printf 'Moves the vibe weight from 24 to 20. Diff regenerated.\n' >"$BODY"
out=$(bash "$BLOCK" "$BODY" 2>&1)
got=$?
[ "$got" = 1 ] && ok "a release with no report block fails" \
  || bad "a release with no report block fails" "want exit 1, got $got"
grep -q 'corpus window' <<<"$out" && ok "the failure names what is missing" \
  || bad "the failure names what is missing"
grep -q 'Recorded corpus' <<<"$out" && ok "and shows the shape to write" \
  || bad "and shows the shape to write"

printf 'corpus window 2026-08-26 → 2026-09-30, and nothing about how much replayed.\n' >"$BODY"
expect_exit 1 "half a block is not a block" bash "$BLOCK" "$BODY"

expect_exit 2 "no body to read is a check that cannot run" bash "$BLOCK"

# It is presence and not truth, and the suite says so out loud: a block whose
# numbers are nonsense passes, because nothing in CI can see the corpus.
printf 'corpus window: the beginning of time. coverage: all of it.\n' >"$BODY"
expect_exit 0 "a block nobody could have measured still passes — presence, not truth" \
  bash "$BLOCK" "$BODY"

echo
echo "ci.yml — the release-report job"

grep -q 'check-release-report-block.sh' "$CI_YML" \
  && ok "a job runs the report-block check" \
  || bad "a job runs the report-block check"

# It must run only on a ruleset release. Asking every pull request for a corpus
# window is how a gate becomes something people paste nonfiction into.
grep -q "needs.changes.outputs.ruleset == 'true'" "$CI_YML" \
  && ok "and only when the ruleset artifacts moved" \
  || bad "and only when the ruleset artifacts moved"

grep -q "ruleset: \${{ steps.filter.outputs.ruleset }}" "$CI_YML" \
  && ok "the filter that decides that is published as an output" \
  || bad "the filter that decides that is published as an output"

# ---------------------------------------------------------------------------
# The check firing is only half of it. It has to be REACHED.
# ---------------------------------------------------------------------------
echo
echo "ci.yml — the change that must trigger it"

grep -q 'check-ruleset-diff.sh' "$CI_YML" \
  && ok "the backend job runs the check" \
  || bad "the backend job runs the check"

grep -q 'test-ruleset-diff.sh' "$CI_YML" \
  && ok "and drives it against a broken tree" \
  || bad "and drives it against a broken tree"

# The artifacts live in docs/, which the backend filter watches file by file.
# Without them a pull request that hand-edits one runs no backend job at all.
for artifact in \
  'docs/specs/matchmaking/ruleset-diff/population.thin.json' \
  'docs/specs/matchmaking/ruleset-diff/answers.thin.json'
do
  grep -q "$artifact" "$CI_YML" \
    && ok "the backend filter watches $(basename "$artifact")" \
    || bad "the backend filter watches $(basename "$artifact")" \
           "a pull request hand-editing it would run no backend job"
done

# ---------------------------------------------------------------------------
echo
printf '\n  %s passed, %s failed\n\n' "$pass" "$fail"
[ "$fail" = 0 ]
