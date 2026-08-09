# Rakieta — Player app (iOS + Android)

The native app players use to find courts, book slots and organise matches.
React Native + Expo + TypeScript, rendering with real platform components — not a
website in a WebView.

One of three independently deployable apps in this monorepo — see the root
[`CONTEXT-MAP.md`](../CONTEXT-MAP.md).

## Bootstrap (first time)

Nothing is installed yet: this directory holds the architecture, config and rules, not
a generated app. To bring it to life:

```bash
cd frontend_player
pnpm install
npx expo-doctor          # verifies the dependency versions agree with the SDK
pnpm start               # then press i (iOS sim) / a (Android emulator)
```

Then create the expo-router entry points — `src/app/_layout.tsx` and
`src/app/index.tsx` — and build outward. The folder contract is in
[`src/features/_template/README.md`](src/features/_template/README.md).

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
pnpm gen:api      # regenerate src/generated/ from ../backend/openapi.json
pnpm check        # lint + typecheck + test — the local gate
```

## Environment

Copy `.env.example` → `.env.local`. On a **physical device**, `EXPO_PUBLIC_API_URL`
must be a LAN IP or tunnel — `localhost` on a phone means the phone.

Every `EXPO_PUBLIC_*` value ships inside the bundle and is readable from a released
app. Config only, never secrets.

## Architecture in one paragraph

Screens live in `src/app/` (expo-router, file-based). Each user-facing capability is a
vertical slice in `src/features/<name>/` with the full layer set
(`domain/ use-cases/ api/ mappers/ schemas/ components/ hooks/`), dependencies pointing
inward. The `api/` layer calls FastAPI **directly** — there is no BFF, because a native
app has no cookie jar; tokens live in the OS keychain via `expo-secure-store`, reached
only through `src/shared/lib/auth`.

Full rules: [`CLAUDE.md`](CLAUDE.md). Vocabulary: [`CONTEXT.md`](CONTEXT.md).
