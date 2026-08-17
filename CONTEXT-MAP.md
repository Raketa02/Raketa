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
| **`CONTEXT.md`** (root) | **Shared domain language — source of truth** | User, Authority, Email, Sport, SportSpec, Club, Court, Booking, statuses, domain events, and the matchmaking words — Pairing, Balance forecast, Match Fit, Coverage, At Stake… |
| **`backend/CONTEXT.md`** | Backend technical vocab only | event-sourced aggregate, outbox, event store, port/adapter, UoW… |
| **`frontend_player/CONTEXT.md`** | Player-app technical vocab only | feature, use-case, mapper, wire type vs DTO, screen, secure store, query/mutation… |
| **`frontend_club/CONTEXT.md`** | Club-app technical vocab only | feature, model/server layer, wire type vs DTO, Server/Client Component, BFF route handler, tenant-scoped query key… |

An app `CONTEXT.md` must **never redefine** a domain term — it points back to the root
glossary.

## Design systems are per-app and never shared

Each client owns its own visual language, tokens and vocabulary, and shares no code with the
other ([ADR-0005](docs/adr/0005-three-app-monorepo-ownership-boundaries.md)). They do not
share an architectural shape either — the club app follows its production architecture
standard, the player app follows ADR-0009
([ADR-0014](docs/adr/0014-club-console-production-architecture-standard.md)).

| File | Owns |
| --- | --- |
| **`frontend_club/docs/design-system.md`** | The club console's rules: colour meanings, the five containers, the calendar, overlays, motion, copy. **Locked** — [ADR-0011](docs/adr/0011-club-console-design-system.md). |
| **`frontend_club/src/shared/ui/tokens.css`** | The club console's values. The only legitimate source of a colour, size, space, radius, shadow or z-index in that app. |
| **`frontend_player/docs/design-system.md`** | The player app's rules: colour meanings, the primitives, the level bar, overlays, touch and accessibility. **Locked** — [ADR-0012](docs/adr/0012-player-app-design-system.md). |
| **`frontend_player/src/shared/ui/theme.ts`** | The player app's values, as a typed object. Same rule: no literal in a component. |

The two palettes **converge because it is one brand** — same paper, same coral, same
semantics, the same "Rule C" for white-on-saturated fills. **The values are duplicated
deliberately.** There is no shared design package and no cross-import; a client that needed
to change its own coral would otherwise be unable to.

Design-system *terms* (token, soft/ink, eyebrow, hairline, severity rail, band ink, sheet
vs drawer) are technical vocabulary and live in that app's `CONTEXT.md`. A design system
never settles a **domain** term — that happens in the root `CONTEXT.md` first.

**Two things sit between the two and are shared.**

[`docs/environments.md`](docs/environments.md) — the four environment names, what each is,
which variable carries it in each app, the refusals, the scheme rule, the test taxonomy, and
the checklist for turning on a remote environment. Not domain language (no nouns a player
would recognise) and not a design system: a **deployment contract**. It lives at the root
because an environment name is the one piece of vocabulary all three apps must spell
identically — `local`, `development`, `staging`, `production` — and a word defined three
times drifts three ways. Decided by
[ADR-0028](docs/adr/0028-four-environment-model-and-typed-configuration.md) and
[ADR-0029](docs/adr/0029-seed-data-through-aggregates-never-in-production.md). Each app's
`CONTEXT.md` may add how *it* reads the value; none of them redefines the names.

[`docs/value-formatting.md`](docs/value-formatting.md) — the exact string a price, a level, a
time or a duration becomes. Not a design system (no colour, no size), not domain language (no
nouns): a rendering contract. The backend sends numbers and machine codes and never display
text ([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)), so both clients
format, and this is the one table they both implement. Enforced by the cross-application
contract suite of [ADR-0021](docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md),
not by hoping.

## Decisions (ADRs)

**`docs/adr/`** (root) holds every decision affecting the system or the contract
between apps, numbered sequentially across the whole repo. There are no per-app ADR
directories: a decision that only affects one app still tends to constrain the others,
and one numbered sequence is easier to reason about than three.

## Claude Code instructions

`CLAUDE.md` files load from the working directory **and every ancestor**, so a session in
`backend/` gets the root file plus the backend's. Files in sibling apps never load. Work
from inside the app you are changing:

- **`CLAUDE.md`** (root) — monorepo orientation and the repo-wide safety list.
- **`backend/CLAUDE.md`** — Python/FastAPI rules (TDD, hexagonal, events, Poetry).
- **`frontend_player/CLAUDE.md`** — Expo/RN rules (feature layering, secure store, codegen).
- **`frontend_club/CLAUDE.md`** — Next.js rules (feature layering, BFF, codegen, TanStack).

**Settings and hooks do not work that way.** Claude Code reads `.claude/settings.json`
**only from the directory the session started in** — it is not inherited from ancestors.
So each app carries its own `.claude/settings.json` that registers the same two hooks and
adds that app's permissions. Registering them only at the root would leave every scoped
session — the ones the ownership boundary exists for — running with no guardrails.

Each app also carries:

- **`.claude/rules/`** — conventions with `paths:` frontmatter, loaded only when Claude
  opens a matching file (design system on UI files, BFF rules on route handlers).
- **`.claude/skills/`** — procedures, loaded only when invoked or judged relevant.

The always-loaded `CLAUDE.md` holds what is true in *every* session in that app; everything
else lives one layer down. See
[`docs/agents/ownership-boundaries.md`](docs/agents/ownership-boundaries.md).

## Where things live

```
/
├── CLAUDE.md                 ← monorepo orientation + safety list
├── CONTEXT-MAP.md            ← you are here
├── CONTEXT.md                ← SHARED domain glossary (source of truth)
├── Makefile                  ← thin root helpers (gen-api, check, afk)
├── .claude/
│   ├── settings.json         ← root-session permissions + hook registration
│   ├── hooks/                ← enforce-ownership.sh, guard-bash.sh, test-hooks.sh
│   └── skills/               ← cross-app procedures (write-adr, guardrails)
├── docs/
│   ├── adr/                  ← system-wide decisions (0001…)
│   ├── agents/               ← ownership boundaries, domain-doc consumption
│   ├── environments.md       ← THE four environment names + deployment contract
│   └── value-formatting.md   ← the one rendering table both clients implement
├── backend/                  ← FastAPI  (CLAUDE.md + CONTEXT.md + its own docs/)
├── frontend_player/          ← Expo     (CLAUDE.md + CONTEXT.md)
│   ├── docs/architecture.md          ← the player app's runtime contract (ADR-0013)
│   ├── docs/design-system.md         ← the player app's LOCKED visual contract
│   └── src/shared/ui/theme.ts        ← its values; components read the theme only
├── frontend_club/            ← Next.js  (CLAUDE.md + CONTEXT.md)
│   ├── docs/design-system.md         ← the club console's LOCKED visual contract
│   └── src/shared/ui/tokens.css      ← its values; components use var(--…) only
└── tools/afk/ + .sandbuket/  ← the AFK agent execution loop and its sandbox image
```
