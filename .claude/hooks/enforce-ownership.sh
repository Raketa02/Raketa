#!/bin/bash
# ---------------------------------------------------------------------------
# Ownership boundary guard for the Raketa monorepo.
#
# The repo holds three independently deployable apps. An agent working in one of
# them must not silently edit another — that is how a "small backend fix" quietly
# rewrites the mobile app. This hook makes that boundary mechanical instead of
# a request in a markdown file.
#
# PreToolUse hook on file-mutating tools. Exit 2 blocks the call and returns the
# stderr text to the agent.
#
# Which app a session owns is resolved in this order:
#   1. $RKTA_TIER  — explicit override: root | backend | player | club
#   2. the session's cwd, relative to the repo root
# A session at the repo root owns everything (you are the orchestrator).
#
# Requires: jq
# ---------------------------------------------------------------------------
set -uo pipefail

INPUT=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  echo 'Ownership hook cannot run: jq is not installed (brew install jq). Blocking to fail safe.' >&2
  exit 2
fi

CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')
TOOL=$(printf '%s' "$INPUT" | jq -r '.tool_name // empty')

# The REPO root, which is not $CLAUDE_PROJECT_DIR. That variable holds the
# directory Claude Code was launched from, so in a `cd backend && claude` session
# it is backend/ — and every path outside backend/ would then look like it sits
# outside the repo and get waved through. git is the authority on where the root
# is; CLAUDE_PROJECT_DIR is only the fallback for a non-git checkout, where the
# launch directory is the best guess available.
ROOT=$(git -C "${CWD:-.}" rev-parse --show-toplevel 2>/dev/null)
[ -z "$ROOT" ] && ROOT="${CLAUDE_PROJECT_DIR:-}"
if [ -z "$ROOT" ]; then exit 0; fi

# Edit/Write/MultiEdit use .file_path; NotebookEdit uses .notebook_path.
TARGET=$(printf '%s' "$INPUT" | jq -r '.tool_input.file_path // .tool_input.notebook_path // empty')
[ -z "$TARGET" ] && exit 0

# --- normalize both paths to be relative to the repo root ----------------------
abs() {
  case "$1" in
    /*) printf '%s' "$1" ;;
    *)  printf '%s' "${CWD:-$ROOT}/$1" ;;
  esac
}
# Collapse '.' and '..' segments textually. Without this, 'backend/../frontend_club/x'
# is classified as belonging to backend, and the whole boundary is one '../' away from
# being bypassed — which is the form a relative path from a scoped session naturally
# takes. Purely lexical on purpose: the target file usually does not exist yet, so
# realpath/readlink -f cannot resolve it.
normalize() {
  local path="$1" out='' seg oldifs="$IFS"
  IFS='/'
  set -f                     # a path segment must never be glob-expanded
  for seg in $path; do
    case "$seg" in
      ''|.) ;;
      ..)   out="${out%/*}" ;;   # at the root this stays empty — cannot escape upward
      *)    out="$out/$seg" ;;
    esac
  done
  set +f
  IFS="$oldifs"
  printf '%s' "${out:-/}"
}
relpath() { # strip "$ROOT/" prefix; returns "." when equal
  local p
  p=$(normalize "$1")
  p="${p%/}"
  case "$p" in
    "$ROOT")   printf '.' ;;
    "$ROOT"/*) printf '%s' "${p#"$ROOT"/}" ;;
    *)         printf '%s' "$p" ;;   # outside the repo entirely
  esac
}

REL_TARGET=$(relpath "$(abs "$TARGET")")
REL_CWD=$(relpath "${CWD:-$ROOT}")

app_of() { # map a repo-relative path to the app that owns it
  case "$1" in
    backend|backend/*)                 printf 'backend' ;;
    frontend_player|frontend_player/*) printf 'player'  ;;
    frontend_club|frontend_club/*)     printf 'club'    ;;
    *)                                 printf 'shared'  ;;
  esac
}

# --- which app does this session own? -----------------------------------------
TIER="${RKTA_TIER:-}"
if [ -z "$TIER" ]; then
  if [ "$REL_CWD" = "." ]; then TIER="root"; else TIER=$(app_of "$REL_CWD"); fi
  [ "$TIER" = "shared" ] && TIER="root"
fi

# --- guardrail 1: never let a scoped session disarm its own guardrails ---------
case "$REL_TARGET" in
  .claude/hooks/*|.claude/settings.json)
    if [ "$TIER" != "root" ]; then
      echo "Blocked: '$REL_TARGET' is the ownership/safety guardrail itself, and this session is scoped to '$TIER'. Editing it from inside an app session would let an agent disable its own boundary. Make this change from a repo-root session." >&2
      exit 2
    fi
    ;;
esac

# --- guardrail 2: no writing real secrets, from ANY session --------------------
# guard-bash.sh covers this for the shell; without the same rule here, an agent
# refused `cp x .env.local` could simply Write the file instead. Templates
# (.env*.example) are editable — they exist to be.
BASE="${REL_TARGET##*/}"
case "$BASE" in
  *.example) ;;                       # templates are fine
  .env|.env.*|*.pem|*.key|*.p12|*.jks|*.p8|*.keystore|*.mobileprovision)
    echo "Blocked: '$REL_TARGET' is a real secret/credential file. Agents don't create or edit these — edit the matching .env*.example template and let a human copy it. See CLAUDE.md Safety." >&2
    exit 2
    ;;
esac

# --- guardrail 2: no cross-app writes -----------------------------------------
[ "$TIER" = "root" ] && exit 0

TARGET_APP=$(app_of "$REL_TARGET")
[ "$TARGET_APP" = "shared" ] && exit 0
[ "$TARGET_APP" = "$TIER" ] && exit 0

dir_of() { # bash 3.2 on macOS has no associative arrays — keep this a case
  case "$1" in
    backend) printf 'backend/'         ;;
    player)  printf 'frontend_player/' ;;
    club)    printf 'frontend_club/'   ;;
    *)       printf '%s' "$1"          ;;
  esac
}

cat >&2 <<EOF
Blocked: this session owns '${TIER}' ($(dir_of "$TIER")) but ${TOOL} targets '${REL_TARGET}', which belongs to '${TARGET_APP}' ($(dir_of "$TARGET_APP")).

The three apps are separate deployables and communicate over HTTP only — see docs/adr/0005 and CONTEXT-MAP.md.

If '${TARGET_APP}' genuinely needs a change, the correct move is one of:
  - state what the other app needs and let a session scoped to it make the change;
  - if it is an API contract change, change it in backend/ and regenerate the clients (make gen-api).
EOF
exit 2
