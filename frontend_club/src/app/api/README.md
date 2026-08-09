# `src/app/api/` — the BFF (backend-for-frontend)

These route handlers are **the only thing the browser is allowed to call**. They run
server-side, hold the FastAPI base URL (`BACKEND_API_URL`, never `NEXT_PUBLIC_*`), and
own the httpOnly session cookie. See
[ADR-0007](../../../../docs/adr/0007-club-web-bff-httponly-cookie-session.md).

```
browser ──▶ /api/*  (this BFF, same origin)  ──▶  FastAPI
        ✗ never straight to FastAPI
```

## Rules

- **A Client Component never calls FastAPI directly.** It calls `/api/*`.
- **Tokens never reach the browser.** Access/refresh JWTs live in
  httpOnly + Secure + SameSite cookies set here. Never in `localStorage`, never in a
  JS-readable cookie, never as a Client Component prop.
- `auth/` proxies login / refresh / logout and manages those cookies.
- A 401 from FastAPI triggers a server-side rotate against `/api/v1/auth/refresh`;
  the browser never sees the refresh token.
- Server Components may read the session cookie and call FastAPI directly through
  `@/shared/lib/http` — they are server-side, so that is not a browser call.

## Why the mobile app differs

`frontend_player` (Expo) has no BFF: a native app has no cookie jar and no XSS surface
of the same shape, so it holds tokens in the OS keychain via `expo-secure-store` and
calls FastAPI directly. Same backend, deliberately different session model — see
[ADR-0008](../../../../docs/adr/0008-player-mobile-securestore-direct-api.md).
