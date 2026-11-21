# Raketa — Player app (iOS + Android)

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
pnpm test:affected # while iterating: only the suites the branch's changes reach — never the gate
pnpm format       # Prettier --write   pnpm format:check → --check
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.json
pnpm check        # lint + format check + typecheck + test — the local gate
```

## Running on a real phone

`pnpm ios --device` and `pnpm android --device` build the development build (`Raketa local`),
install it over USB and serve it from Metro on 8081. What has stopped them:

- **A Metro already listening on 8081 is reused, however old.** `expo run:*` finds this project's
  server, prints `Skipping dev server` and starts none. One started before a `pnpm install`
  cannot resolve the new package and answers every bundle with a 500, so the phone sits on the
  splash screen (Android's logcat: `Unable to resolve module …`). Stop it —
  `lsof -ti tcp:8081 -sTCP:LISTEN | xargs kill` — and run the command again. Do the same after
  switching branches.
- **A config plugin added after `android/` or `ios/` was generated is not applied.** Its native
  code is autolinked, but what its plugin writes into the manifest or Info.plist is not. Run
  `EXPO_PUBLIC_ENV=local npx expo prebuild --platform <android|ios> --no-install`. Leave out
  `--clean`, which drops the iOS signing team.
- **Android's `--device` takes the model name** that `adb devices -l` prints (`SM_A556B`), not
  the serial. With no value it asks.
- **iOS:** a free Apple team's profile lasts 7 days, so rebuild to renew it. If the install fails
  with `InvalidHostID`, install the built `.app` with `xcrun devicectl device install app`. The
  Mac's LAN IP is baked into the build, so after the IP changes, update `.env.local` and rebuild.
  `No script URL provided` means the phone's Local Network permission for the app is off.

## Environment

Copy `.env.example` → `.env.local`. `EXPO_PUBLIC_API_URL`, `EXPO_PUBLIC_FEATURES_URL` and
`EXPO_PUBLIC_ENV` are all **required**: `src/shared/config/env.ts` validates them once at launch and the app stops on a
startup screen naming whichever is missing or malformed, rather than failing later inside a
feature. On a **physical device**, the API URL must be a LAN IP or tunnel — `localhost` on a
phone means the phone. **`EXPO_PUBLIC_FEATURES_URL`** is the feature-flag datafiles' host (#826,
ADR-0206): run `npm run serve` in the flags repo (`Raketa02/raketa-features`) and point it at
`http://localhost:3040` — on a phone, `http://<your machine's LAN IP>:3040`. It is never waited
on: with nothing served, every feature flag is at its code default, which is how the app ships
(Play titled _Groups_, no Explore). To see Explore, set the flags repo's `local` rule for `explore`
to `percentage: 100`, serve, and cold-start the app.

`EXPO_PUBLIC_ENV` is one of `local`, `development`, `staging`, `production` — the same
four names the backend uses. **Only `local` runs today**; the other three
are validated but not provisioned. The environment decides the URL scheme, and that is
validated too: the three deployed ones must be `https://` for the API URL and the features URL,
because each is reached from a phone over the internet. `local` takes either — a tunnel is how a physical device
reaches a laptop, and every tunnel hands back `https://`. A laptop URL under a deployed
name is a startup failure naming both variables. See [`../docs/environments.md`](../docs/environments.md).

The environment also decides what the app calls itself. `app.config.ts` is a **function**
of it — not a static `app.json` — and delegates the one decision to
`src/shared/config/appIdentity.ts`: outside `production` the app is named for its
environment (`Raketa local`) and wears an amber badge over every screen; `production` is
`Raketa`, unbadged. There is one installable variant — one bundle identifier, one URL
scheme — so today all four resolve to the same app pointed at the same laptop. That is
the point: the machinery is exercised in the only environment that runs, so it will not
be wrong the first time it matters.

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
