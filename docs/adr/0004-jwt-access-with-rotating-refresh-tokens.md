# ADR-0004 — JWT access tokens with rotating refresh tokens

- **Status:** Accepted
- **Date:** 2026-08-09 *(captured retroactively from the existing implementation)*

## Context

The API serves two clients with different threat models: a **web app** (XSS is the
primary risk; a browser has a cookie jar) and a **native mobile app** (no cookie jar; a
stolen device and an extracted token are the primary risks). Both need sessions that
survive longer than a single short-lived credential, without leaving a long-lived bearer
token lying around to be replayed.

## Decision

We will issue **short-lived access JWTs plus long-lived, rotating refresh tokens**.

- **Access token** — short-lived JWT (`ACCESS_TOKEN_EXPIRE_SECONDS`), sent as
  `Authorization: Bearer`, verified statelessly.
- **Refresh token** — longer-lived (`REFRESH_TOKEN_EXPIRE_SECONDS`) and **persisted**.
  The database stores only the **bcrypt `token_hash`** and the **`jti`** — never the
  plaintext.
- **Rotation:** each refresh atomically revokes the presented token and issues a new one
  (`RefreshToken.rotate_to(...)`). Presenting an already-rotated token is rejected —
  that is replay detection, and it is the reason rotation exists rather than simply
  re-issuing.
- **Logout is idempotent** and does not reveal whether the token existed.
- **Login returns one error** for both unknown-email and wrong-password
  (`InvalidCredentials`) — no account enumeration.
- Each client stores these differently, per its own threat model:
  [ADR-0007](0007-club-web-bff-httponly-cookie-session.md) (httpOnly cookies) and
  [ADR-0008](0008-player-mobile-securestore-direct-api.md) (OS keychain).

## Consequences

**Easier**
- Access-token verification needs no database round trip.
- A leaked access token is useful only briefly.
- Stolen-and-replayed refresh tokens are **detectable**, because the legitimate client's
  next refresh presents a token the server has already rotated away.

**Harder**
- Refresh is stateful: revocation and rotation need a table and a transaction, so the
  "stateless JWT" simplicity is only true of the access token.
- Every client must implement the 401 → refresh → retry cycle correctly, **single-flight**.
  Getting this wrong produces a burst of concurrent refreshes that rotate each other out
  and log the user out — a bug that only appears under real-world concurrency.
- Access tokens cannot be revoked before expiry. Disabling an account takes effect at
  the next refresh, not immediately. If immediate revocation is ever required, that is a
  new decision (a denylist or a much shorter access lifetime), not a tweak to this one.
