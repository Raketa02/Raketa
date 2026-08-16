# Rakieta — Monorepo

A racket-sport platform: players find and book courts; clubs manage those courts.
Three **independently deployable** apps share one repository and one domain language,
and communicate **only over HTTP**.

| App | Path | Stack |
| --- | --- | --- |
| Backend API | `backend/` | FastAPI, Clean/hexagonal, DDD, event sourcing, Poetry |
| Player app | `frontend_player/` | React Native + Expo + TypeScript (iOS & Android) |
| Club web app | `frontend_club/` | Next.js (App Router) + React + TypeScript |

## Start the session inside the app you are changing

```bash
cd backend && claude          # likewise frontend_club/ and frontend_player/
```

**YOU MUST launch from the app directory. This is mechanical, not etiquette.** Claude
Code loads settings, hooks and skills from the directory it starts in — not from
ancestors. A session started in `backend/` loads `backend/.claude/settings.json`, which
registers the ownership guardrails and that app's permissions. A session started at the
repo root loads the root's settings instead and owns *everything*.

Launch at the root only for work that is genuinely cross-app: ADRs, the shared glossary,
the hooks themselves, `make gen-api`.

## Invariants

- **Never import across apps.** They are separate deployables; the only contract between
  them is HTTP ([ADR-0005](docs/adr/0005-three-app-monorepo-ownership-boundaries.md)).
- **The backend owns the API contract.** It is emitted as two documents —
  `backend/openapi.player.json` and `backend/openapi.club.json` — and each client generates
  its wire types from its own, never hand-writing a DTO mirroring a backend response
  ([ADR-0006](docs/adr/0006-backend-owns-api-contract.md)). Regenerate with `make gen-api`
  and commit the result — CI regenerates and diffs, so a contract change shipped without
  its client types fails the build
  ([`.github/scripts/check-contract-drift.sh`](.github/scripts/check-contract-drift.sh),
  proven still to fire by `make test-drift`).
- **One session changes one app.** A `PreToolUse` hook blocks writes that cross an app
  boundary. A block is information — surface it, don't route around it. See
  [`docs/agents/ownership-boundaries.md`](docs/agents/ownership-boundaries.md).
- **Domain terms are defined once,** in [`CONTEXT.md`](CONTEXT.md). Each app's
  `CONTEXT.md` adds only its own *technical* vocabulary and never redefines a domain term.
- **The two clients do not share a shape.** `frontend_club/` follows its production
  architecture standard ([ADR-0014](docs/adr/0014-club-console-production-architecture-standard.md));
  `frontend_player/` follows feature-first Clean Architecture
  ([ADR-0009](docs/adr/0009-feature-first-clean-architecture-frontends.md)). A rule
  learned in one **does not** transfer to the other.

## Safety — never do these without an explicit human request

- Run deployment or release commands (`make build-prod`, `ecr-*`, `ecs-*`,
  `docker push`, `aws ecs|ecr`, `eas build|submit`, `vercel`).
- Create or modify a real `.env*` / secret / certificate / credential file. Edit the
  `.env*.example` template instead and let a human copy it.
- Rewrite git history or force-push (`git push --force`, `reset --hard`, `clean -f`,
  `branch -D`).
- Edit an already-applied Alembic migration.
- Change public API behavior without calling it out in the plan first.

The first three are enforced by `.claude/hooks/guard-bash.sh`. A blocked command is the
guardrail doing its job.

## Repo-wide docs

- [`CONTEXT.md`](CONTEXT.md) — the shared domain glossary. **Source of truth for domain
  terms.** Much of the racket-sport domain is still unwritten; see
  [`docs/agents/domain.md`](docs/agents/domain.md) before naming something new.
- [`CONTEXT-MAP.md`](CONTEXT-MAP.md) — topology: which file owns which vocabulary.
- [`docs/adr/`](docs/adr/) — decisions affecting the system or the contract between apps.

After changing either hook, run `make test-hooks` (65 assertions). A guardrail that
silently stops matching is worse than none, because you stop watching for it.

## Agent skills

### Issue tracker

GitHub Issues on `RobertConstantin02/rakieta`, via the `gh` CLI. Blocking edges live in
the issue body and a spec is labelled `prd`, not `ready-for-agent` — both are load-bearing
for the AFK loop. See [`docs/agents/issue-tracker.md`](docs/agents/issue-tracker.md).

### Triage labels

The five canonical triage roles, each label string equal to its name. See
[`docs/agents/triage-labels.md`](docs/agents/triage-labels.md).

### Domain docs

Multi-context: `CONTEXT-MAP.md` is the topology, the root `CONTEXT.md` owns the domain
language, and each app's `CONTEXT.md` adds technical vocabulary only. See
[`docs/agents/domain.md`](docs/agents/domain.md).
