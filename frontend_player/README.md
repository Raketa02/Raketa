# Rakieta — Player app (iOS + Android)

The native app players use to find courts, book slots and organise matches.
React Native + Expo + TypeScript, rendering with real platform components — not a
website in a WebView.

One of three independently deployable apps in this monorepo — see the root
[`CONTEXT-MAP.md`](../CONTEXT-MAP.md).

## First run

```bash
cd frontend_player
pnpm install
cp .env.example .env.local   # both values are required — see Environment below
npx expo-doctor              # verifies the dependency versions agree with the SDK
pnpm start                   # then press i (iOS sim) / a (Android emulator)
```

The app boots to a placeholder screen. `src/app/_layout.tsx` composes the root providers
and gates the splash screen on the **bootstrap sequence** — the ordered startup path in
[`docs/architecture.md` Part 3](docs/architecture.md#part-3--bootstrap-and-the-session-state-machine),
implemented in `src/shared/lib/bootstrap/`. It validates config, then loads Archivo and
IBM Plex Mono with `expo-font` and awaits them before the splash hides. Routing, sessions
and features arrive in later slices; build them outward from the folder contract in
[`src/features/_template/README.md`](src/features/_template/README.md). The design system
is already locked — see below.

`.npmrc` pins pnpm to `node-linker=hoisted`, because Metro and jest-expo resolve what to
transform through `node_modules/(?!…)` allowlists that pnpm's symlinked layout defeats.

> Deliberately **not** scaffolded with `create-expo-app`: its default template
> contradicts the feature-first structure recorded in
> [ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md).
>
> The dependency versions in `package.json` target **Expo SDK 52**. Expo pins RN and
> its own packages tightly, so run `npx expo install --check` after the first install
> and let Expo correct anything that drifted — trust its resolution over the pins here.

## Commands

```bash
pnpm start        # Expo dev server
pnpm ios          # build & run on the iOS simulator
pnpm android      # build & run on an Android emulator
pnpm lint         # ESLint (also enforces the import boundaries)
pnpm typecheck    # tsc --noEmit, strict
pnpm test         # Jest (jest-expo)
pnpm format       # Prettier --write   pnpm format:check → --check
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.json
pnpm check        # lint + format check + typecheck + test — the local gate
```

## Environment

Copy `.env.example` → `.env.local`. `EXPO_PUBLIC_API_URL` and `EXPO_PUBLIC_ENV` are both
**required**: `src/shared/config/env.ts` validates them once at launch and the app stops
on a startup screen naming whichever is missing or malformed, rather than failing later
inside a feature. On a **physical device**, `EXPO_PUBLIC_API_URL` must be a LAN IP or
tunnel — `localhost` on a phone means the phone.

Every `EXPO_PUBLIC_*` value ships inside the bundle and is readable from a released
app. Config only, never secrets.

## Architecture in one paragraph

Screens live in `src/app/` (expo-router, file-based, route groups `(public)` `(auth)`
`(app)`). Each user-facing capability is a vertical slice in `src/features/<name>/` with
the full layer set (`domain/ use-cases/ api/ mappers/ schemas/ components/ hooks/`),
dependencies pointing inward. Cross-cutting infrastructure — the HTTP client, auth, the
Query client, bootstrap, platform adapters, observability — lives in `src/shared/lib/`.
The `api/` layer calls FastAPI **directly** — there is no BFF, because a native app has
no cookie jar; tokens live in the OS keychain via `expo-secure-store`, reached only
through `src/shared/lib/auth`. TanStack Query owns every backend-derived value; Zustand
owns UI state only.

The full contract — state ownership, the session state machine, single-flight token
refresh, the error taxonomy, Query defaults, native and delivery policy — is
[`docs/architecture.md`](docs/architecture.md), recorded as
[ADR-0013](../docs/adr/0013-player-app-runtime-architecture.md). **Read it before writing
a feature.**

## Design system

The visual language was designed and audited before the app existed, and is **locked**:

- [`docs/design-system.md`](docs/design-system.md) — the rules. **Start at Part 0**, which
  separates the prototype's harness from the product and tabulates every web→native
  translation.
- [`src/shared/ui/theme.ts`](src/shared/ui/theme.ts) — every colour, type role, spacing
  step, radius, metric, shadow and duration. **A literal in a component is a bug.**
- [`docs/design-system-v34-prototype-audit.md`](docs/design-system-v34-prototype-audit.md)
  — the archived measurement of the v34 web prototype. Descriptive, superseded by the rules.

The prototype's phone frame, dark stage, scenario rail and time bar are **harness and do
not ship** — the app _is_ the phone. Styling is a typed theme plus `StyleSheet.create`; no
NativeWind, no styling library — [ADR-0012](../docs/adr/0012-player-app-design-system.md).

Full rules: [`CLAUDE.md`](CLAUDE.md). Vocabulary: [`CONTEXT.md`](CONTEXT.md).
