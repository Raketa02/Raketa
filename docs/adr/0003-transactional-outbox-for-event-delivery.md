# ADR-0003 — Transactional outbox for event delivery

- **Status:** Accepted
- **Date:** 2026-08-09 *(captured retroactively from the existing implementation)*

## Context

A use case that changes state usually also needs to cause something else to happen: send
a booking confirmation, notify a club, warm a cache. Doing that work inline, inside the
use case, creates two problems that only show up in production:

- **Dual-write inconsistency.** If the database commit succeeds and the email send fails
  (or vice versa), the system is in a state no test covered. Retrying is unsafe because
  you cannot tell which half happened.
- **Latency and coupling.** The user's request now waits on a third party, and the use
  case now knows about email.

## Decision

We will deliver all side effects through a **transactional outbox**.

- Use cases enqueue events onto the `event_delivery_queue` table **in the same
  transaction** as the state change. Either both land or neither does.
- An embedded **`EventWorker`** polls the queue using `SELECT … FOR UPDATE SKIP LOCKED`
  and dispatches to subscribed handlers **after commit**. Toggle via
  `EVENT_DELIVERY_WORKER_ENABLED`.
- **Side effects live in handlers, never in use cases.** A use case that calls an
  external API directly is a defect.
- Events are serialized through an **event catalog** that maps each class to a stable
  durable name and integer version (e.g. `users.user_registered` / v1), so the wire
  format is a contract rather than a consequence of the Python class name.

## Consequences

**Easier**
- Atomicity: no state change is ever visible without its corresponding event enqueued.
- Handlers can fail and be retried without corrupting domain state.
- `SKIP LOCKED` means multiple workers can drain the queue without coordination.
- Renaming or moving a Python event class cannot break already-stored history.

**Harder**
- Delivery is **at-least-once**, so every handler must be **idempotent**. This is the
  single easiest thing to get wrong, and it fails silently — a duplicate confirmation
  email is a bug report, a duplicate charge is worse.
- Side effects are eventually consistent. A caller cannot assume the email has been sent
  when the request returns.
- The queue is operational surface: it can back up, and it needs monitoring.

**Neutral**
- Handlers are registered in each module's `event_subscriptions.py` and assembled in
  `app/bootstrap/events.py`, so the full set of side effects is enumerable in one place.
