#!/bin/bash
# ---------------------------------------------------------------------------
# The emitted API contracts reproduce from the code.
#
#   bash .github/scripts/check-contract-freshness.sh
#
# The backend owns the API contract (docs/adr/0006) and `app/api/contract.py`
# emits one document per *surface*. This regenerates them and looks for a diff,
# the way `make gen-api` and the judged pairings do.
#
# **It is not check-contract-drift.sh, and the difference is the point.** That
# script diffs a *client's generated types* against a regeneration with that
# client's own pinned codegen — it takes the backend's document as given and
# never rewrites it. The dev console has no client and no codegen (#256), so the
# analogue for its contract is **freshness**: regenerate the document itself and
# diff the JSON. The two checks compose — freshness says the document matches
# the code, drift says the client's types match the document — and neither is
# the other. `check-contract-drift.sh` keeps taking `frontend_player` as its
# only argument.
#
# It watches **every** document `SURFACES` emits rather than only the dev one,
# because one command writes them all: a run that regenerated `openapi.dev.json`
# while silently rewriting `openapi.player.json` beside it would be a check with
# an unreported side effect. It also closes a real hole — a stale
# `openapi.player.json` is invisible to the drift check, which regenerates the
# client's types *from* it and finds them in perfect agreement.
#
#   exit 0  every emitted contract reproduces from the code
#   exit 1  drift — a route or schema changed and the document was not
#           regenerated, or a document was hand-edited
#   exit 2  the check could not run (no poetry, no document, the emit failed)
#
# **What it compares is the file on disk against what regenerating it produces,
# and never the working tree against HEAD** — the argument check-judged-pairings.sh
# writes out: regeneration overwrites the evidence, so by the time git could be
# asked the hand edit is already gone.
#
# **It leaves the files regenerated**, which is the fix and not a side effect:
# the failure below tells you to commit them.
#
# Tested by .github/scripts/test-contract-freshness.sh (`make test-contract-freshness`).
# A check that has never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

GENERATED=(
  "backend/openapi.player.json"
  "backend/openapi.dev.json"
)

for f in "${GENERATED[@]}"; do
  [ -f "$ROOT/$f" ] || { echo "missing: $f" >&2; exit 2; }
done

BEFORE=$(mktemp -d) || exit 2
trap 'rm -rf "$BEFORE"' EXIT INT TERM
for f in "${GENERATED[@]}"; do
  cp "$ROOT/$f" "$BEFORE/$(basename "$f")" || exit 2
done

cd "$ROOT/backend" || exit 2

# The settings the emit needs, supplied here rather than inherited. A contract is
# the same document in every environment, so pinning them makes the check
# reproducible on a laptop that has a `.env` and on a runner that has nothing.
# `local` specifically because the dev surface refuses to be imported in
# production — which is the gate doing its job, and would read here as a check
# that cannot run.
if ! APP_ENV=local \
     JWT_SECRET_KEY=contract-emit-does-not-sign-anything \
     WRITER_DB_URL="sqlite+aiosqlite:///:memory:" \
     DB_SSL_MODE=disable \
     poetry run python -m app.api.contract; then
  echo >&2
  echo "Could not emit the API contracts." >&2
  echo "The check needs the backend installed — 'poetry install' in backend/." >&2
  exit 2
fi

cd "$ROOT" || exit 2

drifted=()
for f in "${GENERATED[@]}"; do
  cmp -s "$BEFORE/$(basename "$f")" "$ROOT/$f" || drifted+=("$f")
done

if [ ${#drifted[@]} -eq 0 ]; then
  echo
  echo "OK — every emitted contract reproduces from the code."
  exit 0
fi

# ---------------------------------------------------------------------------
# Drift. Say what to run. A drift failure that does not tell you how to fix it
# is one that gets worked around.
# ---------------------------------------------------------------------------
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  echo "::error title=Contract freshness::An emitted OpenAPI document does not reproduce from the code. Run 'make openapi' at the repository root and commit the result — and 'make gen-api' too if openapi.player.json moved."
fi

cat >&2 <<EOF

────────────────────────────────────────────────────────────────────────────
  CONTRACT FRESHNESS
────────────────────────────────────────────────────────────────────────────

  Re-emitting the API contracts produced files different from the ones on disk.
  Either a route or a schema changed and the document was not regenerated, or a
  document was edited by hand — it never should be.

  Did not reproduce:

$(printf '      %s\n' "${drifted[@]}")

  They have been regenerated in place — this check and \`make openapi\` run the
  same emit. Read the diff, then:

      git add ${drifted[*]}

  If backend/openapi.player.json is among them, the player client's wire types
  are generated from it: run \`make gen-api\` and commit those too, or the drift
  check fails next.

────────────────────────────────────────────────────────────────────────────
EOF

for f in "${drifted[@]}"; do
  echo >&2
  echo "  --- $f: on disk → re-emitted" >&2
  diff -u "$BEFORE/$(basename "$f")" "$ROOT/$f" >&2
done

exit 1
