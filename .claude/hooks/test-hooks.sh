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

# ---------------------------------------------------------------------------
# load-app-context.sh has a different contract from the two guards. A SessionStart
# hook that fails must never stop a session from starting, so it exits 0 in every
# path — the exit code asserts nothing. What is asserted is whether it CONTRIBUTES
# context, and to which sessions.
# ---------------------------------------------------------------------------
ctx() { printf '{"cwd":"%s","source":"%s","hook_event_name":"SessionStart"}' "$1" "${2:-startup}"; }

expect_ctx() { # <want: emit|silent> <name> <json>
  local want="$1" name="$2" json="$3" out code got
  out=$(printf '%s' "$json" | "$HOOKS/load-app-context.sh" 2>/dev/null); code=$?
  got=silent; [ -n "$out" ] && got=emit
  if [ "$code" != 0 ]; then
    fail=$((fail + 1)); printf '  FAIL  %-52s exit %s — must never block a session\n' "$name" "$code"
  elif [ "$got" = "$want" ]; then
    pass=$((pass + 1)); printf '  ok    %-52s %s\n' "$name" "$got"
  else
    fail=$((fail + 1)); printf '  FAIL  %-52s want %s, got %s\n' "$name" "$want" "$got"
  fi
}

expect_doc() { # <name> <substring-that-must-appear>
  local name="$1" needle="$2"
  # A here-string, NOT `printf ... | grep`. `grep -q` exits at the first match, which
  # SIGPIPEs the printf feeding it, and `set -o pipefail` (line 16) then reports the
  # whole pipeline as failed. Against a 260KB haystack every needle found early looks
  # missing and only one at the very end looks present — a false red that says
  # "document not loaded" when the document is right there.
  if grep -Fq -- "$needle" <<<"$CTX_ROOT"; then
    pass=$((pass + 1)); printf '  ok    %-52s present\n' "$name"
  else
    fail=$((fail + 1)); printf '  FAIL  %-52s missing: %s\n' "$name" "$needle"
  fi
}

echo
echo "load-app-context.sh — which sessions receive the apps' documents"
expect_ctx emit   "root session, startup"                  "$(ctx "$ROOT" startup)"
expect_ctx emit   "root session, clear"                    "$(ctx "$ROOT" clear)"
expect_ctx emit   "root session, compact"                  "$(ctx "$ROOT" compact)"
expect_ctx silent "root session, resume (transcript has it)" "$(ctx "$ROOT" resume)"
# A scoped session already loads its own CLAUDE.md by walking up, and handing it the
# sibling app's documents is an invitation to the cross-app edit the ownership hook
# exists to block. Silence here is the feature, not a gap.
expect_ctx silent "backend session"                        "$(ctx "$ROOT/backend")"
expect_ctx silent "player session"                         "$(ctx "$ROOT/frontend_player")"
expect_ctx silent "nested cwd is still a scoped session"   "$(ctx "$ROOT/backend/app/modules")"
expect_ctx silent "cwd outside the repo"                   "$(ctx /tmp)"

echo
echo "load-app-context.sh — cannot break a session start"
expect_ctx silent "empty payload"                          ''
expect_ctx silent "payload that is not JSON"               'not json at all'
expect_ctx emit   "payload without cwd falls back to project dir" '{"source":"startup"}'

echo
echo "load-app-context.sh — RKTA_TIER override (same variable as the ownership hook)"
export RKTA_TIER=root
expect_ctx emit   "RKTA_TIER=root overrides a backend cwd" "$(ctx "$ROOT/backend")"
export RKTA_TIER=backend
expect_ctx silent "RKTA_TIER=backend overrides a root cwd" "$(ctx "$ROOT")"
unset RKTA_TIER

echo
echo "load-app-context.sh — what a root session actually receives"
CTX_RAW=$(ctx "$ROOT" startup | "$HOOKS/load-app-context.sh" 2>/dev/null)
CTX_ROOT=$(printf '%s' "$CTX_RAW" | jq -r '.hookSpecificOutput.additionalContext // empty' 2>/dev/null)
if [ "$(printf '%s' "$CTX_RAW" | jq -r '.hookSpecificOutput.hookEventName' 2>/dev/null)" = SessionStart ]; then
  pass=$((pass + 1)); printf '  ok    %-52s present\n' "valid SessionStart hook JSON"
else
  fail=$((fail + 1)); printf '  FAIL  %-52s not the SessionStart output shape\n' "valid SessionStart hook JSON"
fi

# The assertion this hook exists for. Claude Code inlines only the first ~2KB of a
# SessionStart hook's additionalContext and spills the rest to a file in the session's
# tool-results/ directory — measured against 2.1.263 with canaries at doubling byte
# depths, where only the 1KB one came back. An earlier version of this hook inlined all
# 268KB of the apps' documents and arrived as its own first two kilobytes: a root
# session got a header and half of backend/CLAUDE.md, silently, with nothing anywhere
# reporting a problem. Nothing in the hook's own output can reveal that, so the budget
# is asserted here instead.
CTX_BYTES=$(printf '%s' "$CTX_ROOT" | wc -c | tr -d ' ')
if [ "$CTX_BYTES" -gt 0 ] && [ "$CTX_BYTES" -lt 2000 ]; then
  pass=$((pass + 1)); printf '  ok    %-52s %s bytes\n' "fits the ~2KB inline budget" "$CTX_BYTES"
else
  fail=$((fail + 1)); printf '  FAIL  %-52s %s bytes — will be truncated, inline only a directive\n' "fits the ~2KB inline budget" "$CTX_BYTES"
fi

# The directive has to NAME each app's documents. The needles are derived from the tree,
# so an app added or a CONTEXT.md removed shows up here rather than going quietly unnamed.
for app in backend frontend_player; do
  expect_doc "$app/ named"                "  $app/ — CLAUDE.md ("
  [ -f "$ROOT/$app/CONTEXT.md" ] && expect_doc "$app/CONTEXT.md named" "CONTEXT.md ("
done
# The rules directories are the sharpest case for the directive: nothing in Claude Code
# reads .claude/rules/, and no app CLAUDE.md links to them, so they are inert in every
# session at every depth and this is the only thing that mentions they exist.
expect_doc "rules directories named"      '.claude/rules/*.md ('
# Naming the documents is not the same as being scoped to the app, and the directive has
# to say so — a root session still holds root permissions, root skills, and every app.
expect_doc "states root still owns every app" 'one session changes one app'
expect_doc "states the app skills are absent" 'api-contract-change'

echo
echo "-------------------------------------------------------------"
printf '  %s passed, %s failed\n\n' "$pass" "$fail"
[ "$fail" -eq 0 ] || exit 1
