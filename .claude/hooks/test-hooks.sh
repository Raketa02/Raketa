#!/bin/bash
# ---------------------------------------------------------------------------
# Test suite for the Raketa guardrail hooks.
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
unset RKTA_TIER   # tests exercise cwd-based resolution; with_tier sets it for one assertion
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

says() { # <hook> <name> <phrase> <json> — blocked, and the refusal names <phrase>
  local hook="$1" name="$2" phrase="$3" json="$4" err got
  err=$(printf '%s' "$json" | "$HOOKS/$hook" 2>&1 >/dev/null); got=$?
  case "$got:$err" in
    2:*"$phrase"*) pass=$((pass + 1)); printf '  ok    %-52s says %s\n' "$name" "$phrase" ;;
    *)             fail=$((fail + 1)); printf '  FAIL  %-52s exit %s, want a refusal saying %s\n' "$name" "$got" "$phrase" ;;
  esac
}

counts_no_apps() { # <hook> <name> <json> — blocked, and the refusal puts no number on the apps
  # A count in a refusal goes stale the day an app lands, and "three apps" outlived the
  # reset by a month. Blocked is part of the assertion: a hook that stopped refusing would
  # otherwise pass by saying nothing at all.
  local hook="$1" name="$2" json="$3" err got
  err=$(printf '%s' "$json" | "$HOOKS/$hook" 2>&1 >/dev/null); got=$?
  if [ "$got" = 2 ] && ! printf '%s\n' "$err" | grep -qiE '(two|three|four|five|six|[0-9]+) apps'; then
    pass=$((pass + 1)); printf '  ok    %-52s exit %s\n' "$name" "$got"
  else
    fail=$((fail + 1)); printf '  FAIL  %-52s exit %s, or the refusal counts the apps\n' "$name" "$got"
  fi
}

with_tier() { # <tier> <assertion…> — run one assertion with $RKTA_TIER set, then put it back
  local was_set=${RKTA_TIER+x} was="${RKTA_TIER:-}"
  export RKTA_TIER="$1"; shift
  "$@"
  if [ -n "$was_set" ]; then export RKTA_TIER="$was"; else unset RKTA_TIER; fi
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
expect enforce-ownership.sh 2 "club session edits backend"         "$(edit "$ROOT/frontend_club" "$ROOT/backend/app/main.py")"
expect enforce-ownership.sh 2 "player session edits backend"       "$(edit "$ROOT/frontend_player" "$ROOT/backend/app/main.py")"
expect enforce-ownership.sh 2 "player session edits club"          "$(edit "$ROOT/frontend_player" "$ROOT/frontend_club/src/a.tsx")"
expect enforce-ownership.sh 0 "club session edits club"            "$(edit "$ROOT/frontend_club" "$ROOT/frontend_club/src/a.tsx")"
expect enforce-ownership.sh 0 "nested cwd still owns its app"      "$(edit "$ROOT/backend/app/modules" "$ROOT/backend/app/x.py")"
expect enforce-ownership.sh 2 "nested cwd still blocked cross-app" "$(edit "$ROOT/backend/app/modules" "$ROOT/frontend_club/x.ts")"
expect enforce-ownership.sh 0 "relative path resolves via cwd"     "$(edit "$ROOT/backend" "app/core/config.py")"
expect enforce-ownership.sh 0 "root session edits any app"         "$(edit "$ROOT" "$ROOT/backend/app/main.py")"
# The '../' escape. These are not exotic — a relative path out of a scoped session is
# the ordinary way an agent names a sibling app, and until the hook normalized '..' it
# classified 'backend/../frontend_club/x' as backend and waved every one of them through.
expect enforce-ownership.sh 2 "relative ../ escape to club"        "$(edit "$ROOT/backend" "../frontend_club/src/a.tsx")"
expect enforce-ownership.sh 2 "relative ../ escape to player"      "$(edit "$ROOT/frontend_club" "../frontend_player/src/a.ts")"
expect enforce-ownership.sh 2 "absolute path with .. segment"      "$(edit "$ROOT/backend" "$ROOT/backend/../frontend_club/x.ts")"
expect enforce-ownership.sh 2 "../ escape from a nested cwd"       "$(edit "$ROOT/backend/app/modules" "../../../frontend_club/x.ts")"
expect enforce-ownership.sh 2 "./ noise does not hide the target"  "$(edit "$ROOT/backend" "./../frontend_club/./x.ts")"
expect enforce-ownership.sh 0 ".. that stays inside the same app"  "$(edit "$ROOT/backend/app" "../app/core/config.py")"
expect enforce-ownership.sh 2 "../ escape to a real env file"      "$(edit "$ROOT/frontend_club" "../backend/${DOTENV}.local")"

echo
echo "enforce-ownership.sh — the public tier (frontend_public, ADR-0187)"
# Until it had a tier, frontend_public/ classified as *shared*: every scoped session could
# write into it, and a session launched inside it resolved to root and owned everything.
expect enforce-ownership.sh 0 "public session edits public"        "$(edit "$ROOT/frontend_public" "$ROOT/frontend_public/src/app/page.tsx")"
expect enforce-ownership.sh 0 "nested cwd still owns public"       "$(edit "$ROOT/frontend_public/src/app" "../features/join/a.tsx")"
expect enforce-ownership.sh 2 "public session edits backend"       "$(edit "$ROOT/frontend_public" "$ROOT/backend/app/main.py")"
expect enforce-ownership.sh 2 "public session edits player"        "$(edit "$ROOT/frontend_public" "$ROOT/frontend_player/src/a.ts")"
expect enforce-ownership.sh 2 "public session edits club"          "$(edit "$ROOT/frontend_public" "$ROOT/frontend_club/src/a.tsx")"
expect enforce-ownership.sh 2 "backend session edits public"       "$(edit "$ROOT/backend" "$ROOT/frontend_public/src/a.tsx")"
expect enforce-ownership.sh 2 "player session edits public"        "$(edit "$ROOT/frontend_player" "$ROOT/frontend_public/src/a.tsx")"
expect enforce-ownership.sh 2 "club session edits public"          "$(edit "$ROOT/frontend_club" "$ROOT/frontend_public/src/a.tsx")"
expect enforce-ownership.sh 2 "relative ../ escape out of public"  "$(edit "$ROOT/frontend_public" "../backend/app/main.py")"
expect enforce-ownership.sh 2 "relative ../ escape into public"    "$(edit "$ROOT/frontend_club" "../frontend_public/src/a.tsx")"
expect enforce-ownership.sh 0 "root session edits public"          "$(edit "$ROOT" "$ROOT/frontend_public/src/a.tsx")"
expect enforce-ownership.sh 0 "public session writes shared ADR"   "$(edit "$ROOT/frontend_public" "$ROOT/docs/adr/0099-x.md")"
expect enforce-ownership.sh 2 "public session edits a hook"        "$(edit "$ROOT/frontend_public" "$ROOT/.claude/hooks/guard-bash.sh")"
expect enforce-ownership.sh 2 "public session writes a real env"   "$(edit "$ROOT/frontend_public" "$ROOT/frontend_public/${DOTENV}.local")"
# The tier is the directory, not a prefix of it: a sibling that merely starts with the name
# is somebody else's, or nobody's.
expect enforce-ownership.sh 0 "a name that only starts like it"    "$(edit "$ROOT/backend" "$ROOT/frontend_publicity/a.md")"
with_tier public expect enforce-ownership.sh 0 "RKTA_TIER=public edits public"   "$(edit "$ROOT" "$ROOT/frontend_public/src/a.tsx")"
with_tier public expect enforce-ownership.sh 2 "RKTA_TIER=public edits backend"  "$(edit "$ROOT" "$ROOT/backend/app/main.py")"
says enforce-ownership.sh "refusal names the public directory" "frontend_public/" "$(edit "$ROOT/backend" "$ROOT/frontend_public/src/a.tsx")"
counts_no_apps enforce-ownership.sh "refusal counts no apps" "$(edit "$ROOT/frontend_public" "$ROOT/backend/app/main.py")"

echo
echo "enforce-ownership.sh — every app with its own settings has a tier"
# An app directory the hooks don't list classifies as *shared*: a session started in it
# resolves to root and owns everything, and every other session may write into it. That is
# how frontend_public/ stood before it had a tier. So each directory that registers the hooks
# must be one the hooks know — probed through behaviour: a session started there may not
# edit the guardrails, which only a root (or unknown) session may do.
for settings in "$ROOT"/*/.claude/settings.json; do
  app_dir=${settings%/.claude/settings.json}
  expect enforce-ownership.sh 2 "${app_dir##*/}/ is a tier, not shared" "$(edit "$app_dir" "$ROOT/.claude/hooks/guard-bash.sh")"
done

echo
echo "both hooks — scoped session (CLAUDE_PROJECT_DIR is the LAUNCH dir, not the root)"
# `cd backend && claude` sets CLAUDE_PROJECT_DIR=<root>/backend. A hook that trusted
# that variable as the repo root saw every sibling app as "outside the repo" and
# allowed everything. These assertions are the regression guard for that.
export CLAUDE_PROJECT_DIR="$ROOT/backend"
expect enforce-ownership.sh 2 "scoped: backend session edits club"  "$(edit "$ROOT/backend" "$ROOT/frontend_club/src/a.tsx")"
expect enforce-ownership.sh 2 "scoped: ../ escape still blocked"    "$(edit "$ROOT/backend" "../frontend_club/src/a.tsx")"
expect enforce-ownership.sh 0 "scoped: backend edits its own tree"  "$(edit "$ROOT/backend" "$ROOT/backend/app/main.py")"
expect guard-bash.sh        2 "scoped: shell write into club"       "$(cmd "$ROOT/backend" 'cp x.json ../frontend_club/src/y.json')"
expect guard-bash.sh        0 "scoped: ordinary test run"           "$(cmd "$ROOT/backend" 'poetry run pytest tests -q')"
export CLAUDE_PROJECT_DIR="$ROOT/frontend_public"
expect enforce-ownership.sh 2 "scoped: public session edits backend" "$(edit "$ROOT/frontend_public" "$ROOT/backend/app/main.py")"
expect enforce-ownership.sh 0 "scoped: public edits its own tree"    "$(edit "$ROOT/frontend_public" "src/app/page.tsx")"
expect guard-bash.sh        2 "scoped: public shell write to player" "$(cmd "$ROOT/frontend_public" 'cp x.json ../frontend_player/src/y.json')"
export CLAUDE_PROJECT_DIR="$ROOT"

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
expect guard-bash.sh 2 "write a nested real env file"  "$(cmd "$ROOT" "tee backend/${DOTENV}.docker")"
expect guard-bash.sh 0 "touch an example template"    "$(cmd "$ROOT/backend" "touch ${DOTENV}.local.example")"
expect guard-bash.sh 0 "edit an example template"     "$(cmd "$ROOT/backend" "sed -i '' s/a/b/ ${DOTENV}.docker.example")"
# Four characters matched anywhere made `record${DOTENV}elope` — the Play search DTO's
# own field — read as a dotenv write, and the refusal named a cause that was not the
# cause (#281). The two assertions above it are the half that must not be lost: the
# fix is precision, never a weaker guard.
expect guard-bash.sh 0 "a field named ...elope in a heredoc" \
  "$(cmd "$ROOT" "cat > frontend_player/src/a.tsx <<EOF\\n<Text>{record${DOTENV}elope.total}</Text>\\nEOF")"
expect guard-bash.sh 0 "process${DOTENV} beside a JSX close tag" \
  "$(cmd "$ROOT" "cat > frontend_player/src/a.tsx <<EOF\\n<Text>{process${DOTENV}.API_URL}</Text>\\nEOF")"
# Filing the report reproduced the report: a body quoting the refusal carries the glob
# after a '>' blockquote marker, so #281 had to be filed with --body-file.
expect guard-bash.sh 0 "the refusal quoted in an issue body" \
  "$(cmd "$ROOT" "gh issue create --body 'was refused:\\n> Blocked: modifying a real ${DOTENV}* / secret file'")"

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
expect guard-bash.sh 2 "redirect through a .. segment"       "$(cmd "$ROOT/frontend_club" 'echo x > ../../repo/backend/app/y.py')"
expect guard-bash.sh 2 "absolute path into another app"      "$(cmd "$ROOT/backend" "cp x.json $ROOT/frontend_club/src/y.json")"
expect guard-bash.sh 0 "club session writes its own tree"   "$(cmd "$ROOT/frontend_club" 'mkdir -p src/features/booking')"
expect guard-bash.sh 0 "root session may write anywhere"    "$(cmd "$ROOT" 'cp a.txt backend/b.txt')"
expect guard-bash.sh 0 "pnpm install"                       "$(cmd "$ROOT/frontend_club" 'pnpm install')"
expect guard-bash.sh 0 "expo start"                         "$(cmd "$ROOT/frontend_player" 'pnpm start')"

echo
echo "guard-bash.sh — the public tier (frontend_public)"
expect guard-bash.sh 2 "public session copies into backend"  "$(cmd "$ROOT/frontend_public" 'cp x.json ../backend/app/y.json')"
expect guard-bash.sh 2 "public session redirects into club"  "$(cmd "$ROOT/frontend_public" 'echo x > ../frontend_club/src/y.ts')"
expect guard-bash.sh 2 "public session rm -rf in player"     "$(cmd "$ROOT/frontend_public" 'rm -rf ../frontend_player/src/old')"
expect guard-bash.sh 2 "backend session writes into public"  "$(cmd "$ROOT/backend" 'cp x.json ../frontend_public/src/y.json')"
expect guard-bash.sh 2 "player session tees into public"     "$(cmd "$ROOT/frontend_player" 'echo x | tee ../frontend_public/a.ts')"
expect guard-bash.sh 2 "club session absolute path to public" "$(cmd "$ROOT/frontend_club" "mkdir -p $ROOT/frontend_public/src")"
expect guard-bash.sh 0 "public session writes its own tree"  "$(cmd "$ROOT/frontend_public" 'mkdir -p src/features/join')"
expect guard-bash.sh 0 "root session writes into public"     "$(cmd "$ROOT" 'cp a.txt frontend_public/b.txt')"
expect guard-bash.sh 0 "public session runs playwright"      "$(cmd "$ROOT/frontend_public" 'pnpm exec playwright test')"
with_tier public expect guard-bash.sh 2 "RKTA_TIER=public shell write to backend" "$(cmd "$ROOT" 'cp a.txt backend/b.txt')"
says guard-bash.sh "shell refusal names the public tier" "owns 'public'" "$(cmd "$ROOT/frontend_public" 'cp x.json ../backend/y.json')"
counts_no_apps guard-bash.sh "shell refusal counts no apps" "$(cmd "$ROOT/backend" 'cp x.json ../frontend_club/y.json')"

echo
echo "-------------------------------------------------------------"
printf '  %s passed, %s failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
