# ADR-0008 — Player mobile: secure-store tokens, direct to the API

- **Status:** Accepted
- **Date:** 2026-08-09

## Context

The club web app protects its session by keeping it out of JavaScript entirely, in
httpOnly cookies behind a BFF ([ADR-0007](0007-club-web-bff-httponly-cookie-session.md)).
The obvious question is whether the player app should do the same, for consistency.

It should not, because the premises differ:

- A native app has **no cookie jar** and no browser to enforce `httpOnly`. Cookie
  semantics would have to be emulated, badly.
- There is **no XSS surface of the same shape** — no third-party script executing in the
  app's origin with access to its storage.
- The platform offers something the browser does not: a **hardware-backed OS keychain**
  (iOS Keychain, Android Keystore), which is stronger storage than anything a web page
  can reach.
- A BFF would be an extra deployed service on the request path of every mobile call,
  buying nothing the keychain does not already provide.

The real mobile threats are different: a token extracted from an unencrypted store on a
rooted/jailbroken or backed-up device, and secrets read straight out of the shipped
bundle.

## Decision

The player app will call **FastAPI directly** and store credentials in the **OS keychain**.

- Tokens live in **`expo-secure-store`**, reached **only** through
  `src/shared/lib/auth`. No feature, screen, or hook imports the keychain directly — one
  module owning it is what makes token lifetime auditable.
- **`AsyncStorage` must never hold a credential** — it is unencrypted plaintext on
  device. ESLint blocks the import outright.
- **No BFF.** A feature's `api/` layer calls FastAPI over HTTPS with
  `Authorization: Bearer`.
- The 401 → refresh → retry rotation lives once in `src/shared/lib/http` and is
  **single-flight**: concurrent 401s wait on one refresh rather than each firing their
  own, which would rotate each other out and log the user out
  ([ADR-0004](0004-jwt-access-with-rotating-refresh-tokens.md)).
- **Nothing in the bundle is secret.** `app.json` `extra` and every `EXPO_PUBLIC_*`
  variable can be read out of a released app. They carry config only; a secret a mobile
  client appears to need belongs behind the backend.

## Consequences

**Easier**
- Strongest storage the platform offers, with no emulation of browser semantics.
- One less service on the mobile request path — fewer moving parts, lower latency.
- The keychain survives app restarts and is excluded from ordinary backups.

**Harder**
- The FastAPI origin is public and must be internet-reachable and correctly CORS'd and
  rate-limited. There is no BFF hiding it.
- Refresh rotation is implemented client-side, and the single-flight requirement is easy
  to get wrong in a way that only appears under real-world concurrency.
- **Old versions live on real phones for months.** Users cannot be forced to update, so
  backend contract changes must be additive by default and removals treated as breaking
  ([ADR-0006](0006-backend-owns-api-contract.md)).
- A compromised device is not defensible from the app side; server-side revocation is the
  backstop.

**Neutral**
- The two clients are deliberately asymmetric in exactly one place — session storage and
  whether a BFF exists. Everything above the `api/` layer is the same shape
  ([ADR-0009](0009-feature-first-clean-architecture-frontends.md)). Do not copy the club
  app's cookie code here, and do not add a proxy to make the diagrams match.
