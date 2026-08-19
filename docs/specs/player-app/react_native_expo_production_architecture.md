# Production-Ready React Native + Expo Architecture

## Native iOS / Android Player Application

**Target stack**

- Expo SDK 52
- React Native 0.76
- React 18
- TypeScript
- Expo Router
- `expo-secure-store`
- TanStack Query
- Zod
- Zustand
- Jest + `jest-expo`
- `openapi-typescript`
- FastAPI backend over HTTPS
- Access and refresh token authentication

---

# 1. Purpose

This document defines a senior-level, production-ready architecture for a native iOS and Android application built with React Native + Expo + TypeScript.

The application is a real native React Native application. It must not be architected as a WebView application and should not depend on browser-specific architecture patterns for its core functionality.

The architecture is designed for a project that will:

- grow substantially over time;
- contain many independent product features;
- be developed by multiple engineers or teams in parallel;
- evolve together with a FastAPI backend;
- require frequent API changes;
- require strong authentication and session management;
- need predictable testing and release processes;
- need observability in production;
- require controlled native Android/iOS customization;
- remain maintainable through multiple Expo and React Native upgrades.

The primary objective is not to create the maximum possible number of layers. The objective is to create **clear ownership, stable dependency boundaries, predictable data flow, and low-cost change**.

---

# 2. Recommended Architecture in One Sentence

Use a **feature-first modular architecture with lightweight Clean Architecture boundaries**, where:

```text
Expo Router
    ↓
Feature presentation
    ↓
Feature application / query hooks
    ↓
Feature domain logic, when needed
    ↓
Feature API repository / adapter
    ↓
Shared typed HTTP client
    ↓
Generated OpenAPI contract
    ↓
FastAPI backend
```

Cross-cutting infrastructure such as authentication, secure storage, networking, configuration, logging, analytics, and TanStack Query configuration belongs in a small `core` layer.

The architecture must **not** become:

```text
screens/
components/
hooks/
services/
utils/
types/
```

for the entire application.

That structure looks simple initially but becomes increasingly coupled as the application grows because every feature shares the same global buckets.

---

# 3. Version and Platform Context

## 3.1 Expo SDK 52 and React Native 0.76

Expo SDK 52 originally shipped with React Native 0.76.

React Native 0.76 is important because the React Native New Architecture became production-ready and the default architecture for new React Native 0.76 projects.

Expo SDK 52 also enabled the New Architecture by default for newly created Expo projects.

For an existing or upgraded SDK 52 application, verify explicitly whether the New Architecture is enabled instead of assuming that it is.

Recommended rule:

```text
New Architecture = enabled
unless a verified production dependency blocks it.
```

If a dependency blocks the New Architecture, that dependency should be treated as technical debt with a migration plan.

## 3.2 SDK 52 must be treated as an upgradeable baseline

SDK 52 is an older platform baseline. The architecture should therefore minimize direct framework coupling so that Expo and React Native can be upgraded without restructuring product features.

Framework-specific code should be concentrated in:

- `app/`
- `src/core/platform/`
- `src/core/navigation/`
- `src/core/storage/`
- configuration files;
- native/config plugins.

Product domain logic should not care which Expo SDK version is being used.

---

# 4. Architectural Principles

The following rules should be considered non-negotiable.

## 4.1 One source of truth per kind of state

Do not represent the same state simultaneously in multiple systems.

Use:

| State category | Owner |
|---|---|
| Remote/backend data | TanStack Query |
| Authentication credentials | Secure token/session subsystem |
| Logged-in/logged-out session status | Auth/session state |
| Local component UI state | React `useState` / `useReducer` |
| Shared ephemeral UI state | Zustand |
| Form input | Form layer + Zod validation |
| Navigation state | Expo Router |
| Build/environment config | Typed configuration module |

Do not copy TanStack Query server data into Zustand.

Do not put access or refresh tokens into Zustand.

Do not use navigation parameters as a replacement for application state.

---

## 4.2 Dependency direction must be intentional

High-level feature logic must not depend directly on low-level infrastructure details when doing so would make the feature difficult to test or change.

Example:

```text
Feature UI
    ↓
Feature hooks/application logic
    ↓
Feature domain types/rules
    ↓
Feature data adapter
    ↓
Core HTTP client
```

Dependencies should generally flow downward.

Avoid arbitrary imports between unrelated features.

---

## 4.3 Feature ownership is more important than technical buckets

All code primarily belonging to one product capability should remain close to that feature.

For example:

```text
features/
  matches/
  profile/
  clubs/
  bookings/
  payments/
```

Each feature can independently own its:

- API operations;
- query keys;
- query hooks;
- mutations;
- schemas;
- domain rules;
- screens/components;
- feature-specific Zustand state;
- tests.

This makes parallel development substantially safer.

---

## 4.4 Keep abstractions proportional to complexity

Do not create a `UseCase`, `Repository`, interface, mapper, and DTO for every trivial GET endpoint.

Use abstraction where it protects something valuable:

- important business rules;
- API/domain model separation;
- testability;
- complex orchestration;
- multiple data sources;
- feature reuse;
- anticipated backend evolution.

A senior architecture avoids both extremes:

```text
everything directly in the component
```

and:

```text
seven abstraction layers for a simple query
```

---

# 5. Recommended Project Structure

```text
frontend_player/
│
├── app/
│   ├── _layout.tsx
│   │
│   ├── (public)/
│   │   ├── welcome.tsx
│   │   └── ...
│   │
│   ├── (auth)/
│   │   ├── sign-in.tsx
│   │   ├── sign-up.tsx
│   │   └── ...
│   │
│   └── (app)/
│       ├── _layout.tsx
│       ├── (tabs)/
│       │   ├── _layout.tsx
│       │   ├── index.tsx
│       │   └── ...
│       └── ...
│
├── src/
│   │
│   ├── core/
│   │   ├── api/
│   │   │   ├── httpClient.ts
│   │   │   ├── apiError.ts
│   │   │   ├── requestId.ts
│   │   │   └── retryPolicy.ts
│   │   │
│   │   ├── auth/
│   │   │   ├── authService.ts
│   │   │   ├── authSession.ts
│   │   │   ├── tokenManager.ts
│   │   │   ├── refreshCoordinator.ts
│   │   │   └── auth.types.ts
│   │   │
│   │   ├── query/
│   │   │   ├── queryClient.ts
│   │   │   ├── queryDefaults.ts
│   │   │   └── queryLifecycle.ts
│   │   │
│   │   ├── storage/
│   │   │   ├── secureStorage.ts
│   │   │   └── storageKeys.ts
│   │   │
│   │   ├── config/
│   │   │   ├── env.ts
│   │   │   └── appConfig.ts
│   │   │
│   │   ├── errors/
│   │   │   ├── AppError.ts
│   │   │   ├── errorMapper.ts
│   │   │   └── errorReporting.ts
│   │   │
│   │   ├── observability/
│   │   │   ├── logger.ts
│   │   │   ├── analytics.ts
│   │   │   └── telemetry.ts
│   │   │
│   │   ├── platform/
│   │   │   ├── appState.ts
│   │   │   ├── networkState.ts
│   │   │   └── permissions.ts
│   │   │
│   │   └── bootstrap/
│   │       └── bootstrapApp.ts
│   │
│   ├── features/
│   │   ├── matches/
│   │   │   ├── api/
│   │   │   ├── domain/
│   │   │   ├── hooks/
│   │   │   ├── schemas/
│   │   │   ├── store/
│   │   │   ├── ui/
│   │   │   ├── __tests__/
│   │   │   └── index.ts
│   │   │
│   │   ├── profile/
│   │   ├── bookings/
│   │   └── ...
│   │
│   ├── shared/
│   │   ├── ui/
│   │   ├── hooks/
│   │   ├── formatting/
│   │   ├── types/
│   │   └── constants/
│   │
│   └── generated/
│       └── api/
│           └── openapi.d.ts
│
├── __tests__/
│   ├── integration/
│   └── router/
│
├── e2e/
│
├── scripts/
│   └── generate-api-types.*
│
├── app.config.ts
├── eas.json
├── jest.config.*
├── tsconfig.json
└── package.json
```

---

# 6. What Belongs in `app/`

Expo Router makes the file system part of navigation.

The `app/` directory should therefore remain a **routing/composition layer**, not the place where product implementation lives.

Bad:

```tsx
// app/matches/[id].tsx
// 700 lines of fetching, mutations, validation, business logic and UI
```

Good:

```tsx
import { MatchDetailsScreen } from '@/features/matches';

export default function MatchDetailsRoute() {
  return <MatchDetailsScreen />;
}
```

Route files may own:

- route declaration;
- route parameters;
- layouts;
- redirects;
- navigation options;
- provider composition when route-scoped;
- very small route adapters.

They should not own:

- HTTP requests;
- token handling;
- domain calculations;
- large UI components;
- complicated mutations;
- business rules.

This separation makes Expo Router replaceable and keeps feature tests independent of file-based routing.

---

# 7. Navigation Architecture

## 7.1 Route groups

Use route groups to make authorization boundaries visible.

Example:

```text
app/
  (public)/
  (auth)/
  (app)/
```

Suggested semantics:

- `(public)` — content accessible without authentication.
- `(auth)` — sign-in, sign-up, password recovery.
- `(app)` — authenticated application.

## 7.2 SDK 52 authentication guard

Expo Router protected routes were introduced after SDK 52.

For SDK 52, route protection should use redirect-based authorization logic in route layouts.

The root auth decision should be based on an explicit session state:

```ts
type SessionStatus =
  | 'bootstrapping'
  | 'authenticated'
  | 'unauthenticated';
```

Do not model bootstrap as:

```ts
user === undefined
```

because that creates ambiguous states.

## 7.3 Deep links are untrusted input

Every route parameter received from:

- deep links;
- push notifications;
- external URLs;
- QR codes;
- universal links;
- Android App Links;

must be treated as untrusted.

Validate route parameters with Zod before using them.

Example:

```ts
const MatchRouteParamsSchema = z.object({
  id: z.string().uuid(),
});
```

A deep link must never bypass authorization.

The application must first determine:

```text
Is this session authorized?
    ↓
Is this route allowed?
    ↓
Are the route parameters valid?
    ↓
Load feature data
```

---

# 8. Root Provider Composition

The root layout should compose infrastructure only.

Conceptually:

```tsx
<ErrorBoundary>
  <ObservabilityProvider>
    <AuthProvider>
      <QueryClientProvider client={queryClient}>
        <AppLifecycleProvider>
          <ThemeProvider>
            <RouterSlot />
          </ThemeProvider>
        </AppLifecycleProvider>
      </QueryClientProvider>
    </AuthProvider>
  </ObservabilityProvider>
</ErrorBoundary>
```

Do not add a global provider for every feature.

Feature-specific dependencies should preferably be scoped to the feature or represented as plain modules/hooks.

Too many global providers create hidden dependencies and excessive root rerenders.

---

# 9. Application Bootstrap

A production application should have an explicit bootstrap sequence.

Recommended sequence:

```text
Native process starts
      ↓
Initialize crash/error reporting
      ↓
Read and validate public runtime configuration
      ↓
Initialize network/focus integrations
      ↓
Read auth credentials from SecureStore
      ↓
Restore/validate session
      ↓
Initialize authenticated application state
      ↓
Release splash screen
      ↓
Render authenticated or unauthenticated route tree
```

The user should never see the authenticated tree briefly before being redirected.

Likewise, the login screen should not flash while valid credentials are still being restored.

Use a real bootstrap state rather than scattered `isLoading` checks.

---

# 10. API Contract Architecture

## 10.1 FastAPI OpenAPI is the API contract source of truth

FastAPI naturally exposes an OpenAPI schema.

That schema should be the authoritative machine-readable contract between backend and frontend.

Recommended flow:

```text
FastAPI models/routes
      ↓
openapi.json
      ↓
openapi-typescript
      ↓
generated TypeScript API types
      ↓
typed frontend API adapter
```

Do not manually maintain duplicate TypeScript DTO interfaces for backend responses.

Bad:

```ts
interface MatchResponse {
  ...
}
```

if the exact same shape already exists in generated OpenAPI types.

---

## 10.2 Generated code must be isolated

Generated files belong in something like:

```text
src/generated/api/
```

Rules:

- generated files are never manually edited;
- feature code must not scatter complex generated OpenAPI expressions everywhere;
- generated API DTOs should enter features through feature API modules;
- code generation must be deterministic;
- CI must verify that generated types match the backend schema.

---

## 10.3 Recommended contract pipeline

For a monorepo or coordinated repositories:

```text
Backend CI
  → export canonical OpenAPI schema
  → validate OpenAPI
  → frontend code generation
  → TypeScript typecheck
```

An even stronger model is:

```text
backend/openapi.json
        ↓
frontend npm run api:generate
        ↓
git diff --exit-code
```

CI fails when generated types are stale.

This prevents:

```text
backend changed
frontend compiles against old contract
production fails later
```

Do not make a production mobile build depend on a random live development server being reachable to generate types.

Use a versioned schema file or deterministic CI artifact.

---

# 11. HTTP Client

There should be exactly one shared network entry point for the FastAPI backend.

Conceptually:

```text
core/api/httpClient
```

It is responsible for transport concerns, not product logic.

Responsibilities:

- base URL;
- request headers;
- authentication header;
- request correlation ID;
- abort/cancellation support;
- standardized response decoding;
- normalized transport errors;
- refresh-token integration;
- observability hooks;
- safe timeout behavior.

It should **not** know what a match, booking, profile, or club means.

---

# 12. Typed API Layer

`openapi-typescript` provides compile-time types, not runtime validation.

A production architecture should therefore use generated types for the static contract while still validating truly untrusted runtime boundaries where appropriate.

A strong option is to pair `openapi-typescript` with the official companion `openapi-fetch`.

If no additional library is desired, build a very thin typed wrapper around `fetch`.

Do not build a giant custom networking framework.

Feature API modules should look conceptually like:

```ts
export const matchesApi = {
  getMatch,
  listMatches,
  joinMatch,
  leaveMatch,
};
```

Then TanStack Query hooks depend on these operations.

---

# 13. Network Error Model

Raw `fetch` errors and arbitrary backend JSON must not leak into screens.

Define a normalized application error family.

Example:

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

The backend should expose a consistent error envelope, for example:

```json
{
  "code": "MATCH_ALREADY_FULL",
  "message": "The match is already full.",
  "details": {},
  "field_errors": {},
  "trace_id": "..."
}
```

Frontend decisions should primarily depend on stable machine-readable `code`, not human-readable messages.

Bad:

```ts
if (error.message === "Match already full")
```

Good:

```ts
if (error.code === 'MATCH_ALREADY_FULL')
```

Human-readable text can then be localized independently.

---

# 14. HTTP Status Semantics

Use consistent semantics across frontend and FastAPI.

Typical policy:

| Status | Meaning |
|---|---|
| 400 | malformed request |
| 401 | missing/expired/invalid authentication |
| 403 | authenticated but forbidden |
| 404 | entity not found |
| 409 | state conflict |
| 422 | input/domain validation |
| 429 | rate limited |
| 5xx | backend/server failure |

The client must not interpret every 4xx as "log out".

Only authentication-invalidating responses should invalidate the session.

---

# 15. Cancellation and Request Lifecycle

TanStack Query can cancel queries through `AbortSignal`.

The HTTP layer should propagate that signal to `fetch`.

Example concept:

```ts
queryFn: ({ signal }) =>
  matchesApi.getMatch(matchId, { signal })
```

This prevents stale work from continuing unnecessarily after:

- screen changes;
- query replacement;
- user logout;
- parameter changes.

Do not create fire-and-forget fetches inside components.

---

# 16. Retry Strategy

Retries must be centralized and intentional.

## Queries

Safe/idempotent reads may usually retry transient failures.

Examples:

- network interruption;
- selected timeouts;
- selected 5xx responses.

Do not retry:

- 401;
- 403;
- deterministic 4xx validation errors;
- not-found responses when not-found is definitive.

## Mutations

Do **not** globally retry arbitrary mutations.

A mutation may only be safely retried when one of the following is true:

1. the endpoint itself is idempotent;
2. the backend accepts an idempotency key;
3. the operation is explicitly known to be safe to repeat.

This is extremely important for operations involving:

- payments;
- reservations;
- bookings;
- purchases;
- creation of records;
- irreversible actions.

---

# 17. Timeouts

`fetch` should not be allowed to hang indefinitely.

Implement a shared timeout policy using cancellation/AbortController semantics.

Different operation classes can have different thresholds:

```text
normal API request
upload
download
background synchronization
```

Do not scatter hard-coded timeout numbers through features.

---

# 18. Authentication Architecture

Authentication is a cross-cutting subsystem and should be implemented centrally.

Recommended components:

```text
core/auth/
  tokenManager.ts
  refreshCoordinator.ts
  authService.ts
  authSession.ts
```

Responsibilities must be separate.

---

# 19. Token Manager

The token manager owns raw token values.

Components must never read from SecureStore directly.

Bad:

```ts
const token = await SecureStore.getItemAsync('accessToken');
```

inside a screen or query.

Good:

```text
Screen
  ↓
Query
  ↓
HTTP client
  ↓
TokenManager
  ↓
SecureStore
```

The token manager should expose operations such as:

```ts
getAccessToken()
getRefreshToken()
setTokens()
clearTokens()
```

but preferably hide even these details behind the HTTP/auth subsystem.

---

# 20. SecureStore Usage

`expo-secure-store` is appropriate for small secrets such as tokens.

On Android, SecureStore values are encrypted using the Android Keystore-backed mechanism.

On iOS, SecureStore uses Keychain services.

Important production considerations:

1. use asynchronous SecureStore APIs;
2. do not synchronously block the JS thread for token reads;
3. keep payloads small;
4. handle read/write/delete failures;
5. explicitly clear credentials on logout;
6. do not log stored values;
7. do not place tokens in crash reports;
8. do not place tokens in analytics properties.

---

# 21. In-Memory Token Mirror

Reading SecureStore before every request is unnecessary.

A better model is:

```text
App bootstrap
    ↓
Read secure credentials once
    ↓
Create in-memory session
    ↓
HTTP requests read current in-memory access token
    ↓
Token changes are atomically persisted to SecureStore
```

SecureStore remains the persistence mechanism across application restarts.

The in-memory token value is the fast runtime representation.

Raw token data still must not be exposed to components.

---

# 22. Refresh Token Concurrency

This is one of the most important production authentication details.

Imagine ten requests receive `401` at the same time.

Bad architecture:

```text
Request 1 → refresh
Request 2 → refresh
Request 3 → refresh
...
Request 10 → refresh
```

This can cause:

- refresh-token rotation races;
- unnecessary backend load;
- valid refresh tokens being invalidated;
- random logout;
- inconsistent credentials.

Use a **single-flight refresh coordinator**.

Concept:

```ts
let refreshPromise: Promise<Tokens> | null = null;
```

When refresh begins:

```text
first failing request
    ↓
creates refreshPromise
```

Subsequent failing requests:

```text
reuse same refreshPromise
```

After success:

```text
tokens updated atomically
waiting requests retry once
refreshPromise cleared
```

After authentication-invalidating refresh failure:

```text
tokens cleared
query cache cleared
session becomes unauthenticated
```

---

# 23. Retry an Authenticated Request Only Once

The HTTP client must prevent loops such as:

```text
request
→ 401
→ refresh
→ retry
→ 401
→ refresh
→ retry
→ ...
```

A retried request should carry internal metadata indicating that refresh has already been attempted.

If it fails again with an authentication error, terminate the session.

---

# 24. Refresh Failure Classification

Do not log the user out because the device temporarily lost internet connectivity during token refresh.

Differentiate:

```text
Refresh rejected by authentication server
```

from:

```text
Refresh could not reach server
```

Typical behavior:

### Invalid/expired/revoked refresh token

```text
clear credentials
clear private caches
set session unauthenticated
redirect to auth
```

### Temporary network failure

```text
preserve credentials
surface connectivity state
retry according to controlled policy
```

---

# 25. Refresh Token Rotation

If the backend rotates refresh tokens, updating credentials must be atomic.

Conceptually:

```text
old access + old refresh
       ↓
refresh response
       ↓
new access + new refresh
       ↓
persist as one session update
```

Do not update only one half and leave the session inconsistent.

---

# 26. Logout

Logout is a system operation, not merely navigation to `/sign-in`.

A complete logout should perform:

```text
1. optionally revoke server session/refresh token
2. clear token manager memory
3. delete SecureStore credentials
4. cancel active authenticated requests
5. clear authenticated TanStack Query data
6. clear sensitive feature UI state
7. reset auth session state
8. navigate to unauthenticated route tree
```

If the server logout call fails because the network is unavailable, local credentials still need a defined product policy rather than being left accidentally active.

---

# 27. iOS Reinstall Behavior

iOS Keychain data can persist across uninstall/reinstall under some circumstances.

Therefore:

```text
SecureStore token exists
```

must not be treated as proof that a valid backend session exists.

The bootstrap flow should validate or refresh the session.

This also means logout must explicitly remove tokens rather than relying on app uninstall behavior.

---

# 28. Biometric Protection

`SecureStore.requireAuthentication` can add user-authentication requirements, but it must not be applied blindly.

Important trade-off:

A background/silent refresh flow should not unexpectedly trigger biometric authentication every time the app needs a token.

If biometric app locking is desired, model it as a deliberate product/security feature.

For example:

```text
backend session authentication
        +
optional local biometric app unlock
```

rather than making every HTTP token lookup inherently biometric.

Also account for biometric enrollment changes, which can invalidate protected SecureStore entries.

---

# 29. Auth State Is Not the Same as Token State

The UI should consume something like:

```ts
interface AuthState {
  status: 'bootstrapping' | 'authenticated' | 'unauthenticated';
  userId?: string;
}
```

It should not consume:

```ts
{
  accessToken: "...",
  refreshToken: "..."
}
```

Raw credentials belong below the presentation layer.

---

# 30. TanStack Query: Server-State Source of Truth

TanStack Query should own all backend-derived asynchronous state.

Examples:

- player profile;
- match lists;
- match details;
- club details;
- booking status;
- notifications fetched from backend;
- server settings;
- remote feature data.

Do not copy this data into Zustand.

Bad:

```text
GET /matches
→ Query
→ set Zustand matches
→ UI reads Zustand
```

Good:

```text
GET /matches
→ Query cache
→ UI reads query result
```

---

# 31. Query Key Factories

Every feature should centrally define its query keys.

Example:

```ts
export const matchKeys = {
  all: ['matches'] as const,
  lists: () => [...matchKeys.all, 'list'] as const,
  list: (filters: MatchFilters) =>
    [...matchKeys.lists(), filters] as const,
  details: () => [...matchKeys.all, 'detail'] as const,
  detail: (id: string) =>
    [...matchKeys.details(), id] as const,
};
```

Benefits:

- consistent invalidation;
- lower typo risk;
- predictable cache structure;
- easier refactors;
- easier tests.

---

# 32. Query Hooks Belong to Features

Feature code should expose semantic hooks:

```ts
useMatch(id)
useMatches(filters)
useJoinMatch()
useLeaveMatch()
```

rather than making every screen manually construct query options.

This concentrates:

- query keys;
- stale times;
- selection/mapping;
- enabled conditions;
- invalidation behavior;
- mutation callbacks.

---

# 33. Configure Query Defaults Deliberately

Do not accept library defaults without deciding whether they fit the application.

At minimum decide:

- `staleTime`;
- garbage-collection/cache lifetime;
- retry count;
- retry predicate;
- mutation retry policy;
- network mode;
- refetch-on-focus behavior.

Different data classes can have different freshness requirements.

Example:

```text
slow-changing reference data → longer stale time
live match availability      → short stale time
current profile              → moderate stale time
```

Avoid a single global "everything refreshes every 5 seconds" strategy.

---

# 34. React Native Focus Integration

TanStack Query's browser focus assumptions do not automatically represent native app foreground/background behavior.

Integrate TanStack Query's focus manager with React Native `AppState`.

Concept:

```text
App becomes active
      ↓
focusManager.setFocused(true)
```

This allows appropriate stale-query refresh behavior when the application returns to the foreground.

---

# 35. Network Status Integration

Integrate TanStack Query's `onlineManager` with native network state.

Possible implementation dependencies include:

- `expo-network`;
- `@react-native-community/netinfo`.

This gives the query layer awareness of native connectivity changes.

Network awareness is especially important for:

- reconnect behavior;
- paused mutations;
- offline messaging;
- reducing pointless repeated requests.

---

# 36. Cache Isolation Between Users

A serious privacy bug occurs when user A logs out and user B logs in while user A's private Query cache still exists.

On logout/account switch:

```ts
queryClient.cancelQueries()
queryClient.clear()
```

or apply an equivalent explicit cache-partitioning policy.

Never assume that route replacement clears memory state.

---

# 37. Mutation Strategy

Use `useMutation` for server-side state changes.

A mutation should define:

- operation;
- error mapping;
- success behavior;
- related cache update;
- invalidation;
- optimistic behavior when justified;
- retry/idempotency rules.

Example:

```text
join match succeeds
     ↓
update match detail cache
     ↓
invalidate related match lists
     ↓
invalidate player's upcoming matches
```

Cache effects should be deliberate.

---

# 38. Prefer Response-Driven Cache Updates When Possible

If a mutation returns the canonical updated entity, use it.

Example:

```text
PATCH match
→ server returns updated match
→ setQueryData(detailKey, updatedMatch)
```

Then invalidate broader lists when required.

Avoid unnecessary immediate refetches when the mutation response already contains authoritative data.

---

# 39. Optimistic Updates

Optimistic updates are useful but should not be the default.

Use them when:

- perceived latency matters;
- rollback is deterministic;
- conflicting concurrent changes are manageable;
- backend rejection is uncommon.

Avoid them when:

- server business rules are complex;
- inventory/availability changes quickly;
- money is involved;
- rollback would confuse users;
- server response changes several related entities unpredictably.

For these cases, a pending UI state is often safer.

---

# 40. Pagination

For large changing datasets, prefer cursor-based backend pagination.

Frontend query keys must include all server-affecting parameters:

```ts
[
  'matches',
  'list',
  {
    sport,
    level,
    date,
    location,
    cursor
  }
]
```

Never omit a parameter that changes the response from the query key.

---

# 41. Zustand: Strictly UI/Application State

Zustand should not become the application's general-purpose database.

Good uses:

- multi-screen wizard progress;
- temporary filters;
- UI preferences;
- currently selected local context;
- modal coordination;
- non-server transient feature state.

Poor uses:

- API entities;
- token storage;
- backend cache;
- authentication secrets;
- every form field;
- global loading state;
- navigation state.

---

# 42. Local State Before Zustand

Prefer this order:

```text
component-local?
    ↓ yes
useState/useReducer
    ↓ no
feature-local shared?
    ↓ yes
small feature Zustand store
    ↓ no
truly application-wide UI state?
    ↓
shared store only if justified
```

Do not create a global store because it feels convenient.

---

# 43. Small Feature Stores

Prefer:

```text
features/matches/store/matchFiltersStore.ts
features/onboarding/store/onboardingStore.ts
```

over:

```text
store/useAppStore.ts
```

containing hundreds of properties.

Feature stores improve:

- ownership;
- testing;
- tree readability;
- reset behavior;
- parallel development.

---

# 44. Zustand Selectors

Components should subscribe only to the state they need.

Good:

```ts
const selectedSport = useFilterStore(s => s.selectedSport);
```

Avoid subscribing to the complete store when unnecessary.

This limits avoidable rerenders.

---

# 45. Zustand Slices

Use Zustand's slice pattern when a single store becomes genuinely complex.

Do not use slices simply to imitate Redux architecture.

The store should still have a clear bounded purpose.

---

# 46. Side Effects and Zustand

Avoid hiding significant HTTP/network orchestration inside arbitrary store actions.

Server operations belong primarily in API/query/application modules.

Zustand actions should mainly mutate owned local state.

This makes server state ownership obvious.

---

# 47. Zod Architecture

Zod provides runtime validation.

Use it at boundaries where TypeScript cannot guarantee runtime correctness.

Appropriate boundaries include:

- form input;
- route parameters;
- push notification payloads;
- deep links;
- environment variables;
- persisted local data;
- external SDK payloads;
- complex user input;
- selected critical backend payloads.

---

# 48. Do Not Duplicate the Entire OpenAPI Schema Manually in Zod

`openapi-typescript` and Zod solve different problems.

OpenAPI-generated TypeScript types:

```text
compile-time contract
```

Zod:

```text
runtime validation
```

Do not hand-write Zod versions of every generated backend DTO unless there is a clear reason.

That creates two independently maintained API schemas.

If full runtime response validation becomes a requirement, generate runtime schemas from the same authoritative OpenAPI source rather than manually mirroring every model.

---

# 49. Form Validation

A form should generally have one canonical schema.

Example:

```ts
const SignUpSchema = z.object({
  email: z.string().email(),
  password: z.string().min(8),
});
```

Use the schema to produce:

- validation result;
- typed form data;
- field-level errors;
- normalized submit payload where appropriate.

For large forms, consider adding React Hook Form with a Zod resolver rather than building a custom form framework.

---

# 50. Domain Models vs API DTOs

Not every endpoint needs a domain model.

Use a separate domain model when:

- backend representation is unstable;
- several backend fields combine into one domain concept;
- dates/currency/units require normalization;
- business rules operate on the object;
- the UI should not depend on transport naming;
- multiple endpoints produce the same conceptual entity differently.

Example:

```text
MatchApiDto
    ↓ map
Match
```

For trivial read-only models, using generated types directly can be acceptable.

The point is to isolate meaningful domain semantics, not to maximize mapper count.

---

# 51. Business Logic Placement

Business rules must not live in JSX.

Bad:

```tsx
<Button
  disabled={
    match.status === 'OPEN' &&
    match.players.length >= match.maxPlayers &&
    ...
  }
/>
```

when the rule is important and repeated.

Better:

```ts
canJoinMatch(match, player)
```

or:

```ts
getJoinEligibility(match, player)
```

Pure domain functions are:

- easy to test;
- framework-independent;
- reusable;
- explicit;
- safe to change.

---

# 52. Feature Public APIs

Each feature should expose a controlled public surface.

Example:

```text
features/matches/index.ts
```

exports:

```ts
export { MatchDetailsScreen } from './ui/MatchDetailsScreen';
export { useMatch } from './hooks/useMatch';
export type { Match } from './domain/Match';
```

Other features should not import deep private files such as:

```ts
features/matches/api/internal/mappers/privateMapper
```

Use lint/import-boundary rules to enforce this at scale.

---

# 53. Cross-Feature Dependencies

Avoid:

```text
feature A
  ↔
feature B
```

If two features genuinely share a stable concept, move that concept to a shared domain/core location.

Do not move code into `shared` merely because two files import it once.

Shared code has a higher maintenance cost because every feature may become coupled to it.

A good rule is:

```text
keep code local until its cross-feature ownership is proven
```

---

# 54. Shared UI / Design System

Reusable design primitives should live outside product features.

Examples:

```text
shared/ui/
  Button
  Text
  Card
  Input
  Modal
  Screen
  EmptyState
  ErrorState
  Skeleton
```

Use design tokens for:

- spacing;
- typography;
- border radius;
- colors;
- shadows;
- interaction states.

Avoid hard-coded visual values scattered across feature screens.

---

# 55. Accessibility

Accessibility is part of production quality.

Every reusable UI component should support:

- VoiceOver;
- TalkBack;
- accessibility labels;
- accessibility roles;
- scalable text where appropriate;
- sufficient touch targets;
- logical focus order;
- dynamic state announcements when necessary.

Accessibility behavior should be tested on both Android and iOS because platform semantics differ.

---

# 56. Internationalization Readiness

Even if the first release supports one language, do not build business logic around user-visible strings.

Bad:

```ts
if (status === 'Cancelled')
```

Good:

```ts
status === MatchStatus.Cancelled
```

Translate only at the presentation boundary.

Dates, numbers, currency, and pluralization should be formatted through central utilities.

---

# 57. Date and Time Architecture

Mobile/backend systems commonly fail around time zones.

Recommended rules:

- backend stores authoritative timestamps;
- API transmits ISO-8601 values;
- distinguish timestamps from local calendar dates;
- do not silently parse date-only strings as UTC timestamps;
- centralize date parsing/formatting;
- never make business decisions from localized display strings.

If a rule depends on the backend's authoritative clock, do not trust the user's manually changed device time.

---

# 58. Environment Configuration

Use environment configuration for values such as:

- API base URL;
- environment name;
- public analytics identifiers;
- public feature-service identifiers.

Validate configuration at startup.

Example:

```ts
const EnvSchema = z.object({
  EXPO_PUBLIC_API_URL: z.string().url(),
  EXPO_PUBLIC_ENV: z.enum(['development', 'staging', 'production']),
});
```

Fail fast in development/CI for invalid configuration.

---

# 59. Never Put Secrets in the Mobile Bundle

Anything compiled into the application can be extracted.

Therefore never put:

- private API keys;
- backend credentials;
- signing secrets;
- encryption master keys;
- privileged service credentials;

inside:

- TypeScript;
- `.env` exposed to the client;
- `EXPO_PUBLIC_*`;
- app config fields shipped to the bundle.

`EXPO_PUBLIC_*` values are public by definition.

Real secrets belong on trusted servers.

---

# 60. Environment Separation

Maintain explicit application environments such as:

```text
development
staging
production
```

Prefer separate:

- API hosts;
- app identifiers/bundle IDs when useful;
- analytics environments;
- monitoring environments;
- EAS build profiles;
- update channels.

A production build must never accidentally point to staging.

Add CI validation for this.

---

# 61. Native Build Variants

Use development and preview builds rather than treating Expo Go as the production development environment.

Expo Go is useful for fast experiments, but a production application should regularly run in a real development build containing its actual native dependencies.

Typical environments:

```text
development build
preview/internal build
production build
```

---

# 62. Continuous Native Generation

For a greenfield Expo application, prefer Continuous Native Generation unless the project has a concrete reason to manually maintain native projects.

In a CNG model:

```text
app.config.ts
+ config plugins
+ dependencies
       ↓
expo prebuild
       ↓
android/
ios/
```

Avoid manual edits to generated native files because they can be overwritten on regeneration.

Native configuration should be expressed through:

- Expo app config;
- official config plugins;
- local config plugins when necessary.

---

# 63. Native Code Boundary

If native code becomes necessary, expose it through a narrow TypeScript-facing interface.

Feature code should depend on:

```ts
LocationService
PaymentNativeBridge
BiometricService
```

rather than importing native modules throughout the UI.

This makes:

- testing easier;
- Android/iOS differences explicit;
- native replacements safer;
- Expo upgrades easier.

---

# 64. Platform-Specific Files

Use platform files only when behavior truly differs.

Example:

```text
share.ts
share.ios.ts
share.android.ts
```

Do not scatter:

```ts
if (Platform.OS === 'ios')
```

through every feature.

Concentrate platform differences behind adapters.

---

# 65. Security Baseline

Use OWASP MASVS as a mobile security verification baseline.

At minimum, explicitly review:

- secure storage;
- authentication;
- authorization;
- network security;
- data leakage;
- logging;
- privacy;
- platform interaction;
- code integrity;
- resilience as required by the threat model.

---

# 66. HTTPS Only

Production API traffic must use HTTPS.

Do not disable platform TLS verification.

Do not ship permissive development trust settings into production.

Certificate pinning may be considered for higher-risk applications, but it introduces certificate rotation and operational complexity and therefore requires an explicit lifecycle plan.

---

# 67. Backend Authorization Is Mandatory

Mobile UI authorization is not a security boundary.

Hiding a button does not authorize an operation.

Every protected FastAPI operation must validate:

```text
identity
+
authorization
+
resource ownership / permissions
```

on the backend.

The mobile app may prevent obviously invalid actions for UX, but the server remains authoritative.

---

# 68. Sensitive Logging

Never log:

- access tokens;
- refresh tokens;
- passwords;
- authorization headers;
- payment credentials;
- personal data unless explicitly approved;
- full backend payloads by default.

Create a structured logger with redaction.

Production logging should be significantly stricter than development logging.

---

# 69. Screenshots and Background Privacy

For applications with sensitive screens, evaluate:

- Android secure-window flags;
- iOS app-switcher privacy overlays;
- masking sensitive values;
- clipboard policies.

Do this based on threat model rather than applying it indiscriminately.

---

# 70. Root/Jailbreak Detection

Do not assume root/jailbreak detection makes a mobile app secure.

It can be a risk signal, not a fundamental authorization mechanism.

Critical security decisions remain on the backend.

---

# 71. App/Device Attestation

For high-risk backend operations, consider platform app/device attestation where appropriate.

This can help the backend identify requests originating from recognized application instances.

Treat attestation as an additional signal, not a replacement for user authentication and authorization.

---

# 72. Performance Architecture

React Native performance should be measured on real production-like builds.

Development mode is not a reliable performance benchmark.

Monitor:

- cold startup;
- warm startup;
- time to interactive;
- JS thread stalls;
- slow renders;
- navigation latency;
- network waterfalls;
- list scrolling;
- image memory;
- crash-free sessions.

---

# 73. Keep the JavaScript Thread Responsive

Avoid large synchronous work on the JS thread.

Examples:

- parsing huge payloads repeatedly;
- expensive array transforms during render;
- synchronous secure-storage operations;
- heavy crypto in JS;
- large JSON serialization loops;
- unnecessary rerenders.

Move expensive work:

- outside render;
- into memoized/precomputed stages when measurement justifies it;
- to native/background mechanisms when appropriate;
- to the backend when it is fundamentally server work.

---

# 74. Rendering Discipline

Do not apply `memo`, `useMemo`, and `useCallback` everywhere blindly.

Use profiling to identify actual rerender costs.

Senior performance work follows:

```text
measure
→ identify bottleneck
→ optimize
→ measure again
```

Avoid speculative optimization that increases complexity without measurable improvement.

---

# 75. Large Lists

For large datasets:

- use virtualized lists;
- provide stable item keys;
- avoid inline heavyweight row work;
- paginate backend data;
- avoid rendering entire datasets;
- keep list row state minimal.

If list scale justifies it, evaluate a high-performance list implementation such as FlashList compatible with the selected Expo version.

---

# 76. Images

Images can dominate memory and bandwidth.

Define a strategy for:

- thumbnail sizes;
- server-side resizing;
- aspect ratio;
- placeholders;
- cache behavior;
- retry behavior;
- large image avoidance;
- upload compression when required.

Do not download full-resolution originals when a small card image is sufficient.

---

# 77. Query Waterfalls

Avoid:

```text
request A
wait
request B
wait
request C
```

when B and C can run independently.

Use parallel queries or backend aggregation when appropriate.

Network architecture is part of frontend performance architecture.

---

# 78. Observability

Production applications require visibility after release.

At minimum implement:

- crash reporting;
- JavaScript error reporting;
- native crash reporting;
- release/build identification;
- API failure metrics;
- navigation/performance traces for important flows;
- structured breadcrumbs;
- correlation IDs.

Sentry is one Expo-supported option.

The exact vendor can change; the architecture should depend on an internal observability interface rather than vendor calls scattered throughout features.

---

# 79. Correlation IDs

Every client request should preferably carry or receive a request/trace identifier.

When FastAPI returns:

```json
{
  "trace_id": "abc123"
}
```

the mobile client can include the same identifier in its error report.

This lets developers correlate:

```text
mobile failure
↔
backend request
↔
server logs
```

without logging sensitive payloads.

---

# 80. Observability Context

Error reports should include safe metadata such as:

- application version;
- native build number;
- runtime/update version;
- environment;
- operating system;
- route name;
- feature;
- anonymous/internal user identifier if privacy rules allow;
- trace ID.

Never attach tokens.

---

# 81. Analytics Architecture

Analytics events should pass through one internal interface.

Example:

```ts
analytics.track('match_join_started', {
  matchId,
});
```

Feature code should not call a specific analytics SDK directly everywhere.

This enables:

- vendor replacement;
- centralized consent;
- PII filtering;
- event naming governance;
- testing.

---

# 82. Analytics Event Governance

Create an event catalog.

Each event should define:

```text
event name
owner
trigger
properties
property types
PII classification
expected business meaning
```

Do not allow arbitrary event names created ad hoc by every engineer.

---

# 83. Error Boundaries

Use React error boundaries around meaningful UI scopes.

At minimum:

- application/root boundary;
- optionally feature/screen boundaries for recoverable sections.

A root crash screen should provide:

- safe fallback UI;
- retry/restart path where possible;
- error report;
- no raw stack traces in production.

Error boundaries do not replace promise/network error handling.

---

# 84. Loading and Error UX

Every server-driven screen should intentionally model:

```text
initial loading
loaded
empty
refreshing
recoverable error
terminal error
offline/stale
```

Avoid generic:

```ts
if (isLoading) return <Spinner />;
if (error) return <Text>Error</Text>;
```

for important product flows.

Design reusable states:

```text
LoadingState
EmptyState
ErrorState
OfflineBanner
Skeleton
```

---

# 85. Testing Strategy

Use a testing pyramid rather than relying on one type of test.

Recommended layers:

```text
many pure unit tests
       ↓
feature/component tests
       ↓
integration tests
       ↓
smaller number of E2E tests
```

---

# 86. Unit Tests

Use Jest for:

- domain rules;
- mappers;
- schemas;
- formatters;
- query-key factories;
- auth refresh coordinator;
- error mapping;
- feature store logic.

Pure business logic should be testable without rendering React.

---

# 87. Component Tests

Add/use React Native Testing Library with `jest-expo`.

Test behavior:

```text
given state
when user performs action
then visible behavior changes
```

Prefer assertions based on what the user can observe.

Avoid testing implementation details such as internal state variables.

---

# 88. Expo Router Tests

Keep tests outside the `app/` directory.

Use Expo Router testing utilities for:

- redirects;
- authenticated route boundaries;
- deep-link routes;
- route parameters;
- navigation behavior.

Critical authorization routing deserves integration tests.

---

# 89. Authentication Concurrency Tests

Explicitly test:

### Multiple simultaneous 401 responses

Expected:

```text
only one refresh request
all waiting requests reuse result
```

### Refresh rejected

Expected:

```text
single logout transition
tokens cleared
cache cleared
```

### Refresh network timeout

Expected:

```text
session not incorrectly destroyed
```

### Retried request returns 401

Expected:

```text
no infinite refresh loop
```

These tests catch production bugs that ordinary login tests miss.

---

# 90. Query Integration Tests

Test:

- correct query key;
- correct enabled conditions;
- cache update after mutation;
- invalidation after mutation;
- optimistic rollback if used;
- user-cache cleanup on logout;
- offline/focus behavior where important.

---

# 91. Contract Tests

API compatibility should be tested in CI.

At minimum:

```text
export FastAPI OpenAPI
→ generate TypeScript
→ typecheck frontend
```

For critical endpoints, backend/frontend integration tests may additionally verify concrete payloads.

Contract drift should fail before merge, not after release.

---

# 92. E2E Tests

Jest is not sufficient for production confidence.

Add an E2E solution such as Maestro or an equivalent mature native mobile E2E framework.

Cover a small number of critical journeys:

```text
launch
sign in
session restoration
core navigation
one primary business flow
logout
deep link
```

Do not try to express the entire application test suite as E2E tests.

---

# 93. Real Device / Platform Testing

A cross-platform React Native app still requires platform-specific testing.

Release qualification should include:

- Android emulator;
- representative physical Android device;
- iOS simulator;
- representative physical iPhone;
- low/mid-range Android performance testing where relevant.

Do not assume "works on iOS simulator" means "works on Android device."

---

# 94. Snapshot Testing

Snapshots can be useful in narrow cases but should not be the primary testing strategy.

Large snapshots tend to:

- produce noisy diffs;
- be updated without review;
- test implementation structure instead of behavior.

Use explicit behavioral assertions for important logic.

---

# 95. CI Pipeline

A production pull request pipeline should approximately run:

```text
install dependencies with lockfile
      ↓
lint
      ↓
format check
      ↓
TypeScript typecheck
      ↓
OpenAPI generation/drift check
      ↓
unit tests
      ↓
component/integration tests
      ↓
Expo Doctor / dependency validation
      ↓
build/config validation
```

Selected branches can additionally run:

```text
Android development/preview build
iOS development/preview build
E2E smoke tests
```

---

# 96. Lockfile Discipline

The lockfile must be committed.

CI should use a frozen/immutable dependency install.

Avoid dependency resolution changing between developer machines and CI.

---

# 97. Dependency Installation

For Expo/native-compatible dependencies, prefer Expo's installation command where appropriate so compatible native versions are selected.

New dependencies should be evaluated for:

- Expo SDK 52 compatibility;
- React Native 0.76 compatibility;
- New Architecture compatibility;
- maintenance health;
- native code requirements;
- config plugin requirements;
- license;
- bundle impact;
- security history.

Run Expo Doctor in CI.

---

# 98. Dependency Governance

Do not allow uncontrolled library growth.

Before adding a dependency, ask:

1. Is the functionality difficult enough to justify it?
2. Is the project maintained?
3. Does it support the New Architecture?
4. Does it require native configuration?
5. What is its bundle/runtime cost?
6. Does it duplicate an existing dependency?
7. Can it be upgraded independently?
8. Is the license acceptable?

---

# 99. TypeScript Standards

Enable strict TypeScript settings.

At minimum aim for:

```json
{
  "strict": true,
  "noUncheckedIndexedAccess": true
}
```

where compatible with the existing codebase.

Avoid:

```ts
any
```

except at tightly controlled interoperability boundaries.

Prefer:

```ts
unknown
```

for untrusted data and refine it through Zod/type guards.

---

# 100. Avoid Type Assertions as Validation

Bad:

```ts
const response = json as Match;
```

This performs no runtime validation.

Type assertions should not be used to silence uncertain boundaries.

Either:

- rely on the generated trusted API contract where appropriate;
- or validate untrusted runtime values.

---

# 101. Naming

Use names that encode architectural meaning.

Good:

```text
getMatch
useMatch
joinMatch
MatchApiDto
Match
MatchError
matchKeys
```

Avoid generic names:

```text
handleData
service
helper
manager2
common
misc
utils2
```

---

# 102. Avoid the `utils` Dumping Ground

Generic `utils/` folders tend to become dependency magnets.

Prefer semantic locations:

```text
formatting/
date/
currency/
validation/
logging/
```

A utility should have an obvious owner.

---

# 103. Code Formatting and Linting

Use automated:

- ESLint;
- Prettier or equivalent formatting;
- import ordering if desired;
- unused-code checks;
- dependency-boundary checks.

Formatting and linting should run in CI.

Do not make style conformity dependent on manual review.

---

# 104. Module Boundary Enforcement

As the team grows, architectural boundaries should be machine-enforced.

Useful rules:

- feature may not deep-import another feature;
- generated code cannot import product code;
- core cannot import features;
- shared cannot depend on features;
- route layer may import feature public APIs;
- feature UI cannot import SecureStore directly;
- feature UI cannot import generated OpenAPI internals directly if adapters are required.

Use ESLint import restrictions or equivalent tooling.

Architecture that exists only in documentation will eventually be violated.

---

# 105. Circular Dependencies

Circular dependencies should fail CI or be treated as defects.

They usually indicate:

- unclear ownership;
- cross-feature coupling;
- misplaced shared code;
- poorly defined interfaces.

Do not accept them as normal in a large TypeScript codebase.

---

# 106. Feature Flags

A scalable application needs a feature-flag strategy.

Do not hard-code:

```ts
if (env === 'production') {
  ...
}
```

for gradual product rollouts.

Use a controlled feature configuration system when product complexity requires it.

Separate:

```text
build-time configuration
```

from:

```text
runtime product feature flags
```

A flag should have:

- owner;
- purpose;
- default;
- rollout strategy;
- removal date/condition.

Old flags should be removed after rollout.

---

# 107. Backward-Compatible Backend Evolution

Mobile clients cannot all update instantly.

Therefore FastAPI must remain compatible with older released app versions for a defined support window.

Avoid removing or changing fields in ways that immediately break installed clients.

Prefer additive API evolution.

For breaking changes:

- version the endpoint/schema;
- maintain transition period;
- measure active client versions;
- force upgrades only when product/security requirements justify it.

Mobile architecture must assume multiple client versions exist in production simultaneously.

---

# 108. Client Capability Versioning

For selected backend behavior, send safe client metadata such as:

```text
app version
build number
platform
```

This can help backend observability and controlled compatibility behavior.

Do not make the backend depend on arbitrary user-agent parsing when explicit headers are clearer.

---

# 109. API Versioning

Do not version every endpoint preemptively.

Introduce API version boundaries when actual breaking-contract requirements appear.

The more important principle is:

```text
published mobile clients are immutable from the backend's perspective
```

Once a version is in app stores, the backend must assume it may continue making requests for a long time.

---

# 110. OTA / EAS Update Strategy

If using EAS Update, updates must respect native-code compatibility.

Use an explicit `runtimeVersion` policy.

Key rule:

```text
JavaScript update compatible with installed native runtime
    → OTA possible

native dependency/configuration changed
    → new native build required
```

Never push JavaScript that expects native code absent from the installed binary.

---

# 111. OTA Release Safety

Production OTA updates should use:

- separate channels/environments;
- staged internal validation;
- release notes;
- monitoring after rollout;
- rollback strategy;
- runtime version discipline.

For higher-security requirements, evaluate EAS Update code signing.

---

# 112. Versioning

Track separately:

- user-facing app version;
- Android version code;
- iOS build number;
- Expo runtime/update version.

Observability reports must identify the exact binary and update combination.

Otherwise a crash cannot reliably be tied to deployed code.

---

# 113. Release Pipeline

Recommended:

```text
merge to main
    ↓
CI verification
    ↓
preview/internal build
    ↓
automated smoke/E2E
    ↓
QA/product validation
    ↓
production candidate
    ↓
store submission
    ↓
staged rollout where available
    ↓
production monitoring
```

Do not make developer laptops the only source of production binaries.

Builds must be reproducible and CI-controlled.

---

# 114. Secrets in CI

Build signing credentials and CI service secrets must use secure CI/EAS secret management.

Do not commit them.

Remember:

```text
build-time secret
```

does not automatically mean:

```text
safe to embed in client bundle
```

If client-side JS needs the value at runtime, assume the user can extract it.

---

# 115. Crash-Free Release Gates

For mature production operation, define release health metrics.

Examples:

- crash-free sessions;
- ANR rate;
- startup regression;
- API error rate;
- authentication failure rate;
- core-flow completion rate.

A release should be stopped or rolled back when agreed thresholds regress materially.

---

# 116. Source Maps

Production JS errors need correctly uploaded source maps.

Without them, minified stack traces are far less useful.

Integrate source-map upload into the build/update pipeline rather than depending on manual steps.

---

# 117. Privacy

Define a data classification policy.

Examples:

```text
public
internal
personal
sensitive
credential
```

Every storage, logging, analytics, and monitoring decision should follow this classification.

Data collection should be minimized to what the feature and observability actually require.

---

# 118. Data Retention

Frontend telemetry and analytics should have explicit retention and deletion policies through the chosen vendors and backend systems.

Do not collect data simply because an SDK makes it easy.

---

# 119. Network Data Minimization

Do not fetch large objects when screens use three fields if the backend can provide a suitable representation.

For highly scaled systems, API design and client performance are linked.

Use purpose-appropriate response models.

---

# 120. Background Work

If later features require background execution, treat it as native platform-constrained functionality.

Do not assume a JavaScript timer continues reliably while the application is backgrounded.

Use Expo/native background APIs designed for the use case.

The backend should handle work that does not fundamentally need to happen on-device.

---

# 121. Push Notifications

When push notifications are added:

- treat payloads as untrusted;
- do not put sensitive content in notification payloads unnecessarily;
- validate deep-link targets;
- authorize the destination after app open;
- centralize notification routing;
- support token rotation;
- synchronize push token lifecycle with backend.

Push notification receipt must not directly mutate critical business state without backend confirmation.

---

# 122. Permissions

Permissions should be requested:

```text
just in time
```

when the user understands why the feature needs them.

Do not request every permission at first launch.

Centralize permission handling and distinguish:

- not requested;
- granted;
- denied;
- permanently denied/requires settings.

Android and iOS behaviors differ.

---

# 123. Offline Strategy

Do not claim the app is offline-first unless the architecture truly supports local authoritative data and conflict resolution.

With the declared stack, the default model should be:

```text
network-backed application
+
in-memory query cache
+
graceful offline UX
```

If true offline operation becomes a product requirement, introduce a persistent local data layer deliberately.

Do not misuse Zustand as an offline database.

---

# 124. Persistent Query Cache

Persisting TanStack Query cache can improve launch/offline behavior, but it should be added only when requirements justify it.

If added:

- use an appropriate persistent storage adapter;
- define cache version/migrations;
- define maximum age;
- exclude sensitive data when necessary;
- clear user-scoped cache on logout;
- handle schema changes.

Do not store arbitrary query cache inside SecureStore. SecureStore is intended for small secrets, not general application caching.

---

# 125. Database Introduction Criteria

Introduce SQLite or another local database when the product requires:

- true offline workflows;
- large structured local datasets;
- durable operation queues;
- complex local queries;
- conflict resolution;
- reliable persistence beyond query cache.

Do not introduce a database merely because "production apps need one."

---

# 126. Domain Concurrency

For backend business operations, the server remains responsible for concurrency correctness.

The frontend may show optimistic state, but cannot guarantee uniqueness or availability.

Examples:

```text
two users take final seat
two devices submit same operation
same user taps twice
retry after timeout
```

The backend must enforce invariants transactionally.

The client should support idempotency and map conflict responses cleanly.

---

# 127. Prevent Duplicate User Actions

Critical mutation buttons should have intentional duplicate-submit behavior.

Possibilities:

- disable while mutation is pending;
- attach idempotency key;
- deduplicate operation;
- allow multiple operations only when semantically valid.

Do not rely exclusively on button disabling for correctness.

Backend idempotency is stronger.

---

# 128. Loading State Granularity

Do not use one global spinner for every network operation.

Differentiate:

```text
screen initial load
pull-to-refresh
background refresh
button mutation
pagination load-more
```

The UI should remain usable when background refresh is happening.

---

# 129. Skeletons vs Spinners

Use skeletons when layout is known and initial perceived performance matters.

Use localized activity indicators for localized actions.

Avoid blocking the entire screen for small mutations unless the operation genuinely requires it.

---

# 130. App Lifecycle

Centralize important app lifecycle handling.

Examples:

```text
foreground
background
inactive
```

Use it for:

- Query focus state;
- optional session freshness checks;
- privacy screen behavior;
- observability;
- reconnect logic.

Do not register dozens of independent AppState listeners across unrelated screens.

---

# 131. Error Recovery

Every error should fall into an intentional category:

```text
retryable automatically
retryable by user
requires new authentication
requires user correction
business conflict
terminal/unsupported
```

This prevents random behavior such as showing the same generic modal for every failure.

---

# 132. Domain Error Localization

Backend error messages are useful for diagnostics but should not be the primary localization source.

Prefer:

```text
backend error code
      ↓
frontend localized user message
```

The backend may still send a safe fallback message.

---

# 133. API Schema Compatibility and Zod

A senior approach is:

```text
OpenAPI = API schema source of truth
TypeScript generation = static safety
Zod = runtime validation at selected boundaries
```

Not:

```text
OpenAPI schema
+
manual API interfaces
+
manual Zod copy
+
manual mapper copy
```

unless each layer has a concrete reason.

---

# 134. Recommended Feature Template

A medium-complexity feature can follow:

```text
features/matches/
├── api/
│   ├── matchesApi.ts
│   └── matchMapper.ts
├── domain/
│   ├── Match.ts
│   ├── matchRules.ts
│   └── matchErrors.ts
├── hooks/
│   ├── matchKeys.ts
│   ├── useMatch.ts
│   ├── useMatches.ts
│   └── useJoinMatch.ts
├── schemas/
│   └── matchFilters.schema.ts
├── store/
│   └── matchFilters.store.ts
├── ui/
│   ├── MatchDetailsScreen.tsx
│   ├── MatchCard.tsx
│   └── MatchList.tsx
├── __tests__/
└── index.ts
```

For a simple feature, omit layers that add no value.

---

# 135. Example Feature Data Flow

```text
MatchDetailsRoute
        ↓
MatchDetailsScreen
        ↓
useMatch(matchId)
        ↓
TanStack Query
        ↓
matchesApi.getMatch()
        ↓
shared HTTP client
        ↓
auth middleware
        ↓
FastAPI
        ↓
generated response type
        ↓
optional API→domain mapping
        ↓
Query cache
        ↓
screen
```

For a mutation:

```text
Join button
    ↓
useJoinMatch()
    ↓
matchesApi.joinMatch()
    ↓
FastAPI
    ↓
canonical updated response
    ↓
update detail cache
    ↓
invalidate relevant lists
```

---

# 136. Example Authentication Data Flow

```text
App starts
    ↓
Auth bootstrap
    ↓
SecureStore
    ↓
TokenManager
    ↓
Session validation/refresh
    ↓
authenticated
    ↓
Expo Router authenticated group
```

Request:

```text
Query
  ↓
HTTP client
  ↓
TokenManager access token
  ↓
FastAPI
```

Expired access token:

```text
401
 ↓
RefreshCoordinator
 ↓
single refresh request
 ↓
new token pair
 ↓
TokenManager + SecureStore
 ↓
original request retried once
```

Refresh rejected:

```text
clear tokens
clear private query cache
set unauthenticated
redirect
```

---

# 137. Recommended Missing Production Dependencies / Capabilities

The declared stack is a strong base, but a production application will normally need several additional capabilities.

Evaluate adding:

## Essential or near-essential

- `@testing-library/react-native` — component behavior tests.
- `expo-network` or `@react-native-community/netinfo` — native network state for Query.
- crash/error monitoring such as Sentry or BugSnag.
- ESLint.
- Prettier or equivalent formatter.
- an E2E framework such as Maestro.
- a form library such as React Hook Form if forms become complex.

## Strong optional additions depending on requirements

- `openapi-fetch` — thin type-safe HTTP client companion to `openapi-typescript`.
- persistent storage / SQLite — only for true offline requirements.
- feature flag SDK/service — when staged rollout becomes necessary.
- analytics SDK — behind an internal analytics abstraction.
- performance monitoring — for production startup/render monitoring.

Dependencies should be introduced because of explicit requirements, not because a boilerplate includes them.

---

# 138. Architecture Rules for AI-Agent Development

If AI agents will implement large parts of the application, architectural boundaries must be even more explicit.

Agents tend to optimize locally unless repository rules constrain them.

Create repository-level rules that state:

```text
1. app/ files are route adapters only.
2. server data belongs in TanStack Query.
3. Zustand cannot store API entities or credentials.
4. SecureStore is accessed only through core/storage/auth.
5. all API operations pass through the shared HTTP client.
6. API types come from generated OpenAPI.
7. feature code may not edit generated types.
8. feature code may not deep-import other features.
9. business rules must not be duplicated across UI components.
10. critical mutations must define retry/idempotency behavior.
11. every new endpoint must include error mapping.
12. every feature includes tests for its important domain rules.
13. route/deep-link input is runtime validated.
14. no secrets are placed in EXPO_PUBLIC variables.
15. new native dependencies must be checked for SDK/New Architecture compatibility.
```

These rules should exist in:

- contributor documentation;
- agent instructions;
- lint rules where possible;
- templates/generators;
- CI.

Do not rely only on prompts to preserve architecture.

---

# 139. Pull Request Architecture Checklist

Every significant PR should answer:

- Which feature owns this code?
- Is remote state stored only in Query?
- Is UI state local unless sharing is required?
- Are API types generated rather than duplicated?
- Is new runtime input validated?
- Are tokens inaccessible to UI code?
- Are errors normalized?
- Is retry behavior safe?
- Are cache invalidations defined?
- Could this introduce a user-data cache leak after logout?
- Is the feature accessible?
- Are Android and iOS differences handled?
- Does the change require a native rebuild?
- Is the Expo SDK/New Architecture dependency compatible?
- Are tests added at the correct level?
- Is telemetry safe and non-sensitive?
- Does backend compatibility with older clients remain intact?

---

# 140. Definition of Done for a Production Feature

A feature is not complete when the screen visually works.

A production Definition of Done should include where applicable:

```text
[ ] route/navigation implemented
[ ] API contract generated and current
[ ] backend errors mapped
[ ] domain rules tested
[ ] query keys defined
[ ] stale/retry policy defined
[ ] mutation invalidation/update defined
[ ] loading state designed
[ ] empty state designed
[ ] error state designed
[ ] offline behavior considered
[ ] duplicate-submit behavior considered
[ ] authorization enforced server-side
[ ] route/deep-link params validated
[ ] accessibility implemented
[ ] analytics events defined if needed
[ ] crash/error breadcrumbs added where useful
[ ] no sensitive logging
[ ] Android tested
[ ] iOS tested
[ ] component/integration tests added
[ ] E2E critical path updated when appropriate
[ ] monitoring impact considered
[ ] backward API compatibility considered
```

---

# 141. Anti-Patterns to Explicitly Ban

## Architecture

Do not create one global:

```text
services/
hooks/
types/
store/
utils/
```

for all features.

## Networking

Do not call `fetch` directly from random components.

## Authentication

Do not read SecureStore from components.

Do not expose tokens through React props.

Do not store tokens in Zustand.

Do not refresh separately for every 401.

## Query

Do not duplicate Query data into Zustand.

Do not globally retry all mutations.

Do not use random string query keys throughout components.

## OpenAPI

Do not manually edit generated files.

Do not create parallel hand-maintained API interfaces without reason.

## Zod

Do not pretend TypeScript assertions are runtime validation.

Do not manually duplicate every OpenAPI model in Zod unless deliberately required.

## Navigation

Do not put substantial feature implementation inside route files.

Do not trust deep-link parameters.

## Security

Do not place private keys in `EXPO_PUBLIC_*`.

Do not log authorization headers.

Do not rely on hidden UI controls for authorization.

## Performance

Do not optimize without profiling.

Do not do large synchronous work during render.

## Native

Do not repeatedly hand-edit generated `android/` and `ios/` files in a CNG architecture.

## Testing

Do not rely entirely on snapshots.

Do not leave authentication concurrency untested.

---

# 142. Recommended Dependency Graph

```text
┌────────────────────────────────────┐
│             app/ router            │
└─────────────────┬──────────────────┘
                  │
                  ▼
┌────────────────────────────────────┐
│          feature presentation      │
│ screens / feature components       │
└─────────────────┬──────────────────┘
                  │
                  ▼
┌────────────────────────────────────┐
│ feature hooks / application logic  │
│ query hooks / orchestration        │
└─────────┬─────────────────┬────────┘
          │                 │
          ▼                 ▼
┌────────────────┐   ┌────────────────┐
│ feature domain │   │ feature Zustand│
│ rules/models   │   │ UI state only  │
└───────┬────────┘   └────────────────┘
        │
        ▼
┌────────────────────────────────────┐
│          feature API adapter       │
└─────────────────┬──────────────────┘
                  │
                  ▼
┌────────────────────────────────────┐
│ core HTTP/auth/error infrastructure│
└─────────────────┬──────────────────┘
                  │
                  ▼
┌────────────────────────────────────┐
│ generated OpenAPI TypeScript types │
└─────────────────┬──────────────────┘
                  │
                  ▼
┌────────────────────────────────────┐
│              FastAPI               │
└────────────────────────────────────┘
```

Shared UI and generic platform utilities can be consumed horizontally where explicitly allowed, but they must not reverse the dependency direction.

---

# 143. Recommended Architecture Decision Records

For a long-lived project, record major architectural decisions as ADRs.

Suggested initial ADRs:

```text
ADR-001 Feature-first frontend architecture
ADR-002 TanStack Query owns server state
ADR-003 Zustand restricted to UI/client state
ADR-004 OpenAPI is backend/frontend contract SSOT
ADR-005 SecureStore token/session architecture
ADR-006 Single-flight refresh-token strategy
ADR-007 Expo Router route files remain thin
ADR-008 Expo CNG/config-plugin native workflow
ADR-009 New Architecture enabled
ADR-010 Error-envelope and frontend error taxonomy
ADR-011 Mobile API backward-compatibility policy
ADR-012 EAS Update/runtime-version policy
ADR-013 Testing pyramid and E2E tooling
ADR-014 Observability and data-redaction policy
```

ADRs prevent the same architectural questions from being reopened repeatedly as the team grows.

---

# 144. Upgrade Strategy

Because Expo and React Native evolve rapidly, upgrades should be routine engineering work, not emergency projects.

Recommended:

```text
1. keep framework-specific code isolated
2. avoid abandoned native dependencies
3. run Expo Doctor in CI
4. track Expo/RN releases
5. schedule periodic SDK upgrades
6. test New Architecture compatibility continuously
7. use development/preview builds before production
8. run critical E2E tests against upgrade branches
9. inspect native changes generated by prebuild
10. upgrade incrementally rather than skipping many major SDK generations
```

The longer a mobile project stays pinned to an old SDK, the more difficult eventual Android/iOS toolchain upgrades become.

---

# 145. Final Recommended Architecture

The recommended implementation is:

```text
EXPO ROUTER
- navigation only
- auth route guards
- thin route adapters

FEATURE MODULES
- feature UI
- query hooks
- schemas
- local feature state
- domain rules
- feature API adapter

TANSTACK QUERY
- complete server-state ownership
- query-key factories
- mutation cache strategy
- foreground/network integration

ZUSTAND
- small, feature-scoped client/UI stores
- never backend cache
- never credentials

ZOD
- forms
- deep links
- config
- external/runtime boundaries
- selected critical payload validation

OPENAPI
- FastAPI schema is contract source of truth
- openapi-typescript generation in CI
- generated code isolated

HTTP CLIENT
- one shared transport layer
- auth middleware
- cancellation
- timeout
- normalized errors
- request tracing

AUTH
- SecureStore persistence
- in-memory runtime token mirror
- single-flight token refresh
- atomic rotation
- retry request once
- correct logout/cache cleanup

CORE
- config
- auth
- API
- query
- storage
- errors
- platform
- observability

NATIVE
- New Architecture
- development builds
- CNG/config plugins
- narrow native adapters

QUALITY
- strict TypeScript
- lint/format
- unit + component + integration + E2E
- OpenAPI drift CI
- Android/iOS validation
- dependency compatibility checks

PRODUCTION
- crash/error monitoring
- structured logging
- correlation IDs
- source maps
- build/version observability
- controlled OTA runtime versions
- secure CI/release pipeline
- API backward compatibility
```

The most important result is that every piece of data and every type of logic has **one obvious owner**.

When the project changes, engineers should be able to answer immediately:

```text
Where does this code belong?
Who owns this state?
Which layer may depend on which layer?
What is the API source of truth?
Where are credentials allowed?
How is this behavior tested?
How does this fail in production?
How will this survive the next SDK/backend change?
```

If those answers remain obvious as the application grows, the architecture is working.

---

# 146. Official Reference Material

The architectural recommendations above are aligned with the official documentation and standards below.

## Expo / React Native

- Expo SDK 52 release notes:  
  https://expo.dev/changelog/2024-11-12-sdk-52

- React Native 0.76 / New Architecture:  
  https://reactnative.dev/blog/2024/10/23/release-0.76-new-architecture

- Expo New Architecture guide:  
  https://docs.expo.dev/guides/new-architecture/

- Expo Router authentication for SDK 52 and earlier:  
  https://docs.expo.dev/router/advanced/authentication-rewrites/

- Expo Router testing:  
  https://docs.expo.dev/router/reference/testing/

- Expo SecureStore:  
  https://docs.expo.dev/versions/latest/sdk/securestore/

- Expo environment variables:  
  https://docs.expo.dev/guides/environment-variables/

- Expo development builds:  
  https://docs.expo.dev/develop/development-builds/introduction/

- Expo Continuous Native Generation:  
  https://docs.expo.dev/workflow/continuous-native-generation/

- Expo config plugins:  
  https://docs.expo.dev/config-plugins/introduction/

- Expo Doctor / development tools:  
  https://docs.expo.dev/develop/tools/

- Expo EAS Update runtime versions:  
  https://docs.expo.dev/eas-update/runtime-versions/

- Expo EAS Update code signing:  
  https://docs.expo.dev/eas-update/code-signing/

- Expo unit testing with Jest:  
  https://docs.expo.dev/develop/unit-testing/

- Expo E2E with Maestro:  
  https://docs.expo.dev/eas/workflows/examples/e2e-tests/

- Expo Sentry integration:  
  https://docs.expo.dev/guides/using-sentry/

- React Native security:  
  https://reactnative.dev/docs/security

- React Native performance:  
  https://reactnative.dev/docs/performance

- React Native accessibility:  
  https://reactnative.dev/docs/accessibility

## TanStack Query

- React Native integration:  
  https://tanstack.com/query/latest/docs/framework/react/react-native

- Query keys:  
  https://tanstack.com/query/latest/docs/framework/react/guides/query-keys

- Query invalidation:  
  https://tanstack.com/query/latest/docs/framework/react/guides/query-invalidation

- Mutation invalidation:  
  https://tanstack.com/query/latest/docs/framework/react/guides/invalidations-from-mutations

- Updates from mutation responses:  
  https://tanstack.com/query/latest/docs/framework/react/guides/updates-from-mutation-responses

- Optimistic updates:  
  https://tanstack.com/query/latest/docs/framework/react/guides/optimistic-updates

## OpenAPI TypeScript

- OpenAPI TypeScript:  
  https://openapi-ts.dev/

- `openapi-fetch`:  
  https://openapi-ts.dev/openapi-fetch/

- Authentication middleware:  
  https://openapi-ts.dev/openapi-fetch/middleware-auth

## Zustand

- Zustand documentation:  
  https://zustand.docs.pmnd.rs/

- Slice pattern:  
  https://zustand.docs.pmnd.rs/learn/guides/slices-pattern

- Selector guidance:  
  https://zustand.docs.pmnd.rs/learn/guides/auto-generating-selectors

## Zod

- Zod documentation:  
  https://zod.dev/

## Mobile Security

- OWASP Mobile Application Security Verification Standard:  
  https://mas.owasp.org/MASVS/

- MASVS Storage:  
  https://mas.owasp.org/MASVS/05-MASVS-STORAGE/

- MASVS Authentication:  
  https://mas.owasp.org/MASVS/07-MASVS-AUTH/

- MASVS Network Security:  
  https://mas.owasp.org/MASVS/controls/MASVS-NETWORK-1/

---

# 147. Architecture Summary Checklist

```text
PROJECT STRUCTURE
[ ] feature-first structure
[ ] thin Expo Router files
[ ] core infrastructure isolated
[ ] shared modules intentionally limited
[ ] module boundaries linted

API
[ ] FastAPI OpenAPI = SSOT
[ ] generated TS contract
[ ] generation verified in CI
[ ] one shared HTTP client
[ ] normalized backend errors
[ ] cancellation supported
[ ] safe timeout policy
[ ] retry policy centralized

AUTH
[ ] SecureStore only through token manager
[ ] async SecureStore APIs
[ ] tokens mirrored in memory
[ ] no tokens in Zustand
[ ] no tokens in logs/analytics
[ ] single-flight refresh
[ ] refresh rotation atomic
[ ] request retry only once
[ ] logout clears query cache
[ ] network refresh failure does not automatically destroy session

STATE
[ ] Query = server state
[ ] Zustand = UI/client state
[ ] React state = local state
[ ] Router = navigation state
[ ] no duplicated ownership

QUERY
[ ] query-key factories
[ ] intentional stale times
[ ] intentional retry policy
[ ] native focus manager
[ ] native online manager
[ ] mutation invalidation
[ ] optimistic updates only when safe
[ ] cache cleared/partitioned on account change

VALIDATION
[ ] Zod for forms
[ ] Zod for deep links
[ ] Zod for config
[ ] runtime boundaries identified
[ ] no unnecessary duplicate OpenAPI schemas

SECURITY
[ ] HTTPS only
[ ] no app-bundled secrets
[ ] backend authorization enforced
[ ] sensitive logging prohibited
[ ] OWASP MASVS review
[ ] threat model for higher-risk operations

NATIVE
[ ] New Architecture verified
[ ] development builds used
[ ] CNG/config plugin strategy documented
[ ] native modules hidden behind adapters
[ ] Android/iOS platform differences isolated

TESTING
[ ] pure domain unit tests
[ ] component tests
[ ] router tests
[ ] auth concurrency tests
[ ] query integration tests
[ ] OpenAPI contract checks
[ ] critical E2E journeys
[ ] Android and iOS testing

PRODUCTION
[ ] crash reporting
[ ] source maps
[ ] correlation IDs
[ ] release/build metadata
[ ] structured redacted logging
[ ] performance monitoring
[ ] analytics governance
[ ] environment separation

DELIVERY
[ ] immutable lockfile installs
[ ] Expo Doctor in CI
[ ] build validation
[ ] preview/internal distribution
[ ] controlled production rollout
[ ] OTA runtime-version discipline
[ ] rollback strategy
[ ] SDK upgrade policy

BACKEND COMPATIBILITY
[ ] additive changes preferred
[ ] released mobile versions supported
[ ] breaking changes versioned/migrated
[ ] idempotency for critical retriable mutations
[ ] stable machine-readable error codes
```
