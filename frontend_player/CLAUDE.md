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
the first session here, read [`README.md`](README.md) for the first-run steps, and
build outward from the structure rather than reaching for `create-expo-app` (its default
template contradicts
[ADR-0009](../docs/adr/0009-feature-first-clean-architecture-frontends.md)).

**Dependency versions target Expo SDK 52.** Expo pins React Native and its own packages
tightly, so after the first install run `npx expo install --check` and trust Expo's
resolution over the pins in `package.json`.

Two contracts predate the code and are **already settled** — read them before writing a
feature, not after:

| Doc | Settles |
| --- | --- |
| [`docs/architecture.md`](docs/architecture.md) | Where code lives, who owns which state, how auth/errors/Query/native behave in production. |
| [`docs/design-system.md`](docs/design-system.md) | Every colour, type role, spacing step and interaction rule. |

The first `src/app/_layout.tsx` must load Archivo (400–800) and IBM Plex Mono
(400–600) with `expo-font` and **await them before hiding the splash screen** — a font that
arrives late reflows every number on screen. See [Design system](#design-system).

## Default workflow

For non-trivial changes:
0. **If the change renders anything at all**, read
   [`docs/design-system.md` Appendix B](docs/design-system.md#appendix-b--quick-reference-card)
   before you write a component. It is ~20 lines and it is not optional. The visual
   language is locked and predates the app — see [Design system](#design-system).
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
- **Call `fetch` outside `src/shared/lib/http`,** or add a second networking path.
- **Copy server data into Zustand.** TanStack Query owns every backend-derived value.
- **Retry a mutation** unless the endpoint is idempotent, takes an idempotency key, or is
  explicitly safe to repeat. Booking and payment calls are exactly where a silent retry
  charges someone twice.
- **Trust a deep-link, push or route param.** Validate with Zod before use.
- **Write a literal colour, font size, spacing or radius in a component.** Every value
  comes from `src/shared/ui/theme.ts`. See [Design system](#design-system).
- **Add a dependency that owns styling** — NativeWind, styled-components, Unistyles,
  Restyle, a component kit. The system is a typed theme + `StyleSheet.create`
  ([ADR-0012](../docs/adr/0012-player-app-design-system.md)).
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

Full contract: [`docs/architecture.md`](docs/architecture.md). The load-bearing parts,
for a session that will not read it:

Source lives under `src/`. **Every feature carries the full layer set** — the same
discipline the backend and the club app use:

```
src/
  app/                      expo-router screens (thin). File-based routing.
    _layout.tsx             root providers + the bootstrap gate
    (public)/               reachable without a session
    (auth)/                 sign-in, sign-up, recovery
    (app)/                  authenticated tree — _layout.tsx holds the redirect guard
      (tabs)/
  features/<feature>/
    domain/                 entities + value objects + rules (pure TS, no RN/fetch)
    use-cases/              one fn per workflow; orchestrates domain + ports
    api/                    calls FastAPI directly; speaks wire types
    mappers/                wire DTO  <->  domain object
    schemas/                Zod schemas (form/input/deep-link validation)
    components/             rendering + interaction only
    hooks/                  thin adapters over use-cases; TanStack Query + key factory
    store/                  OPTIONAL — a small feature-scoped Zustand store
    types.ts                the feature's public surface
  shared/
    ui/                     theme.ts (THE source of every value) + primitives + states
    lib/
      http/                 the ONLY place fetch is configured
      auth/                 the ONLY expo-secure-store consumer
                            tokenManager · refreshCoordinator · authService · authSession
      query-client/         the QueryClient + deliberate defaults
      bootstrap/            the ordered startup sequence
      platform/             appState · networkState · permissions · native adapters
      observability/        logger (redacting) · analytics · telemetry
    config/                 env.ts (Zod-validated, read from expo-constants)
    errors/                 AppError family + backend-code → error mapping
    store/                  Zustand — app-wide UI state only, and only with a reason
  generated/                openapi-typescript output — raw wire types ONLY
```

The per-layer contract is in
[`src/features/_template/README.md`](src/features/_template/README.md). Copy that folder
to start a feature.

Rules to preserve:
- **Dependencies point inward:** `app/ → components/ → hooks/ → use-cases/ → domain/`.
  `domain/` imports nothing from React Native, Expo, `fetch`, or `generated/`.
- **The wire boundary is `api/` + `mappers/`.** ESLint enforces it.
- **`src/shared/lib/auth` is the single chokepoint for credentials.** No feature, screen
  or hook imports `expo-secure-store`. One module owning the keychain is what makes
  token lifetime auditable.
- **`src/shared/lib/http` is the only place `fetch` is configured** — and the only place
  the 401 → refresh → retry rotation lives, so a burst of 401s cannot fan out into N
  concurrent refresh calls racing each other.
- **`shared/` never imports a feature,** and a feature never deep-imports another
  feature — go through its `types.ts`, or move the concept to `shared/`. But **do not
  move code to `shared/` because two files use it**; keep it local until cross-feature
  ownership is proven.
- **No global `services/`, `utils/`, `types/` or `hooks/` bucket.** A capability is one
  directory. Utilities get semantic homes (`formatting/`, `date/`, `currency/`).

### One owner per kind of state

| State | Owner |
| --- | --- |
| Anything from the backend | **TanStack Query** — never mirrored into a store |
| Access + refresh tokens | `shared/lib/auth` → `expo-secure-store` (+ in-memory mirror) |
| Logged-in / out | `SessionStatus`: `bootstrapping \| authenticated \| unauthenticated` |
| Local component state | `useState` / `useReducer` |
| Shared ephemeral UI state | Zustand, **feature-scoped first** |
| Form input | The form + one Zod schema |
| Navigation | expo-router — a route param is not app state |
| Config | `shared/config/env.ts`, Zod-validated at startup |

Reach for Zustand last: component-local → feature store → app-wide store, and only with
a reason. Zustand never holds API entities, tokens, a backend cache, or a global loading
flag, and its actions do not perform network orchestration.

### Session, bootstrap and routing

Model bootstrap as a **state**, never as `user === undefined` — that ambiguity is what
produces a login-screen flash while valid credentials are still being read out of the
keychain, and an authenticated-tree flash before a redirect.

`shared/lib/bootstrap` runs one ordered sequence — error reporting → validate config →
wire focus/online managers → read SecureStore → restore/validate session → hide splash →
render a tree. Nothing renders a route tree before it resolves.

Expo Router's declarative protected routes landed **after SDK 52**, so the guard is a
redirect in `(app)/_layout.tsx` keyed on `SessionStatus`. Route groups exist so the
authorization boundary is visible in the file tree.

### Auth, in four rules that are easy to get wrong

1. **Single-flight refresh.** One `refreshPromise`; every concurrent 401 awaits the same
   one. Ten parallel refreshes rotate each other out and log the user out at random.
2. **Retry an authenticated request exactly once.** The retry carries a flag saying
   refresh was attempted; a second 401 terminates the session instead of looping forever.
3. **Rejected ≠ unreachable.** A refresh the auth server *rejects* clears credentials and
   caches. A refresh that *times out* preserves them — losing signal in a lift is not a
   logout.
4. **Logout is a system operation.** Revoke → clear memory → delete keychain → cancel
   in-flight requests → `queryClient.cancelQueries()` + `clear()` → reset sensitive UI
   state → set unauthenticated → navigate. Skipping the cache clear leaks user A's data
   to user B on the same device.

Also: iOS Keychain data can survive a reinstall, so *a token existing is not proof a
session exists* — bootstrap validates it.

### Errors

Raw `fetch` failures and backend JSON never reach a screen. `shared/errors` normalizes
into one `AppError` family, and **decisions branch on the backend's stable `code`, never
on `message`** — the message is copy and will change. Every mapped error gets a recovery
category (auto-retry · user-retry · re-auth · user correction · conflict · terminal), and
the envelope's `trace_id` goes into the error report so a mobile failure can be tied to a
server log without logging a payload.

**Not every 4xx is a logout** — only authentication-invalidating responses touch the
session. A 403 means "not allowed", not "sign in again".

### TanStack Query

- **A query-key factory per feature** in `hooks/` — no inline string keys. Every
  parameter that changes the response is in the key, including the cursor.
- **Semantic hooks** (`useMatch(id)`), not query options assembled per screen.
- **Choose the defaults** — stale time, gc, retry predicate, `networkMode`, refetch on
  focus — per data class. Live slot availability and reference data are not the same.
- **Wire `focusManager` to `AppState` and `onlineManager` to native connectivity.**
  Query's browser assumptions are wrong here; without this, nothing refreshes on
  foreground and paused mutations never resume.
- **Mutations declare their cache effect:** prefer writing the canonical response with
  `setQueryData`, then invalidate the broader lists. Optimistic updates only when
  rollback is deterministic and rejection is rare — booking a slot is not that case.
- **Cancellation:** pass Query's `signal` through to `fetch`. No fire-and-forget request
  in a component.

### Product surface

Every server-driven screen models **initial loading · loaded · empty · refreshing ·
recoverable error · terminal error · offline** — `if (isLoading) <Spinner/>` is not
acceptable for a real flow. Distinguish initial load from pull-to-refresh from background
refresh from a button mutation; one global spinner makes the app feel broken.

Critical mutations decide their duplicate-submit behaviour. A disabled button is UX;
**backend idempotency is the correctness mechanism.**

Never branch on a user-visible string (`status === MatchStatus.Cancelled`, not
`'Cancelled'`). Distinguish a timestamp from a local calendar date, and never make a
business decision from the device clock or a formatted string.

### Why there is no BFF here

The club app routes everything through a server-side BFF with httpOnly cookies. This app
does not, and that is deliberate: a native app has no cookie jar and no shared-origin
browser context, so the equivalent protection is the **OS keychain**
([ADR-0008](../docs/adr/0008-player-mobile-securestore-direct-api.md)). Don't "fix" the
asymmetry by adding a proxy, and don't copy the club app's cookie code here.

**Uniform-strict escape hatch:** when a feature genuinely has no business rule, its
`use-cases/` may be thin pass-throughs and `domain/` may be just types. Keep the folders
for predictability, but **do not invent fake invariants to fill them**.

## Design system

**Locked.** The player app's visual language was designed and audited before the app
existed. Full rules: [`docs/design-system.md`](docs/design-system.md). The decision and
its corrections: [ADR-0012](../docs/adr/0012-player-app-design-system.md).

Three artefacts that **change together, in the same commit**:

| File | Is |
| --- | --- |
| [`src/shared/ui/theme.ts`](src/shared/ui/theme.ts) | The source of every value. Read via `StyleSheet.create`. |
| [`docs/design-system.md`](docs/design-system.md) | The rules. 1145 lines — see the reading order below. |
| [`docs/design-system-v34-prototype-audit.md`](docs/design-system-v34-prototype-audit.md) | Archived measurement of the web prototype. Not the rules. |

### What to read, and when

The rules document is long; **you are not expected to read it end to end,** and "it was
long" is not a reason to skip it. Read in this order:

| When | Read |
| --- | --- |
| **Every time you touch a rendered surface** | [Appendix B — quick reference card](docs/design-system.md#appendix-b--quick-reference-card). ~20 lines. The floor. |
| **Once, before your first component** | [Part 0](docs/design-system.md#part-0--reading-a-web-prototype-as-a-native-app) (harness vs product, web→native translation) and [`src/shared/ui/README.md`](src/shared/ui/README.md) (how to consume the theme). |
| **Building a specific surface** | Part 5 primitives · 6 controls · 7 data display · 9 overlays · 12 screens. |
| **A value you need does not exist** | [Part 15 — extension guide](docs/design-system.md#part-15--extension-guide). Extend deliberately; never invent beside the system. |

ESLint rejects hex and `rgb()`/`rgba()` literals and the `fontWeight` property outright,
so a component that ignores the theme fails `pnpm lint` rather than review.

### The prototype is a web page. This app is not.

The audit describes an HTML file, and **its phone frame, dark stage, scenario rail, time
bar and 900px breakpoint are harness — they do not ship.** The app *is* the phone. Never
build a frame, a stage or a scenario switcher, and never use the four stage colours
(`#08222B` `#071C24` `#0B2B36` `#24505E`) — they are not in the theme.

### The four React Native traps

1. **`fontWeight` is ignored on Android** with a custom `fontFamily`. Weight is a family
   name: `theme.font.sans[700]`, never `fontWeight: '700'`.
2. **`letterSpacing` and `lineHeight` are points**, not em and multiples. `theme.type` and
   `theme.num` carry pre-converted values — never re-derive from the audit's em figures.
3. **44 × 44pt minimum reachable area** on everything tappable. Keep the visual small, grow
   the target with `theme.hit.*`.
4. **There is no hover.** Every pressable declares its pressed appearance explicitly.

### The rules an agent gets wrong

- **`line` bounds a thing; `line2` is a fold inside one thing.**
- **9 between stacked cards · 15 at the gutter.** Everything else from the 3pt grid.
- **Content width is screen width − 30**, and the rail card is `0.74 × content width` —
  never a fixed 362 or 268. Those are the prototype's phone picture.
- **Colour is picked by meaning:** coral = the one accent · mint = settled · amber =
  reversible, not yet wrong · red = ended badly · info = explanation, not status.
- **Rule C — white text never sits on `coral` or `mint`** (3.89:1 and 4.07:1). Use
  `coralInk` / `mintInk`. `ink` is the only dark that may sit on coral (4.50:1).
- **`volt` on dark surfaces only.** On paper it is ~1.3:1.
- **Every number is mono and tabular** — that is what stops a row reflowing when a level
  goes from 2,71 to 2,80. Polish formatting: `38,00 zł`, `2,71`, `65%`, `18:30`.
- **Cards never cast a shadow.** Three shadows exist; all are for things that float.
- **Band `ink` for text and rails**, `tint`/`deep` for the bar only. And a printed level
  range always comes from the model's `bandLo`/`bandHi`, never the bar's drawing values.
- **Every state carries a word or a shape**, never colour alone.
- **`eyebrow` labels a region you are reading; `flab` labels a control you are about to
  operate.** They are not interchangeable.

The design system covers `frontend_player/` **only**. The club app has its own; the
palettes converge because it is one brand, but the values are never shared.

## Testing (TDD — test first)

Write the failing test first, make it pass, refactor. Pyramid: many pure unit tests →
component tests → integration → a few E2E journeys.

- **Jest (`jest-expo`) + Testing Library React Native.** `domain/`, `use-cases/`,
  `mappers/`, schemas, formatters, key factories and the refresh coordinator are pure —
  test those first and hardest, with no renderer.
- Colocate as `*.test.ts(x)` next to the file under test — **except router tests, which
  live outside `src/app/`.** Cover redirects, the authenticated boundary, deep-link
  routes and params.
- Component tests assert what the user can observe, never internal state.
- Mock ports with hand-written stubs, not deep module mocks.
- **Auth concurrency is mandatory, not optional.** Ordinary login tests miss all four:
  many simultaneous 401s → exactly one refresh; refresh rejected → one logout, tokens and
  cache cleared; refresh times out → session survives; retried request 401s again → no
  infinite loop.
- Query integration: correct key, correct `enabled`, cache update and invalidation after
  a mutation, cache cleanup on logout.
- Snapshots are a narrow tool — large ones get updated without being read.

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
  breaking unless they are additive — you cannot force everyone to update. A released
  build is immutable from the backend's point of view.
- **Offline and flaky networks are the normal case,** not an edge case. Prefer TanStack
  Query's cache/retry behavior over hand-rolled loading flags. That is *not* a licence to
  call this app offline-first — it is network-backed with an in-memory cache and graceful
  offline UX, and stays that way until a persistent local layer is decided deliberately.
- **`fetch` has no default timeout.** Timeouts are centralized in `shared/lib/http` as
  classes (request/upload/download/background) — no millisecond literal in a feature.
- **Keep the JS thread free.** No big synchronous parses, heavy array work in render, or
  synchronous secure-storage calls. Profile before optimizing — `memo` everywhere is
  complexity without evidence. Virtualize long lists; don't fetch full-resolution images
  for a card.
- **New Architecture stays on.** A dependency that blocks it is technical debt with a
  migration plan, not an exemption. Check any new native dependency for SDK 52 + New
  Architecture compatibility, and run `pnpm doctor`.
- **`android/` and `ios/` are `expo prebuild` output.** Native config goes through
  `app.json` and config plugins; a hand edit is lost on the next prebuild.
- **Concentrate platform differences behind adapters** (`share.ios.ts` / `share.android.ts`
  in `shared/lib/platform`), not `if (Platform.OS === 'ios')` scattered through features.
- **OTA respects native compatibility.** JS-only change → EAS Update; a native dependency
  or config change → a new build. Never ship JS expecting native code the installed
  binary lacks.
- **Never log a token, an `Authorization` header, a password or a full payload.** The
  logger redacts structurally; production logging is stricter than development.

## Git & PRs

- Conventional Commits scoped `player`: e.g. `feat(player): court search filters`.
- CI runs `lint`, `typecheck` and `test` for `frontend_player/` when
  `frontend_player/**` changed; all must pass. Run `pnpm check` before pushing.
- **Contract drift fails the build:** CI regenerates from `backend/openapi.json` and
  diffs. Commit the regenerated `src/generated/`.
- Before opening a PR, walk the Definition of Done in
  [`docs/architecture.md` Part 20](docs/architecture.md#part-20--definition-of-done-and-the-pr-checklist).

## Domain language

Shared domain terms: [`../CONTEXT.md`](../CONTEXT.md). Player-app-only technical
vocabulary: [`CONTEXT.md`](CONTEXT.md). Never redefine a domain term locally.
