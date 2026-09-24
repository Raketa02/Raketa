#!/bin/bash
# ---------------------------------------------------------------------------
# Only the suites the branch's changes can reach — the inner loop, never the gate.
#
#   bash scripts/test-affected.sh [jest flags]     # or: pnpm test:affected
#
# ADR-0181 §2. While iterating on a ticket, this runs Jest's related-test
# selection: `--changedSince` the point where the branch left main, which picks
# every suite that imports — directly or through any chain of imports — a file
# changed on the branch or in the working tree (staged, unstaged or untracked).
# Where there is no such point (no main to compare with, or a shallow clone that
# cannot reach it) it falls back to `--onlyChanged`, the uncommitted changes alone.
#
# The base is the merge base with `main` and `origin/main` taken together, so
# whichever has seen more of this branch's history decides it: a stale local main
# never widens the run by what has since landed upstream.
#
# Extra arguments reach the run, and are meant as Jest flags: given a path
# pattern, Jest drops the selection and runs every suite the pattern matches, as
# `pnpm test <pattern>` would. The deck is a suite like any other: it ran apart
# while it needed 5.4 GB, which was React's scheduler keeping every call on React
# Native's `performance.now` mock (#494, src/test-support/schedulerClock.ts).
#
# It is never the gate. `pnpm test` runs every suite at the end of every ticket
# and in CI. The saving is partial — the router-harness suites import the whole
# route tree, so a change under any screen selects nearly all of them — and a
# change that reaches a suite without an import is invisible to it; CLAUDE.md
# names those.
# ---------------------------------------------------------------------------
set -uo pipefail

APP=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
JEST="$APP/node_modules/.bin/jest"

[ -e "$JEST" ] || { echo "missing: $JEST — run pnpm install first" >&2; exit 2; }

cd "$APP" || exit 2

refs=()
for ref in main origin/main; do
  if git rev-parse --verify --quiet "$ref^{commit}" >/dev/null; then
    refs+=("$ref")
  fi
done

base=""
if [ ${#refs[@]} -gt 0 ]; then
  base=$(git merge-base HEAD "${refs[@]}" 2>/dev/null)
fi

if [ -n "$base" ]; then
  selection="--changedSince=$base"
  echo "test:affected — suites reached by changes since $(git rev-parse --short "$base"), the merge base with main" >&2
else
  selection="--onlyChanged"
  echo "test:affected — no merge base with main; suites reached by uncommitted changes only" >&2
fi

exec "$JEST" "$selection" "$@"
