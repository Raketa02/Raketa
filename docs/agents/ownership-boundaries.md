# Ownership boundaries

How "one session owns one app" is enforced, why it is built this way, and what to do
when it blocks you.

The decision behind it is
[ADR-0005](../adr/0005-three-app-monorepo-ownership-boundaries.md), which
[ADR-0187](../adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
extended to four apps.

## The rule

| Session started in | Owns | May write |
| --- | --- | --- |
| repo root | everything | anywhere — this is the human's orchestrator seat |
| `backend/…` | `backend` | `backend/**` + shared docs |
| `frontend_player/…` | `player` | `frontend_player/**` + shared docs |
| `frontend_club/…` | `club` | `frontend_club/**` + shared docs |
| `frontend_public/…` | `public` | `frontend_public/**` + shared docs |

> **The two web apps are fenced before they exist.** `frontend_club/` (the club website) and
> `frontend_public/` (the public site) hold nothing but their `.claude/settings.json` until
> [#522](https://github.com/Raketa02/Raketa/issues/522) and
> [#525](https://github.com/Raketa02/Raketa/issues/525) scaffold them. That order is the point:
> the `club` tier survived the 2026-08-25 reset so that the day a second client landed it
> would already be fenced, and `public` got its tier
> ([#502](https://github.com/Raketa02/Raketa/issues/502)) before any session could be
> launched inside it. Until then `frontend_public/` classified as *shared* — writable by every
> scoped session — and a session started inside it resolved to root and owned everything.

"Shared docs" means the root glossary, `CONTEXT-MAP.md`, `docs/adr/` and `docs/agents/`.
The boundary is about **code ownership**, not about preventing documentation — an agent
that discovers a cross-cutting decision should be able to write the ADR.

## How a session's app is resolved

1. **`$RKTA_TIER`**, if set — `root` | `backend` | `player` | `club` | `public`.
2. Otherwise, the session's **working directory**, relative to the repo root.

So the ordinary workflow is simply:

```bash
cd backend         && claude     # owns the backend
cd frontend_player && claude     # owns the player app
cd frontend_club   && claude     # owns the club website
cd frontend_public && claude     # owns the public site
claude                           # started at the root: owns everything
```

Use the env var when the working directory can't be trusted to say what you mean:

```bash
RKTA_TIER=player claude          # scoped to the player app wherever you launched it
```

> **Note:** the working directory is the session's, and a `cd` inside a Bash tool call
> changes it. A session that starts at the root and then `cd backend`s becomes scoped to
> the backend. That is usually what you want; when it isn't, set `RKTA_TIER` explicitly.

## What enforces it

A pair of `PreToolUse` hooks, keyed on the session's working directory:

| File | Matcher | Blocks |
| --- | --- | --- |
| `.claude/hooks/enforce-ownership.sh` | `Edit`, `Write`, `MultiEdit`, `NotebookEdit` | writes whose target path belongs to another app |
| `.claude/hooks/guard-bash.sh` | `Bash` | deploys/releases, real `.env*`/secret writes, destructive git, and cross-app writes via shell |

Both exit `2` to block, and the stderr text is returned to the agent as the reason.

### They are registered five times, and that is not redundancy

Claude Code reads `.claude/settings.json` **from the directory the session started in**, and
does **not** inherit it from ancestor directories the way it inherits `CLAUDE.md`. So the
hooks are registered in the root `.claude/settings.json` *and* in each app's
`backend/.claude/settings.json`, `frontend_player/.claude/settings.json`,
`frontend_club/.claude/settings.json` and `frontend_public/.claude/settings.json`.

This was originally built the other way round, on the belief that root settings covered every
session. They did not: a session started with `cd backend && claude` ran with **no hooks at
all**, no `.env` read denials and no `git push` confirmation. Enforcement existed only in the
root session — the one session where the ownership hook deliberately allows everything.

Two mechanical details that follow from this, and that will bite anyone editing the hooks:

- **`$CLAUDE_PROJECT_DIR` is the launch directory, not the repo root.** In a `backend/`
  session it is `<repo>/backend`. The per-app registrations therefore invoke
  `"$CLAUDE_PROJECT_DIR"/../.claude/hooks/…`, and both hooks resolve the repo root with
  `git rev-parse --show-toplevel` rather than trusting the variable. A hook that trusted it
  would treat every sibling app as "outside the repo" and allow the write.
- **Paths are normalized before classification.** `backend/../frontend_club/x` is a
  `frontend_club` path, and a relative path out of a scoped session is the ordinary way an
  agent names a sibling app. Without normalization the boundary was one `../` from being
  bypassed.

The per-app settings files also carry that app's permission allowlist, so routine commands
(`pnpm test`, `poetry run pytest`) stop prompting, and `additionalDirectories: [".."]`, which
restores read access to the rest of the repo — reading across apps is legitimate, and the
ownership hook is what stops the writes.

Two further rules:

- **A scoped session cannot edit the guardrails.** Writes to `.claude/hooks/**` and
  `.claude/settings.json` are blocked unless the session is at the repo root. Otherwise
  an agent can disable the constraint and then cross it — the boundary has to be
  reachable only from outside the thing it constrains.
- **The shell can't do what the editor was refused.** `guard-bash.sh` applies the same
  ownership check to redirects and to `cp`/`mv`/`rm`/`tee`/`touch`/`mkdir`/`sed -i`, so a
  blocked `Edit` cannot be laundered through `echo … > ../other_app/file`.

`.claude/settings.json` also carries a `deny` list for reading real `.env*` files and
key material, and an `ask` list for `git push` / `gh pr merge` / `gh release`.

## Verifying it

```bash
make test-hooks        # or: bash .claude/hooks/test-hooks.sh
```

109 assertions across both hooks: cross-app writes for every ordered pair of apps through the
editor tools, the `public` tier's fence in both directions, every directory that carries its
own `.claude/settings.json` resolving to a tier rather than to *shared*, refusals that never
count the apps, `../` escapes, scoped-session resolution, `$RKTA_TIER`,
shared-doc writes, self-defence, deploy commands, secret writes, destructive git, and the
false-positive cases that must **not** be blocked (a commit message mentioning `ecs-deploy`,
editing a `.env.example` template, an ordinary `git push`, a heredoc whose body says
`record.envelope`).

Passing unit tests do **not** prove the hooks are registered for a given session. Verify that
separately, end to end:

```bash
cd backend && claude -p "Use the Write tool to create ../frontend_club/probe.txt" \
  --allowedTools Write
```

That must be blocked, and so must the same probe from each app into another — for the
public site, `cd frontend_public && claude -p "… create ../backend/probe.txt"` and
`cd backend && claude -p "… create ../frontend_public/probe.txt"`. If one succeeds, the
problem is that app's `.claude/settings.json`, not the hook script.

Run both after touching either hook. A guardrail that silently stops matching is worse than
none, because you stop watching for what it was supposed to catch.

**Requires `jq`.** If `jq` is missing the hooks block rather than waving everything
through — fail closed, not open. `brew install jq`.

## When you get blocked

A block is information, not an obstacle to route around. Three common cases:

**"I need to change the other app too."**
Don't. Finish your side, then say explicitly what the other app needs, and let a session
scoped to it make that change. Two clean sessions beat one that reached across.

**"The backend contract changed and the clients need regenerating."**
That is the designed path, not a workaround: change the backend, run `make openapi`, and
report that the clients need `make gen-api`. See
[ADR-0006](../adr/0006-backend-owns-api-contract.md).

**"I need to deploy / write a real `.env`."**
Those need a human. Surface the blocked command and why you wanted to run it. Don't
reconstruct it in a form the guard doesn't recognise — if you can defeat the guard, the
guard is worth fixing, so report that instead.

**"The refusal names something my command never touched."**
Then the pattern matched a word, and the guard is worth fixing — the same report, from the
other side. Reach for the Edit/Write tool, which is scoped by path and unaffected, and file
the false positive; do **not** re-word the command until it slips through. `.env` matching
those four characters anywhere read `record.envelope` as a secret write and refused a
`.tsx` heredoc (#281), and the natural misreading — *"the hook is broken"* — is the one
that ends in routing around it.

## What this deliberately does not do

- It does not prevent **reading** across apps. Understanding how a client consumes an
  endpoint is legitimate and often necessary.
- It does not sandbox the process. A determined script could bypass it; it is a guardrail
  against plausible mistakes, not a security boundary against an adversary.
- It does not replace review. It catches the class of error where an agent edits the
  wrong app — not the class where it writes the wrong code in the right one.
