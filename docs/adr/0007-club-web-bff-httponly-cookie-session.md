# ADR-0007 — Club web: BFF with an httpOnly-cookie session

- **Status:** Accepted
- **Date:** 2026-08-09

## Context

The club web app runs in a browser, which means any token reachable from JavaScript is
reachable from an XSS payload — including one injected through a dependency the team
never reviewed. Storing JWTs in `localStorage` is convenient and is the single most
common way web sessions get stolen.

Next.js App Router gives us a server tier inside the frontend deployment: Server
Components and route handlers. That makes a backend-for-frontend cheap, where in a
pure-SPA setup it would be an extra service to run.

## Decision

The club app will talk to FastAPI **only through its own server tier**, and hold the
session in **httpOnly cookies**.

- **The browser only ever calls this app's own origin** — route handlers under
  `src/app/api/*`. It never calls FastAPI directly.
- Those handlers proxy FastAPI and own the session: access/refresh JWTs are set as
  **httpOnly + Secure + SameSite** cookies. Browser JavaScript can never read them.
- `BACKEND_API_URL` is **server-only** and deliberately not prefixed `NEXT_PUBLIC_`;
  anything so prefixed is inlined into the client bundle.
- Server Components may read the session cookie and call FastAPI directly through
  `shared/lib/http` — they are server-side, so that is not a browser call.
- `middleware.ts` guards routes by reading the session cookie.
- A 401 triggers a **server-side** rotation against the backend's `/auth/refresh`
  ([ADR-0004](0004-jwt-access-with-rotating-refresh-tokens.md)); the browser never sees a
  refresh token.
- The Playwright auth spec asserts tokens are **not** readable from `document.cookie` —
  the rule is tested, not just documented.

## Consequences

**Easier**
- XSS cannot exfiltrate the session, because the session is not in the JavaScript
  environment at all.
- The FastAPI origin is not public knowledge, and CORS becomes a non-problem: the browser
  makes same-origin requests only.
- Server Components can render authenticated pages with no client-side auth flash.

**Harder**
- Every backend endpoint the browser needs requires a corresponding BFF route handler.
  That is real, ongoing boilerplate, and the temptation to "just call FastAPI directly
  this once" will recur.
- One more network hop for client-side mutations.
- Cookies bring CSRF into scope; `SameSite` covers the common cases but a
  state-changing endpoint reachable cross-site needs thought.
- The BFF is stateful surface that must be deployed with the app.

**Neutral**
- The player app deliberately does **not** do this
  ([ADR-0008](0008-player-mobile-securestore-direct-api.md)). The asymmetry is the point:
  each client uses the strongest storage its platform actually offers. Do not "unify"
  them.
