#!/bin/bash
# ---------------------------------------------------------------------------
# Bash guardrail for the Raketa monorepo.
#
# Covers what enforce-ownership.sh cannot: a shell command can deploy, clobber a
# secret, or write into another app through a redirect without ever touching the
# Edit/Write tools.
#
# Mirrors the Safety list in each CLAUDE.md. PreToolUse hook on Bash;
# exit 2 blocks the command and returns the stderr text to the agent.
#
# Requires: jq
# ---------------------------------------------------------------------------
set -uo pipefail

INPUT=$(cat)

if ! command -v jq >/dev/null 2>&1; then
  echo 'Bash guard cannot run: jq is not installed (brew install jq). Blocking to fail safe.' >&2
  exit 2
fi

COMMAND=$(printf '%s' "$INPUT" | jq -r '.tool_input.command // empty')
CWD=$(printf '%s' "$INPUT" | jq -r '.cwd // empty')
[ -z "$COMMAND" ] && exit 0

# The REPO root — see the note in enforce-ownership.sh. $CLAUDE_PROJECT_DIR is the
# launch directory, so it is backend/ in a scoped session and cannot be used to
# decide which app a path belongs to.
ROOT=$(git -C "${CWD:-.}" rev-parse --show-toplevel 2>/dev/null)
[ -z "$ROOT" ] && ROOT="${CLAUDE_PROJECT_DIR:-}"

# Match only when the trigger is in COMMAND position — start of line, or right
# after a shell separator. Keeps a deploy word inside a quoted commit message
# from tripping the guard.
SEP='(^|[;&|(])[[:space:]]*'

# --- 1. deployment / registry / release ---------------------------------------
if printf '%s' "$COMMAND" | grep -qE "${SEP}(make[[:space:]]+(build-prod|ecr-login|ecr-push|ecs-deploy)|ecr-login|ecr-push|ecs-deploy|docker[[:space:]]+push|aws[[:space:]]+(ecs|ecr)|eas[[:space:]]+(build|submit|update)|vercel|expo[[:space:]]+publish)([[:space:]]|$)"; then
  echo 'Blocked: deployment/release commands (make build-prod, ecr-*, ecs-*, docker push, aws ecs|ecr, eas build|submit|update, vercel, expo publish) require an explicit human request. See the Safety section of the relevant CLAUDE.md.' >&2
  exit 2
fi

# --- 2. writing to .env* / secrets --------------------------------------------
# A write verb aimed at a .env target, or any redirect into one. `.env*.example`
# templates are fine — those exist to be edited.
if printf '%s' "$COMMAND" | grep -qE "${SEP}(cp|mv|rm|tee|touch|sed[[:space:]]+-i)[^|;&]*\.env|>>?[[:space:]]*[^|;&]*\.env"; then
  # Inspect each .env token individually: `cp .env.local.example .env.local`
  # mentions an example but still writes a real secret file, so testing the whole
  # command string for ".example" would wave it through.
  if printf '%s' "$COMMAND" \
      | grep -oE "[^[:space:]\"']*\.env[^[:space:]\"']*" \
      | grep -qvE '\.example$'; then
    echo 'Blocked: creating or modifying a real .env* / secret file is not allowed without an explicit human request. Edit the .env*.example template instead, and let a human copy it. See CLAUDE.md Safety.' >&2
    exit 2
  fi
fi

# --- 3. git history rewriting / force push ------------------------------------
if printf '%s' "$COMMAND" | grep -qE "${SEP}git[[:space:]]+(push[^|;&]*(--force|-f)([[:space:]]|$)|reset[[:space:]]+--hard|clean[[:space:]]+-[a-z]*f|filter-branch|branch[[:space:]]+-D)"; then
  echo 'Blocked: destructive git operations (force push, reset --hard, clean -f, filter-branch, branch -D) require an explicit human request.' >&2
  exit 2
fi

# --- 4. cross-app writes via the shell ----------------------------------------
# Same boundary as enforce-ownership.sh, applied to shell redirects and file verbs.
if [ -n "$ROOT" ]; then
  REL_CWD="${CWD:-$ROOT}"
  case "$REL_CWD" in
    "$ROOT")   REL_CWD='.' ;;
    "$ROOT"/*) REL_CWD="${REL_CWD#"$ROOT"/}" ;;
  esac

  app_of() {
    case "$1" in
      backend|backend/*)                 printf 'backend' ;;
      frontend_player|frontend_player/*) printf 'player'  ;;
      frontend_club|frontend_club/*)     printf 'club'    ;;
      *)                                 printf 'shared'  ;;
    esac
  }

  TIER="${RKTA_TIER:-}"
  if [ -z "$TIER" ]; then
    if [ "$REL_CWD" = "." ]; then TIER='root'; else TIER=$(app_of "$REL_CWD"); fi
    [ "$TIER" = 'shared' ] && TIER='root'
  fi

  if [ "$TIER" != 'root' ]; then
    for other in backend frontend_player frontend_club; do
      [ "$(app_of "$other")" = "$TIER" ] && continue
      # a write verb or a redirect aimed at the other app's directory. Both arms
      # allow arbitrary leading path text so an absolute path, a '../' and a
      # 'backend/../frontend_club/' all match the same way.
      if printf '%s' "$COMMAND" | grep -qE "(${SEP}(cp|mv|rm|tee|touch|mkdir|sed[[:space:]]+-i)|>>?)[^|;&]*(^|[[:space:]/])${other}/"; then
        echo "Blocked: this session owns '${TIER}', but the command writes into '${other}/'. The three apps are separate deployables — see docs/adr/0005. Make the change from a session scoped to that app." >&2
        exit 2
      fi
    done
  fi
fi

exit 0
