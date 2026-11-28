#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the brand check.
#
#   bash .github/scripts/test-brand.sh     # or: make test-brand
#
# check-brand.sh landed last in the rename (ADR-0211 §7), on a tree it already
# passed, so on the committed tree it has never been seen to fail. That is the
# reason test-taskdef.sh, test-contract-freshness.sh and .claude/hooks/
# test-hooks.sh exist. This drives it red the three ways #907 names, plus the
# edges its rule claims:
#
#   * a planted word, in title case, in capitals inside an identifier, and
#     inside a binary file;
#   * a planted path, a file name and a directory;
#   * one extra occurrence in an allowlisted file, and the other way round, an
#     allowlisted file that no longer holds its count;
#
# and asserts it stays green for the new name, for an untracked file, and on a
# tree that keeps the allowlist.
#
# **Every case runs against a scratch tree**: a new git repository holding the
# allowlisted files, copied from this tree, and the check itself among them.
# The check searches what git tracks, so planting means `git add`, and nothing
# here touches this repository's files or its index.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CHECK="$ROOT/.github/scripts/check-brand.sh"
CI_YML="$ROOT/.github/workflows/ci.yml"

# The old name, and the one place this suite spells it. Spelled here and not
# read from the check: a check whose pattern had drifted would otherwise plant
# its own wrong word and pass every case below.
OLD=Raketa
LOWER=$(printf '%s' "$OLD" | tr '[:upper:]' '[:lower:]')
UPPER=$(printf '%s' "$OLD" | tr '[:lower:]' '[:upper:]')

# A hook or a caller's shell may point git elsewhere; each scratch tree must be
# its own repository.
unset GIT_DIR GIT_WORK_TREE GIT_INDEX_FILE GIT_OBJECT_DIRECTORY GIT_COMMON_DIR

pass=0
fail=0

ok()  { pass=$((pass + 1)); printf '  ok    %s\n' "$1"; }
bad() { fail=$((fail + 1)); printf '  FAIL  %s\n' "$1"; [ $# -gt 1 ] && printf '        %s\n' "$2"; }

# The output is captured before it is searched rather than piped into grep:
# `set -o pipefail` above makes a pipeline take the check's exit 1, so
# `check | grep -q` would report a miss on every case that correctly went red.
OUT=""
CODE=0

run_check() { # <tree> — runs the copy of the check inside that tree
  OUT=$(bash "$1/.github/scripts/check-brand.sh" 2>&1)
  CODE=$?
}

had_exit() { # <want> <name>
  [ "$CODE" = "$1" ] && ok "$2" || bad "$2" "want exit $1, got $CODE"
}

said() { # <needle> <name>
  if printf '%s' "$OUT" | grep -qF -- "$1"; then
    ok "$2"
  else
    bad "$2" "output never mentioned '$1'"
  fi
}

for f in "$CHECK" "$CI_YML"; do
  [ -f "$f" ] || { echo "missing: $f" >&2; exit 2; }
done

ALLOWED=$(bash "$CHECK" allowlist) || { echo "the check could not print its allowlist" >&2; exit 2; }
[ -n "$ALLOWED" ] || { echo "the check's allowlist is empty, so no scratch tree can keep it" >&2; exit 2; }

TMP=$(mktemp -d) || exit 2
trap 'rm -rf "$TMP"' EXIT INT TERM

# git in the scratch tree, quietly, and with no line-ending conversion: the
# copies keep the bytes this tree has, CRLF or not.
git_in() {
  git -C "$TREE" -c core.autocrlf=false -c core.safecrlf=false "$@" >/dev/null 2>&1
}

# A fixture that does not happen stops the run rather than counting one failure
# and going on: every case after it would test a tree that was never perturbed.
must() { # <what> <command…>
  local what="$1"
  shift
  "$@" && return 0
  printf '  FAIL  fixture: %s\n' "$what"
  printf '        every case below would run against the wrong tree.\n'
  exit 2
}

trees=0
TREE=""

# A new repository holding every allowlisted file at its path (the check and
# this suite among them), and the new name in a file and in a path. All tracked.
fresh_tree() {
  local count path
  trees=$((trees + 1))
  TREE="$TMP/tree-$trees"
  must "git init $TREE" git init -q "$TREE"
  while read -r count path; do
    mkdir -p "$TREE/$(dirname "$path")"
    must "copy $path into the scratch tree" cp "$ROOT/$path" "$TREE/$path"
  done <<<"$ALLOWED"
  mkdir -p "$TREE/frontend_club/src/features/rakieta-settings"
  printf 'Rakieta for Clubs, rakieta://join, RAKIETA_SETTINGS_PATH\n' \
    >"$TREE/frontend_club/src/features/rakieta-settings/README.md"
  must "git add the scratch tree" git_in add -A
}

plant() { # <path> <printf format> [args…] — writes a file and tracks it
  local path="$1"
  shift
  mkdir -p "$TREE/$(dirname "$path")"
  # shellcheck disable=SC2059 # the format is the caller's, on purpose
  printf "$@" >"$TREE/$path"
  must "git add $path" git_in add -- "$path"
}

# The first file on the allowlist, whichever it is, and the count it is given.
read -r FIRST_COUNT FIRST <<<"$(printf '%s\n' "$ALLOWED" | head -1)"

# ---------------------------------------------------------------------------
echo
echo "check-brand.sh — the committed tree"

run_check "$ROOT"
had_exit 0 "the old name is only where the allowlist says, as often as it says"

# ---------------------------------------------------------------------------
echo
echo "a scratch tree that keeps the allowlist"

fresh_tree
run_check "$TREE"
had_exit 0 "the allowlisted files at their counts pass, and the new name in a file and a path with them"

fresh_tree
printf 'Notes on the %s days.\n' "$OLD" >"$TREE/scratch.md"
run_check "$TREE"
had_exit 0 "an untracked file is not the tree's, so it cannot fail a run"

# ---------------------------------------------------------------------------
echo
echo "a planted word"

# The case the check exists for: a sentence copied from an old issue or mock.
fresh_tree
plant "frontend_player/src/features/home/copy.ts" 'export const TITLE = "Book a court on %s";\n' "$OLD"
run_check "$TREE"
had_exit 1 "a planted word is red"
said "BRAND CHECK" "the failure says what went red"
said "frontend_player/src/features/home/copy.ts" "the failure names the file"
said "Book a court on" "the failure shows the line"
said "ADR-0211" "the failure points at the rule"

# Case-insensitive, and a substring: inside an identifier it is still the brand.
fresh_tree
plant "backend/app/paths.py" 'NEW_IN_%s_PATH = "/api/v1/new"\n' "$UPPER"
run_check "$TREE"
had_exit 1 "the word in capitals, inside an identifier, is red"
said "backend/app/paths.py" "the failure names that file"

# A binary file is content too: a mock's embedded title, an exported PDF.
fresh_tree
plant "docs/mocks/home.png" '\211PNG\r\n\032\n\000\000\000\015tEXtTitle\000%s home\000\000' "$OLD"
run_check "$TREE"
had_exit 1 "the word inside a binary file is red"
said "docs/mocks/home.png" "the failure names the binary file"

# ---------------------------------------------------------------------------
echo
echo "a planted path"

# The file's content is the new name, so only the path rule can catch it.
fresh_tree
plant "docs/mocks/${LOWER}-home.txt" 'Rakieta\n'
run_check "$TREE"
had_exit 1 "a file name carrying the word is red"
said "In tracked paths" "the failure reads it as a path"
said "docs/mocks/${LOWER}-home.txt" "the failure names the path"

# A directory, so a rule that read only a file's own name would miss it.
fresh_tree
plant "frontend_public/${OLD}/notes.md" 'Rakieta\n'
run_check "$TREE"
had_exit 1 "a directory carrying the word is red"
said "frontend_public/${OLD}/notes.md" "the failure names the whole path"

# ---------------------------------------------------------------------------
echo
echo "the allowlist counts, it does not wave a file through"

# One more occurrence in a file that may already say it. Left unstaged on
# purpose: the check reads the working tree, which is what the next commit
# takes, not the index.
fresh_tree
printf '\nAnd one more: %s.\n' "$OLD" >>"$TREE/$FIRST"
run_check "$TREE"
had_exit 1 "one extra occurrence in an allowlisted file is red"
said "$FIRST" "the failure names the allowlisted file"
said "holds $((FIRST_COUNT + 1)), the allowlist allows $FIRST_COUNT" "the failure gives both counts"

# The other way round. A count above what its file holds is slack the next
# occurrence would fill unseen, so a passage gone is a line to delete.
fresh_tree
must "git rm $FIRST" git_in rm -q -f -- "$FIRST"
run_check "$TREE"
had_exit 1 "an allowlisted file that no longer holds its count is red"
said "holds 0, the allowlist still says $FIRST_COUNT" "the failure says the line is stale"

# ---------------------------------------------------------------------------
echo
echo "the check refuses rather than passing when it cannot run"

# Outside a repository nothing is tracked. Nothing searched is not a pass.
mkdir -p "$TMP/no-git/.github/scripts"
cp "$CHECK" "$TMP/no-git/.github/scripts/check-brand.sh"
OUT=$(GIT_CEILING_DIRECTORIES="$TMP" bash "$TMP/no-git/.github/scripts/check-brand.sh" 2>&1)
CODE=$?
had_exit 2 "a tree that is not a git repository is a usage error, not a pass"

# An allowlist line the check cannot read is refused by name, never skipped.
fresh_tree
copy="$TREE/.github/scripts/check-brand.sh"
cp "$copy" "$TMP/check.before"
sed -i.bak 's|^\([0-9][0-9]*\) docs/adr/|x docs/adr/|' "$copy" && rm -f "$copy.bak"
if cmp -s "$copy" "$TMP/check.before"; then
  bad "an unreadable allowlist line" "the perturbation matched nothing in check-brand.sh, so the case tests nothing"
else
  run_check "$TREE"
  had_exit 2 "an allowlist line with no count is a usage error, not a pass"
  said "does not start with a count" "the refusal names the line"
fi

# ---------------------------------------------------------------------------
echo
echo "CI wiring"

# The reason this suite exists at all: a check CI does not run is not a gate.
grep -q 'check-brand.sh' "$CI_YML" \
  && ok "ci.yml runs the check" \
  || bad "ci.yml runs the check" "no step invokes check-brand.sh"

grep -q 'test-brand.sh' "$CI_YML" \
  && ok "ci.yml runs this suite" \
  || bad "ci.yml runs this suite" "no step invokes test-brand.sh"

# ---------------------------------------------------------------------------
echo
printf '  %d passed, %d failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
