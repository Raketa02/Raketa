#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the contract-freshness check.
#
#   bash .github/scripts/test-contract-freshness.sh   # or: make test-contract-freshness
#
# check-contract-freshness.sh was added to a tree that already satisfied it, so
# it has never been seen to fail — the same reason test-contract-drift.sh,
# test-judged-pairings.sh and .claude/hooks/test-hooks.sh exist. This drives it
# against each shape of failure it claims to catch and asserts it goes red, and
# against the committed tree and asserts it goes green.
#
# **Every document is perturbed, separately** — the player's, the dev console's,
# the club website's and the public site's. A suite that only ever broke the
# player one would leave the others unexercised, which is the exact failure the
# whole idiom exists to refuse; and for as long as the check typed its own list
# of two, the club's and the public site's documents went unwatched (#527). The
# check now reads its documents from what the emit writes, so the last cases
# here are the two ways that set and the files on disk can disagree: a document
# the emit writes that is not on disk, and one on disk that nothing emits.
#
# Every case perturbs a real file in place and restores the original bytes on
# exit — including on failure or interrupt — so it is safe to run on a dirty
# tree. It needs no git: the check compares a file against what regenerating it
# produces, never against HEAD.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-contract-freshness.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"
PLAYER="$ROOT/backend/openapi.player.json"
DEV="$ROOT/backend/openapi.dev.json"
CLUB="$ROOT/backend/openapi.club.json"
PUBLIC="$ROOT/backend/openapi.public.json"
ORPHAN="$ROOT/backend/openapi.orphan.json"
ROUTES="$ROOT/backend/app/api/dev/routes.py"

pass=0
fail=0

ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

# Run ONCE per perturbation and hold the output, because the check REPAIRS what
# it finds: a second invocation would see a regenerated tree, exit 0 and say
# nothing, and every assertion about the failure message would miss for the
# wrong reason.
OUT=""
CODE=0

run_check() {
  OUT=$(bash "$CHECK" 2>&1)
  CODE=$?
}

had_exit() { # <want> <name>
  [ "$CODE" = "$1" ] && ok "$2" || bad "$2" "want exit $1, got $CODE"
}

said() { # <needle> <name>
  if printf '%s' "$OUT" | grep -qF "$1"; then
    ok "$2"
  else
    bad "$2" "output never mentioned '$1'"
  fi
}

expect_exit() { # <want> <name>
  run_check
  had_exit "$1" "$2"
}

# `jq` is not assumed — CI's backend job has Python and nothing else guaranteed.
edit_doc() { # <path> <python expression over `data`>
  python3 - "$1" "$2" <<'PY'
import json, sys
path, program = sys.argv[1], sys.argv[2]
data = json.load(open(path, encoding="utf-8"))
exec(program)
with open(path, "w", encoding="utf-8") as out:
    json.dump(data, out, indent=2)
    out.write("\n")
PY
}

# One surface's source, edited by a literal replacement that must happen — a
# replacement that silently matched nothing would leave the source untouched and
# turn a red case green for the wrong reason.
edit_source() { # <path> <old> <new>
  python3 - "$1" "$2" "$3" <<'PY'
import sys
path, old, new = sys.argv[1], sys.argv[2], sys.argv[3]
source = open(path, encoding="utf-8").read()
if old not in source:
    sys.exit(f"edit_source: {old!r} is not in {path}")
open(path, "w", encoding="utf-8").write(source.replace(old, new))
PY
}

for f in "$CHECK" "$CI_YML" "$PLAYER" "$DEV" "$CLUB" "$PUBLIC" "$ROUTES"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done
[ -e "$ORPHAN" ] && { echo "in the way: $ORPHAN" >&2; exit 2; }

TMP=$(mktemp -d)
cp "$PLAYER" "$TMP/player.json"
cp "$DEV" "$TMP/dev.json"
cp "$CLUB" "$TMP/club.json"
cp "$PUBLIC" "$TMP/public.json"
cp "$ROUTES" "$TMP/routes.py"
restore() {
  cp "$TMP/player.json" "$PLAYER"
  cp "$TMP/dev.json" "$DEV"
  cp "$TMP/club.json" "$CLUB"
  cp "$TMP/public.json" "$PUBLIC"
  cp "$TMP/routes.py" "$ROUTES"
  rm -f "$ORPHAN"
}
trap 'restore; rm -rf "$TMP"' EXIT INT TERM

# ---------------------------------------------------------------------------
echo
echo "check-contract-freshness.sh — the committed tree"

expect_exit 0 "every emitted contract reproduces"

# ---------------------------------------------------------------------------
echo
echo "a hand-edited document"

# The case the generate-commit-diff idiom exists for: somebody corrects a
# description in the JSON instead of in the code that emits it.
edit_doc "$DEV" "data['paths']['/dev/roster']['get']['summary'] = 'hand-edited'"
run_check
had_exit 1 "a hand-edited openapi.dev.json is drift"
said "CONTRACT FRESHNESS" "the failure names the drift"
said "backend/openapi.dev.json" "the failure names the document that did not reproduce"
said "git add" "the failure says what to run"
restore

edit_doc "$PLAYER" "data['info']['version'] = '0.0.0-hand-edited'"
run_check
had_exit 1 "a hand-edited openapi.player.json is drift"
said "backend/openapi.player.json" "the failure names that document too"
said "make gen-api" "the failure says the client's types are generated from it"
said "frontend_player" "the failure names the client that generates from it"
restore

# The two documents ADR-0187 §5 added, each with a client of its own. A stale
# one is invisible to that client's drift check, which regenerates the types
# FROM it and finds them in perfect agreement — so this is the only gate that
# sees it.
edit_doc "$CLUB" "data['info']['title'] = 'Raketa Club API, hand-edited'"
run_check
had_exit 1 "a hand-edited openapi.club.json is drift"
said "backend/openapi.club.json" "the failure names the club website's document"
said "frontend_club" "the failure names the club website as its client"
restore

edit_doc "$PUBLIC" "data['info']['title'] = 'Raketa Public API, hand-edited'"
run_check
had_exit 1 "a hand-edited openapi.public.json is drift"
said "backend/openapi.public.json" "the failure names the public site's document"
said "frontend_public" "the failure names the public site as its client"
restore

# ---------------------------------------------------------------------------
echo
echo "a surface changed without regenerating"

# The real shape: the code moves and the committed document does not. This is
# the half `check-contract-drift.sh` cannot see — it regenerates the client's
# types FROM the stale document and finds them in perfect agreement.
edit_source "$ROUTES" \
  'summary="The accounts the console may act as, and the one password"' \
  'summary="A summary nobody regenerated the document for"'
run_check
had_exit 1 "a route changed without regenerating is drift"
said "backend/openapi.dev.json" "the failure names the dev document"
restore

# ---------------------------------------------------------------------------
echo
echo "the documents are what the emit writes, not a list"

# A surface whose document was never committed: the emit writes a file that was
# not on disk. Removing one is the same shape, and it is the shape a new surface
# arrives in — so it is drift, named, and never a pass.
mv "$DEV" "$TMP/moved.json"
run_check
had_exit 1 "a document the emit writes and the tree lacks is drift"
said "backend/openapi.dev.json" "the failure names the document that was not on disk"
said "git add" "the failure says to commit it"
restore
rm -f "$TMP/moved.json"

# The other way round: a document on disk that no surface emits any more. A
# client could go on generating from it for ever, and a check that only compared
# what it re-emitted would never look at it.
cp "$DEV" "$ORPHAN"
run_check
had_exit 1 "a document no surface emits is drift"
said "backend/openapi.orphan.json" "the failure names the orphaned document"
said "git rm" "the failure says to delete it"
restore

# ---------------------------------------------------------------------------
echo
echo "the check refuses rather than passing when it cannot run"

# A backend that cannot even import has emitted nothing, and nothing compared
# is not a pass.
printf '\nthis is not python\n' >>"$ROUTES"
expect_exit 2 "a backend that cannot emit is a usage error, not a pass"
restore

expect_exit 0 "the tree is restored between cases"

# ---------------------------------------------------------------------------
echo
echo "CI wiring"

# The reason this suite exists at all: a check CI does not run is not a gate.
if grep -q 'check-contract-freshness.sh' "$CI_YML"; then
  ok "ci.yml runs the check"
else
  bad "ci.yml runs the check" "no step invokes check-contract-freshness.sh"
fi

if grep -q 'test-contract-freshness.sh' "$CI_YML"; then
  ok "ci.yml runs this suite"
else
  bad "ci.yml runs this suite" "no step invokes test-contract-freshness.sh"
fi

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
