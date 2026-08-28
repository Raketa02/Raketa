#!/bin/bash
# ---------------------------------------------------------------------------
# The ruleset diff: regenerated, twice, under two different hash seeds.
#
#   bash .github/scripts/check-ruleset-diff.sh
#
# `docs/adr/0119`: **shipping a ruleset is an offline diff and a deploy.** The
# rollout ladder in matchmaking-engine.md §22 collapses — canary cannot measure
# its own success and shadow buys a slower version of an answer already on hand
# — so what is left is the diff, and it has to be a build gate rather than a
# habit. That is this, in the idiom this repository already uses twice:
# regenerate, then look for a diff.
#
# The synthetic corpus's answers are a committed artifact. A ruleset edited
# without regenerating its diff fails the build, exactly as a contract changed
# without its client types does — and the report the generator prints on the way
# through **is the diff**, because the file on disk is what the last released
# ruleset answered.
#
#   exit 0  the artifacts reproduce, under both seeds
#   exit 1  drift — a ruleset moved and its diff was not regenerated, or an
#           artifact was hand-edited; or the pipeline is not deterministic
#   exit 2  the check could not run (no poetry, no backend installed)
#
# **It regenerates under two different PYTHONHASHSEEDs and requires both to
# reproduce.** That is `docs/adr/0105` §4's sanctioned exception used a second
# time — *"the one place a seed is set deliberately is the test in §2, which
# sets two of them and compares"* — and it costs one environment variable. It
# turns the artifact into a **continuous whole-pipeline determinism assertion**:
# §2 asserts determinism over one test, and this asserts it over a population, a
# generator, four surfaces and every sort between them, on every pull request.
# Two pinned seeds rather than one, because the committed file was produced
# under whatever seed its author's shell happened to hand them, and a check that
# compared against one seed would be comparing against an unknown.
#
# **What it compares is the file on disk against what regenerating it produces,
# and never the working tree against HEAD.** Regeneration overwrites the
# evidence, so by the time git could be asked the hand edit is already gone —
# which reports an uncommitted hand edit as clean and, worse, reports a
# perfectly regenerated but not-yet-committed artifact as drift. Snapshotting
# first is right in both directions and needs no git at all.
#
# **It leaves the files regenerated**, which is the fix and not a side effect.
# `make gen-ruleset-diff` is the same run without the comparison.
#
# **Half of this gate is a signature and that is said out loud.** The
# recorded-corpus diff cannot run here — there is no database, and
# `docs/adr/0118` §7 restricts it to a restore — so nothing below asserts
# anything about it. What the pull request owes is a report block naming its
# corpus window and its coverage, signed by the owner accountable for the
# quality floor (`docs/adr/0119` §5): **presence, not truth.**
#
# Tested by .github/scripts/test-ruleset-diff.sh (`make test-ruleset-diff`).
# A check that has never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

# The committed artifacts, named file by file. Watching the directory would
# report a neighbouring file as ruleset drift, which is the sort of false
# failure that teaches people to ignore a check.
GENERATED=(
  "docs/specs/matchmaking/ruleset-diff/population.thin.json"
  "docs/specs/matchmaking/ruleset-diff/answers.thin.json"
)

# Two seeds, neither of them 0 — which disables hash randomisation rather than
# choosing a value for it, and would make one of the two runs the odd one out
# for a reason unrelated to the ruleset.
SEEDS=(1 524287)

for f in "${GENERATED[@]}"; do
  [ -f "$ROOT/$f" ] || { echo "missing: $f" >&2; exit 2; }
done

BEFORE=$(mktemp -d) || exit 2
trap 'rm -rf "$BEFORE"' EXIT INT TERM
for f in "${GENERATED[@]}"; do
  cp "$ROOT/$f" "$BEFORE/$(basename "$f")" || exit 2
done

cd "$ROOT/backend" || exit 2

drifted=()
for seed in "${SEEDS[@]}"; do
  if ! PYTHONHASHSEED="$seed" poetry run python -m scripts.ruleset_diff; then
    echo >&2
    echo "Could not re-derive the ruleset diff (PYTHONHASHSEED=$seed)." >&2
    echo "The check needs the backend installed — 'poetry install' in backend/." >&2
    exit 2
  fi
  for f in "${GENERATED[@]}"; do
    cmp -s "$BEFORE/$(basename "$f")" "$ROOT/$f" || drifted+=("$f (PYTHONHASHSEED=$seed)")
    # **Both seeds are compared against the committed file, never against each
    # other**, which is the stronger of the two claims and makes the weaker one
    # free: if each run equals the commit then the runs are equal. Restoring
    # between them is what makes that true — and it also keeps every run's
    # printed report a diff against the *release*, rather than the second one
    # comparing the first run to itself and reporting nothing moved.
    cp "$BEFORE/$(basename "$f")" "$ROOT/$f"
  done
done

# One entry per file, whichever seeds produced it: two seeds drifting on one
# file is one hand-edited artifact, and printing it twice reads as two.
if [ ${#drifted[@]} -gt 0 ]; then
  mapfile -t drifted < <(printf '%s\n' "${drifted[@]}" | sort -u)
fi

cd "$ROOT" || exit 2

if [ ${#drifted[@]} -eq 0 ]; then
  echo
  echo "OK — the ruleset diff reproduces, under both hash seeds."
  exit 0
fi

# Regenerate once more so the tree is left holding the fix rather than the
# snapshot, which is what the failure below tells the reader to commit.
(cd "$ROOT/backend" && poetry run python -m scripts.ruleset_diff >/dev/null 2>&1)

# ---------------------------------------------------------------------------
# Drift. Say what to run. A drift failure that does not tell you how to fix it
# is one that gets worked around.
# ---------------------------------------------------------------------------
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  echo "::error title=Ruleset diff drift::The synthetic corpus answers differently than the committed artifact. Run 'make gen-ruleset-diff' at the repository root, read the report, and argue for the diff in the pull request."
fi

cat >&2 <<EOF

────────────────────────────────────────────────────────────────────────────
  RULESET DIFF DRIFT
────────────────────────────────────────────────────────────────────────────

  Running the synthetic corpus against the ruleset in this tree produced
  answers different from the committed ones. **That difference is the diff**,
  and the report above says what it moves: the classification, the verdict
  rates, the floor crossings and what this corpus cannot see.

  Either a ruleset changed and its diff was not regenerated with it, or an
  artifact was hand-edited — it never should be — or the same seed produced
  two different answers, which is a determinism failure and not a ruleset
  change at all. The seed each run used is printed beside each file below.

  Did not reproduce:

$(printf '      %s\n' "${drifted[@]}")

  **A diff here is a ruleset release** (docs/adr/0119 §5). Regenerating is not
  the whole fix:

      · the pull request carries one line per changed constant — the
        hypothesis, and what would falsify it (ranking-weights.md §13);
      · it carries the recorded-corpus report block, naming its corpus window
        and its coverage. Nothing here can check that block is true; what is
        checked is that somebody wrote it;
      · the owner accountable for the quality floor signs the release.

  They have been regenerated in place — this check and \`make gen-ruleset-diff\`
  run the same derivation. Read the report, then:

      git add ${GENERATED[*]}

────────────────────────────────────────────────────────────────────────────
EOF

exit 1
