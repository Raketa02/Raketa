# Rakieta — Context Map

A **polyglot monorepo** with three independently deployable apps that realize the
**same** bounded contexts:

- **`backend/`** — async FastAPI service. Clean/hexagonal, DDD, event sourcing,
  transactional outbox. Python 3.11 + Poetry. **Source of truth for the API contract.**
- **`frontend_player/`** — React Native + Expo, TypeScript. The native iOS/Android app
  for players. Talks to FastAPI directly; tokens live in the OS keychain.
- **`frontend_club/`** — Next.js (App Router) + TypeScript. The web app clubs use to
  manage courts. Talks to FastAPI through its own BFF; session lives in httpOnly cookies.

```
                    ┌──────────────────┐
                    │   backend/       │  owns the domain + the contract
                    │   FastAPI        │
                    └────────┬─────────┘
                     HTTP    │    HTTP
              ┌──────────────┴──────────────┐
              │                             │
   ┌──────────▼──────────┐      ┌───────────▼───────────┐
   │  frontend_player/   │      │   frontend_club/      │
   │  Expo · direct API  │      │   Next.js · via BFF   │
   │  token in keychain  │      │   httpOnly cookie     │
   └─────────────────────┘      └───────────────────────┘

   No arrows between the two clients. They share no code.
```

## How the domain language is split

A `Court` means the same thing in all three apps. To stop the ubiquitous language
drifting, the **domain** glossary lives in exactly one place and each app adds only its
own **technical** vocabulary:

| File | Scope | Owns |
| --- | --- | --- |
| **`CONTEXT.md`** (root) | **Shared domain language — source of truth** | User, Authority, Email, Club, Court, Booking, statuses, domain events… |
| **`backend/CONTEXT.md`** | Backend technical vocab only | event-sourced aggregate, outbox, event store, port/adapter, UoW… |
| **`frontend_player/CONTEXT.md`** | Player-app technical vocab only | feature, use-case, mapper, wire type vs DTO, screen, secure store, query/mutation… |
| **`frontend_club/CONTEXT.md`** | Club-app technical vocab only | feature, use-case, mapper, wire type vs DTO, Server/Client Component, BFF route handler… |

An app `CONTEXT.md` must **never redefine** a domain term — it points back to the root
glossary.

## Decisions (ADRs)

**`docs/adr/`** (root) holds every decision affecting the system or the contract
between apps, numbered sequentially across the whole repo. There are no per-app ADR
directories: a decision that only affects one app still tends to constrain the others,
and one numbered sequence is easier to reason about than three.

## Claude Code instructions

Claude Code auto-loads the nearest `CLAUDE.md` up the tree. Work from inside the app
you are changing so you get its rules and not another's:

- **`CLAUDE.md`** (root) — monorepo orientation and the repo-wide safety list.
- **`backend/CLAUDE.md`** — Python/FastAPI rules (TDD, hexagonal, events, Poetry).
- **`frontend_player/CLAUDE.md`** — Expo/RN rules (feature layering, secure store, codegen).
- **`frontend_club/CLAUDE.md`** — Next.js rules (feature layering, BFF, codegen, TanStack).

Settings and hooks are **root-only** — Claude Code reads `.claude/settings.json` from
the repository root, not from subdirectories. That is why the ownership boundary is a
hook keyed on the session's working directory rather than per-app settings files. See
[`docs/agents/ownership-boundaries.md`](docs/agents/ownership-boundaries.md).

## Where things live

```
/
├── CLAUDE.md                 ← monorepo orientation + safety list
├── CONTEXT-MAP.md            ← you are here
├── CONTEXT.md                ← SHARED domain glossary (source of truth)
├── Makefile                  ← thin root helpers (gen-api, check, afk)
├── .claude/
│   ├── settings.json         ← permissions + hook registration (root-only)
│   └── hooks/                ← enforce-ownership.sh, guard-bash.sh, test-hooks.sh
├── docs/
│   ├── adr/                  ← system-wide decisions (0001…)
│   └── agents/               ← ownership boundaries, domain-doc consumption
├── backend/                  ← FastAPI  (CLAUDE.md + CONTEXT.md + its own docs/)
├── frontend_player/          ← Expo     (CLAUDE.md + CONTEXT.md)
├── frontend_club/            ← Next.js  (CLAUDE.md + CONTEXT.md)
└── tools/afk/ + .sandbuket/  ← the AFK agent execution loop and its sandbox image
```
