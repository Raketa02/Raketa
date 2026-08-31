# `src/shared/` — cross-feature infrastructure

Generic, feature-agnostic building blocks. If something here starts to know about
courts, bookings or matches, it belongs in a feature instead. This is the layer the
source architecture calls `core/` — the framework-facing code, concentrated here so an
Expo SDK upgrade never has to touch a feature.

| Folder               | Holds                                                                                                                                                                                                                                                                                                                                                                                                                                                      |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ui/`                | `theme.ts` — the source of every value — plus the design-system primitives and the reusable `Loading` / `Empty` / `Error` / `Offline` / `Skeleton` states.                                                                                                                                                                                                                                                                                                 |
| `lib/http/`          | The typed fetch layer: base URL, headers, `Authorization`, correlation ID, `AbortSignal`, timeout classes, retry policy, error normalization, 401 → refresh → retry. **The only place `fetch` is configured.**                                                                                                                                                                                                                                             |
| `lib/auth/`          | **The only module that touches `expo-secure-store`.** `tokenManager` (raw values + in-memory mirror) · `refreshCoordinator` (single-flight) · `authService` · `authSession` (the `SessionStatus` machine).                                                                                                                                                                                                                                                 |
| `lib/query-client/`  | The TanStack Query client and its **deliberate** defaults — stale times, gc, retry predicate, `networkMode`, refetch-on-focus.                                                                                                                                                                                                                                                                                                                             |
| `lib/bootstrap/`     | The ordered startup sequence, and the splash gate that hides it.                                                                                                                                                                                                                                                                                                                                                                                           |
| `lib/platform/`      | `appState` (drives Query's `focusManager`) · `networkState` (drives `onlineManager`) · `permissions` · narrow adapters over any native module.                                                                                                                                                                                                                                                                                                             |
| `lib/observability/` | `logger` (structured, redacting) · `analytics` · `telemetry`. The interface features depend on instead of a vendor SDK.                                                                                                                                                                                                                                                                                                                                    |
| `config/`            | `env.ts` — Zod-validated `EXPO_PUBLIC_*` config, failing fast at startup · `appIdentity.ts` — the pure environment → display-name-and-badge table `app.config.ts` calls · `EnvironmentBadge.tsx` — what it draws.                                                                                                                                                                                                                                          |
| `errors/`            | The `AppError` family, the backend-`code` → error mapping, each error's recovery category, and the two sentences no feature's own table can write: `recoveryMessage` under every `code` table, and `offlineMessage` for a query that **paused** — which attempted nothing, produced no `AppError` at all, and so has no category to be read by. `codeMessage` is the lookup those tables share.                                                            |
| `vocabulary/`        | The platform's **closed vocabularies** and the words this app gives them: the four Sports Raketa rates; the nineteen Social tag ids with their labels, names and emoji; the week's seven days and three parts of the day, and what a cell is called; and the one sentence a build says about a code it is too old to read. Each is here on the rule below — a second feature would have written the identical table — rather than on a count of importers. |
| `formatting/`        | How a value is **written**: levels and percentages in the house format (two decimals, decimal comma, whole percents), and `playerName()` — the whole handle, `You` for yourself, which is ADR-0107's rule with one implementation.                                                                                                                                                                                                                         |
| `store/`             | Zustand for **app-wide** UI state only — and only when a feature-scoped store genuinely will not do. One occupant: `toast.store.ts`, the toast queue, which is app-wide because design-system 9.3 requires a single root-level overlay host and a queue inside a feature would be that feature owning every other feature's toasts.                                                                                                                        |

## Rules

- **A vocabulary in `vocabulary/` is the _platform's_, never a feature's reading of it.**
  A tag id and a weekday are served facts that two features spell the same way; the
  sentences a _step_ says about its own rule are that step's, and stayed behind. The test is
  whether a second feature would have written the identical table — not whether two files
  import it.
- **`shared/` never imports a feature.** That reverses the dependency arrow and couples
  every future feature to this one. ESLint enforces it.
- **`lib/auth/` is the single chokepoint for credentials.** No feature, screen or hook
  imports `expo-secure-store`. One module owning the keychain is what makes the token
  lifetime auditable — and it is why the UI can only ever see
  `{ status, userId? }`, never a token value.
- **Never `AsyncStorage` for tokens** — it is unencrypted plaintext on device. ESLint
  blocks the import.
- **`lib/http` is the only place `fetch` is configured,** and the only place the refresh
  rotation lives — so a 401 storm waits on **one** `refreshPromise` instead of firing N
  refreshes that rotate each other out and log the user out at random. A retried request
  is retried exactly once; a second 401 ends the session rather than looping.
- **A rejected refresh and an unreachable one are different events.** Rejected clears
  credentials and caches; unreachable preserves them. Losing signal is not a logout.
- **Logout clears the Query cache** (`cancelQueries()` then `clear()`). Route replacement
  clears nothing, and user A's cached data sitting in memory when user B signs in is a
  privacy bug, not untidiness.
- **Anything in the shipped bundle is public.** `app.config.ts` `extra` and any `EXPO_PUBLIC_*`
  variable can be read out of the binary. Config, never secrets.
- **Server data is never mirrored into a Zustand store.** TanStack Query owns server
  state; Zustand owns UI state — and prefers a feature-scoped store to this one.
- **Nothing here logs a token, an `Authorization` header, a password or a full payload.**
  The logger redacts structurally rather than trusting each call site.
- **Vendor SDKs stay behind `lib/observability`.** Features call `analytics.track(…)` and
  `logger.*`, never Sentry or an analytics client directly. ESLint enforces it.

The full reasoning for every rule above is in
[`docs/architecture.md`](../../docs/architecture.md) — Parts 3–7 and 15.
