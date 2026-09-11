#!/bin/bash
# ---------------------------------------------------------------------------
# Per-app context pointer for a ROOT session.
#
# SessionStart hook. Tells a session launched at the repo root which per-app
# documents exist and that it does not have them, so it reads them deliberately
# instead of meeting them halfway through the first task.
#
# Why this exists
# ---------------
# Claude Code reads CLAUDE.md from the launch directory *upward*, never
# downward. A session started at the repo root therefore loads the root
# CLAUDE.md alone; backend/CLAUDE.md and frontend_player/CLAUDE.md arrive only
# lazily, when a file in that subtree is first read — which is after the
# session has already chosen an approach. CONTEXT.md and .claude/rules/*.md are
# not a Claude Code convention at all and are loaded automatically in no
# session at any depth; the rules files are linked from nothing and, before
# this hook, had never been read by anything.
#
# Why it names the documents instead of inlining them
# ---------------------------------------------------
# Because inlining does not work, and fails silently. Claude Code inlines only
# the first ~2KB of a SessionStart hook's additionalContext and spills the rest
# to a file in the session's tool-results/ directory. The first version of this
# hook inlined all 268KB of the apps' documents; a root session received the
# header and part of backend/CLAUDE.md, and nothing anywhere reported a
# problem. Measured against 2.1.263 with canaries at doubling byte depths —
# only the 1KB canary came back. test-hooks.sh asserts the budget for that
# reason. The 2KB therefore buys an instruction, and the agent spends the
# tokens with Read, on the app it is actually touching.
#
# What it deliberately does NOT do
# --------------------------------
# It stays silent in a scoped session (`cd backend && claude`). That session
# already gets backend/CLAUDE.md natively by walking up, and pointing it at the
# player app's documents would invite exactly the cross-app edit the ownership
# hook exists to block.
#
# It addresses DOCUMENTS only. Permissions, hooks and skills still come from
# the launch directory alone, so a root session still lacks the apps'
# allowlists and their `api-contract-change` / `new-feature-slice` skills, and
# still owns every app as far as enforce-ownership.sh is concerned. Reading an
# app's documents is not the same as being scoped to it, and the emitted text
# says so.
#
# Requires: jq (already required by enforce-ownership.sh)
# ---------------------------------------------------------------------------
set -uo pipefail

INPUT=$(cat)

# A SessionStart hook must never be able to stop a session from starting, so
# every failure below exits 0 and simply contributes no context.
command -v jq >/dev/null 2>&1 || exit 0

CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')
SOURCE=$(printf '%s' "$INPUT" | jq -r '.source // "startup"')
[ -z "$CWD" ] && CWD="${CLAUDE_PROJECT_DIR:-}"
[ -z "$CWD" ] && exit 0

# `resume` replays the transcript, which already holds this block. The other
# three sources each begin from a context that does not: `startup` and `clear`
# from an empty one, `compact` from a summary that may have dropped the apps'
# invariants while the session is still editing their code.
case "$SOURCE" in
  startup|clear|compact) ;;
  *) exit 0 ;;
esac

# git is the authority on the repo root, not CLAUDE_PROJECT_DIR — that variable
# holds the launch directory, so in a scoped session it IS backend/ and every
# comparison below would call it the root. Same reasoning as enforce-ownership.sh.
ROOT=$(git -C "$CWD" rev-parse --show-toplevel 2>/dev/null)
[ -z "$ROOT" ] && ROOT="${CLAUDE_PROJECT_DIR:-}"
[ -z "$ROOT" ] && exit 0

# Which session is this? RKTA_TIER is the same explicit override the ownership
# hook honours; otherwise a session is "root" only when it launched at the root.
TIER="${RKTA_TIER:-}"
if [ -z "$TIER" ]; then
  [ "$CWD" = "$ROOT" ] && TIER=root || TIER=scoped
fi
[ "$TIER" = root ] || exit 0

# --- name the documents ------------------------------------------------------
# An app is any immediate subdirectory carrying a CLAUDE.md. Deriving the list
# rather than naming backend/ and frontend_player/ means a third app is wired the
# day it lands a CLAUDE.md, and a removed one stops being referenced —
# frontend_club was in this repo once and is named in the hooks still.
#
# This block NAMES the documents, it does not inline them, and that is forced.
# Claude Code inlines only the first ~2KB of a SessionStart hook's
# additionalContext and spills the remainder to a file in the session's
# tool-results/ directory; a 268KB payload arrived as its own first two
# kilobytes and nothing else. Measured against 2.1.263 by injecting canaries at
# doubling byte depths — only the 1KB canary came back. So the budget here buys
# an instruction, and the agent spends the tokens with Read, on the app it is
# actually touching.
kb() { echo "$(( ($(wc -c < "$1") + 512) / 1024 ))K"; }

LIST=""
for app_claude in "$ROOT"/*/CLAUDE.md; do
  [ -f "$app_claude" ] || continue
  app_dir=$(dirname "$app_claude")
  app=$(basename "$app_dir")
  docs="CLAUDE.md ($(kb "$app_claude"))"
  [ -f "$app_dir/CONTEXT.md" ] && docs="$docs, CONTEXT.md ($(kb "$app_dir/CONTEXT.md"))"
  n=0
  for rule in "$app_dir"/.claude/rules/*.md; do [ -f "$rule" ] && n=$((n + 1)); done
  [ "$n" -gt 0 ] && docs="$docs, .claude/rules/*.md ($n files)"
  LIST="$LIST  $app/ — $docs"$'\n'
done

[ -z "$LIST" ] && exit 0

read -r -d '' CTX <<CTX_EOF
This session launched at the REPO ROOT, so it is missing every per-app document.
Claude Code reads CLAUDE.md from the launch directory upward, never downward, so
you have the root CLAUDE.md and neither app's. CONTEXT.md and .claude/rules/*.md
are not memory files at all and are loaded automatically at no depth, in no
session — the rules files in particular are linked from nothing and have never
been read by anything.

Before planning or editing inside an app's tree, read that app's documents:

$LIST
Read the app the work actually touches, not both — both is roughly 65k tokens.
An app's CLAUDE.md is the one to read first; its CONTEXT.md is a glossary and is
worth reading in full only when the work turns on the domain vocabulary.

Two things this does not give you. The session holds the ROOT permission set and
the root skills, not each app's — 'api-contract-change' and 'new-feature-slice'
are not loaded here. And enforce-ownership.sh grants a root session ownership of
every app, so nothing mechanically stops a cross-app edit in this session. The
invariant in CLAUDE.md still stands: one session changes one app. If the work
sits inside a single app, cd into it and relaunch rather than reading your way
around the boundary.
CTX_EOF

jq -n --arg ctx "$CTX" \
  '{hookSpecificOutput: {hookEventName: "SessionStart", additionalContext: $ctx}}'
