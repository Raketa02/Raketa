# Raketa

A racket-sport platform. Players find and book courts; clubs manage those courts.

This is a **monorepo of three independently deployable applications** that share one
domain language and communicate only over HTTP.

| App | Path | Stack | Status |
| --- | --- | --- | --- |
| **Backend API** | [`backend/`](backend/) | FastAPI · Clean/hexagonal · DDD · event sourcing · Poetry | running — Users + Auth implemented |
| **Player app** | [`frontend_player/`](frontend_player/) | React Native · Expo · TypeScript (iOS + Android) | scaffolded — not yet installed |
| **Club web app** | [`frontend_club/`](frontend_club/) | Next.js App Router · React · TypeScript | scaffolded — not yet installed |

```
                    ┌──────────────────┐
                    │   backend/       │  owns the domain + the API contract
                    │   FastAPI        │
                    └────────┬─────────┘
                     HTTP    │    HTTP
              ┌──────────────┴──────────────┐
   ┌──────────▼──────────┐      ┌───────────▼───────────┐
   │  frontend_player/   │      │   frontend_club/      │
   │  Expo · direct API  │      │   Next.js · via BFF   │
   │  token in keychain  │      │   httpOnly cookie     │
   └─────────────────────┘      └───────────────────────┘
```

## Start here

- **[`CONTEXT-MAP.md`](CONTEXT-MAP.md)** — the topology: what lives where, and which file
  owns which vocabulary.
- **[`CONTEXT.md`](CONTEXT.md)** — the shared domain glossary. One definition of `Court`,
  obeyed by all three apps.
- **[`docs/adr/`](docs/adr/)** — why the architecture is the way it is.
- **[`CLAUDE.md`](CLAUDE.md)** — instructions for AI agents working in this repo.

## Running each app

Each app owns its own commands. **Run them from that app's directory.**

Everything runs locally. The backend needs **no env file** for the normal path —
compose supplies the database URLs and runs migrations on start.

```bash
# Backend — the whole stack in Docker (Postgres 17 + API + Redis)
cd backend
make up                               # http://localhost:8000  ·  /health
make logs                             # tail the API
make down                             # stop

# Backend — tests and checks (run on the host, no Docker needed)
make install                          # poetry install  (needs Python 3.11)
make check                            # lint + typecheck + test

# Club web app  (first run: see frontend_club/README.md)
cd frontend_club && pnpm install && pnpm dev

# Player app    (first run: see frontend_player/README.md)
cd frontend_player && pnpm install && pnpm start
```

Only if you want uvicorn on the **host** rather than in the container:
`cd backend && cp .env.example .env`. The name matters — `config.py` loads `.env`, so a
file called `.env.local` is read by nothing.

The two frontends hold architecture, config and rules but have **not** been installed or
generated yet — each README has its bootstrap sequence. They were deliberately not
created with `create-next-app` / `create-expo-app`, whose default layouts contradict
[ADR-0009](docs/adr/0009-feature-first-clean-architecture-frontends.md).

## Repo-wide commands

```bash
make gen-api      # regenerate BOTH clients' wire types from backend/openapi.json
make check        # every app's gate
make test-hooks   # verify the ownership guardrails still match
```

## The API contract

The backend is the **single source of truth**
([ADR-0006](docs/adr/0006-backend-owns-api-contract.md)). Both clients generate their
TypeScript wire types from `backend/openapi.json` — neither hand-writes a type mirroring
a backend response. After a contract change:

```bash
make gen-api      # dumps openapi.json, regenerates both clients
```

Commit `backend/openapi.json` together with both generated files.

## Working with AI agents

The repo is built to be developed by several agents in parallel, which is why the
app boundary is **mechanically enforced** rather than merely requested.

Start each session inside the app you intend to change:

```bash
cd backend         && claude
cd frontend_club   && claude
cd frontend_player && claude
```

A session scoped to one app **cannot write into another** — a `PreToolUse` hook blocks
it, through both the edit tools and the shell. A session started at the repo root owns
everything; that is your orchestrator seat.

Full explanation, including what to do when you get blocked:
[`docs/agents/ownership-boundaries.md`](docs/agents/ownership-boundaries.md).

```bash
make test-hooks    # 45 assertions over both guardrails
```

The guardrails need `jq` (`brew install jq`); without it they block rather than wave
things through.

## Deployment — none, for now

Everything runs **locally**: local Postgres and local Docker via
`backend/docker-compose-dev.yml`. There is no deployed environment, and no AWS account
is needed to work on this project.

The AWS ECS/Fargate path is **kept intact but dormant** — the task definition, the
pipeline, the Makefile targets and
[`backend/docs/deployment/aws-ecs.md`](backend/docs/deployment/aws-ecs.md) all remain, so
deployment can resume later without being rebuilt from memory. It is dormant three ways:
the workflow is manual-only, its deploy job is gated on `vars.AWS_REGION` being set, and
deploy commands are blocked outright for agent sessions.

Reactivation instructions are in the header of
[`.github/workflows/deploy-ecs.yml`](.github/workflows/deploy-ecs.yml). Start by checking
the task definition against the current settings — dormant infrastructure drifts from the
code silently. The reasoning is in
[ADR-0010](docs/adr/0010-local-first-development-aws-deferred.md).

## Licence

[MIT](LICENSE).
