---
name: guardrails
description: Change, debug or verify the Claude Code guardrails — the ownership hook, the bash guard, and the per-app settings files. Use when a hook blocked something wrongly, when adding a rule, or when the guardrails seem not to be running.
---

# The guardrails

Two `PreToolUse` hooks at `.claude/hooks/`, registered **four times** — once in the root
`.claude/settings.json` and once in each app's `.claude/settings.json`.

## Why four registrations

Claude Code loads project settings **from the directory the session started in**, and does
not inherit them from ancestors. A session started with `cd backend && claude` reads
`backend/.claude/settings.json` and never sees the root file. Registering the hooks only at
the root meant every scoped session — the ones the ownership boundary exists for — ran with
no guardrails at all.

Two consequences to keep in mind when editing them:

- **`$CLAUDE_PROJECT_DIR` is the launch directory, not the repo root.** In a `backend/`
  session it is `<repo>/backend`. That is why the per-app registrations invoke
  `"$CLAUDE_PROJECT_DIR"/../.claude/hooks/…`, and why both hooks resolve the repo root with
  `git rev-parse --show-toplevel` rather than trusting the variable.
- **A scoped session cannot edit the guardrails.** Writes to `.claude/hooks/**` and
  `.claude/settings.json` are blocked unless the session is at the repo root — otherwise an
  agent could disable the constraint and then cross it. Make these changes from a root
  session.

## After any change

```bash
make test-hooks        # 69 assertions across both hooks
```

The suite covers the false-positive cases too — a commit message mentioning `ecs-deploy`, a
`.env.example` template, an ordinary `git push` — because a guard that blocks ordinary work
gets disabled.

Then verify **end to end**, because passing unit tests do not prove the hook is registered:

```bash
cd backend && claude -p "Use the Write tool to create ../frontend_club/probe.txt" \
  --allowedTools Write
```

That must be blocked by the ownership hook. If it succeeds, the hook is not registered for
that session — check the app's `.claude/settings.json`, not the hook script.

## When a block is wrong

A block is information. If a guard blocks legitimate work, fix the guard and add the case to
`test-hooks.sh` — do not reconstruct the command in a form the guard doesn't recognise. If
you can defeat the guard, the guard is worth fixing, so report that instead.

Both hooks **fail closed**: if `jq` is missing they block rather than wave everything
through. `brew install jq`.
