#!/bin/bash
# ---------------------------------------------------------------------------
# The half of the ruleset gate that is a signature.
#
#   bash .github/scripts/check-release-report-block.sh <file-holding-the-pr-body>
#
# `docs/adr/0119` §4: **the recorded-corpus diff cannot run in CI.** There is no
# database, and `docs/adr/0118` §7 restricts it to a restore. So what CI asserts
# is that the pull request carries a report block naming its **corpus window**
# and its **coverage figure** — **presence, not truth**.
#
# That distinction is the whole of this script and it is not a hedge: nothing
# here can tell whether the window is the one that was replayed or the coverage
# figure is the one the harness printed. What it can refuse is a ruleset release
# shipped with no report at all, which is the failure that actually happens —
# and it makes the obligation visible at the moment somebody is trying to merge
# rather than in a document they have not read.
#
#   exit 0  the block is there and names both facts
#   exit 1  a ruleset release with no report block, or one missing a fact
#   exit 2  the check could not run (no file to read)
#
# It runs **only when a ruleset release is in the pull request**, which the
# workflow decides by the artifacts having changed. Every other pull request
# owes nothing, because most pull requests are not ruleset releases and a gate
# that asks everybody for a corpus window is a gate everybody learns to paste
# nonsense into.
#
# Tested by .github/scripts/test-ruleset-diff.sh (`make test-ruleset-diff`).
# ---------------------------------------------------------------------------
set -uo pipefail

body="${1:-}"
[ -n "$body" ] && [ -f "$body" ] || {
  echo "usage: $0 <file-holding-the-pull-request-body>" >&2
  exit 2
}

# Two facts, spelled as the report prints them. Case-insensitive and tolerant of
# the punctuation around them, because what is being checked is that somebody
# wrote the numbers down — not that they formatted them the way this script
# would have.
missing=()
grep -Eiq 'corpus window' "$body" || missing+=("the corpus window — the dates the recorded corpus was replayed over")
grep -Eiq 'coverage' "$body" || missing+=("the coverage figure — what fraction of searches replayed, and how many erasure excluded")

if [ ${#missing[@]} -eq 0 ]; then
  echo "OK — the pull request carries a recorded-corpus report block."
  echo "    Presence, not truth: nothing here can check the numbers are right."
  exit 0
fi

if [ -n "${GITHUB_ACTIONS:-}" ]; then
  echo "::error title=No recorded-corpus report block::This pull request changes the ruleset diff. docs/adr/0119 §5 asks the release for a recorded-corpus report naming its corpus window and coverage, signed by the owner accountable for the quality floor."
fi

cat >&2 <<EOF

────────────────────────────────────────────────────────────────────────────
  A RULESET RELEASE WITH NO RECORDED-CORPUS REPORT
────────────────────────────────────────────────────────────────────────────

  This pull request regenerates the synthetic diff, so it is a ruleset release
  (docs/adr/0119 §5). The synthetic half is checked by a machine; **the
  recorded half is a signature**, and it is missing:

$(printf '      · %s\n' "${missing[@]}")

  Add a block to the pull request body, from a run of the recorded-corpus diff
  against a restore — the-replay-harness.md §4 shows the shape:

      ## Recorded corpus
      corpus window   2026-08-26 → 2026-09-30
      searches        12 481
      replayed        12 402  (coverage 99.4%)
      excluded           79   redacted by erasure

  Nothing here can check those numbers are true. What it refuses is a release
  that never looked.

────────────────────────────────────────────────────────────────────────────
EOF
exit 1
