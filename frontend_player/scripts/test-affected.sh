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
# **The deck runs in a process of its own**, as CI runs it (ci.yml, "Test — the
# deck, in a process of its own", which has the measurements). It peaks near
# 5.4 GB, over Node's default heap, so in a shared run its worker dies with every
# assertion passing — and it is a router suite, so nearly every change under a
# screen selects it. The selection is listed first; everything else runs as
# `pnpm test` would, and the deck after it, only when it was selected. Extra
# arguments reach the listing and both runs, and are meant as Jest flags: given
# a path pattern, Jest drops the selection and runs every suite the pattern
# matches, as `pnpm test <pattern>` would. Not a watch mode — a `--watch` run
# never ends, so the deck's would never start.
#
# A deck that moved fails here loudly: its pattern would match nothing, and the
# deck would join the shared run and bring back the crash.
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
DECK=src/features/play/components/deck.test.tsx
DECK_PATTERN="/$(printf '%s' "$DECK" | sed 's/\./\\./g')\$"

[ -e "$JEST" ] || { echo "missing: $JEST — run pnpm install first" >&2; exit 2; }
[ -e "$APP/$DECK" ] || { echo "missing: $DECK — the deck moved; follow it here and in ci.yml" >&2; exit 2; }

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

listed=$("$JEST" "$selection" --listTests "$@") || exit $?

shared_status=0
"$JEST" "$selection" "$@" --testPathIgnorePatterns '/node_modules/' "$DECK_PATTERN" || shared_status=$?

deck_status=0
if printf '%s\n' "$listed" | grep -q -- "$DECK_PATTERN"; then
  echo "test:affected — the deck, in a process of its own" >&2
  NODE_OPTIONS="${NODE_OPTIONS:+$NODE_OPTIONS }--max-old-space-size=8192" \
    "$JEST" --runTestsByPath "$DECK" --runInBand "$@" || deck_status=$?
fi

[ "$shared_status" -ne 0 ] && exit "$shared_status"
exit "$deck_status"
