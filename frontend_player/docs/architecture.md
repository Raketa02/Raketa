# Raketa Player App — Production Architecture

**Status: adopted.** This is the player app's runtime and engineering contract, the
counterpart to the [design system](design-system.md). The design system says what a
screen looks like; this says where its code lives, who owns its state, and how it fails
in production.

- **Origin:** distilled from
  [`docs/specs/player-app/react_native_expo_production_architecture.md`](../../docs/specs/player-app/react_native_expo_production_architecture.md)
  (147 sections), adapted to the structure this repo already committed to in
  [ADR-0009](../../docs/adr/0009-feature-first-clean-architecture-frontends.md) and
  [ADR-0008](../../docs/adr/0008-player-mobile-securestore-direct-api.md). The runtime
  decisions it introduces are recorded in
  [ADR-0013](../../docs/adr/0013-player-app-runtime-architecture.md).
- **Scope: `frontend_player/` only.** A web client would share the _shape_ of Parts 1, 6, 7
  and 9 but not this document, and never this code
  ([ADR-0005](../../docs/adr/0005-three-app-monorepo-ownership-boundaries.md)).
- **The rule that generates the rest:** every piece of data and every kind of logic has
  **one obvious owner**. If you cannot answer "who owns this?" in one sentence, the code
  is in the wrong place.

The objective is not the maximum number of layers. It is **clear ownership, stable
dependency direction, predictable data flow, and cheap change**.

---

## Part 0 — Reading the source document against this repo

The source document proposes a directory layout. This repo had already chosen a
compatible but differently-named one, and that choice is locked by an accepted ADR shared
with other clients. **This repo's names win.** Translate as follows:

| Source document                      | Here                                  | Why the difference                                                                                                         |
| ------------------------------------ | ------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `app/` at the project root           | `src/app/`                            | expo-router is configured for `src/app`; everything the app owns sits under `src/`.                                        |
| `src/core/api/httpClient.ts`         | `src/shared/lib/http/`                | This repo groups cross-cutting infrastructure under `shared/lib/` rather than a second top-level `core/`.                  |
| `src/core/auth/*`                    | `src/shared/lib/auth/`                | Same. The internal split — token manager, refresh coordinator, session, service — is adopted verbatim.                     |
| `src/core/query/*`                   | `src/shared/lib/query-client/`        | Same.                                                                                                                      |
| `src/core/storage/*`                 | `src/shared/lib/auth/` (secure)       | The only secure-store consumer is auth. A general storage module arrives only when a non-credential persistence need does. |
| `src/core/config/env.ts`             | `src/shared/config/env.ts`            | Already exists as a directory.                                                                                             |
| `src/core/errors/*`                  | `src/shared/errors/`                  | Already exists as a directory.                                                                                             |
| `src/core/observability/*`           | `src/shared/lib/observability/`       | New; see [Part 15](#part-15--observability).                                                                               |
| `src/core/platform/*`                | `src/shared/lib/platform/`            | New; see [Part 13](#part-13--native-and-platform).                                                                         |
| `src/core/bootstrap/bootstrapApp.ts` | `src/shared/lib/bootstrap/`           | New; see [Part 3](#part-3--bootstrap-and-the-session-state-machine).                                                       |
| feature `ui/`                        | feature `components/`                 | ADR-0009. `ui` at this repo means the design system (`src/shared/ui/`).                                                    |
| feature `store/`                     | feature `store/` — **optional layer** | Adopted. See [Part 8](#part-8--zustand).                                                                                   |
| —                                    | feature `use-cases/`, `mappers/`      | ADR-0009 adds these two; the source document folds them into hooks and api. Keep them.                                     |
| `src/generated/api/openapi.d.ts`     | `src/generated/schema.d.ts`           | Existing `pnpm gen:api` output path.                                                                                       |
| `__tests__/` at the root             | colocated `*.test.ts(x)`              | Existing convention — **except router tests**, which must live outside `src/app/`. See [Part 16](#part-16--testing).       |

Everything else in the source document is adopted as written.

---

## Part 1 — The dependency graph

```
              src/app/            expo-router. Route adapters only.
                  │
                  ▼
        features/<f>/components/   rendering + interaction
                  │
                  ▼
        features/<f>/hooks/        TanStack Query, orchestration    ──┐
                  │                                                  │
                  ▼                                                  ▼
        features/<f>/use-cases/                          features/<f>/store/
                  │                                      Zustand — UI state only
                  ▼
        features/<f>/domain/       pure rules. No RN, no Expo, no fetch.
                  │
                  ▼
        features/<f>/api/  +  mappers/     THE wire boundary
                  │
                  ▼
        src/shared/lib/http · auth · errors · observability
                  │
                  ▼
        src/generated/schema.d.ts          generated from backend/openapi.json
                  │
                  ▼
                FastAPI
```

`src/shared/ui/` and `src/shared/lib/platform/` are consumed **horizontally** by any
layer allowed to render or touch the platform. They must never reverse the arrow:
nothing in `shared/` may import a feature.

### The non-negotiables

1. **Dependencies point inward.** `app/ → components/ → hooks/ → use-cases/ → domain/`.
2. **Feature ownership beats technical buckets.** There is no global `services/`,
   `hooks/`, `types/`, `store/` or `utils/`. A capability is one directory.
3. **A feature never deep-imports another feature.** Cross-feature access goes through
   the target's `types.ts` public surface, or the concept moves to `shared/`.
4. **Do not move code to `shared/` because two files use it.** Shared code couples every
   future feature to itself. _Keep code local until its cross-feature ownership is
   proven._
5. **Abstraction stays proportional.** No `UseCase` + `Repository` + interface + mapper +
   DTO for a trivial GET. ADR-0009's escape hatch stands: where a feature genuinely has no
   business rule, `use-cases/` may be pass-throughs and `domain/` may be types. **Do not
   invent fake invariants to fill a folder.**
6. **Circular dependencies are defects,** not a style preference. They mean unclear
   ownership.

### One source of truth per kind of state

| State                         | Owner                                                                                  |
| ----------------------------- | -------------------------------------------------------------------------------------- |
| Remote/backend data           | **TanStack Query**                                                                     |
| Access + refresh tokens       | `src/shared/lib/auth` → `expo-secure-store`                                            |
| Logged-in / logged-out status | The session state machine ([Part 3](#part-3--bootstrap-and-the-session-state-machine)) |
| Local component UI state      | `useState` / `useReducer`                                                              |
| Shared ephemeral UI state     | Zustand, feature-scoped                                                                |
| Form input                    | The form layer + a Zod schema                                                          |
| Navigation state              | expo-router                                                                            |
| Build/environment config      | `src/shared/config/env.ts`                                                             |
| A choice the phone remembers  | `src/shared/lib/preferences` → AsyncStorage, per account, wiped at sign-out (ADR-0188) |

Never represent the same state in two of these at once. In particular: **never copy
Query data into Zustand**, **never put a token in Zustand**, and **never use a navigation
param as application state**.

---

## Part 2 — Routing

`src/app/` is a **routing and composition layer**. A route file that grew a fetch, a
mutation, a domain calculation or 200 lines of JSX has stopped being a route file.

```
src/app/
├── _layout.tsx            root providers + bootstrap gate
├── (public)/              reachable without a session
├── (auth)/                sign-in, sign-up, recovery
├── (administrator)/       the administrator area: one club's Groups · You, its own stack and bar
└── (app)/                 authenticated tree
    ├── _layout.tsx        the redirect guard
    └── (tabs)/            the shell: one Stack; Home · Play · You, five tabs with Classic play
        ├── _layout.tsx    TabShell — the navigator and the bar, mounted once
        ├── index.tsx      Home, and the app's landing
        ├── around.tsx  chats.tsx  you.tsx
        └── play/          the one tab with depth
```

Route groups exist so the **authorization boundary is visible in the file tree**.

### The shell is a `Stack`, and never `<Tabs>`

Four of the five tabs are single-screen roots and only Play has depth, which is thrown away
every time a player leaves it. `<Tabs>` keeps a history per tab and restores it on return —
so built out of the box, a player who leaves the deck and comes back lands on the deck, and
the rule fails with **no symptom at all**. Switching tabs **replaces**; entering Play lays
down `[Home, Play's root]`; and both go through one function, `resetShellStack`, which is also
where a Play session ends
([#227](https://github.com/Raketa02/Raketa/issues/227),
[#261](https://github.com/Raketa02/Raketa/issues/261)).

A route file may own: the route declaration, its params, a layout, a redirect, navigation
options, route-scoped provider composition, and a very small adapter. That is the entire
list.

```tsx
// src/app/(app)/matches/[id].tsx
import { MatchDetailsScreen } from '@/features/matches/types';

export default function MatchDetailsRoute() {
  return <MatchDetailsScreen />;
}
```

### The SDK 52 guard

Expo Router's declarative protected routes landed **after** SDK 52. Until this app moves
past 52, route protection is a **redirect in `(app)/_layout.tsx`**, keyed on the session
status — never on `user === undefined`, which conflates "still loading" with "logged
out" and produces a login-screen flash.

### Deep links are untrusted input

Every param arriving from a deep link, push notification, universal link, Android App
Link, QR code or external URL is attacker-controlled. **Validate it with Zod in the
feature's `schemas/` before use**, and never let it short-circuit the guard:

```
Is the session authorized?  →  Is this route allowed?  →  Are the params valid?  →  load
```

**Before any of that, an address from outside is read, and only three are links**
([#520](https://github.com/Raketa02/Raketa/issues/520)). expo-router hands every address the
operating system opens the app with to `src/app/+native-intent.ts` before it routes one, and the
links feature answers: `join/<code>`, `invite/<token>` and `reset/<token>` — by the app's scheme, or
the web domain once one is set — are read value by value and **held** until a place that can answer
them is reached (and so is the bare `raketa://`, the existing-account invitation email's button);
**anything else is ignored**, so no screen in the app is reachable from outside by its path. A held link never short-circuits the guard: it waits through sign-in and onboarding, and is
answered by the authenticated tree once the account is in it. The rules are
[`features/links.md`](features/links.md).

---

## Part 3 — Bootstrap and the session state machine

```ts
type SessionStatus = 'bootstrapping' | 'authenticated' | 'unauthenticated';
```

Three states, explicitly. Scattered `isLoading` booleans cannot express
"bootstrapping" and so produce the two bugs every mobile app ships once: the
authenticated tree flashing before a redirect, and the login screen flashing while valid
credentials are still being read out of the keychain.

`src/shared/lib/bootstrap/` runs one ordered sequence:

```
native process starts
   → initialise crash/error reporting          (so a bootstrap crash is visible)
   → read + Zod-validate public runtime config (fail fast on bad config)
   → wire focusManager / onlineManager to native state
   → read credentials from SecureStore
   → restore + validate/refresh the session
   → initialise authenticated app state
   → hide the splash screen
   → render the authenticated or unauthenticated tree
```

The splash screen is the gate. Nothing renders a route tree before the sequence resolves.

Fonts belong in this sequence too: Archivo (400–800) and IBM Plex Mono (400–600) are
loaded with `expo-font` and **awaited before the splash hides** — a late font reflows
every number on screen.

### Root provider composition

```tsx
<ErrorBoundary>
  <ObservabilityProvider>
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <AppLifecycleProvider>
          <ThemeProvider>
            <Slot />
          </ThemeProvider>
        </AppLifecycleProvider>
      </QueryClientProvider>
    </AuthProvider>
  </ObservabilityProvider>
</ErrorBoundary>
```

The order is load-bearing: reporting wraps everything so it can see failures; auth sits
above Query so a session change can reach the cache. **Do not add a global provider per
feature** — that is a hidden dependency and a root rerender. Feature dependencies are
plain modules, hooks, or route-scoped providers.

One view sits outside this order and is not a provider: `GestureHandlerRootView`, the
outermost element of the root layout since
[ADR-0176](../../docs/adr/0176-the-radar-moves-on-the-ui-thread-and-draws-one-card.md).
It is `react-native-gesture-handler`'s root — the touch system every `GestureDetector` in
the tree delivers through, and on Android one that is missing is one that silently never
fires — added for the radar's field, which is the one surface on the library; the swipe
row, the deck's drag and the radius slider stay on React Native's own responder.

---

## Part 4 — The HTTP client

`src/shared/lib/http` is the **single network entry point**. Exactly one place configures
`fetch`. It owns transport, not product:

- base URL · headers · `Authorization` · client capability headers
  ([Part 17](#part-17--delivery-and-backward-compatibility))
- correlation ID per request
- `AbortSignal` propagation
- response decoding
- normalized errors ([Part 6](#part-6--the-error-model))
- the refresh integration ([Part 5](#part-5--authentication))
- timeout policy
- observability hooks

It must not know what an Assessment, a Skill rating or a Sport is.

Feature `api/` modules are thin and named for operations:

```ts
export const matchesApi = { getMatch, listMatches, joinMatch, leaveMatch };
```

`openapi-typescript` gives compile-time types only. Either pair it with `openapi-fetch`
(its official companion, which types paths and methods against the same schema) or keep a
**very thin** typed wrapper over `fetch`. **Do not build a networking framework.**

### Cancellation

TanStack Query passes an `AbortSignal`; the HTTP layer forwards it to `fetch`.

```ts
queryFn: ({ signal }) => matchesApi.getMatch(matchId, { signal });
```

This is what stops work continuing after a screen change, a param change, a query
replacement or a logout. **No fire-and-forget fetch inside a component, ever.**

### Timeouts

`fetch` has no default timeout — an unreachable host hangs until the OS gives up. The
timeout policy is centralized and expressed as classes (`request`, `upload`, `download`,
`background`), implemented with `AbortController`. **No hard-coded millisecond literal in
a feature.**

### Uploads

`httpUpload` is the module's second verb, not a second path: it builds the same wire call
and goes through the same 401 rotation, differing only in what it puts in the body and how
long it may take. It also turns the local `file://` URI a picker hands back into bytes,
because reading one is a `fetch` and `fetch` lives here.

**Progress is stages, not bytes.** React Native's `fetch` cannot report how much of a body
has been sent; `XMLHttpRequest` and a native uploader can, and either would be a second
transport with its own headers, timeout and rotation. So an upload reports the two stages
it genuinely passes through — the bytes are read, then they are sent — and a screen drawing
that never claims a percentage nobody measured.

### The features host

`httpGetFromFeaturesHost` is the module's third verb, and the only request the app makes to a
host that is not the API: the feature-flag datafile, served from `EXPO_PUBLIC_FEATURES_URL`
([ADR-0180](../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md) §4). It goes
through the same `sendOnce` — timeout, correlation id, cancellation, error model — and is a verb
rather than a flag on `httpRequest` because of what it must never send: the call is built
unauthenticated, so no bearer token can reach a laptop on the LAN or a public bucket. It takes
the `background` timeout class; nobody is waiting on it.

### Retry

Centralized in `src/shared/lib/http` and `query-client`, never per call site.

**Queries** (idempotent reads) may retry network interruptions, selected timeouts and
selected 5xx. They must **not** retry 401, 403, deterministic 4xx validation errors, or a
definitive 404.

**Mutations are not retried globally.** A mutation may be retried only when one of these
is true, and the reason is stated at the call site:

1. the endpoint is idempotent, or
2. the backend accepts an idempotency key, or
3. the operation is explicitly known to be safe to repeat.

This matters most for exactly the things this app does: **bookings, reservations,
payments, joins, record creation.** A silent retry of "book this court" is a double
booking.

---

## Part 5 — Authentication

Cross-cutting, implemented once, in `src/shared/lib/auth/`:

```
tokenManager.ts        owns raw token values
refreshCoordinator.ts  single-flight refresh
authService.ts         sign-in / sign-out / session validation
authSession.ts         the SessionStatus state machine
auth.types.ts
```

### Tokens never leave the subsystem

```
Screen → hook → HTTP client → TokenManager → SecureStore
```

A component calling `SecureStore.getItemAsync('accessToken')` is a bug, and so is a token
passed through a React prop, held in Zustand, or written to a log. `AsyncStorage` is
unencrypted plaintext and must never hold a credential — ESLint blocks the import.

The UI consumes `{ status, userId? }`. It never sees a token value.

### In-memory mirror

Reading the keychain before every request is wasteful and blocks on I/O. Read once at
bootstrap into an in-memory session; requests read the in-memory access token;
**every token change is persisted back to SecureStore atomically.** SecureStore remains
the cross-restart persistence, the memory copy is the runtime representation, and neither
is reachable from a component.

Use the **async** SecureStore APIs. Keep payloads small — SecureStore is for secrets, not
caching. Handle read/write/delete failure explicitly.

### Single-flight refresh — the one that bites

Ten in-flight requests get 401 at the same moment. Ten refreshes fire. The backend rotates
the refresh token ten times, nine of them invalidate each other, and the user is logged
out at random.

```ts
let refreshPromise: Promise<Tokens> | null = null;
```

The first 401 creates it. Every subsequent 401 **awaits the same promise**. On success:
tokens update atomically, waiters retry **once**, the promise clears.

### Retry an authenticated request exactly once

A retried request carries internal metadata saying refresh was already attempted. If it
401s again, the session terminates. Without the flag you get an infinite
`401 → refresh → retry → 401` loop that looks like a hung app.

### Classify refresh failure

Losing signal in a lift must not log the user out.

| Failure                                                           | Behaviour                                                                       |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| Refresh **rejected** by the auth server (invalid/expired/revoked) | clear credentials · clear private caches · set `unauthenticated` · redirect     |
| Refresh **could not reach** the server                            | preserve credentials · surface connectivity · retry under the controlled policy |

### Rotation is atomic

`new access + new refresh` persist as **one** session update. Updating one half leaves a
session that cannot recover.

### Logout is a system operation, not a `router.replace`

```
1. optionally revoke the server session / refresh token — and, beside it, let the phone go:
   its push token removed, so the next player on it is not pushed this one's notices (#559)
2. clear the token manager's memory
3. delete the SecureStore credentials
4. cancel in-flight authenticated requests
5. queryClient.cancelQueries() ; queryClient.clear()
6. forget the phone's preferences (ADR-0188 §3)
7. reset sensitive feature UI state
8. set session unauthenticated
9. navigate to the unauthenticated tree
```

Step 5 is a **privacy control**, not tidiness: user A's cached profile, bookings and
matches sitting in memory when user B signs in on the same device is a data leak. Route
replacement clears nothing. **Step 6 is the same control one store over**
([#512](https://github.com/Raketa02/Raketa/issues/512)): the Play segment, and later the last
sport and profile, are kept per account on the phone, and a sign-out of any kind — by hand, or
by the server refusing the credentials — empties them, because the store cannot tell _me again_
from _somebody else_. `endSession` runs it after the status change, awaited, because it waits
on no query.

If the server revoke call fails offline, local credentials still need a defined product
policy — decide it, don't leave them accidentally active.

### iOS reinstall

iOS Keychain data can survive an uninstall/reinstall. **"A token exists" is not proof a
backend session exists** — bootstrap validates or refreshes it. This is also why logout
must delete explicitly rather than relying on uninstall.

### Biometrics

`SecureStore.requireAuthentication` must not be applied blindly: a silent background
refresh would then prompt for Face ID. If biometric locking is wanted, model it as a
deliberate product feature — _backend session_ **+** _optional local app unlock_ — rather
than making every token read biometric. Account for enrolment changes invalidating
protected entries.

---

## Part 6 — The error model

Raw `fetch` rejections and arbitrary backend JSON must not reach a screen.
`src/shared/errors/` defines one normalized family:

```ts
type AppError =
  | NetworkUnavailableError
  | TimeoutError
  | UnauthorizedError
  | ForbiddenError
  | ValidationError
  | ConflictError
  | RateLimitError
  | ServerError
  | UnknownError;
```

The backend's envelope is stable and machine-readable:

```json
{
  "code": "MATCH_ALREADY_FULL",
  "message": "...",
  "details": {},
  "field_errors": {},
  "trace_id": "..."
}
```

**Branch on `code`, never on `message`.** `error.message === "Match already full"` breaks
the moment someone improves the copy or the app is localized.

### Status semantics

| Status | Meaning                                    |
| ------ | ------------------------------------------ |
| 400    | malformed request                          |
| 401    | missing / expired / invalid authentication |
| 403    | authenticated but forbidden                |
| 404    | not found                                  |
| 409    | state conflict                             |
| 422    | input / domain validation                  |
| 429    | rate limited                               |
| 5xx    | server failure                             |

**Not every 4xx is a logout.** Only authentication-invalidating responses touch the
session. A 403 means "you may not do this", and logging the user out in response is both
wrong and infuriating.

### Every error has a recovery category

`retryable automatically` · `retryable by user` · `requires re-authentication` ·
`requires user correction` · `business conflict` · `terminal`.

Assigning the category is part of adding an endpoint. Without it you get one generic
modal for every failure.

Localization goes **backend code → frontend message**. The backend's `message` is a
diagnostic fallback, not the copy.

---

## Part 7 — TanStack Query

Query owns **all** backend-derived asynchronous state: the current user, the sport
registry, an assessment and its questions, a player's ratings. There is no
`GET → set Zustand → read Zustand` path anywhere in this app.

### Query key factories

Every feature defines its keys in one file (`hooks/matchKeys.ts`):

```ts
export const matchKeys = {
  all: ['matches'] as const,
  lists: () => [...matchKeys.all, 'list'] as const,
  list: (f: MatchFilters) => [...matchKeys.lists(), f] as const,
  details: () => [...matchKeys.all, 'detail'] as const,
  detail: (id: string) => [...matchKeys.details(), id] as const,
};
```

No string keys typed inline in a component. **Every parameter that changes the response
belongs in the key** — omit the cursor or a filter and two different result sets collide
in one cache entry.

### Semantic hooks

Features expose `useMatch(id)`, `useMatches(filters)`, `useJoinMatch()` — not raw query
options assembled per screen. The hook concentrates the key, stale time, `enabled`,
selection, and invalidation, so changing any of them is a one-file change.

### Decide the defaults

`staleTime`, gc time, retry count, retry predicate, mutation retry, `networkMode`, and
refetch-on-focus are **decisions**, taken in `src/shared/lib/query-client/`, not library
defaults inherited by accident. Different data classes differ:

```
slow-changing reference data  → long stale time
live court/slot availability  → short stale time
current profile               → moderate
```

Avoid a global "refresh everything every 5 seconds" strategy — on mobile that is the
user's battery and data plan.

### Native focus and network

Query's defaults assume a browser. A React Native app is neither focused nor blurred in
the DOM sense, and has no `navigator.onLine` worth trusting.

- Wire `focusManager` to `AppState` via `shared/lib/platform/appState.ts`.
- Wire `onlineManager` to native connectivity via `shared/lib/platform/networkState.ts`
  (`expo-network` or `@react-native-community/netinfo`).

Without these, stale data does not refresh on foreground and paused mutations never
resume.

### Mutations

A mutation declares: the operation, error mapping, success behaviour, the cache update,
the invalidations, optimistic behaviour if any, and its retry/idempotency rule.

```
join match succeeds
  → setQueryData(matchKeys.detail(id), response)   ← the canonical entity, from the server
  → invalidate match lists
  → invalidate the player's upcoming matches
```

**Prefer response-driven updates.** If the mutation returns the updated entity, write it
into the cache; don't immediately refetch what you were just handed.

### Optimistic updates are not the default

Use them when latency is perceptible, rollback is deterministic, conflicts are
manageable, and rejection is rare. **Avoid them** when server rules are complex, when
availability moves fast, when money is involved, when rollback would confuse, or when the
server response touches several entities. Booking a court is the textbook case for a
pending state rather than an optimistic one — someone else may have taken the slot.

### Cache isolation

On logout and on account switch: `cancelQueries()` then `clear()`, or an explicit
partitioning policy. See [Part 5](#part-5--authentication).

---

## Part 8 — Zustand

Zustand holds **UI and client state**. It is not a database, not a cache, not a token
store.

**Good:** wizard progress across screens · temporary filters · UI preferences · the
currently selected local context · modal/sheet coordination.

**Bad:** API entities · tokens · backend cache · every form field · a global loading flag
· navigation state.

### Reach for it last

```
component-local?         → useState / useReducer
feature-local shared?    → a small store at features/<f>/store/
truly app-wide UI state? → src/shared/store/, and only with a reason
```

`features/matches/store/matchFilters.store.ts` beats `store/useAppStore.ts` with two
hundred properties, on ownership, testing, reset behaviour and parallel work. The feature
`store/` folder is an **optional** ninth layer — present when the feature needs one,
absent otherwise. It does not join ADR-0009's mandatory set.

Subscribe with selectors — `useFilterStore(s => s.selectedSport)` — not the whole store.

Use the slice pattern only when one store is genuinely complex, not to imitate Redux. And
**keep network orchestration out of store actions**: server calls live in `api/`,
`use-cases/` and `hooks/`. A store action that fetches hides who owns the data.

---

## Part 9 — Zod and validation boundaries

Zod is **runtime** validation, for places TypeScript's compile-time guarantees end:

form input · route params · deep links · push payloads · environment config · persisted
local data · external SDK payloads · selected critical backend payloads.

### Do not mirror the OpenAPI schema in Zod

`openapi-typescript` and Zod solve different problems — static contract versus runtime
validation. Hand-writing a Zod copy of every generated DTO creates **two independently
maintained API schemas** that will drift. If full runtime response validation becomes a
requirement, generate the runtime schemas from the same `openapi.json`.

### Forms

One canonical schema per form, producing the validation result, the typed data, the
field errors and the normalized payload. For large forms add React Hook Form with the Zod
resolver — do not hand-roll a form framework.

### Type assertions are not validation

`const match = json as Match` checks nothing at runtime. Either trust the generated
contract deliberately, or validate. Prefer `unknown` for untrusted data and narrow it.

---

## Part 10 — The API contract

`backend/openapi.json` is the source of truth
([ADR-0006](../../docs/adr/0006-backend-owns-api-contract.md)).

```
FastAPI models/routes → openapi.json → openapi-typescript → src/generated/schema.d.ts
   → feature api/ + mappers/ → domain objects
```

- Generated files are **never hand-edited**.
- Generated types enter a feature only through `api/` and `mappers/`. ESLint enforces it.
- Generation is deterministic and its output is committed.
- CI runs `pnpm gen:api && git diff --exit-code`. **Contract drift fails before merge**,
  not in production.
- A production build never depends on a live dev server being reachable to generate
  types. Use the committed schema file.

### Domain models vs wire types

Not every endpoint needs a domain model. Introduce one when the backend representation is
unstable, when several fields combine into one concept, when dates/currency/units need
normalizing, when business rules operate on the object, when the UI should not depend on
transport naming, or when several endpoints express the same entity differently. For a
trivial read-only shape, the generated type behind a mapper is enough. The point is to
isolate meaning, not to maximise mapper count.

---

## Part 11 — Product surface

### Business rules are not JSX

```tsx
<Button disabled={match.status === 'OPEN' && match.players.length >= match.maxPlayers && …} />
```

becomes `canJoinMatch(match, player)` in `domain/`. Pure functions are testable without a
renderer, reusable, and safe to change — which is precisely why the rule stops being
duplicated across three screens.

### Model every state a server-driven screen can be in

`initial loading` · `loaded` · `empty` · `refreshing` · `recoverable error` ·
`terminal error` · `offline/stale`.

`if (isLoading) return <Spinner/>; if (error) return <Text>Error</Text>;` is not
acceptable for a product flow. Build the reusable states — `LoadingState`, `EmptyState`,
`ErrorState`, `OfflineBanner`, `Skeleton` — in `src/shared/ui/`.

> **Amendment — `OfflineBanner` is declined, and the offline sentence is a function
> instead.** A screen-level banner assumes that being offline makes what is on screen
> wrong. In Play it does not: every ranked list is a mutation-minted record pinned at
> `staleTime: Infinity`, so a pool held offline is not stale — it is the record, exactly as
> it was recorded. What breaks offline is never the data, it is the **acts** — searching,
> filling, forecasting, sending — and each of those has a control the sentence can sit
> beside. A banner over correct data teaches the player to ignore banners.
>
> The app had already answered this three times before the question was asked:
> `SocialRadiusStep`, `SocialTagsStep` and `SportsPickerScreen` each render an inline
> `<Note variant="amber">` at the paused thing. Three copies is the threshold
> `recoveryMessage.ts` names as the signal to promote, so the sentence moves to **one
> shared function beside `recoveryMessage`** — and it has exactly **two** values, because
> only one distinction matters: _does this resume by itself when the connection comes
> back?_ Everything that pauses says it will load as soon as you are back; the one act that
> is set to fail rather than defer says it cannot be sent. The test is resumption, **not**
> the HTTP verb — the line-up forecast is a `POST` that pauses, and it takes the first
> sentence.
>
> `LoadingState`, `EmptyState`, `ErrorState` and `Skeleton` stand as written. This list is
> a menu of states to model, and declining one of its components is a decision about where
> a state renders, never about whether it is modelled.
> Decided by [#239](https://github.com/Raketa02/Raketa/issues/239), built as
> `src/shared/errors/offlineMessage.ts` by
> [#265](https://github.com/Raketa02/Raketa/issues/265).

### Loading granularity

Distinguish screen initial load · pull-to-refresh · background refresh · button mutation ·
pagination load-more. One global spinner for all five makes the app feel broken. The UI
stays usable during a background refresh.

Skeletons where the layout is known and perceived speed matters; a localized indicator for
a localized action. Don't block the screen for a small mutation.

### Duplicate submission

Every critical mutation button declares its behaviour: disabled while pending, an
idempotency key, deduplication, or explicitly-valid repetition. **Button disabling is UX,
not correctness** — the backend's idempotency is what actually prevents the double
booking. Two users taking the last slot, two devices submitting once, one user
double-tapping, and a retry after a timeout are all the server's problem to resolve
transactionally; the client's job is to send an idempotency key and map 409 cleanly.

### Accessibility

Every reusable component supports VoiceOver and TalkBack: labels, roles, scalable text,
44 × 44pt touch targets, logical focus order, and state announcements where they matter.
Test on both platforms — the semantics differ. See the design system for the app's
specific rules.

### Internationalization readiness

Never branch on a user-visible string. `status === MatchStatus.Cancelled`, not
`status === 'Cancelled'`. Translate at the presentation boundary only. Dates, numbers,
currency and pluralization go through central formatters in `src/shared/`.

### Dates and time

The backend holds authoritative timestamps and transmits ISO-8601. Distinguish a
**timestamp** from a **local calendar date** — a booking date is not an instant — and
never silently parse a date-only string as a UTC timestamp. Centralize parsing and
formatting. Never make a business decision from a formatted display string, and never
trust the device clock for a rule that depends on the backend's.

---

## Part 12 — Performance

Measure on production-like builds. Dev mode is not a benchmark.

Watch: cold start · warm start · time to interactive · JS thread stalls · slow renders ·
navigation latency · network waterfalls · list scrolling · image memory · crash-free
sessions.

- **Keep the JS thread free.** No repeated parsing of huge payloads, expensive array work
  during render, synchronous secure-storage calls, heavy in-JS crypto, or large
  serialization loops. Move work out of render, precompute, push it native, or push it to
  the backend where it belongs.
- **Profile before optimizing.** `memo` / `useMemo` / `useCallback` everywhere is
  complexity without evidence. measure → find the bottleneck → fix → measure again.
- **Large lists** are virtualized, with stable keys, light rows, backend pagination and
  minimal row state. Evaluate FlashList if scale justifies it.
- **Images** need a strategy: thumbnail sizes, server-side resizing, aspect ratio,
  placeholders, cache and retry behaviour, upload compression. Do not download a
  full-resolution original for a card.
- **No waterfalls.** If B and C do not depend on A, run them in parallel or ask the
  backend to aggregate. Network shape is frontend performance.
- **Fetch what the screen uses.** A screen showing three fields should not pull the whole
  object if the backend can express a smaller representation.

---

## Part 13 — Native and platform

- **New Architecture stays enabled** (`newArchEnabled: true` in `app.config.ts`) unless a
  verified production dependency blocks it — and then that dependency is technical debt
  with a migration plan, not a permanent exemption.
- **SDK 52 is an upgradeable baseline, not a destination.** Framework-specific code is
  concentrated in `src/app/`, `src/shared/lib/platform/`, `src/shared/lib/auth/`, the
  config files and config plugins, so an SDK upgrade never restructures a feature.
- **Continuous Native Generation.** `app.config.ts` + config plugins +
  dependencies → `expo prebuild` → `android/`, `ios/`. Those directories are build output
  and are not committed; hand-editing them loses the edit on the next prebuild. Native
  configuration is expressed as official or local config plugins.
- **Development builds, not Expo Go**, as the day-to-day environment: `development` →
  `preview/internal` → `production`. Expo Go is for quick experiments and cannot contain
  this app's native dependencies.
- **Native code hides behind a narrow TS interface** in `src/shared/lib/platform/`, never
  imported raw across the UI. Three ports exist: `LocationPort` over `expo-location`,
  `ImagePickingPort` over `expo-image-picker`, and `LiveStreamPort` over `react-native-sse`
  — each the only importer of its module, each with a hand-written fake in
  `src/test-support/platform.ts`. A native module has no JS implementation underneath it,
  so a feature that imports one is a feature no test can drive — which is the argument,
  more than tidiness, and it is the argument the third one is here on too even though its
  far side is a socket. The linter enforces all three bans and
  `scripts/test-import-boundaries.sh` proves it still does. Four more have joined them since —
  haptics, the clipboard, the share sheet, and **`PaymentsPort` over `@stripe/stripe-react-native`**
  ([#552](https://github.com/Raketa02/Raketa/issues/552)), the one port that carries a component:
  Stripe's card fields are a native view whose entry stays inside it, so the port hands a screen
  `CardFields` beside its verbs, and `fakePayments()` behaves as Stripe's test cards do
  ([`docs/features/_shared.md`](features/_shared.md)). The eighth is **`PushPort` over
  `expo-notifications`** ([#559](https://github.com/Raketa02/Raketa/issues/559)): the permission, the
  push token, a push arriving while the app is open and a push tapped, with `fakePush()` beside it.
- **A screen reaches a port through its context** — `useLocation()` /
  `useImagePicking()` / `useLiveStream()`, each defaulting to the real device, so nothing
  in the app wires anything up and a test wraps the tree in the device it wants. A screen
  that imported `deviceLocation` directly would be a screen no test can put in front of a
  refused permission.
- **A `blocked` permission has exactly one remedy, and it is not a prompt.**
  `openAppSettings()` opens the app's own page in Settings; the OS resolves a blocked
  permission itself, instantly and negatively, so a control that asked again would be a
  control that does nothing.
- **Location is foreground only.** Nothing asks for, checks or starts a background
  location, `app.config.ts` disables it on both platforms, and two tests assert the
  absence. A background permission is not a stronger foreground one — it collects a
  movement trail while the player is doing something else, which is a different privacy
  class from the one they were asked about.
- **Platform files over scattered branches.** `share.ios.ts` / `share.android.ts` when
  behaviour genuinely differs; not `if (Platform.OS === 'ios')` in twenty components.
- **Permissions are requested just in time**, when the user understands why, through one
  central module distinguishing _not requested / granted / denied / permanently denied_.
  Never a permission wall at first launch. Android and iOS behave differently here.
- **Push notifications:** payloads are untrusted, sensitive content stays out of them,
  deep-link targets are validated, the destination is authorized _after_ open, routing is
  centralized, token rotation is supported and synchronized with the backend. **A push
  never mutates business state without backend confirmation.**
- **Background work** is a native, platform-constrained capability. A JS timer does not
  survive backgrounding. Use the Expo/native background APIs, and prefer the backend for
  anything that doesn't fundamentally need the device.
- **App lifecycle is centralized** in `shared/lib/platform/appState.ts` — Query focus,
  session freshness, privacy screens, observability, reconnect. Not dozens of `AppState`
  listeners across unrelated screens.
- **No overlay touches `Modal`; it draws on `ModalStage`, which is the native window on iOS
  and a layer in the tree on Android** ([ADR-0178](../../docs/adr/0178-an-overlay-on-android-is-a-layer-in-the-tree-not-a-native-window.md)).
  Under the New Architecture a modal's content on Android is laid out at 0 × 0 first and again
  at the window's size when the dialog reports it as native state — and Reanimated 3.16 loses
  that second pass whenever any animated style is mounted anywhere in the tree (measured
  2026-09-17: a 1 × 1 `useAnimatedStyle` view on the deck pane collapsed the deck's own sheet).
  Sized by hand the sheet drew and could not be pressed: a 0 × 0 view makes Android
  re-dispatch every touch's start and the modal's host wins the second negotiation. So on
  Android `shared/ui/overlay`'s `OverlayHost`, wrapped around the route tree in the root
  layout, renders every stage as a layer beside the toast host, ordered by `theme.layer`, the
  app hidden beneath it from a screen reader, the back gesture answered by the stage. A
  layer's children keep the root's contexts and lose a screen's — every provider is at the
  root, and no sheet's content reads the navigation; keep it so. The first overlay to hold a
  text input takes on `KeyboardAvoidingView` in its stage, on both platforms.
- **Nothing on the UI thread scales a layer to move it.** The radar's tiles are placed by
  translating a one-point anchor per tile from three shared values; the earlier one scaled
  transform with counter-scaled tiles was a blur on iOS at the floor, because a 4 700-point
  layer is rasterised at its unscaled resolution (ADR-0176 §2 as amended). And a pinch on
  Android does not end when one finger lifts — the recogniser stays active on the one that
  remains and reports it as the focal point — so a pinch is over on the event's pointer
  count, never on the recogniser's end (ADR-0177 §1 as amended).

### The live surface

**The app has exactly one, and it is a conversation's**
([ADR-0147](../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md),
built by [#365](https://github.com/Raketa02/Raketa/issues/365)). This is the section that
record left to the first client build, and it is short because the record spent its design
budget making it short.

- **What crosses is a nudge — `{ v, conversation_id, last_seq }` — and nothing else.** No
  message, no system line, no plan slot. On receiving one the client re-reads through the
  ordinary authenticated path from **its own** high-water mark, so a dropped frame is
  repaired by the next one for free. _Whether the UI may render what it did not read from
  the authoritative path_ is not a rule anybody keeps here; it is a thing the wire cannot
  express.
- **Above the port the number does not exist.** `liveStream.ts` parses `last_seq` to know a
  frame is a nudge and drops it, so `LiveNudge` carries the room and nothing else. A number
  handed up is a number somebody eventually pages from.
- **The nudge invalidates. The Query cache stays the single copy.** There is no second store
  for a conversation, no client-side append and no sequence arithmetic — the posture Part 7
  already takes for mutations. _Nothing in Play background-refetches_ is a **scope
  clarification, not an exception**: that rule is about a ranked list reordering under a
  finger, and a conversation is append-ordered.
- **A nudge re-reads what the room draws, and nothing it does not.** The room's query,
  `planKeys.list()` and `gameKeys.list()` — the plan card is `(game, plan)`, read off `GET /plans`
  and `GET /games`, two lists beside the room, and a slot another member set reaches this phone
  as a line on the same frame ([#405](https://github.com/Raketa02/Raketa/issues/405)); a court
  that completes while the room is open, and a standing that moves on a _we played_ line, reach
  it through the games list ([#406](https://github.com/Raketa02/Raketa/issues/406)). On every
  nudge, never on sighting a plan line, because a trigger keyed on the line vocabulary goes stale
  on exactly the build too old to read a new code. The Chats list is not re-read: the room draws
  nothing from it. And because a plan write is written in rather than refetched, every plan write
  first **cancels** the plan list's in-flight read — not optimism, a read that can only be older
  than the reply; the games list needs none, because a result write invalidates rather than
  writes in.
- **One stream per open conversation, and never one for a list.** The port opens while a room
  is on screen and closes when it leaves. ADR-0147's _never build_ list says the rest.
- **The port owns the route as well as the transport.** A port taking an arbitrary path
  would be a generic SSE client, and the one thing that buys is the second stream the record
  forbids.
- **The stream closes at the access token's `exp` — roughly every fifteen minutes — so
  reconnecting is the ordinary path.** Every attempt mints a fresh credential through
  `streamAttempt`, and a `401` goes through the app's own single-flight rotation, once per
  channel. A channel that captured its headers would reconnect for ever with the token that
  had just expired.
- **Foreground only.** The channel is closed on the way to the background and re-opened on
  the way back, through the same `focusManager` every other lifecycle answer comes from —
  and a deliberate close is a status of its own, because it is not news about the room.
- **It composes with `networkState`** rather than adding a rule: no attempt while
  `onlineManager` says there is nothing to attempt over, reported as _lost_ rather than as a
  handshake in progress.
- **A severed stream, a dead subscriber, a Redis outage and a phone with no signal all
  produce the same thing**, and the read path works throughout. What a screen draws about it
  is a fold in `domain/`, never a socket read in a component — see
  `features/conversations/domain/liveState.ts`.

---

## Part 14 — Configuration, environments and secrets

`src/shared/config/env.ts` validates at startup and fails fast:

```ts
const EnvSchema = z.object({
  EXPO_PUBLIC_API_URL: z.string().url(),
  EXPO_PUBLIC_FEATURES_URL: z.string().url(),
  EXPO_PUBLIC_ENV: z.enum(['local', 'development', 'staging', 'production']),
  EXPO_PUBLIC_LINK_DOMAIN: z.string().optional(), // a bare host, or nothing
});
```

`EXPO_PUBLIC_LINK_DOMAIN` is the one **optional** value: the web domain the app's links live on
(`raketa.app`, bare), and **empty in every environment today**
([#520](https://github.com/Raketa02/Raketa/issues/520), ADR-0187 §7). Set, `app.config.ts` gives iOS
an associated domain and Android a verified intent filter for the three link paths; empty, the links
use the app's scheme alone. The native document and the runtime read it through one pure function,
`src/shared/config/appLinks.ts`, so the binary and the running app cannot disagree about which links
are the app's.

`EXPO_PUBLIC_FEATURES_URL` is the base the feature-flag datafile is fetched from —
`<base>/<environment>/featurevisor-player.json` — the Mac's LAN address today, a bucket later
([ADR-0180](../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)
§4). It obeys the scheme rule below exactly as the API URL does, for the same reason: it is
reached from a phone, and a datafile read in the clear is one somebody on the network can
rewrite.

The four names are the platform's, shared verbatim with the backend.
`local` is a developer's own machine and is the only one that runs today; `development`
and `staging` are validated but **not provisioned**, and there is no production
deployment. Naming a laptop `development` — which is what this app did before the four
names existed — makes a laptop and a shared remote deployment indistinguishable in a log
line.

**The URL scheme is part of the contract.** Both URLs are reached from a phone over the
internet, so each takes the **public-network** form of the platform's scheme rule:
`development`, `staging` and `production` must be `https://`. `local` takes either —
`expo start --tunnel`, cloudflared and tailscale funnel all hand back `https://`, and a
tunnel is precisely what a physical device that cannot reach the laptop's LAN IP needs.
The rule is checked across the two variables together, so a laptop URL under a deployed
name is a startup failure naming both — not a build that silently points at nothing. It
stays silent when the URL is malformed, so one typo produces one complaint rather than a
second one blaming the environment. The cross-app rule is
[`../../docs/environments.md`](../../docs/environments.md).

**The native config is a function of the environment.** `app.config.ts` replaced
`app.json`, and holds no logic: `src/shared/config/appIdentity.ts` maps each environment
to the app's display name and whether a badge shows, and the document calls it. Outside
`production` the app is named for its environment and an amber badge sits over every
screen; `production` is bare and unbadged. Expo evaluates the document in Node before
Metro exists, so it reads `process.env` directly and refuses an unknown environment
rather than defaulting — and it registers sucrase's TS require hook first, because Node
cannot otherwise load the `.ts` identity module.

**One installable variant.** One bundle identifier, one package name, one URL scheme, no
build-profile configuration. Per-environment identifiers wait until a second backend
exists to point them at; three installable apps that all reach the same laptop would be
ceremony, and the badge already answers the question they would.

**Nothing in the bundle is secret.** `EXPO_PUBLIC_*` values and `app.config.ts` `extra` are
extractable from a shipped binary — they are _public config_. Private API keys, backend
credentials, signing secrets, encryption keys and privileged service credentials belong on
a server. A secret the mobile client appears to need is a design error.

Keep the four genuinely separate: API hosts, analytics and monitoring environments, EAS
build profiles, update channels, and app identifiers where useful. **A production build
must never point at staging** — validate it in CI.

Build-time secret ≠ safe to embed. If client JS reads it at runtime, assume the user can
extract it. CI and EAS secret management hold signing credentials; they are never
committed.

---

## Part 15 — Observability

Production visibility is part of the feature, not a follow-up.

`src/shared/lib/observability/` provides `logger.ts`, `analytics.ts`, `telemetry.ts`.
Features depend on **this interface**, never on a vendor SDK directly — that is what makes
the vendor replaceable and consent, PII filtering and testing centralizable.

At minimum: crash reporting · JS error reporting · native crash reporting · release/build
identification · API failure metrics · traces for important flows · structured
breadcrumbs · correlation IDs. Sentry is the Expo-supported default choice.

### Correlation IDs

Each request carries or receives a request/trace ID; FastAPI returns `trace_id` in the
error envelope; the client attaches it to the error report. That links _mobile failure ↔
backend request ↔ server logs_ **without logging any payload**.

### Redaction

**Never** log or attach to a report: access or refresh tokens, passwords, `Authorization`
headers, payment credentials, unapproved personal data, or full backend payloads by
default. The logger redacts structurally rather than relying on each call site. Production
logging is stricter than development logging.

Safe report context: app version, native build number, runtime/update version,
environment, OS, route name, feature, an anonymous user identifier if privacy rules
allow, and the trace ID.

### Analytics governance

One interface — `analytics.track('match_join_started', { matchId })` — and an **event
catalog**: every event has a name, owner, trigger, properties with types, PII
classification and business meaning. Ad-hoc event names invented per PR make the data
useless within a quarter.

Define a data classification (`public / internal / personal / sensitive / credential`) and
let it drive every storage, logging, analytics and monitoring decision. Collect the
minimum the feature and observability actually need, with explicit retention.

### Error boundaries

A root boundary always; feature/screen boundaries for recoverable sections. The root crash
screen offers a safe fallback, a retry or restart path, and an error report — and **never
a raw stack trace in production**. Boundaries do not replace promise/network error
handling; they catch render failures only.

---

## Part 16 — Testing

TDD as this repo already practices it, arranged as a pyramid:

```
many pure unit tests → component tests → integration tests → a few E2E journeys
```

- **Unit (Jest):** domain rules, mappers, schemas, formatters, query-key factories, the
  refresh coordinator, error mapping, store logic. Pure — no renderer.
- **Component (`@testing-library/react-native` + `jest-expo`):** _given state, when the
  user acts, then observable behaviour changes._ Assert what the user can see, never
  internal state variables.
- **Router:** tests live **outside `src/app/`**. Cover redirects, the authenticated route
  boundary, deep-link routes, params, navigation. Authorization routing deserves
  integration tests.
- **Auth concurrency — mandatory, and the reason this section exists.** Ordinary login
  tests never catch these:

  | Scenario                         | Expected                                                  |
  | -------------------------------- | --------------------------------------------------------- |
  | Many simultaneous 401s           | exactly **one** refresh request; all waiters reuse it     |
  | Refresh rejected                 | a single logout transition; tokens cleared; cache cleared |
  | Refresh times out on the network | the session is **not** destroyed                          |
  | The retried request 401s again   | no infinite refresh loop; session terminates once         |

- **Query integration:** correct key, correct `enabled`, cache update after mutation,
  invalidation after mutation, optimistic rollback if used, cache cleanup on logout,
  offline/focus behaviour where it matters.
- **Contract:** export OpenAPI → generate → typecheck, in CI. See
  [Part 10](#part-10--the-api-contract).
- **E2E (Maestro or equivalent):** a small set of critical journeys — launch, sign in,
  session restoration, core navigation, one primary business flow, logout, deep link. Do
  not express the whole suite as E2E.
- **Real devices:** Android emulator, a representative physical Android, iOS simulator, a
  representative physical iPhone, and low/mid-range Android where relevant. "Works on the
  iOS simulator" says nothing about a mid-range Android.
- **Snapshots** are a narrow tool. Large snapshots produce noisy diffs, get updated
  without reading, and test structure instead of behaviour.

---

## Part 17 — Delivery and backward compatibility

### CI, per pull request

```
install with a frozen lockfile → lint → format check → typecheck
→ OpenAPI drift check → unit tests → component/integration tests
→ expo-doctor → build/config validation
```

Selected branches add Android/iOS preview builds and E2E smoke tests. The lockfile is
committed and CI installs immutably.

### Dependencies

Install Expo-managed packages with `npx expo install` so compatible native versions are
chosen. Before adding anything, answer: is the problem hard enough to justify it · is it
maintained · does it support the New Architecture · does it need native config or a config
plugin · what does it cost in bundle and runtime · does it duplicate something we have ·
can it be upgraded independently · is the license acceptable. Run `expo-doctor` in CI.

### Release

```
merge → CI → preview/internal build → automated smoke/E2E → QA
→ production candidate → store submission → staged rollout → monitoring
```

Builds are reproducible and CI-controlled. A developer laptop is not a release channel.

Define release health gates — crash-free sessions, ANR rate, startup regression, API error
rate, auth failure rate, core-flow completion — and stop or roll back when they regress.
Upload source maps as part of the pipeline; a minified production stack trace without them
is nearly worthless.

Track separately: user-facing app version, Android version code, iOS build number, and the
Expo runtime/update version. A crash you cannot tie to an exact binary + update is a crash
you cannot fix.

### OTA / EAS Update

An explicit `runtimeVersion` policy, always:

```
JS change compatible with the installed native runtime → OTA
native dependency or configuration changed            → new native build
```

**Never ship JS expecting native code the installed binary does not contain.** Production
OTA uses separate channels, staged internal validation, release notes, post-rollout
monitoring, a rollback plan, and code signing where the security bar requires it.

### Released clients are immutable

This is the constraint that makes mobile different from a web client: **old versions live
on real phones for months.** The backend must stay compatible with released clients for a
defined support window. Prefer additive changes; for a breaking one, version the
endpoint/schema, keep a transition period, measure active client versions, and force an
upgrade only when product or security justifies it. Do not version every endpoint
preemptively.

Send safe client metadata — app version, build number, platform — as explicit headers, so
the backend can observe and adapt without parsing user agents.

---

## Part 18 — Offline and persistence

This app is **network-backed with an in-memory Query cache and graceful offline UX**. It
is not offline-first, and must not be described as such unless it grows authoritative
local data and conflict resolution. Offline and flaky networks are the normal case, not an
edge case — which is a reason to lean on Query's cache and retry behaviour, not a licence
to invent a local database.

**Persisting the Query cache** is a later, deliberate step. If added: a real persistence
adapter, a cache version with migrations, a maximum age, exclusion of sensitive data,
user-scoped clearing on logout, and schema-change handling. **Never store a query cache in
SecureStore** — it is for small secrets.

**The one thing persisted outside the keychain is the feature-flag datafile**
([ADR-0180](../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md) §6): the last one the app
could read, kept raw in AsyncStorage by `features/feature_flags/api/datafileCache.ts` and read
back at launch, so a player offline keeps the flags they last saw. It is not a query-cache
persistence and none of the rules above are waived for it: it is public-read by design, names no
player, is checked on the way out as it was on the way in, and a read that fails is simply no
cache.

**The second is the phone-preferences store**
([ADR-0188](../../docs/adr/0188-the-phone-remembers-three-choices-per-account-and-forgets-them-at-sign-out.md)):
`src/shared/lib/preferences/phonePreferences.ts` keeps the choices a player made on this phone —
the Play segment since [#512](https://github.com/Raketa02/Raketa/issues/512), the last sport and
the last profile to come — **one key per account per value**, and **empties itself at sign-out**
as step 4 of `endSession`, beside the cache clear. It holds a choice, never a copy of server
state; a value it cannot read, or one the owning feature no longer recognises, is that value's
default. AsyncStorage stays banned everywhere else ([Part 19](#part-19--what-the-linter-enforces)).

**Introduce SQLite** only for true offline workflows, large structured local datasets,
durable operation queues, complex local queries, conflict resolution, or persistence
genuinely beyond the query cache. Not because "production apps have one". And never
Zustand as an offline database.

---

## Part 19 — What the linter enforces

Architecture that lives only in a document is eventually violated. `eslint.config.mjs`
encodes:

- generated wire types are importable only in `api/` and `mappers/`
- `domain/` and `use-cases/` import no React, React Native, Expo or wire types
- no imports from `../backend/` or any sibling app
- `@react-native-async-storage/async-storage` is importable only by
  `features/feature_flags/api/datafileCache.ts`, which keeps the public flag datafile, and by
  `shared/lib/preferences/phonePreferences.ts`, which keeps the per-account choices ADR-0188
  lists — never a credential (ADR-0008, ADR-0180 §6, ADR-0188 §1)
- `@featurevisor/sdk` is importable only by `features/feature_flags/api/featurevisor.ts`, the
  one module that holds the instance (ADR-0180 §5)
- `expo-secure-store` is importable only inside `src/shared/lib/auth/`
- `expo-location`, `expo-image-picker`, `react-native-sse`, `expo-haptics` and `expo-clipboard`
  are importable only by the port that owns each — `platform/location.ts`,
  `platform/imagePicking.ts`, `platform/liveStream.ts`, `platform/haptics.ts` and
  `platform/clipboard.ts`, one file each rather than the platform directory, so a module of
  ports cannot become the device bucket. The ban holds in tests too, which could not drive a
  native module anyway
- **`Share` from `react-native`** — one name out of a module every screen imports — is importable
  only by `platform/share.ts`, the share sheet's port (#513). It is a path ban with
  `importNames` rather than a pattern, so every other name out of `react-native` stays free
- `platform/liveStream.ts` is the one file outside a feature's `api/` and `mappers/` that
  may read `src/generated/`, and it is exempt from **two** bans rather than one: ADR-0147 §7
  requires the live envelope to be the generated type, and a stream body is not a response
  model, so the operation's own `200` generates as `unknown` and the frame is parsed against
  `LiveNudgeSchema` by name. It is that route's `api/` layer with nowhere else to live,
  because a feature's `api/` may not import a transport
- **every exemption is a subtraction from the full ban list, never a re-listing.** An
  exception block that enumerates its patterns by hand loses each ban added after it, and
  loses it in silence — which is how `expo-location` was briefly importable from
  `shared/lib/auth/` while three documents said it was importable nowhere but a port
- `fetch` is configured only in `src/shared/lib/http/`; features call it through there
- `src/shared/**` may not import `src/features/**`
- a feature may not deep-import another feature's internals
- `src/app/**` may not import a feature's internals — only its `types.ts` surface
- nothing imports `features/play`, `features/challenges` or `features/plans` — the old loop
  #569 removes and #576 deletes whole — except those three and the files `OLD_LOOP_SURFACES`
  names, each a part of it that #576 takes out too. The pieces the new games share moved out
  first (#574): the deck's stage, the yes screen's parts and the leave sheet to
  `features/proposals`, the seat face to `shared/ui`, the seat and balance words to
  `shared/vocabulary`

Circular dependencies fail CI.

And the rules are themselves tested. Every ban above was added to a tree that already
satisfied it, so not one had ever been seen to fail — which is indistinguishable from one
that cannot. `pnpm test:boundaries` (`scripts/test-import-boundaries.sh`) feeds the real
linter code that breaks each module ban, on stdin so nothing is written to disk, and
asserts it goes red — then asserts it stays quiet in the one module that owns the import.
It runs in `pnpm check` and as its own CI step, for the reason `make test-hooks` and
`make test-drift` exist.

### Anti-patterns, stated plainly

**Architecture** — one global `services/ hooks/ types/ store/ utils/` for the whole app; a
`utils/` dumping ground instead of semantic homes (`formatting/`, `date/`, `currency/`,
`validation/`); generic names (`handleData`, `service`, `helper`, `manager2`, `common`,
`misc`).

**Networking** — `fetch` in a component; a bespoke networking framework.

**Auth** — SecureStore read from a component; a token in a prop, a store, or a log; a
separate refresh per 401.

**Query** — Query data copied into Zustand; global mutation retry; inline string keys.

**OpenAPI** — editing generated files; parallel hand-written API interfaces.

**Zod** — assertions passed off as validation; a hand-maintained Zod copy of every DTO.

**Navigation** — feature implementation inside a route file; trusting deep-link params.

**Security** — a private key in `EXPO_PUBLIC_*`; logging an `Authorization` header;
treating a hidden button as authorization.

**Performance** — optimizing without profiling; heavy synchronous work in render.

**Native** — hand-editing generated `android/` and `ios/` under CNG.

**Testing** — relying on snapshots; leaving auth concurrency untested.

### Backend authorization is the only authorization

Hiding a button is not a security boundary. Every protected FastAPI operation validates
_identity + authorization + resource ownership_ server-side. The app may prevent an
obviously invalid action for UX; the server remains authoritative. Root/jailbreak
detection is a risk signal, not a control. Attestation is an additional signal, not a
replacement for authentication.

HTTPS only in production. Never disable TLS verification, never ship permissive
development trust settings. Certificate pinning is possible but brings a rotation
lifecycle that must be planned before it is adopted. Use OWASP MASVS as the review
baseline: storage, authentication, authorization, network, data leakage, logging, privacy,
platform interaction, code integrity, resilience.

---

## Part 20 — Definition of done, and the PR checklist

A feature is not done when the screen looks right.

```
[ ] route/navigation implemented, guard respected
[ ] API contract regenerated and committed
[ ] backend error codes mapped to AppError + recovery category
[ ] domain rules covered by pure tests
[ ] query keys defined in the feature's key factory
[ ] stale time and retry policy chosen deliberately
[ ] mutation cache update + invalidations defined
[ ] loading / empty / error / offline states designed
[ ] every value from theme.ts — no literal colour, size, spacing or radius
[ ] surfaces conform to the design system; a new value changed theme.ts AND its doc
[ ] duplicate-submit behaviour decided (idempotency, not just a disabled button)
[ ] authorization enforced server-side
[ ] route + deep-link params validated with Zod
[ ] accessibility implemented (labels, roles, 44pt targets — 6.8's hour cell the one recorded exception)
[ ] analytics events defined and catalogued, if any
[ ] breadcrumbs added where useful; no sensitive logging
[ ] tested on Android and iOS
[ ] component/integration tests added
[ ] E2E critical path updated if it changed
[ ] backward compatibility with released clients considered
[ ] native rebuild required? said so explicitly
```

**Review questions:** Which feature owns this? Is remote state only in Query? Is UI state
local unless sharing is required? Are API types generated rather than duplicated? Is new
runtime input validated? Are tokens unreachable from UI code? Are errors normalized? Is
retry safe? Are invalidations defined? Could this leak user data across a logout? Is it
accessible? Are Android/iOS differences handled? Does it need a native rebuild? Is the
dependency SDK-52 and New-Architecture compatible? Are tests at the right level? Is
telemetry non-sensitive? Does the backend stay compatible with older clients?

---

## Part 21 — Capabilities not yet in `package.json`

The manifest currently targets Expo SDK 52 with expo-router, secure-store, expo-network,
TanStack Query, Zod, Zustand, Jest/jest-expo, Testing Library, ESLint, Prettier and
openapi-typescript. The architecture above additionally requires, and these should be added
when the code that needs them is written — not preemptively:

**Near-essential**

- Crash/error monitoring — Sentry (`@sentry/react-native`, Expo-supported) or equivalent,
  behind `shared/lib/observability` ([Part 15](#part-15--observability)).
- Maestro — E2E journeys ([Part 16](#part-16--testing)).

> `expo-notifications` joined the manifest with the notices
> ([#559](https://github.com/Raketa02/Raketa/issues/559)), at the version Expo SDK 52 pins (0.29.14),
> behind the eighth platform port — a native module, so it needs a development build rebuilt with
> it; its config plugin's iPhone push entitlement is taken back out until the Apple Developer
> membership exists (`plugins/push.ts`).
>
> `@stripe/stripe-react-native` joined the manifest with You › Payments
> ([#552](https://github.com/Raketa02/Raketa/issues/552)), at the version Expo SDK 52 pins (0.38.6),
> behind the seventh platform port — a native module and a native view, so it needs a development
> build rebuilt with it.
>
> `expo-network` was on this list and has since joined the manifest, with the code that
> wires the online and focus managers ([Part 7](#part-7--tanstack-query)). So have
> `expo-location` and `expo-image-picker`, with the two ports that own them
> ([Part 13](#part-13--native-and-platform)) — added when onboarding's location and photo
> steps were specified, and not one screen earlier. So has
> `react-native-svg`, with the confidence ring — the one drawn object that needs vector
> arcs ([design system 7.8](design-system.md#78-the-confidence-ring)); the level bar beside
> it is still built from Views, and nothing else in the app needs drawing yet. And so has
> `react-native-sse`, with the app's first live surface — pure JS over `XMLHttpRequest`, no
> native module, and therefore nothing for an SDK bump to break
> ([ADR-0147](../../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)
> §4, [the live surface](#the-live-surface)). And so has a feature-flag service —
> Featurevisor, pinned exactly, with AsyncStorage for its saved datafile — with the first gate,
> `find_a_game` ([ADR-0180](../../docs/adr/0180-a-feature-is-turned-on-by-a-pull-request-and-decided-on-the-device.md)),
> folded into `classic_play` by [#550](https://github.com/Raketa02/Raketa/issues/550). The rule it
> carried here still stands, whole: build-time config and runtime product flags stay separate,
> no `if (env === 'production')` is a rollout mechanism, and every flag has an owner, purpose,
> default, rollout strategy and a removal condition — the first three and the last beside its key
> in `features/feature_flags/domain/featureFlags.ts`, the rollout in the flags repo — and is
> deleted after rollout. All of them are
> listed as present rather than pending — this list is what is _missing_, and an entry that
> outlives its own arrival makes the list untrustworthy.

**Strong optional**

- `openapi-fetch` — the typed companion to `openapi-typescript`, if the thin `fetch`
  wrapper starts growing ([Part 4](#part-4--the-http-client)).
- React Hook Form + `@hookform/resolvers` — once a form outgrows local state
  ([Part 9](#part-9--zod-and-validation-boundaries)).
- Analytics SDK — behind the internal interface, never called directly from a feature.
- Persistent storage / SQLite — only under [Part 18](#part-18--offline-and-persistence).

Dependencies are added because of an explicit requirement, never because a boilerplate
includes them.

---

## Part 22 — Upgrades

Expo and React Native move fast; upgrades are routine work, not emergencies. Keep
framework code isolated, avoid abandoned native dependencies, run `expo-doctor` in CI,
track releases, schedule periodic SDK upgrades, test New Architecture compatibility
continuously, use development/preview builds before production, run critical E2E against
the upgrade branch, inspect the native diff `prebuild` generates, and **upgrade
incrementally** — the longer this app sits on SDK 52, the harder the eventual Android/iOS
toolchain jump becomes.

---

## Reference material

**Expo / React Native** —
[SDK 52 release notes](https://expo.dev/changelog/2024-11-12-sdk-52) ·
[RN 0.76 / New Architecture](https://reactnative.dev/blog/2024/10/23/release-0.76-new-architecture) ·
[New Architecture guide](https://docs.expo.dev/guides/new-architecture/) ·
[Auth for SDK 52 and earlier](https://docs.expo.dev/router/advanced/authentication-rewrites/) ·
[Router testing](https://docs.expo.dev/router/reference/testing/) ·
[SecureStore](https://docs.expo.dev/versions/latest/sdk/securestore/) ·
[Environment variables](https://docs.expo.dev/guides/environment-variables/) ·
[Development builds](https://docs.expo.dev/develop/development-builds/introduction/) ·
[CNG](https://docs.expo.dev/workflow/continuous-native-generation/) ·
[Config plugins](https://docs.expo.dev/config-plugins/introduction/) ·
[Doctor / tools](https://docs.expo.dev/develop/tools/) ·
[EAS Update runtime versions](https://docs.expo.dev/eas-update/runtime-versions/) ·
[Update code signing](https://docs.expo.dev/eas-update/code-signing/) ·
[Unit testing](https://docs.expo.dev/develop/unit-testing/) ·
[E2E with Maestro](https://docs.expo.dev/eas/workflows/examples/e2e-tests/) ·
[Sentry](https://docs.expo.dev/guides/using-sentry/) ·
[RN security](https://reactnative.dev/docs/security) ·
[RN performance](https://reactnative.dev/docs/performance) ·
[RN accessibility](https://reactnative.dev/docs/accessibility)

**TanStack Query** —
[React Native](https://tanstack.com/query/latest/docs/framework/react/react-native) ·
[Query keys](https://tanstack.com/query/latest/docs/framework/react/guides/query-keys) ·
[Invalidation](https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation) ·
[Invalidation from mutations](https://tanstack.com/query/latest/docs/framework/react/guides/invalidations-from-mutations) ·
[Updates from mutation responses](https://tanstack.com/query/latest/docs/framework/react/guides/updates-from-mutation-responses) ·
[Optimistic updates](https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates)

**Contract & validation** —
[openapi-typescript](https://openapi-ts.dev/) ·
[openapi-fetch](https://openapi-ts.dev/openapi-fetch/) ·
[Auth middleware](https://openapi-ts.dev/openapi-fetch/middleware-auth) ·
[Zod](https://zod.dev/)

**Zustand** —
[Docs](https://zustand.docs.pmnd.rs/) ·
[Slice pattern](https://zustand.docs.pmnd.rs/learn/guides/slices-pattern) ·
[Selectors](https://zustand.docs.pmnd.rs/learn/guides/auto-generating-selectors)

**Security** —
[OWASP MASVS](https://mas.owasp.org/MASVS/) ·
[Storage](https://mas.owasp.org/MASVS/05-MASVS-STORAGE/) ·
[Authentication](https://mas.owasp.org/MASVS/07-MASVS-AUTH/) ·
[Network](https://mas.owasp.org/MASVS/controls/MASVS-NETWORK-1/)
