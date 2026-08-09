#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the Rakieta guardrail hooks.
#
#   bash .claude/hooks/test-hooks.sh
#
# Feeds synthetic PreToolUse payloads to the hooks and asserts the exit code
# (0 = allowed, 2 = blocked). Run this after touching either hook — a guardrail
# that silently stops matching is worse than no guardrail, because you stop
# watching for the thing it was supposed to catch.
#
# Note: this lives in a file rather than being typed at the prompt on purpose —
# the payloads contain the very strings (.env, ecr-push) the guard blocks, so
# pasting them as a command would be blocked by the hook under test.
# ---------------------------------------------------------------------------
set -uo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
export CLAUDE_PROJECT_DIR="$ROOT"
unset RKTA_TIER   # tests exercise cwd-based resolution
HOOKS="$ROOT/.claude/hooks"

pass=0; fail=0

expect() { # <hook> <want-exit> <name> <json>
  local hook="$1" want="$2" name="$3" json="$4" got
  printf '%s' "$json" | "$HOOKS/$hook" >/dev/null 2>&1; got=$?
  if [ "$got" = "$want" ]; then
    pass=$((pass + 1)); printf '  ok    %-52s exit %s\n' "$name" "$got"
  else
    fail=$((fail + 1)); printf '  FAIL  %-52s want %s, got %s\n' "$name" "$want" "$got"
  fi
}

edit() { printf '{"cwd":"%s","tool_name":"%s","tool_input":{"file_path":"%s"}}' "$1" "${3:-Edit}" "$2"; }
cmd()  { printf '{"cwd":"%s","tool_input":{"command":"%s"}}' "$1" "$2"; }

DOTENV='.env'   # built indirectly so this file stays greppable without self-matching

echo
echo "enforce-ownership.sh — cross-app write boundary"
expect enforce-ownership.sh 0 "backend session edits backend"      "$(edit "$ROOT/backend" "$ROOT/backend/app/main.py")"
expect enforce-ownership.sh 2 "backend session edits club"         "$(edit "$ROOT/backend" "$ROOT/frontend_club/src/a.tsx")"
expect enforce-ownership.sh 2 "backend session edits player"       "$(edit "$ROOT/backend" "$ROOT/frontend_player/src/a.ts")"
expect enforce-ownership.sh 2 "club session edits player"          "$(edit "$ROOT/frontend_club" "$ROOT/frontend_player/src/a.ts")"
expect enforce-ownership.sh 2 "player session edits backend"       "$(edit "$ROOT/frontend_player" "$ROOT/backend/app/main.py")"
expect enforce-ownership.sh 0 "club session edits club"            "$(edit "$ROOT/frontend_club" "$ROOT/frontend_club/src/a.tsx")"
expect enforce-ownership.sh 0 "nested cwd still owns its app"      "$(edit "$ROOT/backend/app/modules" "$ROOT/backend/app/x.py")"
expect enforce-ownership.sh 2 "nested cwd still blocked cross-app" "$(edit "$ROOT/backend/app/modules" "$ROOT/frontend_club/x.ts")"
expect enforce-ownership.sh 0 "relative path resolves via cwd"     "$(edit "$ROOT/backend" "app/core/config.py")"
expect enforce-ownership.sh 0 "root session edits any app"         "$(edit "$ROOT" "$ROOT/backend/app/main.py")"

echo
echo "enforce-ownership.sh — shared files and self-defence"
expect enforce-ownership.sh 0 "app session writes shared ADR"      "$(edit "$ROOT/frontend_player" "$ROOT/docs/adr/0099-x.md")"
expect enforce-ownership.sh 0 "app session writes root CONTEXT"    "$(edit "$ROOT/backend" "$ROOT/CONTEXT.md")"
expect enforce-ownership.sh 2 "app session edits a hook"           "$(edit "$ROOT/backend" "$ROOT/.claude/hooks/guard-bash.sh")"
expect enforce-ownership.sh 2 "app session edits settings.json"    "$(edit "$ROOT/frontend_club" "$ROOT/.claude/settings.json")"
expect enforce-ownership.sh 0 "root session may edit a hook"       "$(edit "$ROOT" "$ROOT/.claude/hooks/guard-bash.sh")"
expect enforce-ownership.sh 2 "Write tool honours the boundary"    "$(edit "$ROOT/backend" "$ROOT/frontend_club/x.ts" Write)"
expect enforce-ownership.sh 2 "MultiEdit honours the boundary"     "$(edit "$ROOT/backend" "$ROOT/frontend_club/x.ts" MultiEdit)"
expect enforce-ownership.sh 2 "NotebookEdit honours the boundary" \
  "$(printf '{"cwd":"%s","tool_name":"NotebookEdit","tool_input":{"notebook_path":"%s"}}' "$ROOT/backend" "$ROOT/frontend_club/a.ipynb")"

echo
echo "enforce-ownership.sh — secret files (the shell guard's counterpart)"
expect enforce-ownership.sh 2 "Write a real env file"            "$(edit "$ROOT/backend" "$ROOT/backend/${DOTENV}.local")"
expect enforce-ownership.sh 2 "Write a bare .env"                "$(edit "$ROOT/frontend_club" "$ROOT/frontend_club/${DOTENV}")"
expect enforce-ownership.sh 2 "root session is not exempt"       "$(edit "$ROOT" "$ROOT/backend/${DOTENV}.docker")"
expect enforce-ownership.sh 2 "private key material"             "$(edit "$ROOT/backend" "$ROOT/backend/certs/server.key")"
expect enforce-ownership.sh 0 "the .example template is fine"    "$(edit "$ROOT/backend" "$ROOT/backend/${DOTENV}.local.example")"
expect enforce-ownership.sh 0 "an ordinary source file"          "$(edit "$ROOT/backend" "$ROOT/backend/app/core/config.py")"

echo
echo "guard-bash.sh — deployment and release"
expect guard-bash.sh 0 "ordinary test run"           "$(cmd "$ROOT/backend" 'poetry run pytest tests -q')"
expect guard-bash.sh 2 "make ecr-push"               "$(cmd "$ROOT/backend" 'make ecr-push')"
expect guard-bash.sh 2 "make build-prod"             "$(cmd "$ROOT/backend" 'make build-prod')"
expect guard-bash.sh 2 "aws ecs update-service"      "$(cmd "$ROOT" 'aws ecs update-service --cluster x')"
expect guard-bash.sh 2 "docker push"                 "$(cmd "$ROOT" 'docker push foo:latest')"
expect guard-bash.sh 2 "eas build"                   "$(cmd "$ROOT/frontend_player" 'eas build --platform ios')"
expect guard-bash.sh 2 "eas submit"                  "$(cmd "$ROOT/frontend_player" 'eas submit -p android')"
expect guard-bash.sh 2 "vercel --prod"               "$(cmd "$ROOT/frontend_club" 'vercel --prod')"
expect guard-bash.sh 0 "deploy word inside a message" "$(cmd "$ROOT" 'git commit -m "docs: explain ecs-deploy"')"

echo
echo "guard-bash.sh — secrets"
expect guard-bash.sh 2 "copy template over real file" "$(cmd "$ROOT/backend" "cp ${DOTENV}.local.example ${DOTENV}.local")"
expect guard-bash.sh 2 "append to a real env file"    "$(cmd "$ROOT/backend" "echo K=v >> ${DOTENV}")"
expect guard-bash.sh 2 "delete a real env file"       "$(cmd "$ROOT/backend" "rm ${DOTENV}.local")"
expect guard-bash.sh 0 "touch an example template"    "$(cmd "$ROOT/backend" "touch ${DOTENV}.local.example")"
expect guard-bash.sh 0 "edit an example template"     "$(cmd "$ROOT/backend" "sed -i '' s/a/b/ ${DOTENV}.docker.example")"

echo
echo "guard-bash.sh — destructive git"
expect guard-bash.sh 2 "git push --force"     "$(cmd "$ROOT" 'git push --force origin main')"
expect guard-bash.sh 2 "git reset --hard"     "$(cmd "$ROOT" 'git reset --hard origin/main')"
expect guard-bash.sh 2 "git clean -fd"        "$(cmd "$ROOT" 'git clean -fd')"
expect guard-bash.sh 2 "git branch -D"        "$(cmd "$ROOT" 'git branch -D feature/x')"
expect guard-bash.sh 0 "ordinary git push"    "$(cmd "$ROOT" 'git push origin main')"
expect guard-bash.sh 0 "git status"           "$(cmd "$ROOT" 'git status --short')"

echo
echo "guard-bash.sh — cross-app shell writes"
expect guard-bash.sh 2 "backend session copies into club"   "$(cmd "$ROOT/backend" 'cp x.json ../frontend_club/src/y.json')"
expect guard-bash.sh 2 "backend session rm -rf in player"   "$(cmd "$ROOT/backend" 'rm -rf ../frontend_player/src/old')"
expect guard-bash.sh 2 "club session redirects into backend" "$(cmd "$ROOT/frontend_club" 'echo x > ../backend/app/y.py')"
expect guard-bash.sh 0 "club session writes its own tree"   "$(cmd "$ROOT/frontend_club" 'mkdir -p src/features/booking')"
expect guard-bash.sh 0 "root session may write anywhere"    "$(cmd "$ROOT" 'cp a.txt backend/b.txt')"
expect guard-bash.sh 0 "pnpm install"                       "$(cmd "$ROOT/frontend_club" 'pnpm install')"
expect guard-bash.sh 0 "expo start"                         "$(cmd "$ROOT/frontend_player" 'pnpm start')"

echo
echo "-------------------------------------------------------------"
printf '  %s passed, %s failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
