# ADR-0013 — Player app: the production runtime architecture

- **Status:** Accepted
- **Date:** 2026-08-12

> **Note — the 2026-08-25 reset.** It cites **ADR-0007** (the club console's cookie session), removed in the 2026-08-25 reset. This ADR's own decision, for the player app, is untouched. See the [ADR index](README.md#the-2026-08-25-reset--why-the-sequence-has-gaps). This ADR's body is left as written: an accepted ADR is immutable, and the reason a past decision looked right is itself information.

## Context

[ADR-0009](0009-feature-first-clean-architecture-frontends.md) settled *where code lives*
in both frontends. [ADR-0008](0008-player-mobile-securestore-direct-api.md) settled
*where the player app's credentials live*. Neither settles how the app **behaves in
production**: what happens during the first 400ms of launch, what happens when ten
requests get a 401 at the same moment, what happens to one user's cached bookings when
another signs in on the same handset, or what a screen shows when the network is present
but slow.

Those questions have conventional answers, and a mobile app that leaves them to be
decided per-feature gets a different answer each time. The failure modes are specific and
familiar:

- Bootstrap modelled as `user === undefined` — so the login screen flashes over a valid
  session, or the authenticated tree flashes before a redirect.
- A refresh fired per 401 — so a burst rotates the refresh token against itself and logs
  the user out at random, under exactly the concurrency that only occurs in production.
- A dropped connection during refresh treated as a rejected refresh — so the user is
  signed out for walking into a lift.
- `queryClient` left populated at logout — so user A's profile and bookings are readable
  by user B on a shared device.
- Screens branching on `error.message` — so a copy change or the first localization pass
  breaks business logic.
- A mutation retried by a global policy — so a tapped **Book** becomes two reservations.
- Query's browser focus and online assumptions left unwired — so nothing refreshes when
  the app returns to the foreground.

Each is cheap to prevent at the architecture layer and expensive to find in the field,
where the only signal is a support ticket saying "it logged me out again".

A comprehensive external reference for React Native + Expo production architecture was
adopted as the input for this decision
([`docs/specs/player-app/react_native_expo_production_architecture.md`](../specs/player-app/react_native_expo_production_architecture.md),
147 sections). It proposes a `core/` directory and a slightly different feature layer set
from the one this repo already committed to, and that conflict had to be resolved rather
than absorbed.

## Decision

The player app adopts that reference as its runtime architecture, **mapped onto this
repo's existing structure**, and distilled into
[`frontend_player/docs/architecture.md`](../../frontend_player/docs/architecture.md) — the
operative document. This ADR records the decisions that document makes and the ones it
deliberately does not.

**Structure is not reopened.** ADR-0009's layer set and `src/app/` stay; the reference's
`core/` maps to `src/shared/lib/`, its feature `ui/` to `components/`, its
`generated/api/` to `src/generated/`. The full translation table is Part 0 of the
architecture doc. This keeps the two clients sharing a shape, which is the whole point of
ADR-0009.

Two things are **added** to the structure:

1. **`src/shared/lib/` gains `bootstrap/`, `platform/` and `observability/`** alongside
   the existing `http/`, `auth/` and `query-client/`. Framework- and vendor-facing code
   concentrates there so an Expo SDK upgrade never touches a feature.
2. **A feature may have an optional `store/` layer** for a small feature-scoped Zustand
   store. It is *optional* — it does not join ADR-0009's mandatory set, and its absence is
   not a gap. A hundred-property app-wide store is what this prevents.

The substantive decisions:

- **Session is a tri-state** — `bootstrapping | authenticated | unauthenticated` — driving
  one ordered bootstrap sequence behind the splash screen. Route protection on SDK 52 is a
  redirect in `(app)/_layout.tsx`; expo-router's declarative protected routes postdate 52.
  Route groups `(public)` / `(auth)` / `(app)` make the authorization boundary visible in
  the file tree.
- **Token refresh is single-flight**, rotation is atomic, an authenticated request is
  retried exactly once, and a *rejected* refresh is distinguished from an *unreachable*
  one. Logout is an eight-step system operation whose fifth step —
  `cancelQueries()` + `clear()` — is a privacy control.
- **Errors are normalized into one `AppError` family**, and client decisions branch on the
  backend's stable `code`, never on `message`. Every mapped error carries a recovery
  category. Not every 4xx is a logout.
- **TanStack Query owns all server state**, with a per-feature key factory, deliberately
  chosen defaults, `focusManager`/`onlineManager` wired to native `AppState` and
  connectivity, and a declared cache effect per mutation. **Mutations are never retried
  globally** — only when idempotent, keyed, or explicitly safe.
- **`fetch` is configured in exactly one place**, which owns timeouts, cancellation,
  correlation IDs and error normalization.
- **Observability is an internal interface**, not vendor calls scattered through features,
  with structural redaction and a governed analytics event catalog.
- **The app is network-backed, not offline-first.** A persistent cache or SQLite arrives
  only against a stated requirement.
- **New Architecture stays enabled; native projects are CNG output**; development builds,
  not Expo Go, are the working environment; OTA respects an explicit runtime version.
- **Released clients are immutable from the backend's perspective**, which constrains
  contract evolution to additive-by-default.

**Enforcement.** The reference's own conclusion — architecture that lives only in a
document is eventually violated — is taken literally. `eslint.config.mjs` now also blocks:
`expo-secure-store` outside `shared/lib/auth`, the `fetch` global outside
`shared/lib/http`, observability vendor SDKs outside `shared/lib/observability`, any
import from `src/features/**` inside `src/shared/**`, and any deep import of another
feature's private layers. Auth concurrency tests — the four scenarios ordinary login tests
miss — are mandatory rather than encouraged.

**Not adopted now.** `openapi-fetch`, Sentry, Maestro, React Hook Form, a feature-flag
service, `expo-network`/netinfo and any persistence layer are documented as required
capabilities with the conditions that trigger them, but are **not** added to
`package.json`. Dependencies arrive with the code that needs them.

## Consequences

**Easier**

- The production failure modes listed above are designed out rather than discovered. The
  auth ones in particular are near-impossible to find by manual testing, because they need
  real concurrency and real network loss.
- An agent starting cold has one answer per question — who owns this state, where does
  this error go, what does this mutation invalidate — instead of a judgment call that
  differs per feature.
- SDK upgrades stay routine: framework contact is concentrated in `src/app/` and four
  `shared/lib/` modules.
- Boundary violations fail at `pnpm lint`, in the editor, not at review.

**Harder**

- Meaningfully more infrastructure before the first screen: bootstrap, session machine,
  refresh coordinator, error taxonomy and Query defaults are all prerequisites of doing
  feature work properly. The temptation to skip them and "add auth later" is the thing
  this ADR exists to resist.
- The reference document and this repo now use different names for the same directories.
  Anyone reading the source must go through Part 0's translation table first, and that is
  a permanent tax on consulting the original.
- The stricter lint rules make intra-feature imports relative and cross-feature imports
  go through `types.ts`. That is a real ergonomic cost, paid to keep features detachable.
- Several documented capabilities have no code yet, so the docs describe more than the
  repo contains until the app is built out. The gap is explicit (architecture doc Part 21)
  but it is still a gap.

**Neutral**

- The club app is unaffected. Parts 1, 6, 7 and 9 describe a shape it happens to share,
  but it has its own session model (ADR-0007) and this document does not govern it.
- The reference's suggested ADR list is largely already covered here — the contract
  (0006), credentials (0008), structure (0009) — so this is one ADR rather than fourteen.
