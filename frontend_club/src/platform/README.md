# `src/platform/` — application-wide infrastructure

Capability that no single feature owns: how the browser talks to the BFF, how the BFF
talks to FastAPI, how sessions and requests are established, how errors are normalized,
how state and config are configured, how the app is observed.

Specified in [`docs/architecture/production-architecture.md`](../../docs/architecture/production-architecture.md)
§5, §18–§20, §31, §42. Changes here get architecture review — they affect every
feature (§35.2).

| Folder | Holds | Runs |
| --- | --- | --- |
| `api/` | Browser client primitives for same-origin `/api/*`, request helpers, error normalization. | browser |
| `server/fastapi-client.ts` | The single typed FastAPI client: base URL, timeouts, auth header construction, header allowlist, tracing, response/error parsing, metrics. | **server-only** |
| `server/auth/` | Cookie helpers, session resolution, the controlled refresh attempt. | **server-only** |
| `server/csrf/` | Origin/Referer checks and any anti-CSRF token mechanism. | **server-only** |
| `server/request-context/` | Per-request correlation/request ID, trace context, resolved session. | **server-only** |
| `server/errors/` | Backend error → BFF error-envelope mapping. | **server-only** |
| `server/observability/` | Structured logging, metrics, trace propagation. | **server-only** |
| `query/` | QueryClient factory, providers, global defaults, truly global key primitives. | both |
| `config/` | Zod-validated env — a **server schema** and a separate **public schema**. | both |
| `observability/` | Browser telemetry: Web Vitals, error reporting. | browser |
| `security/` | CSP and security-header policy, redirect allowlisting. | both |

## Rules

- **`server/` is `server-only`.** Anything that can read a token, a secret or
  `BACKEND_API_URL` must be impossible to import into a client bundle. This is the
  boundary that keeps the FastAPI origin out of the browser. *(§19.1)*
- **The FastAPI client is infrastructure, not a dumping ground.** Endpoint-specific calls
  live in the owning feature's `server/`. This is how you avoid a 5,000-line
  `apiService.ts`. *(§19)*
- **Every FastAPI call has a finite timeout** and an abort signal, categorized by
  endpoint — not one huge global value. *(§8.4)*
- **The browser client never handles tokens,** never learns the FastAPI origin, never
  attaches an `Authorization` header, and never silently retries an unsafe mutation. It
  serializes input, sets `Content-Type`, passes the abort signal, parses the response,
  normalizes errors and carries the request ID. *(§18)*
- **Terminal 401 is handled once, here** — not reinvented as a logout flow per feature.
  Do not redirect on every query error; preserve error semantics and user context. *(§18.1)*
- **Two config schemas, never one.** Anything named `NEXT_PUBLIC_*` is public information
  baked into the bundle. Validate on startup so a malformed URL fails at boot, not when a
  user opens a rare screen. Nothing reads `process.env` directly. *(§20.1, §20.2)*
- **One browser QueryClient for the app lifetime; a request-local one on the server.** A
  QueryClient shared across users on the server leaks data between them. *(§42)*
- **Nothing here is stateful across requests.** No module-global locks, sessions, caches
  or counters for correctness — any two requests may hit different instances. That
  includes the refresh lock and rate-limit counters. *(§3.7, §32.1)*
- **Never log** access/refresh tokens, `Authorization` headers, full cookie headers,
  passwords, payment secrets or unnecessary PII. *(§31.3)*
