# Raketa Player App (iOS + Android)

React Native + Expo SDK 52 + TypeScript, pnpm. Real platform components — not a website in a
WebView. Feature-first Clean Architecture
([ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)), talking to FastAPI
over HTTPS, wire types generated from `backend/openapi.player.json`.

> One app of the monorepo — see the root [`CLAUDE.md`](../CLAUDE.md). Run every command from
> this directory. Never import from `../backend/`; a hook blocks writes outside this app.

Three documents settle what is not decided here. **Read the one you need before writing a
feature, not after:**

| Doc                                              | Settles                                                                                                                                                                                                                             |
| ------------------------------------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`docs/features/`](docs/features/README.md)      | **The design record per feature** — what each screen does and why, one paragraph per decision. Read the file for the feature you are changing. When a ticket changes what a feature does, **the paragraph goes there, never here.** |
| [`docs/architecture.md`](docs/architecture.md)   | Where code lives, who owns which state, how auth / errors / Query / native behave in production. Part 20 is the PR checklist.                                                                                                       |
| [`docs/design-system.md`](docs/design-system.md) | Every colour, type role, spacing step and interaction rule. **Locked.**                                                                                                                                                             |

## Commands

```bash
pnpm start        # Expo dev server (press i / a for simulator)
pnpm ios / android
pnpm lint         # ESLint — also enforces the import boundaries below
pnpm typecheck    # tsc --noEmit (strict)
pnpm test         # Jest (jest-expo)
pnpm test:boundaries   # drive ESLint at code breaking each module ban; it must go red
pnpm test:labels       # drive ESLint at an unnamed Pressable in Play; it must go red
pnpm format       # Prettier --write   pnpm format:check → --check
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.player.json
pnpm doctor       # npx expo-doctor — checks dependency/SDK agreement
pnpm check        # lint + format + typecheck + test + boundaries + labels — the local gate
```

**You cannot see the screen.** If a change is visual, say so and ask for a look rather than
asserting it renders correctly.

## Environment

- **Copy `.env.example` → `.env.local` before the first run.** `EXPO_PUBLIC_API_URL` and
  `EXPO_PUBLIC_ENV` are both required, validated once at launch by `src/shared/config/env.ts`.
  A missing or malformed value stops the app on a startup screen naming it — that is the
  guardrail working, not a bug.
- `EXPO_PUBLIC_ENV` is `local | development | staging | production`, the backend's four names,
  and **only `local` runs today.** The environment fixes the URL scheme — `https://` for the
  three deployed ones — so a laptop URL under a deployed name fails at launch naming both
  variables.
- `app.config.ts` is a function of that environment (it replaced `app.json`) and holds no
  logic: `src/shared/config/appIdentity.ts` is the table it calls. Expo evaluates it in
  **Node**, before Metro, so it registers sucrase's TS require hook first — delete that line and
  `npx expo start` fails on a missing module.
- **After changing dependencies run `npx expo install --check`** and trust Expo's resolution
  over the pins in `package.json`. `eslint-config-expo` is reached through `FlatCompat` because
  its flat config belongs to SDK 53.
- **`.npmrc` sets `node-linker=hoisted`.** Metro and jest-expo decide what to transform with
  `node_modules/(?!…)` allowlists that pnpm's symlinked layout defeats; the first casualty is
  `jest` failing to parse React Native's untranspiled Flow.
- Fonts (Archivo, IBM Plex Mono) are imported **file by file** — each `@expo-google-fonts`
  index `require`s every weight and Metro does not tree-shake, so one name costs 4,2 MB
  instead of 1,0 MB — and awaited before the splash screen hides.

## Safety — never without an explicit request

- **Ask for a background location.** Foreground only, permanently; `app.config.ts` disables it
  on both platforms and two tests assert the absence. A fix is coarsened to about a kilometre
  the moment it is read.
- **Store credentials anywhere but the OS keychain**, reached only through
  `src/shared/lib/auth`. Never `AsyncStorage`, never a module variable that outlives a session,
  never a log line. _(lint)_
- **Put a secret in `app.config.ts` `extra` or in any `EXPO_PUBLIC_*` variable.** Everything in
  the bundle is readable from a shipped app; a secret a mobile client "needs" belongs behind the
  backend.
- **Run a build or release** (`eas build|submit|update`, `expo publish`). _(hook)_
- **Create or edit a real `.env*` file.** Edit `.env.example`. _(hook)_
- **Import from `src/generated/` outside a feature's `api/` or `mappers/`** — one exemption,
  `shared/lib/platform/liveStream.ts`, the live channel's `api/` layer (ADR-0147 §7). _(lint)_
- **Hand-write a type that mirrors a backend response.** Regenerate with `pnpm gen:api`.
- **Put business rules in screens or hooks.** Rules live in `domain/` + `use-cases/`.
- **Call `fetch` outside `src/shared/lib/http`**, or add a second networking path. _(lint)_
- **Copy server data into Zustand.** TanStack Query owns every backend-derived value.
- **Retry a mutation** unless the endpoint is idempotent, takes an idempotency key, or is
  explicitly safe to repeat.
- **Trust a deep-link, push or route param.** Validate with Zod before use.
- **Write a literal colour, font size, spacing or radius in a component.** Every value comes
  from `src/shared/ui/theme.ts`. _(lint, for colour)_
- **Add a dependency that owns styling** — NativeWind, styled-components, Unistyles, Restyle, a
  component kit. The system is a typed theme + `StyleSheet.create`
  ([ADR-0012](../docs/adr/0012-player-app-design-system.md)).
- **Commit `android/` or `ios/`.** They are `expo prebuild` output; native config goes through
  `app.config.ts` and config plugins.

## Architecture

Full contract: [`docs/architecture.md`](docs/architecture.md). **Every feature carries the full
layer set** — copy [`src/features/_template/`](src/features/_template/README.md) to start one,
never `create-expo-app`.

```
src/
  app/                      expo-router screens (thin); _layout.tsx = providers + bootstrap gate
    (public)/ (auth)/ (app)/(tabs)/
  features/<feature>/
    domain/ use-cases/ api/ mappers/ schemas/ components/ hooks/ store/(optional)
    types.ts                the feature's only public surface
  shared/
    ui/                     theme.ts (THE source of every value) + primitives
    lib/  http/ auth/ query-client/ bootstrap/ platform/
    config/ errors/ store/ formatting/ date/ vocabulary/
  generated/                openapi-typescript output — raw wire types ONLY
```

- **Dependencies point inward:** `app/ → components/ → hooks/ → use-cases/ → domain/`.
  `domain/` and `use-cases/` import nothing from React, React Native, Expo, `fetch` or
  `generated/`. _(lint)_
- **The wire boundary is `api/` + `mappers/`.** A feature that keys copy by a wire code spells
  the union itself in `domain/vocabulary.ts` and holds it equal to the generated one with a
  compile-time assertion in `mappers/wireVocabulary.ts`, so a contract change fails
  `pnpm typecheck` in the one file whose job is saying so (`play`, `challenges`, `games`,
  `player_record` do this).
- **One chokepoint per capability**, each the only importer of its module: `shared/lib/auth`
  (keychain), `shared/lib/http` (`fetch`, the 401 → refresh → retry rotation, timeouts as named
  classes), and three platform ports in `shared/lib/platform/` — `location.ts`,
  `imagePicking.ts`, `liveStream.ts`. Features depend on the port and drive the fakes in
  `src/test-support/platform.ts`. _(lint)_
- **`shared/` never imports a feature; a feature never deep-imports another** — go through its
  `types.ts`. `features/plans` may import `features/games`, never the reverse. _(lint)_ But do
  not move code to `shared/` because two files use it; keep it local until cross-feature
  ownership is proven (the third caller).
- **No global `services/`, `utils/`, `types/` or `hooks/` bucket.** Utilities get semantic
  homes (`formatting/`, `date/`, `vocabulary/`).
- **Copy is code**: every sentence a screen says lives in a copy module beside it
  (`*Presentation.ts`, `shellCopy.ts`, `authErrorMessage.ts`), keyed by the wire's code as a
  `Readonly<Record<Code, string>>` so a code with no words fails to compile — never a template
  inlined in a component. That includes accessibility names.
- **Every pressable primitive in `shared/ui/` requires a name** (`accessibilityLabel` or
  `label`). The right answer to a new tappable primitive is a required prop on it, not a wider
  lint selector.
- **Uniform-strict escape hatch:** where a feature has no business rule, `use-cases/` may be
  pass-throughs and `domain/` just types. Keep the folders; do not invent invariants to fill
  them.

### One owner per kind of state

| State                     | Owner                                                                                                                            |
| ------------------------- | -------------------------------------------------------------------------------------------------------------------------------- |
| Anything from the backend | **TanStack Query** — never mirrored into a store                                                                                 |
| A live frame's roster     | React state in the hook that follows the channel — not a query, not a store: it is the frame, and it is dropped with the channel |
| Access + refresh tokens   | `shared/lib/auth` → `expo-secure-store` (+ in-memory mirror)                                                                     |
| Logged-in / out           | `SessionStatus`: `bootstrapping \| authenticated \| unauthenticated`                                                             |
| Local component state     | `useState` / `useReducer`                                                                                                        |
| Shared ephemeral UI state | Zustand, **feature-scoped first**                                                                                                |
| Form input                | The form + one Zod schema                                                                                                        |
| Navigation                | expo-router — a route param is not app state                                                                                     |
| Config                    | `shared/config/env.ts`, Zod-validated at startup                                                                                 |

Reach for Zustand last: component-local → feature store → app-wide store, and only with a
reason. Zustand never holds API entities, tokens, a backend cache, or a global loading flag.

### Session, bootstrap and routing

Bootstrap is a **state**, never `user === undefined` — that ambiguity is what flashes a login
screen while valid credentials are still being read out of the keychain. `shared/lib/bootstrap`
runs one ordered sequence (error reporting → validate config → wire focus/online managers → read
SecureStore → restore/validate session → hide splash → render) and nothing renders a route tree
before it resolves. The guard is a redirect in `(app)/_layout.tsx` keyed on `SessionStatus`;
route groups make the authorization boundary visible in the file tree. iOS Keychain data can
survive a reinstall, so **a token existing is not proof a session exists** — bootstrap validates
it.

**There is no BFF here, deliberately.** A native app has no cookie jar, so the equivalent of
httpOnly cookies is the OS keychain
([ADR-0008](../docs/adr/0008-player-mobile-securestore-direct-api.md)). Don't "fix" the
asymmetry with a proxy or a cookie session.

## Mobile gotchas that bite once

- **`localhost` on a device is the device.** A physical phone needs a LAN IP or tunnel in
  `EXPO_PUBLIC_API_URL`.
- **Old app versions live on real phones for months.** Treat backend contract changes as
  breaking unless additive.
- **`fetch` has no default timeout.** Timeouts are centralized in `shared/lib/http` as classes —
  no millisecond literal in a feature.
- **Archivo ships no ✓, ✉, ★ or ⚡.** Every mark is drawn or is Feather (`@expo/vector-icons`,
  declared in `package.json` on purpose — ADR-0135), never the character.
- **Never log a token, an `Authorization` header, a password or a full payload.**
- **A mounted Reanimated style makes every React Native `Modal` on Android unusable** (New
  Architecture + Reanimated 3.16): its content stays 0 × 0 and no press inside completes. No
  overlay uses `Modal`; it draws on `shared/ui`'s `ModalStage` — the native window on iOS, a
  layer in the tree on Android hosted by `OverlayHost` in the root layout (ADR-0178,
  `docs/architecture.md` Part 13). A sheet's content keeps the root's contexts only: no
  provider below the root, no navigation hook inside a sheet. And never scale a layer to move
  things on the UI thread — iOS rasterises it blurred; translate a point per tile, as the radar
  does.

## Git & domain language

Conventional Commits scoped `player`: `feat(player): court search filters`. Run `pnpm check`
before pushing. **Contract drift fails the build and is not part of `pnpm check`:** CI
regenerates `src/generated/` from `backend/openapi.player.json` and diffs, so commit the
regenerated output — a local gate can be green while CI is not. Before opening a PR, walk the
Definition of Done in
[`docs/architecture.md` Part 20](docs/architecture.md#part-20--definition-of-done-and-the-pr-checklist).

Player-app technical vocabulary: [`CONTEXT.md`](CONTEXT.md). New domain concepts use the shared
glossary ([`../CONTEXT.md`](../CONTEXT.md)) — a `Court` is a `Court`, not a Venue or Facility.
