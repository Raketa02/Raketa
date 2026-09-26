# Raketa

A racket-sport platform. **Today it does one thing end to end:** a player signs up, signs
in, and answers a questionnaire that gives them a Skill rating per sport.

This is a **monorepo of two independently deployable applications** that share one
domain language and communicate only over HTTP.

| App | Path | Stack | Status |
| --- | --- | --- | --- |
| **Backend API** | [`backend/`](backend/) | FastAPI · Clean/hexagonal · DDD · event sourcing · Poetry | running — Users, Auth and the rating questionnaire |
| **Player app** | [`frontend_player/`](frontend_player/) | React Native · Expo · TypeScript (iOS + Android) | sign-up, sign-in and onboarding implemented |

```
                    ┌──────────────────┐
                    │   backend/       │  owns the domain + the API contract
                    │   FastAPI        │
                    └────────┬─────────┘
                             │  HTTP
                  ┌──────────▼──────────┐
                  │  frontend_player/   │
                  │  Expo · direct API  │
                  │  token in keychain  │
                  └─────────────────────┘
```

> **Reset on 2026-08-25.** The repository was cut back to the three features above. A club
> console (`frontend_club/`), the pairing / balance-forecast / Match Fit engines, the
> kernel's money module and the unwritten Clubs / Courts / Matches / Money / Now contexts
> were removed, along with the ADRs and specifications that decided only them. Nothing in
> that set was judged wrong — it was judged premature. See the
> [ADR index](docs/adr/README.md#the-2026-08-25-reset--why-the-sequence-has-gaps).

## Start here

- **[`CONTEXT-MAP.md`](CONTEXT-MAP.md)** — the topology: what lives where, and which file
  owns which vocabulary.
- **[`CONTEXT.md`](CONTEXT.md)** — the shared domain glossary. One definition of
  `Assessment`, obeyed by both apps.
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

# Player app    (first run: see frontend_player/README.md)
cd frontend_player && pnpm install && pnpm start
```

Only if you want uvicorn on the **host** rather than in the container:
`cd backend && cp .env.example .env`. The name matters — `config.py` loads `.env`, so a
file called `.env.local` is read by nothing.

The player app was deliberately not created with `create-expo-app`, whose default layout
contradicts [ADR-0009](docs/adr/0009-feature-first-clean-architecture-frontends.md); see
its README for the bootstrap sequence.

## Repo-wide commands

```bash
make gen-api      # regenerate every client's wire types, each from its own document
make check        # every app's gate
make test-hooks   # verify the ownership guardrails still match
```

## The API contract

The backend is the **single source of truth**
([ADR-0006](docs/adr/0006-backend-owns-api-contract.md)). It emits one document per
surface, and each client generates its TypeScript wire types from its own — the player app
from `backend/openapi.player.json`, the club website from `openapi.club.json`, the public
site from `openapi.public.json`
([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
§5). No client hand-writes a type mirroring a backend response. After a contract change:

```bash
make gen-api      # emits every document, regenerates every client
```

Commit the documents that moved together with the generated files. CI re-emits every
document and regenerates every client, and diffs both, so a contract change shipped
without its client types fails the build.

## Working with AI agents

The repo is built to be developed by several agents in parallel, which is why the
app boundary is **mechanically enforced** rather than merely requested.

Start each session inside the app you intend to change:

```bash
cd backend         && claude
cd frontend_player && claude
```

A session scoped to one app **cannot write into another** — a `PreToolUse` hook blocks
it, through both the edit tools and the shell. A session started at the repo root owns
everything; that is your orchestrator seat.

Full explanation, including what to do when you get blocked:
[`docs/agents/ownership-boundaries.md`](docs/agents/ownership-boundaries.md).

```bash
make test-hooks    # 109 assertions over both guardrails
```

The guardrails need `jq` (`brew install jq`); without it they block rather than wave
things through.

## Deployment — none, for now

Everything runs **locally**: local Postgres and local Docker via
`backend/docker-compose-local.yml`. There is no deployed environment, and no AWS account
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
