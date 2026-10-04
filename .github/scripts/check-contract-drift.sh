#!/bin/bash
# ---------------------------------------------------------------------------
# Contract drift check.
#
#   bash .github/scripts/check-contract-drift.sh <client>
#
# The backend owns the API contract and emits one document per surface
# (docs/adr/0006, docs/adr/0187 §5). Each client generates its wire types from
# its own document. This asserts one client and its document agree: regenerate,
# then look for a diff.
#
# **A client is an app whose package.json declares `gen:api`** — today
# frontend_player (openapi.player.json), frontend_club (openapi.club.json) and
# frontend_public (openapi.public.json). The script names none of them: who is
# a client, and which document each reads, are contract-clients.sh's answers,
# read from each app's own `gen:api` script — so a client added with that script
# is checkable the day it lands, and an app without one is refused rather than
# guessed at.
#
#   exit 0  the committed wire types reproduce from the committed contract
#   exit 1  drift — a contract change was shipped without its client types,
#           or src/generated/ was hand-edited and committed
#   exit 2  the check could not run (bad argument, generator failed)
#
# It runs the app's OWN `pnpm gen:api` rather than restating the generator
# invocation, for two reasons. That script is already the single definition of
# how this client's types are generated and which document it reads, so the two
# cannot disagree. And it resolves openapi-typescript from the app's lockfile:
# the generator's output formatting changes between versions, so regenerating
# with a floating or separately-pinned version reports *version* drift as
# contract drift. A false failure here is worse than no check at all, because it
# is the thing that teaches people to ignore this one.
#
# What git compares is the working tree against HEAD, so the hand-edit case is
# the committed one: a hand-edit that was never committed is simply overwritten
# by the regeneration and there is nothing to report — correctly, since CI only
# ever sees what was committed.
#
# Tested by .github/scripts/test-contract-drift.sh (`make test-drift`). A check
# that has never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

source "$ROOT/.github/scripts/contract-clients.sh"

# The argument is one of the clients by name — never a path, never an app with
# no `gen:api`.
clients=$(contract_clients | tr '\n' ' ')
app="${1:-}"
case " $clients" in
  *" $app "*) [ -n "$app" ] ;;
  *) false ;;
esac || {
  echo "usage: $0 <client>" >&2
  echo "  a client is an app whose package.json declares gen:api: ${clients:-none}" >&2
  exit 2
}

# Both paths come out of the app's own `gen:api` script: the document it reads,
# and the file it writes. Deriving them means the failure message cannot name a
# different document from the command that produced it — and, more importantly,
# that what gets diffed is exactly the generator's output. Scoping the diff to
# src/generated/ as a directory would report an edit to the README.md that lives
# beside the output as contract drift, which is the sort of false failure that
# teaches people to ignore this check.
read -r doc generated <<<"$(gen_api_of "$app")"

if [ -z "$doc" ] || [ -z "${generated:-}" ]; then
  echo "Could not read the document and output path out of $app's gen:api script." >&2
  exit 2
fi

cd "$ROOT/$app" || exit 2

if ! pnpm gen:api; then
  echo >&2
  echo "Could not regenerate $generated." >&2
  echo "The check needs $app installed — 'pnpm install' in $app/." >&2
  exit 2
fi

cd "$ROOT" || exit 2

drift=$(git status --porcelain -- "$generated")

if [ -z "$drift" ]; then
  echo "OK — $generated reproduces from $doc."
  exit 0
fi

# ---------------------------------------------------------------------------
# Drift. Say which app, say what to run. A drift failure that does not tell you
# how to fix it is one that gets worked around.
# ---------------------------------------------------------------------------
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  echo "::error title=Contract drift in $app::$generated does not match $doc. Run 'make gen-api' at the repository root and commit the result."
fi

cat >&2 <<EOF

────────────────────────────────────────────────────────────────────────────
  CONTRACT DRIFT — $app
────────────────────────────────────────────────────────────────────────────

  $doc and $generated disagree.

  Regenerating with this app's own pinned openapi-typescript produced a file
  different from the one committed. Either the contract changed and this
  client was not regenerated with it, or the generated file was edited by
  hand — it never should be.

  Fix — from the repository root:

      make gen-api
      git add $doc $generated

────────────────────────────────────────────────────────────────────────────
EOF

untracked=$(git status --porcelain -- "$generated" | sed -n 's/^?? //p')
if [ -n "$untracked" ]; then
  echo >&2
  echo "  Generated but never committed:" >&2
  echo "$untracked" | sed 's/^/    /' >&2
fi

if ! git --no-pager diff --stat --exit-code -- "$generated" >/dev/null 2>&1; then
  echo >&2
  echo "  The diff:" >&2
  git --no-pager diff -- "$generated" >&2
fi

exit 1
