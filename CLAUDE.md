# Rakieta — Monorepo

A racket-sport platform: players find and book courts; clubs manage those courts.
Three **independently deployable** apps share one repository and one domain language,
and communicate **only over HTTP**.

**Start at [`CONTEXT-MAP.md`](CONTEXT-MAP.md)** for the topology and where everything lives.

## The three apps

| App | Path | Stack | Instructions |
| --- | --- | --- | --- |
| Backend API | `backend/` | FastAPI, Clean/hexagonal, DDD, event sourcing, Poetry | [`backend/CLAUDE.md`](backend/CLAUDE.md) |
| Player app | `frontend_player/` | React Native + Expo + TypeScript (iOS & Android) | [`frontend_player/CLAUDE.md`](frontend_player/CLAUDE.md) |
| Club web app | `frontend_club/` | Next.js (App Router) + React + TypeScript | [`frontend_club/CLAUDE.md`](frontend_club/CLAUDE.md) |

## Working rules

- **Work from inside the app you are changing.** `cd backend`, `cd frontend_player`, or
  `cd frontend_club` and run that app's commands. Claude Code loads the nearest
  `CLAUDE.md`, so a session in `frontend_club/` gets this file plus the club's rules —
  never the backend's Python rules.
- **One session changes one app.** This is enforced, not merely requested: a
  `PreToolUse` hook blocks writes that cross an app boundary. See
  [`docs/agents/ownership-boundaries.md`](docs/agents/ownership-boundaries.md).
- **Never import across apps.** They are separate deployables; the only contract
  between them is HTTP ([ADR-0005](docs/adr/0005-three-app-monorepo-ownership-boundaries.md)).
- **The backend owns the API contract.** Both clients generate their wire types from
  `backend/openapi.json` — they never hand-write DTOs mirroring a backend response
  ([ADR-0006](docs/adr/0006-backend-owns-api-contract.md)). Regenerate with
  `make gen-api` from the repo root.
- **The domain language is shared and singular.** Domain terms are defined once in
  [`CONTEXT.md`](CONTEXT.md). Each app's `CONTEXT.md` holds only its own *technical*
  vocabulary and never redefines a domain term.
- **The two clients share a shape, not code.** Both use the same feature-layer
  structure, so a rule learned in one transfers to the other. They share no source
  ([ADR-0005](docs/adr/0005-three-app-monorepo-ownership-boundaries.md)).

## Safety — never do these without an explicit human request

- Run deployment or release commands (`make build-prod`, `ecr-*`, `ecs-*`,
  `docker push`, `aws ecs|ecr`, `eas build|submit`, `vercel`).
- Create or modify a real `.env*` / secret / certificate / credential file. Edit the
  `.env*.example` template instead and let a human copy it.
- Rewrite git history or force-push (`git push --force`, `reset --hard`, `clean -f`,
  `branch -D`).
- Edit an already-applied Alembic migration.
- Change public API behavior without calling it out in the plan first.

The first three are enforced by `.claude/hooks/guard-bash.sh`. A blocked command is
the guardrail doing its job — surface it to the human, don't work around it.

## Repo-wide docs (at the root)

- [`CONTEXT.md`](CONTEXT.md) — the shared domain glossary. **Source of truth for
  domain terms.**
- [`CONTEXT-MAP.md`](CONTEXT-MAP.md) — topology: which file owns which vocabulary.
- [`docs/adr/`](docs/adr/) — architecture decisions affecting the system or the
  contract between apps.
- [`docs/agents/`](docs/agents/) — how ownership boundaries work and how to consume
  the domain docs.

## Verifying the guardrails

```bash
bash .claude/hooks/test-hooks.sh    # 45 assertions over both hooks
```

Run it after touching either hook. A guardrail that silently stops matching is worse
than none, because you stop watching for what it was supposed to catch.
