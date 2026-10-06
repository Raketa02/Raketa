#!/bin/bash
# ---------------------------------------------------------------------------
# The emitted API contracts reproduce from the code.
#
#   bash .github/scripts/check-contract-freshness.sh
#
# The backend owns the API contract (docs/adr/0006) and `app/api/contract.py`
# emits one document per *surface*. This regenerates them and looks for a diff,
# the way `make gen-api` does.
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
# an unreported side effect. It also closes a real hole — a stale client
# document is invisible to that client's drift check, which regenerates the
# types *from* it and finds them in perfect agreement.
#
# **Which documents those are is the emit's answer, never a list typed here.**
# The check used to name its two, and when ADR-0187 §5 added the club website's
# and the public site's, both went unwatched until #527 — green on a hand-edit,
# because nothing compared them. Now the documents are the ones
# `write_contracts()` reports writing, held against every `openapi.*.json` beside
# the backend's package root, and the two sets must agree: a document the emit
# writes that is not on disk was never committed, and one on disk that nothing
# emits is an orphan some client could go on generating from.
#
#   exit 0  every emitted contract reproduces from the code
#   exit 1  drift — a route or schema changed and the document was not
#           regenerated, a document was hand-edited, a surface's document
#           is not on disk, or a document on disk belongs to no surface
#   exit 2  the check could not run (no poetry, the emit failed or wrote nothing)
#
# **What it compares is the file on disk against what regenerating it produces,
# and never the working tree against HEAD**: regeneration overwrites the
# evidence, so by the time git could be asked the hand edit is already gone.
#
# **It leaves the files regenerated**, which is the fix and not a side effect:
# the failure below tells you to commit them.
#
# Tested by .github/scripts/test-contract-freshness.sh (`make test-contract-freshness`).
# A check that has never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)

source "$ROOT/.github/scripts/contract-clients.sh"

cd "$ROOT/backend" || exit 2

# Every document on disk before the emit, kept byte for byte. Bash 3.2 (macOS's
# own) has no `nullglob`-free way to say "none", so an unmatched glob is dropped
# by testing that the file exists.
BEFORE=$(mktemp -d) || exit 2
trap 'rm -rf "$BEFORE"' EXIT INT TERM
for f in openapi.*.json; do
  [ -f "$f" ] || continue
  cp "$f" "$BEFORE/$f" || exit 2
done

# The settings the emit needs, supplied here rather than inherited. A contract is
# the same document in every environment, so pinning them makes the check
# reproducible on a laptop that has a `.env` and on a runner that has nothing.
# `local` specifically because the dev surface refuses to be imported in
# production — which is the gate doing its job, and would read here as a check
# that cannot run.
#
# `write_contracts()` is what `make openapi` runs — `python -m app.api.contract`
# is it plus a line of prose per document — called here for its answer: the file
# name of every document it wrote, one per line. Anything else on stdout is not
# a name and is dropped.
if ! emitted=$(APP_ENV=local \
     JWT_SECRET_KEY=contract-emit-does-not-sign-anything \
     WRITER_DB_URL="sqlite+aiosqlite:///:memory:" \
     DB_SSL_MODE=disable \
     poetry run python -c '
from app.api.contract import write_contracts
for path in write_contracts():
    print(path.name)
'); then
  echo >&2
  echo "Could not emit the API contracts." >&2
  echo "The check needs the backend installed — 'poetry install' in backend/." >&2
  exit 2
fi
emitted=$(printf '%s\n' "$emitted" | grep -E '^openapi\.[A-Za-z0-9_-]+\.json$')

if [ -z "$emitted" ]; then
  echo "The emit reported writing no document — nothing was compared, which is not a pass." >&2
  exit 2
fi

cd "$ROOT" || exit 2

# Three ways to disagree, each named apart because each has its own fix.
drifted=()   # re-emitted, and not what was on disk
unwritten=() # emitted, and not on disk before: never committed, or removed
orphaned=()  # on disk, and no surface emits it
for name in $emitted; do
  if [ ! -f "$BEFORE/$name" ]; then
    unwritten+=("backend/$name")
  elif ! cmp -s "$BEFORE/$name" "backend/$name"; then
    drifted+=("backend/$name")
  fi
done
for kept in "$BEFORE"/openapi.*.json; do
  [ -f "$kept" ] || continue
  name=$(basename "$kept")
  grep -qxF "$name" <<<"$emitted" || orphaned+=("backend/$name")
done

if [ $((${#drifted[@]} + ${#unwritten[@]} + ${#orphaned[@]})) -eq 0 ]; then
  echo
  echo "OK — every emitted contract reproduces from the code:"
  printf '  backend/%s\n' $emitted
  exit 0
fi

# ---------------------------------------------------------------------------
# Drift. Say what to run. A drift failure that does not tell you how to fix it
# is one that gets worked around.
# ---------------------------------------------------------------------------

# The clients that generate their types from a document — contract-clients.sh's
# answer, the one check-contract-drift.sh reads — so a document with no client
# (the dev console's) names none.
clients_of() { # <backend/openapi.x.json>
  local client doc
  for client in $(contract_clients); do
    read -r doc _ <<<"$(gen_api_of "$client")"
    [ "$doc" = "$1" ] && echo "$client"
  done
}

# Bash 3.2 reads an empty "${array[@]}" under `set -u` as unbound, so each list
# is printed only when it has something in it.
print_list() { # <heading> <item>...
  local heading="$1"
  shift
  [ $# -gt 0 ] || return 0
  printf '  %s\n\n' "$heading"
  printf '      %s\n' "$@"
  printf '\n'
}

to_add=()
[ ${#drifted[@]} -gt 0 ] && to_add+=("${drifted[@]}")
[ ${#unwritten[@]} -gt 0 ] && to_add+=("${unwritten[@]}")

regenerate=""
if [ ${#to_add[@]} -gt 0 ]; then
  for doc in "${to_add[@]}"; do
    for client in $(clients_of "$doc"); do
      regenerate+="      $client generates its wire types from $doc"$'\n'
    done
  done
fi

if [ -n "${GITHUB_ACTIONS:-}" ]; then
  echo "::error title=Contract freshness::The emitted OpenAPI documents do not reproduce from the code. Run 'make openapi' at the repository root and commit the result — and 'make gen-api' too if a client's document moved."
fi

{
  cat <<EOF

────────────────────────────────────────────────────────────────────────────
  CONTRACT FRESHNESS
────────────────────────────────────────────────────────────────────────────

  Re-emitting the API contracts produced files different from the ones on disk.
  Either a route or a schema changed and the document was not regenerated, or a
  document was edited by hand — it never should be.

EOF
  [ ${#drifted[@]} -gt 0 ] && print_list "Did not reproduce:" "${drifted[@]}"
  [ ${#unwritten[@]} -gt 0 ] && print_list "Emitted, and not on disk — a surface's document was never committed:" "${unwritten[@]}"
  [ ${#orphaned[@]} -gt 0 ] && print_list "On disk, and no surface emits it:" "${orphaned[@]}"

  if [ ${#to_add[@]} -gt 0 ]; then
    cat <<EOF
  They have been regenerated in place — this check and \`make openapi\` write
  them with the same function. Read the diff, then:

      git add ${to_add[*]}

EOF
  fi
  if [ -n "$regenerate" ]; then
    printf '  A client generates its types from one of them:\n\n%s\n' "$regenerate"
    cat <<EOF
  Run \`make gen-api\` and commit those too, or the drift check fails next.

EOF
  fi
  if [ ${#orphaned[@]} -gt 0 ]; then
    cat <<EOF
  A document no surface emits is left over from one that was removed or
  renamed, and a client could go on generating from it. Delete it:

      git rm ${orphaned[*]}

EOF
  fi
  echo "────────────────────────────────────────────────────────────────────────────"
} >&2

if [ ${#drifted[@]} -gt 0 ]; then
  for f in "${drifted[@]}"; do
    echo >&2
    echo "  --- $f: on disk → re-emitted" >&2
    diff -u "$BEFORE/$(basename "$f")" "$ROOT/$f" >&2
  done
fi

exit 1
