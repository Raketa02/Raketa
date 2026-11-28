#!/bin/bash
# ---------------------------------------------------------------------------
# The brand check: the old name stays out (ADR-0211 §7).
#
#   bash .github/scripts/check-brand.sh              # or: make brand
#   bash .github/scripts/check-brand.sh allowlist    # print the allowlist
#
# The company is Rakieta. The rename (#889) took the old spelling out of about
# 11,000 places in 1,431 files and 30 paths, and nothing else stops it coming
# back: a sentence copied from an old issue, a mock exported under its old file
# name, an agent's habit. This goes red the day a case-insensitive search for
# the old name finds any tracked file's content or any tracked path outside the
# allowlist below.
#
#   exit 0  the old name is only where the allowlist says, as often as it says
#   exit 1  it is somewhere else, or an allowlisted file holds another count
#   exit 2  the check could not run, which is never a pass
#
# **The allowlist counts occurrences per file.** It lists the passages that quote
# the old spelling as history, each with a note pointing at ADR-0211 (§6); then
# ADR-0211, which has to name what it supersedes; then this check and its test,
# which hold the pattern. Each line gives how often its file may say the old
# name, and the count must match exactly:
#
#   * one more is red, so listing a whole file never lets a new one slip in;
#   * one fewer is red too, because a count above what its file holds is slack
#     the next occurrence would fill unseen. Lower it, or delete the line.
#
# Raising a count is a review question (ADR-0211, Consequences): the new
# occurrence must be a passage about the spelling itself, never copy, an
# identifier or a link. **Paths have no allowlist.** No passage needs one, and a
# path is something people type.
#
# **Tracked files only, and every byte of them.** The content search reads the
# working tree's copy of every tracked file, binary files included (a mock's
# embedded title is content too), and the path search reads every tracked path.
# An untracked scratch file can't fail a run. It fails the day it is added.
#
# Only bash, git and awk, so it runs as is in CI, on the Mac and in Git Bash on
# Windows. Bash 3.2 is enough, which rules out associative arrays.
#
# Tested by .github/scripts/test-brand.sh (`make test-brand`).
# A check that has never once failed is indistinguishable from one that cannot.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
SELF=".github/scripts/check-brand.sh"

# The old name, and the one place this script spells it. It is searched as
# letters in any case, inside anything: within an identifier, a file name or a
# longer word it is still the old brand.
OLD=raketa

# `<count> <path>`, the path from the repo root. Blank lines and `#` lines are
# skipped.
ALLOWLIST='
# The passages ADR-0211 §6 keeps, which quote the old spelling as history.
9 docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md
6 docs/adr/0209-a-drawn-splash-opens-the-app-and-startup-runs-behind-it.md
3 docs/adr/README.md
1 docs/specs/matchmaking/the-words.md
2 docs/specs/splash-screen/README.md
5 docs/specs/splash-screen/decisions.md

# ADR-0211, which names what it supersedes.
2 docs/adr/0211-the-brand-is-rakieta-everywhere.md

# This check and its test, which hold the pattern.
1 .github/scripts/check-brand.sh
1 .github/scripts/test-brand.sh
'

# The allowlist as `<count> <path>` lines, or a refusal naming the bad line.
entries() {
  local line count path seen=""
  while IFS= read -r line; do
    case "$line" in '' | '#'*) continue ;; esac
    count=${line%% *}
    path=${line#* }
    case "$count" in
      '' | *[!0-9]*)
        echo "$SELF: the allowlist line '$line' does not start with a count." >&2
        return 2
        ;;
    esac
    if [ "$path" = "$line" ] || [ -z "$path" ]; then
      echo "$SELF: the allowlist line '$line' names no path." >&2
      return 2
    fi
    case "$seen" in
      *"
$path
"*)
        echo "$SELF: the allowlist names $path twice." >&2
        return 2
        ;;
    esac
    seen="$seen
$path
"
    printf '%s %s\n' "$count" "$path"
  done <<<"$ALLOWLIST"
}

case "${1:-}" in
  '') ;;
  allowlist)
    entries
    exit $?
    ;;
  *)
    echo "usage: check-brand.sh             (search the tree)" >&2
    echo "       check-brand.sh allowlist   (print the allowlist)" >&2
    exit 2
    ;;
esac

allowed=$(entries) || exit 2

cd "$ROOT" || exit 2
command -v git >/dev/null || { echo "check-brand.sh needs git, and there is none." >&2; exit 2; }

# The tree to search is the one this script sits in. Anywhere else, "tracked"
# would mean some other repository's files, or none.
if ! cdup=$(git rev-parse --show-cdup 2>/dev/null); then
  echo "$ROOT is not in a git work tree, so nothing is tracked and nothing was searched." >&2
  exit 2
fi
if [ -n "$cdup" ]; then
  echo "$ROOT is not the top of its git work tree, so its tracked files are not this tree's." >&2
  exit 2
fi

# Pinned, so a user's grep or color settings can't reshape the output parsed
# below: no line numbers, no columns, no escape codes, paths unquoted.
GIT="git -c core.quotepath=off -c color.ui=never -c color.grep=never -c grep.lineNumber=false -c grep.column=false"

tracked=$($GIT ls-files | wc -l | tr -d ' ')
if [ "$tracked" = 0 ]; then
  echo "$ROOT tracks no files, so the check has lost its subject." >&2
  exit 2
fi

# Every occurrence, one `<path>:<match>` line each (-o), in any case (-i), as a
# fixed string (-F), with binary files read as text (-a). The match always has
# the pattern's length, so the path is everything before it and its colon, even
# when the path holds a colon of its own.
hits=$($GIT grep --no-color -a -i -o -F -e "$OLD" -- .)
status=$?
if [ "$status" -gt 1 ]; then
  echo "git grep failed (exit $status), so nothing was searched." >&2
  exit 2
fi

TAB=$(printf '\t')

# `<count><TAB><path>` for every file that holds the old name.
found=$(printf '%s\n' "$hits" | awk -v n="${#OLD}" '
  length($0) > n { held[substr($0, 1, length($0) - n - 1)]++ }
  END { for (path in held) printf "%d\t%s\n", held[path], path }
' | sort -t "$TAB" -k 2)

# The paths are not counted: any path that says it is red.
paths=$($GIT ls-files | grep -i -F -e "$OLD")

# How often a file holds the old name: what `found` says, or 0.
held() {
  P="$1" awk -F '\t' '$2 == ENVIRON["P"] { print $1; found = 1 } END { if (!found) print 0 }' <<<"$found"
}

# What the allowlist gives a file, or nothing when it is not listed.
allows() {
  P="$1" awk '{ count = $1; sub(/^[^ ]+ /, "") } $0 == ENVIRON["P"] { print count }' <<<"$allowed"
}

unlisted=""
miscounted=""
problems=0

while IFS="$TAB" read -r count path; do
  [ -n "$path" ] || continue
  [ -n "$(allows "$path")" ] && continue
  unlisted="$unlisted$count$TAB$path
"
  problems=$((problems + 1))
done <<<"$found"

while IFS= read -r line; do
  [ -n "$line" ] || continue
  want=${line%% *}
  path=${line#* }
  got=$(held "$path")
  [ "$got" = "$want" ] && continue
  miscounted="$miscounted$got$TAB$want$TAB$path
"
  problems=$((problems + 1))
done <<<"$allowed"

if [ -n "$paths" ]; then
  problems=$((problems + $(printf '%s\n' "$paths" | grep -c .)))
fi

listed=$(printf '%s\n' "$allowed" | grep -c .)

if [ "$problems" = 0 ]; then
  echo "OK — no tracked path says the old name, and of $tracked tracked files only the $listed allowlisted ones do, each exactly as often as its line says."
  exit 0
fi

# ---------------------------------------------------------------------------
# Red. Name every file and path, and say what to do: a failure that doesn't
# say how to fix it is one that gets worked around.
# ---------------------------------------------------------------------------
if [ -n "${GITHUB_ACTIONS:-}" ]; then
  while IFS="$TAB" read -r count path; do
    [ -n "$path" ] && echo "::error file=$path,title=Brand check::This file says the old name $count time(s), and the allowlist does not name it. The brand is Rakieta (ADR-0211)."
  done <<<"$unlisted"
  while IFS= read -r path; do
    [ -n "$path" ] && echo "::error file=$path,title=Brand check::This path says the old name. The brand is Rakieta (ADR-0211)."
  done <<<"$paths"
  while IFS="$TAB" read -r got want path; do
    [ -n "$path" ] && echo "::error file=$path,title=Brand check::This file holds the old name $got time(s), and the allowlist in $SELF gives $want."
  done <<<"$miscounted"
fi

cat >&2 <<EOF

────────────────────────────────────────────────────────────────────────────
  BRAND CHECK: the old name is back
────────────────────────────────────────────────────────────────────────────

  The brand is Rakieta (ADR-0211). A case-insensitive search for "$OLD"
  found it outside the allowlist, which is in $SELF.

EOF

if [ -n "$unlisted" ]; then
  echo "  In files the allowlist does not name:" >&2
  echo >&2
  while IFS="$TAB" read -r count path; do
    [ -n "$path" ] || continue
    echo "    $path  ($count)" >&2
    # The lines themselves, binary files read as such, so a PNG prints one
    # line instead of its bytes.
    $GIT grep --no-color -n -i -F -e "$OLD" -- "$path" 2>/dev/null | head -5 | sed 's/^/        /' >&2
  done <<<"$unlisted"
  echo >&2
fi

if [ -n "$paths" ]; then
  echo "  In tracked paths:" >&2
  echo >&2
  printf '%s\n' "$paths" | sed 's/^/    /' >&2
  echo >&2
fi

if [ -n "$miscounted" ]; then
  echo "  In allowlisted files, at a count the allowlist does not give:" >&2
  echo >&2
  while IFS="$TAB" read -r got want path; do
    [ -n "$path" ] || continue
    if [ "$got" -gt "$want" ]; then
      echo "    $path  holds $got, the allowlist allows $want. The extra one is new." >&2
    elif [ "$got" = 0 ]; then
      echo "    $path  holds 0, the allowlist still says $want. Delete its line." >&2
    else
      echo "    $path  holds $got, the allowlist still says $want. Lower the count." >&2
    fi
  done <<<"$miscounted"
  echo >&2
fi

cat >&2 <<EOF
  Fix: rename it letter for letter, keeping the case, as ADR-0211 §1 says.
  It becomes Rakieta, rakieta or RAKIETA, in identifiers and paths too.
  Every occurrence and every path:

      git grep -n -i $OLD
      git ls-files | grep -i $OLD

  Only a passage about the spelling itself keeps the old name, with a note
  pointing at ADR-0211. Its file's count then changes in the same commit,
  in $SELF, and that is a question for the review.

────────────────────────────────────────────────────────────────────────────
EOF

exit 1
