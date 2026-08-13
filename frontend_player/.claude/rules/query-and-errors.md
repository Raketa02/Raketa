---
paths:
  - "src/features/*/hooks/**"
  - "src/shared/lib/query-client/**"
  - "src/shared/errors/**"
---

# TanStack Query and the error family

## Query

- **A query-key factory per feature** in `hooks/` — no inline string keys. Every parameter
  that changes the response is in the key, **including the cursor**.
- **Semantic hooks** (`useMatch(id)`), not query options assembled per screen.
- **Choose the defaults** — stale time, gc, retry predicate, `networkMode`, refetch on focus
  — per data class. Live slot availability and reference data are not the same.
- **Wire `focusManager` to `AppState` and `onlineManager` to native connectivity.** Query's
  browser assumptions are wrong here; without this, nothing refreshes on foreground and
  paused mutations never resume.
- **Mutations declare their cache effect:** prefer writing the canonical response with
  `setQueryData`, then invalidate the broader lists. Optimistic updates only when rollback is
  deterministic and rejection is rare — booking a slot is not that case.
- **Cancellation:** pass Query's `signal` through to `fetch`. No fire-and-forget request in a
  component.

## Errors

Raw `fetch` failures and backend JSON never reach a screen. `shared/errors` normalizes into
one `AppError` family, and **decisions branch on the backend's stable `code`, never on
`message`** — the message is copy and will change.

Every mapped error gets a recovery category (auto-retry · user-retry · re-auth · user
correction · conflict · terminal), and the envelope's `trace_id` goes into the error report
so a mobile failure can be tied to a server log without logging a payload.

**Not every 4xx is a logout** — only authentication-invalidating responses touch the session.
A 403 means "not allowed", not "sign in again".

## The product surface these produce

Every server-driven screen models **initial loading · loaded · empty · refreshing ·
recoverable error · terminal error · offline**. `if (isLoading) <Spinner/>` is not acceptable
for a real flow. Distinguish initial load from pull-to-refresh from background refresh from a
button mutation; one global spinner makes the app feel broken.

Critical mutations decide their duplicate-submit behaviour. A disabled button is UX;
**backend idempotency is the correctness mechanism.**

Never branch on a user-visible string (`status === MatchStatus.Cancelled`, not
`'Cancelled'`). Distinguish a timestamp from a local calendar date, and never make a business
decision from the device clock or a formatted string.

Offline and flaky networks are the normal case, not an edge case — but that is *not* a licence
to call this app offline-first. It is network-backed with an in-memory cache and graceful
offline UX, and stays that way until a persistent local layer is decided deliberately.
