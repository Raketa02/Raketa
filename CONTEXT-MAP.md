# Raketa — Context Map

A **polyglot monorepo** with two independently deployable apps that realize the
**same** bounded contexts:

- **`backend/`** — async FastAPI service. Clean/hexagonal, DDD, event sourcing,
  transactional outbox. Python 3.11 + Poetry. **Source of truth for the API contract.**
- **`frontend_player/`** — React Native + Expo, TypeScript. The native iOS/Android app
  for players. Talks to FastAPI directly; tokens live in the OS keychain.

```
                    ┌──────────────────┐
                    │   backend/       │  owns the domain + the contract
                    │   FastAPI        │
                    └────────┬─────────┘
                             │  HTTP
                  ┌──────────▼──────────┐
                  │  frontend_player/   │
                  │  Expo · direct API  │
                  │  token in keychain  │
                  └─────────────────────┘
```

> **A club console (`frontend_club/`, Next.js + a BFF) used to sit beside the player app and
> was removed in the 2026-08-25 reset**, along with everything built ahead of sign-up,
> sign-in and onboarding. The ownership machinery below still describes the *shape* of a
> multi-app repo, because that is what it is again the moment a second client returns — and
> the guardrail hooks still fence `frontend_club/` for exactly that reason.

> **The matchmaking engine did not add a third app, and that was a decision rather than an
> omission.** Its input document recommends a fourth deployable in Go at `matcher/`;
> [ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) puts it in the
> backend instead — the stateful half as a module, the scorer as the **second engine** beside
> RacketSkill. So there is no `matcher/CLAUDE.md`, no fourth ownership fence and no second CI
> lane, and the only new topology is a spec set under `docs/specs/matchmaking/`. The two engines
> may not import each other, which is why `.importlinter` now carries two `forbidden` contracts
> rather than one: two engines that can reach each other develop two opinions about a level.

## How the domain language is split

An `Assessment` means the same thing in both apps. To stop the ubiquitous language
drifting, the **domain** glossary lives in exactly one place and each app adds only its
own **technical** vocabulary:

| File | Scope | Owns |
| --- | --- | --- |
| **`CONTEXT.md`** (root) | **Shared domain language — source of truth** | User, Authority, Email, Sport, SportSpec, Assessment, Skill rating, Level, Band, Confidence, statuses, domain events, Player profile, Social tag, Availability grid, Search radius, Proposals opt-in, Challenge, Seat, Standing, Game, Result, Score, Counted game, Ghost game, Player Score, Strand, Player card, Record block, Run of form, At stake, On-court check, Sportsmanship, Stars, The card… |
| **`backend/CONTEXT.md`** | Backend technical vocab only | event-sourced aggregate, outbox, event store, port/adapter, UoW… |
| **`frontend_player/CONTEXT.md`** | Player-app technical vocab only | feature, use-case, mapper, wire type vs DTO, screen, secure store, query/mutation, presentation module, copy deck… |

An app `CONTEXT.md` must **never redefine** a domain term — it points back to the root
glossary.

## Design systems are per-app and never shared

Each client owns its own visual language, tokens and vocabulary, and shares no code with
any other ([ADR-0005](docs/adr/0005-three-app-monorepo-ownership-boundaries.md)). One
client ships today, so the rule currently binds one app — it is stated as a rule rather
than as a description because the moment a second client exists, the tempting move is a
shared design package, and that is the thing this forbids.

| File | Owns |
| --- | --- |
| **`frontend_player/docs/design-system.md`** | The player app's rules: colour meanings, the primitives, the level bar, overlays, touch and accessibility. **Locked** — [ADR-0012](docs/adr/0012-player-app-design-system.md). |
| **`frontend_player/src/shared/ui/theme.ts`** | The player app's values, as a typed object. Same rule: no literal in a component. |

Design-system *terms* (token, soft/ink, eyebrow, hairline, severity rail, band ink, sheet
vs drawer) are technical vocabulary and live in that app's `CONTEXT.md`. A design system
never settles a **domain** term — that happens in the root `CONTEXT.md` first.

**Two things sit between the apps and are shared.**

[`docs/environments.md`](docs/environments.md) — the four environment names, what each is,
which variable carries it in each app, the refusals, the scheme rule, the test taxonomy, and
the checklist for turning on a remote environment. Not domain language (no nouns a player
would recognise) and not a design system: a **deployment contract**. It lives at the root
because an environment name is the one piece of vocabulary every app must spell
identically — `local`, `development`, `staging`, `production` — and a word defined once per
app drifts once per app. Decided by
[ADR-0028](docs/adr/0028-four-environment-model-and-typed-configuration.md) and
[ADR-0029](docs/adr/0029-seed-data-through-aggregates-never-in-production.md). Each app's
`CONTEXT.md` may add how *it* reads the value; none of them redefines the names.

[`docs/value-formatting.md`](docs/value-formatting.md) — the exact string a price, a level, a
time or a duration becomes. Not a design system (no colour, no size), not domain language (no
nouns): a rendering contract. The backend sends numbers and machine codes and never display
text ([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)), so the client
formats, and this is the table it implements. Enforced by the cross-application
contract suite of [ADR-0021](docs/adr/0021-kernel-in-backend-clients-derive-by-comparison.md),
not by hoping.

## Decisions (ADRs)

**`docs/adr/`** (root) holds every decision affecting the system or the contract
between apps, numbered sequentially across the whole repo. There are no per-app ADR
directories: a decision that only affects one app still tends to constrain the others,
and one numbered sequence is easier to reason about than several. **The sequence has gaps**
— see the [index](docs/adr/README.md#the-2026-08-25-reset--why-the-sequence-has-gaps).

## Claude Code instructions

`CLAUDE.md` files load from the working directory **and every ancestor**, so a session in
`backend/` gets the root file plus the backend's. Files in sibling apps never load. Work
from inside the app you are changing:

- **`CLAUDE.md`** (root) — monorepo orientation and the repo-wide safety list.
- **`backend/CLAUDE.md`** — Python/FastAPI rules (TDD, hexagonal, events, Poetry).
- **`frontend_player/CLAUDE.md`** — Expo/RN rules (feature layering, secure store, codegen).

**Settings and hooks do not work that way.** Claude Code reads `.claude/settings.json`
**only from the directory the session started in** — it is not inherited from ancestors.
So each app carries its own `.claude/settings.json` that registers the same two hooks and
adds that app's permissions. Registering them only at the root would leave every scoped
session — the ones the ownership boundary exists for — running with no guardrails.

Each app also carries:

- **`.claude/rules/`** — conventions with `paths:` frontmatter, loaded only when Claude
  opens a matching file (the design system on UI files, the HTTP rules on API clients).
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
│   ├── specs/player-app/     ← the player app's product + architecture specifications
│   ├── specs/matchmaking/    ← the matchmaking engine: the spec set + the two frozen inputs
│   │                            the-engine.md is the entry point and states precedence
│   │                            the-words.md is the WHOLE app's copy deck, here for history
│   ├── specs/the-loop/       ← the core loop's screens + seams: Chats, the challenge screen,
│   │                            the conversation, Now, and the one state-detail surface
│   └── value-formatting.md   ← the rendering table the client implements
├── backend/                  ← FastAPI  (CLAUDE.md + CONTEXT.md + its own docs/)
├── frontend_player/          ← Expo     (CLAUDE.md + CONTEXT.md)
│   ├── docs/architecture.md          ← the player app's runtime contract (ADR-0013)
│   ├── docs/design-system.md         ← the player app's LOCKED visual contract
│   └── src/shared/ui/theme.ts        ← its values; components read the theme only
└── tools/afk/ + .sandbuket/  ← the AFK agent execution loop and its sandbox image
```
