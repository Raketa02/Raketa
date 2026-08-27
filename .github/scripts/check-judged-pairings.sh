#!/bin/bash
# ---------------------------------------------------------------------------
# The judged pairings: re-derived, and their tables diffed.
#
#   bash .github/scripts/check-judged-pairings.sh
#
# docs/specs/matchmaking/judged-pairings.json holds six judged pairings as
# INPUTS and a verdict per case (docs/adr/0122). Everything else about them —
# every term value, every renormalised weight, every Fit — is derived by the
# live ruleset, and this asserts the two agree the way `make gen-api` does:
# regenerate, then look for a diff.
#
# It does one thing a diff cannot. `ranking-weights.md` §11 has always demanded
# that turning a term on is a ruleset release that re-runs the six cases and may
# move the floor. That is an inequality —
#
#     max(Fit | not shown)  <  QUALITY_FLOOR  ≤  min(Fit | shown)
#
# — and the generator FAILS when the configured floor sits outside it. A weight
# release that quietly hides the median stranger stops being something somebody
# has to notice.
#
#   exit 0  the tables reproduce, and the floor still sits inside its bound
#   exit 1  drift — a generated table was hand-edited, or a ruleset change was
#           shipped without regenerating; or the floor no longer holds
#   exit 2  the check could not run (no poetry, no fixture, no markers)
#
# It runs the backend's OWN harness rather than restating the derivation, and
# that harness is the one tests/unit/test_matchfit_judged_pairings.py scores its
# cases through. Two harnesses would be two answers, and the second one drifts.
#
# What git compares is the working tree against HEAD, so the hand-edit case is
# the committed one: an uncommitted hand edit is simply overwritten by the
# regeneration and there is nothing to report — correctly, since CI only ever
# sees what was committed.
#
# Tested by .github/scripts/test-judged-pairings.sh (`make test-judged-pairings`).
# A check that has never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

# The three files the harness regenerates. Named here as well as there so the
# diff is scoped to exactly what was generated: diffing docs/specs/matchmaking/
# as a directory would report an edit to a neighbouring spec as judged-pairings
# drift, which is the sort of false failure that teaches people to ignore a
# check.
GENERATED=(
  "docs/specs/matchmaking/judged-pairings.json"
  "docs/specs/matchmaking/the-judged-pairings.md"
  "docs/specs/matchmaking/ranking-weights.md"
)

for f in "${GENERATED[@]}"; do
  [ -f "$ROOT/$f" ] || { echo "missing: $f" >&2; exit 2; }
done

cd "$ROOT/backend" || exit 2

out=$(poetry run python -m scripts.judged_pairings 2>&1)
derived=$?
echo "$out"

case "$derived" in
  0) ;;
  1)
    # The floor moved. The harness has already said which side broke and what to
    # do about it; adding a second explanation here would give the two of them
    # somewhere to disagree.
    if [ -n "${GITHUB_ACTIONS:-}" ]; then
      echo "::error title=The quality floor left its judged bound::QUALITY_FLOOR no longer sits inside max(Fit | not shown) < floor <= min(Fit | shown). See the job log."
    fi
    exit 1
    ;;
  *)
    echo >&2
    echo "Could not re-derive the judged pairings." >&2
    echo "The check needs the backend installed — 'poetry install' in backend/." >&2
    exit 2
    ;;
esac

cd "$ROOT" || exit 2

drift=$(git status --porcelain -- "${GENERATED[@]}")

if [ -z "$drift" ]; then
  echo
  echo "OK — every judged-pairings table reproduces from the fixture."
  exit 0
fi

# ---------------------------------------------------------------------------
# Drift. Say what to run. A drift failure that does not tell you how to fix it
# is one that gets worked around.
# ---------------------------------------------------------------------------
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  echo "::error title=Judged-pairings drift::A generated table does not reproduce from docs/specs/matchmaking/judged-pairings.json. Run 'make gen-judged-pairings' at the repository root and commit the result."
fi

cat >&2 <<EOF

────────────────────────────────────────────────────────────────────────────
  JUDGED-PAIRINGS DRIFT
────────────────────────────────────────────────────────────────────────────

  Re-deriving the six against the live ruleset — named at the top of the
  output above — produced tables different from the ones committed. Either a
  ruleset or a formula changed and the fixture was not regenerated with it, or
  a generated table was edited by hand — it never should be.

  **A diff here is a design change and must be argued for in the pull request**
  (matchmaking-engine.md §20.1). Regenerating is not the whole fix: say which
  case now reads differently and why, and if a verdict moved, land the ADR
  the-five-numbers.md §1 requires.

  Fix — from the repository root:

      make gen-judged-pairings
      git add ${GENERATED[*]}

────────────────────────────────────────────────────────────────────────────
EOF

echo >&2
echo "  The diff:" >&2
git --no-pager diff -- "${GENERATED[@]}" >&2

exit 1
