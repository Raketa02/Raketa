# Rakieta Player App (iOS + Android)

React Native + Expo + TypeScript. The native app players use to find courts, book slots
and organise matches. It renders with **real platform components** — this is not a
website in a WebView. Feature-first **Clean Architecture**, talking to FastAPI over
HTTPS and generating its wire types from `backend/openapi.json`. pnpm.

> **Monorepo note.** This is the `frontend_player/` app of a three-app monorepo (see the
> root [`CLAUDE.md`](../CLAUDE.md) and [`../CONTEXT-MAP.md`](../CONTEXT-MAP.md)).
> Everything here scopes to `frontend_player/` — **run all commands from this
> directory.** The FastAPI backend (`../backend/`) and the Next.js club app
> (`../frontend_club/`) have their own `CLAUDE.md`; **never apply their rules here, and
> never import their source.** A `PreToolUse` hook blocks writes outside
> `frontend_player/` from this session. Shared docs live at the root:
> [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

## Not scaffolded yet

This directory currently holds architecture, config and rules — not a running app.
`pnpm install` has not been run and there is no `src/app/_layout.tsx` yet. If you are
the first session here, read [`README.md`](README.md) for the bootstrap sequence, and
build outward from the structure rather than reaching for `create-expo-app` (its default
template contradicts
[ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)).

**Dependency versions target Expo SDK 52.** Expo pins React Native and its own packages
tightly, so after the first install run `npx expo install --check` and trust Expo's
resolution over the pins in `package.json`.

## Default workflow

For non-trivial changes:
1. Explore the relevant files; state current behavior and constraints.
2. Propose a minimal plan before editing. For changes touching >5 files, confirm first.
3. Write or update tests first when behavior changes (see Testing).
4. Make the smallest safe change.
5. Run the most focused relevant tests first, then `pnpm test` when practical.
6. Run `pnpm lint && pnpm typecheck` before finishing if code changed.
7. Summarize changed files, checks run, and remaining risks.

Do not claim a task is done unless the relevant tests/checks ran — or plainly state why.
**You cannot see the screen.** If a change is visual, say so and ask for a look rather
than asserting it renders correctly.

## Safety — never do these without an explicit request

- **Store credentials anywhere but the OS keychain.** Tokens live in
  `expo-secure-store`, reached only through `src/shared/lib/auth`. **Never**
  `AsyncStorage` (unencrypted plaintext on device), never a plain module variable that
  outlives a session, never a log line. *(ESLint blocks the AsyncStorage import.)*
- **Put a secret in `app.json` `extra`, or in any `EXPO_PUBLIC_*` variable.** Everything
  in the bundle is readable from a shipped app. Those are **config**, not secrets. A
  secret a mobile client "needs" is a design error — it belongs behind the backend.
- **Run a build or release** (`eas build`, `eas submit`, `eas update`, `expo publish`).
  *(hook-enforced)*
- **Create or edit a real `.env*` file.** Edit `.env.example`. *(hook-enforced)*
- **Import from `src/generated/` outside a feature's `api/` or `mappers/` layer.**
- **Hand-write a type that mirrors a backend response.** Regenerate with `pnpm gen:api`.
- **Put business rules in screens or hooks.** Rules live in `domain/` + `use-cases/`.
- **Commit `android/` or `ios/`.** They are `expo prebuild` output, not source.

## Commands

```bash
pnpm start        # Expo dev server (press i / a for simulator)
pnpm ios          # build & run on the iOS simulator
pnpm android      # build & run on an Android emulator
pnpm lint         # ESLint — also enforces the import boundaries below
pnpm typecheck    # tsc --noEmit (strict)
pnpm test         # Jest (jest-expo)
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.json
pnpm doctor       # npx expo-doctor — checks dependency/SDK agreement
pnpm check        # lint + typecheck + test — the local gate
```

Regenerate the API client whenever the backend contract changes, and **commit the
result**. `make gen-api` from the repo root regenerates both clients at once.

## Architecture

Source lives under `src/`. **Every feature carries the full layer set** — the same
discipline the backend and the club app use:

```
src/
  app/                      expo-router screens (thin). File-based routing.
    (auth)/ (tabs)/         route groups
    _layout.tsx
  features/<feature>/
    domain/                 entities + value objects + rules (pure TS, no RN/fetch)
    use-cases/              one fn per workflow; orchestrates domain + ports
    api/                    calls FastAPI directly; speaks wire types
    mappers/                wire DTO  <->  domain object
    schemas/                Zod schemas (form/input validation)
    components/             rendering + interaction only
    hooks/                  thin adapters over use-cases (TanStack Query lives here)
    types.ts
  shared/
    ui/                     design-system primitives
    lib/                    http/ auth/ (the ONLY expo-secure-store consumer) query-client/
    config/                 env.ts (Zod-validated, read from expo-constants)
    errors/                 AppError.ts
    store/                  Zustand — cross-cutting UI state only
  generated/                openapi-typescript output — raw wire types ONLY
```

The per-layer contract is in
[`src/features/_template/README.md`](src/features/_template/README.md). Copy that folder
to start a feature.

Rules to preserve:
- **Dependencies point inward:** `app/ → hooks/ → use-cases/ → domain/`. `domain/`
  imports nothing from React Native, Expo, `fetch`, or `generated/`.
- **The wire boundary is `api/` + `mappers/`.** ESLint enforces it.
- **`src/shared/lib/auth` is the single chokepoint for credentials.** No feature, screen
  or hook imports `expo-secure-store`. One module owning the keychain is what makes
  token lifetime auditable.
- **`src/shared/lib/http` is the only place `fetch` is configured** — and the only place
  the 401 → refresh → retry rotation lives, so a burst of 401s cannot fan out into N
  concurrent refresh calls racing each other.
- **Global state is minimal:** Zustand for cross-cutting UI state only. Server data is
  never mirrored into a store — TanStack Query owns it.

### Why there is no BFF here

The club app routes everything through a server-side BFF with httpOnly cookies. This app
does not, and that is deliberate: a native app has no cookie jar and no shared-origin
browser context, so the equivalent protection is the **OS keychain**
([ADR-0008](../docs/adr/0008-player-mobile-securestore-direct-api.md)). Don't "fix" the
asymmetry by adding a proxy, and don't copy the club app's cookie code here.

**Uniform-strict escape hatch:** when a feature genuinely has no business rule, its
`use-cases/` may be thin pass-throughs and `domain/` may be just types. Keep the folders
for predictability, but **do not invent fake invariants to fill them**.

## Testing (TDD — test first)

Write the failing test first, make it pass, refactor.

- **Jest (`jest-expo`) + Testing Library React Native.** `domain/`, `use-cases/` and
  `mappers/` are pure — test those first and hardest, with no renderer.
- Colocate as `*.test.ts(x)` next to the file under test.
- Mock ports with hand-written stubs, not deep module mocks.

## Code style

- **TypeScript strict** (`strict`, `noUncheckedIndexedAccess`, no implicit `any`).
- **ESLint + Prettier**; run `pnpm format` before committing. Prefer named exports.
- **Zod** for all external input (forms, config, anything crossing a boundary).
- New domain concepts use the **shared glossary's** vocabulary
  ([`../CONTEXT.md`](../CONTEXT.md)). A `Court` is a `Court` — not a Venue or Facility.

## Mobile-specific gotchas

- **`localhost` on a device is the device.** Testing on a physical phone needs a LAN IP
  or tunnel in `EXPO_PUBLIC_API_URL`.
- **Old app versions live on real phones for months.** Treat backend contract changes as
  breaking unless they are additive — you cannot force everyone to update.
- **Offline and flaky networks are the normal case,** not an edge case. Prefer TanStack
  Query's cache/retry behavior over hand-rolled loading flags.

## Git & PRs

- Conventional Commits scoped `player`: e.g. `feat(player): court search filters`.
- CI runs `lint`, `typecheck` and `test` for `frontend_player/` when
  `frontend_player/**` changed; all must pass. Run `pnpm check` before pushing.

## Domain language

Shared domain terms: [`../CONTEXT.md`](../CONTEXT.md). Player-app-only technical
vocabulary: [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally.
