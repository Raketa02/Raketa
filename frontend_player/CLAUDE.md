# Raketa Player App (iOS + Android)

React Native + Expo + TypeScript. The native app players use to find courts, book slots and
organise matches. It renders with **real platform components** — this is not a website in a
WebView. Feature-first Clean Architecture
([ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)), talking to
FastAPI over HTTPS and generating its wire types from `backend/openapi.player.json`
(the player half of the two-document contract). pnpm.

> The `frontend_player/` app of a three-app monorepo — see the root
> [`CLAUDE.md`](../CLAUDE.md). Run every command from this directory. Never import from
> `../backend/` or `../frontend_club/`; a hook blocks writes there. Shared docs:
> [`../CONTEXT.md`](../CONTEXT.md), [`../docs/adr/`](../docs/adr/).

Two contracts predate the code and are **already settled** — read them before writing a
feature, not after:

| Doc                                              | Settles                                                                                    |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------ |
| [`docs/architecture.md`](docs/architecture.md)   | Where code lives, who owns which state, how auth/errors/Query/native behave in production. |
| [`docs/design-system.md`](docs/design-system.md) | Every colour, type role, spacing step and interaction rule. **Locked.**                    |

## What exists

`src/app/_layout.tsx` composes the providers and `src/shared/lib/bootstrap` runs the one
ordered startup sequence. Above that: the HTTP client with its 401 → refresh → retry
rotation, the `AppError` family, `shared/lib/auth` over the keychain, and two features —
`auth` (sign up, sign in, session restore) and `onboarding` (the entry gate, welcome, the
sports picker, the adaptive question loop, the explained result, and the summary and data
screens a player leaves through).

`features/now/` holds the Now section's **vocabulary and nothing else yet** — no screen, no
`api/`, no hooks. Four copy tables (36 situations · 10 term codes · 5 hold reasons · 7 acts),
the shelf-code → Find pre-filter map and the caption codes, all keyed on unions generated from
`openapi.player.json`. **Completeness is a typecheck, not a test**
([ADR-0075](../docs/adr/0075-the-second-table-is-unpaid-and-the-first-ships-in-english.md)): a
contract value added without its sentence fails `pnpm typecheck`. That only holds while the key
is a closed union — a code crossing as a bare `string` turns the `Record` into an index
signature that never fires — so each table carries an `AssertTrue<IsClosedUnion<…>>` pin, and
`copyTables.test.ts` writes the enumeration out so that _growth_ is a decision somebody makes in
a diff. The three guards catch three different edits; do not collapse them.

**The tables live in `mappers/`.** They key on `@/generated`, which only `api/` and `mappers/`
may read, and mapping a wire code to a value object `domain/` owns is what a mapper is. The half
of each entry the wire has no opinion about — tone, tag, the act's surface — is in
`domain/presentation.ts`.

`src/shared/ui/` holds the design-system primitives built so far — the cards, note, row,
hairline, button, tag, bar, header, and the overlays and drawn objects the result screen
needed (bottom sheet, popover, level bar, confidence ring); the rest arrive with the
features that need them. **Build outward from the structure below** rather than reaching
for `create-expo-app` — its default template contradicts ADR-0009 — and copy the shape of
`src/features/auth/` or `src/features/onboarding/` rather than inventing a second one.

**Copy `.env.example` → `.env.local` before the first run.** `EXPO_PUBLIC_API_URL` and
`EXPO_PUBLIC_ENV` are both required and validated once at launch by
`src/shared/config/env.ts`. A missing or malformed value stops the app on a startup screen
naming it — that is the guardrail working, not a bug.

`EXPO_PUBLIC_ENV` is `local | development | staging | production`, the same four the
backend and the club app use, and **only `local` runs today.** The environment fixes the
API URL's scheme — `https://` for the three deployed ones, either for `local` — so a
laptop URL under a deployed name fails at launch naming both variables rather than
shipping a build that points at nothing.

**`app.config.ts` is a function of that environment**, not a static document — it replaced
`app.json`. It holds no logic of its own: `src/shared/config/appIdentity.ts` is a pure
table mapping each environment to the app's display name and its badge, and the config
document calls it. Outside `production` the app is named for its environment and wears an
amber badge over every screen; `production` is bare and unbadged. There is **one**
installable variant — one bundle identifier, one URL scheme, no build profiles — until a
second backend exists to point a second one at.

Expo evaluates that document in **Node**, before Metro, so it reads `process.env`
directly and refuses an unknown environment rather than defaulting to one. It registers
sucrase's TS require hook first, because Node cannot otherwise `require` the `.ts`
identity module — delete that line and `npx expo start` fails on a missing module.

**Dependency versions target Expo SDK 52.** Expo pins React Native and its own packages
tightly, so after changing dependencies run `npx expo install --check` and trust Expo's
resolution over the pins in `package.json`. That pin is why `eslint.config.mjs` reaches
`eslint-config-expo` through `FlatCompat`: its flat config ships from v9, which belongs to
SDK 53.

**`.npmrc` sets `node-linker=hoisted`.** Metro and jest-expo decide what still needs
transforming with `node_modules/(?!…)` allowlists, and pnpm's default symlinked layout
defeats them — React Native ships untranspiled Flow, so the first casualty is `jest`
failing to parse `error-guard.js`. Hoisting is Expo's documented answer; it changes nothing
architectural, and this app still shares no packages with `frontend_club`.

Archivo (400–800) and IBM Plex Mono (400–600) are loaded with `expo-font` and **awaited
before the splash screen hides** — a font that arrives late reflows every number on screen.
They are imported **file by file**: each `@expo-google-fonts` index `require`s every weight
and italic it ships, and Metro does not tree-shake, so importing one name costs 4,2 MB
instead of 1,0 MB.

## Commands

```bash
pnpm start        # Expo dev server (press i / a for simulator)
pnpm ios / android
pnpm lint         # ESLint — also enforces the import boundaries below
pnpm typecheck    # tsc --noEmit (strict)
pnpm test         # Jest (jest-expo)
pnpm format       # Prettier --write   pnpm format:check → --check
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.player.json
pnpm doctor       # npx expo-doctor — checks dependency/SDK agreement
pnpm check        # lint + format check + typecheck + test — the local gate
```

**You cannot see the screen.** If a change is visual, say so and ask for a look rather than
asserting it renders correctly.

## Safety — never without an explicit request

- **Store credentials anywhere but the OS keychain.** Tokens live in `expo-secure-store`,
  reached only through `src/shared/lib/auth`. **Never** `AsyncStorage` (unencrypted
  plaintext on device), never a module variable that outlives a session, never a log line.
  _(ESLint blocks the AsyncStorage import.)_
- **Put a secret in `app.config.ts` `extra`, or in any `EXPO_PUBLIC_*` variable.** Everything in
  the bundle is readable from a shipped app. Those are **config**, not secrets. A secret a
  mobile client "needs" is a design error — it belongs behind the backend.
- **Run a build or release** (`eas build|submit|update`, `expo publish`). _(hook-enforced)_
- **Create or edit a real `.env*` file.** Edit `.env.example`. _(hook-enforced)_
- **Import from `src/generated/` outside a feature's `api/` or `mappers/` layer.**
- **Hand-write a type that mirrors a backend response.** Regenerate with `pnpm gen:api`.
- **Put business rules in screens or hooks.** Rules live in `domain/` + `use-cases/`.
- **Call `fetch` outside `src/shared/lib/http`,** or add a second networking path.
- **Copy server data into Zustand.** TanStack Query owns every backend-derived value.
- **Retry a mutation** unless the endpoint is idempotent, takes an idempotency key, or is
  explicitly safe to repeat. Booking and payment calls are exactly where a silent retry
  charges someone twice.
- **Trust a deep-link, push or route param.** Validate with Zod before use.
- **Write a literal colour, font size, spacing or radius in a component.** Every value comes
  from `src/shared/ui/theme.ts`.
- **Add a dependency that owns styling** — NativeWind, styled-components, Unistyles,
  Restyle, a component kit. The system is a typed theme + `StyleSheet.create`
  ([ADR-0012](../docs/adr/0012-player-app-design-system.md)).
- **Commit `android/` or `ios/`.** They are `expo prebuild` output, not source.

## Architecture

Full contract: [`docs/architecture.md`](docs/architecture.md). **Every feature carries the
full layer set**, so an agent applies one rule rather than judging per feature.

```
src/
  app/                      expo-router screens (thin). File-based routing.
    _layout.tsx             root providers + the bootstrap gate
    (public)/ (auth)/ (app)/(tabs)/
  features/<feature>/
    domain/                 entities + value objects + rules (pure TS, no RN/fetch)
    use-cases/              one fn per workflow; orchestrates domain + ports
    api/                    calls FastAPI directly; speaks wire types
    mappers/                wire DTO <-> domain object
    schemas/  components/  hooks/  store/ (optional)
    types.ts                the feature's public surface
  shared/
    ui/                     theme.ts (THE source of every value) + primitives
    lib/  http/ auth/ query-client/ bootstrap/ platform/ observability/
    config/ errors/ store/
  generated/                openapi-typescript output — raw wire types ONLY
```

The per-layer contract is in [`src/features/_template/README.md`](src/features/_template/README.md).
Copy that folder to start a feature.

Rules to preserve:

- **Dependencies point inward:** `app/ → components/ → hooks/ → use-cases/ → domain/`.
  `domain/` imports nothing from React Native, Expo, `fetch` or `generated/`.
- **The wire boundary is `api/` + `mappers/`.** ESLint enforces it.
- **`src/shared/lib/auth` is the single chokepoint for credentials.** No feature, screen or
  hook imports `expo-secure-store`. One module owning the keychain is what makes token
  lifetime auditable.
- **`src/shared/lib/http` is the only place `fetch` is configured** — and the only place the
  401 → refresh → retry rotation lives.
- **`shared/` never imports a feature,** and a feature never deep-imports another — go
  through its `types.ts`. But **do not move code to `shared/` because two files use it**;
  keep it local until cross-feature ownership is proven.
- **No global `services/`, `utils/`, `types/` or `hooks/` bucket.** A capability is one
  directory; utilities get semantic homes (`formatting/`, `date/`, `currency/`).
- **Uniform-strict escape hatch:** where a feature genuinely has no business rule, its
  `use-cases/` may be thin pass-throughs and `domain/` may be just types. Keep the folders
  for predictability, but **do not invent fake invariants to fill them.**

### One owner per kind of state

| State                     | Owner                                                                |
| ------------------------- | -------------------------------------------------------------------- |
| Anything from the backend | **TanStack Query** — never mirrored into a store                     |
| Access + refresh tokens   | `shared/lib/auth` → `expo-secure-store` (+ in-memory mirror)         |
| Logged-in / out           | `SessionStatus`: `bootstrapping \| authenticated \| unauthenticated` |
| Local component state     | `useState` / `useReducer`                                            |
| Shared ephemeral UI state | Zustand, **feature-scoped first**                                    |
| Form input                | The form + one Zod schema                                            |
| Navigation                | expo-router — a route param is not app state                         |
| Config                    | `shared/config/env.ts`, Zod-validated at startup                     |

Reach for Zustand last: component-local → feature store → app-wide store, and only with a
reason. Zustand never holds API entities, tokens, a backend cache, or a global loading flag.

### Session, bootstrap and routing

Model bootstrap as a **state**, never as `user === undefined` — that ambiguity is what
produces a login-screen flash while valid credentials are still being read out of the
keychain, and an authenticated-tree flash before a redirect.

`shared/lib/bootstrap` runs one ordered sequence: error reporting → validate config → wire
focus/online managers → read SecureStore → restore/validate session → hide splash → render.
Nothing renders a route tree before it resolves.

Expo Router's declarative protected routes landed **after SDK 52**, so the guard is a
redirect in `(app)/_layout.tsx` keyed on `SessionStatus`. Route groups exist so the
authorization boundary is visible in the file tree.

iOS Keychain data can survive a reinstall, so **a token existing is not proof a session
exists** — bootstrap validates it.

### Why there is no BFF here

The club app routes everything through a server-side BFF with httpOnly cookies. This app
does not, and that is deliberate: a native app has no cookie jar and no shared-origin
browser context, so the equivalent protection is the **OS keychain**
([ADR-0008](../docs/adr/0008-player-mobile-securestore-direct-api.md)). Don't "fix" the
asymmetry by adding a proxy, and don't copy the club app's cookie code here.

## Mobile gotchas that bite once

- **`localhost` on a device is the device.** A physical phone needs a LAN IP or tunnel in
  `EXPO_PUBLIC_API_URL`.
- **Old app versions live on real phones for months.** Treat backend contract changes as
  breaking unless additive — you cannot force everyone to update.
- **`fetch` has no default timeout.** Timeouts are centralized in `shared/lib/http` as
  classes (request/upload/download/background) — no millisecond literal in a feature.
- **`android/` and `ios/` are `expo prebuild` output.** Native config goes through
  `app.config.ts` and config plugins; a hand edit is lost on the next prebuild.
- **Never log a token, an `Authorization` header, a password or a full payload.**

## Git & domain language

Conventional Commits scoped `player`: `feat(player): court search filters`. Run `pnpm check`
before pushing. **Contract drift fails the build:** this app's CI job regenerates from
`backend/openapi.player.json` with the `openapi-typescript` its own lockfile pins, and diffs
— commit the regenerated `src/generated/`. It is **not** part of `pnpm check`, so a local
gate can be green while CI is not. The job also runs on a backend-only pull request, because
its paths filter watches that document alongside `frontend_player/**`. Before opening a
PR, walk the Definition of Done in
[`docs/architecture.md` Part 20](docs/architecture.md#part-20--definition-of-done-and-the-pr-checklist).

Player-app technical vocabulary: [`CONTEXT.md`](CONTEXT.md). New domain concepts use the
shared glossary's vocabulary ([`../CONTEXT.md`](../CONTEXT.md)) — a `Court` is a `Court`, not
a Venue or Facility.
