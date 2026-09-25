# Raketa — Context Map

A **polyglot monorepo** of **four independently deployable apps** that realize the
**same** bounded contexts
([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)).
Two ship today; the two web apps are decided and arrive with their scaffolds:

- **`backend/`** — async FastAPI service. Clean/hexagonal, DDD, event sourcing,
  transactional outbox. Python 3.11 + Poetry. **Source of truth for the API contract.**
- **`frontend_player/`** — React Native + Expo, TypeScript. The native iOS/Android app
  for players — and for **Administrators**, as a second profile inside it, never a separate
  app. Talks to FastAPI directly; tokens live in the OS keychain.
- **`frontend_club/`** — the **club website**, Next.js. A club signs up, invites its
  Administrators and watches its official groups. Its server keeps the session in an encrypted
  httpOnly cookie; the browser never holds a token. *Scaffolded by
  [#522](https://github.com/Raketa02/Raketa/issues/522).*
- **`frontend_public/`** — the **public site**, Next.js, server-rendered: the pages a group link,
  an invitation or a password reset opens when the app is not installed, and the app-link files.
  No sign-in, no session. *Scaffolded by [#525](https://github.com/Raketa02/Raketa/issues/525).*

Outside the monorepo, **`Raketa02/raketa-features`** holds the feature flags as Featurevisor
YAML. It is not an app and holds no domain code: its CI builds one datafile per environment,
and the player app fetches its own over HTTP and decides each flag on the device
([ADR-0180](docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)).

```
                          ┌──────────────────┐
                          │   backend/       │  owns the domain + the contract
                          │   FastAPI        │  one document per surface
                          └───┬─────┬─────┬──┘
              player surface  │     │     │  public surface (no auth)
         ┌────────────────────┘     │     └─────────────────────┐
┌────────▼──────────┐   club surface│              ┌────────────▼────────┐
│ frontend_player/  │  ┌────────────▼──────┐       │ frontend_public/    │
│ Expo · direct API │  │ frontend_club/    │       │ Next.js · SSR       │
│ token in keychain │  │ Next.js · server  │       │ holds nothing       │
│ player + admin    │  │ cookie session    │       │ group/invite/reset  │
└───────────────────┘  └───────────────────┘       └─────────────────────┘
```

The dev console's `openapi.dev.json` is a fourth surface with no client.

> **The club console that the 2026-08-25 reset removed returns as a different app.** It was
> a Next.js console with a BFF; what arrives is the **club website** of PRD
> [#500](https://github.com/Raketa02/Raketa/issues/500) — sign-up, Administrators, official
> groups — at the same path, `frontend_club/`, whose fence the guardrail hooks kept for exactly
> this day. `frontend_public/` is new and gets a fence of its own
> ([#502](https://github.com/Raketa02/Raketa/issues/502)).

> **The matchmaking engine did not add an app, and that was a decision rather than an
> omission** — the two web apps above arrived later, for a different reason: they are new
> surfaces with their own users, not a slice of the backend's own work. Its input document
> recommended a deployable in Go at `matcher/`;
> [ADR-0093](docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md) puts it in the
> backend instead — the stateful half as a module, the scorer as the **second engine** beside
> RacketSkill. So there is no `matcher/CLAUDE.md`, no `matcher/` ownership fence and no matcher CI
> lane, and the only new topology is a spec set under `docs/specs/matchmaking/`. The two engines
> may not import each other, which is why `.importlinter` now carries two `forbidden` contracts
> rather than one: two engines that can reach each other develop two opinions about a level.

## How the domain language is split

An `Assessment` means the same thing in both apps. To stop the ubiquitous language
drifting, the **domain** glossary lives in exactly one place and each app adds only its
own **technical** vocabulary:

| File | Scope | Owns |
| --- | --- | --- |
| **`CONTEXT.md`** (root) | **Shared domain language — source of truth** | User, Player, Authority, Email, Sport, SportSpec, Assessment, Skill rating, Level, Band, Confidence, statuses, domain events, Audience, Signing out everywhere, Player profile, Social tag, Availability grid, Search radius, Proposals opt-in, Challenge, Seat, Standing, Game, Result, Score, Counted game, Ghost game, Player Score, Strand, Player card, Record block, Run of form, At stake, On-court check, Sportsmanship, Stars, The card, Club, Club account, Home club, Group, Player group, Official group, Owner, Group member, Join policy, Join request, Group link, WhatsApp group size, Handover, Administrator, Invitation, Tester, Feature flag… |
| **`backend/CONTEXT.md`** | Backend technical vocab only | event-sourced aggregate, outbox, event store, port/adapter, UoW… |
| **`frontend_player/CONTEXT.md`** | Player-app technical vocab only | feature, use-case, mapper, wire type vs DTO, screen, secure store, query/mutation, presentation module, copy deck… |
| **`frontend_club/CONTEXT.md`** | Club-website technical vocab only — *arrives with [#522](https://github.com/Raketa02/Raketa/issues/522)* | server layer, cookie session, server action, view model… |
| **`frontend_public/CONTEXT.md`** | Public-site technical vocab only — *arrives with [#525](https://github.com/Raketa02/Raketa/issues/525)* | preview tags, app-link files, Open in Raketa… |

An app `CONTEXT.md` must **never redefine** a domain term — it points back to the root
glossary. Three words collide across that line and are settled at the root: the app's
switcher says *profile* (UI vocabulary — *Player profile* is an aggregate), a Members list
says **admin** (copy for *runs this group* — not the `ADMIN` Authority), and a conversation's
**Member** is not a **Group member**.

## Design systems are per-app and never shared

Each client owns its own visual language, tokens and vocabulary, and shares no code with
any other ([ADR-0005](docs/adr/0005-three-app-monorepo-ownership-boundaries.md)). It is
stated as a rule rather than as a description because the moment a second client exists,
the tempting move is a shared design package, and that is the thing this forbids — and the
moment is here: the public site **borrows the club website's look** (paper, the coral square
wordmark, a white card) by **copying its values into its own tokens**, never by importing them
([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md) §6).

| File | Owns |
| --- | --- |
| **`frontend_player/docs/design-system.md`** | The player app's rules: colour meanings, the primitives, the level bar, overlays, touch and accessibility. **Locked** — [ADR-0012](docs/adr/0012-player-app-design-system.md). |
| **`frontend_player/src/shared/ui/theme.ts`** | The player app's values, as a typed object. Same rule: no literal in a component. |
| **`frontend_club/src/ui/`** | The club website's tokens, as CSS custom properties taken from the club mocks, and its primitives. *Arrives with [#522](https://github.com/Raketa02/Raketa/issues/522).* |
| **`frontend_public/src/ui/`** | The public site's own copy of that look, laid out for phones first. *Arrives with [#525](https://github.com/Raketa02/Raketa/issues/525).* |

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
- **`frontend_club/CLAUDE.md`** and **`frontend_public/CLAUDE.md`** — each web app's own
  standard ([ADR-0187](docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §6), written by its scaffold. A rule learned in one client does not transfer to another.

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
│   ├── specs/play-groups/    ← Play › Groups, the club website and the Administrator:
│   │                            the product owner's mocks and which area each one draws
│   └── value-formatting.md   ← the rendering table the client implements
├── backend/                  ← FastAPI  (CLAUDE.md + CONTEXT.md + its own docs/)
├── frontend_player/          ← Expo     (CLAUDE.md + CONTEXT.md)
│   ├── docs/architecture.md          ← the player app's runtime contract (ADR-0013)
│   ├── docs/design-system.md         ← the player app's LOCKED visual contract
│   └── src/shared/ui/theme.ts        ← its values; components read the theme only
├── frontend_club/            ← Next.js  the club website  (arrives with #522)
├── frontend_public/          ← Next.js  the public site   (arrives with #525)
└── tools/afk/ + .sandbuket/  ← the AFK agent execution loop and its sandbox image
```
