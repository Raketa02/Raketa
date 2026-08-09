# ADR-0002 — Event-sourced User aggregate

- **Status:** Accepted
- **Date:** 2026-08-09 *(captured retroactively from the existing implementation)*

## Context

State changes to a user account (registration, disabling, promotion) are the kind of
thing you later need to explain: *when did this account become an admin, and who did
it?* A row that only carries current state cannot answer that, and bolting on an audit
table afterwards tends to drift from the real transitions.

At the same time, not every entity earns this cost. A refresh token's history is
uninteresting; only its current validity matters.

## Decision

We will make **`User` an event-sourced aggregate**, and treat event sourcing as a
**per-context choice rather than a house style**.

- `User` state is rebuilt from its event stream via `User.from_history(events)`; it is
  constructed only through `User.register(...)`.
- The aggregate carries an `EventRecorder`; the application layer drains pending events
  with `pull_events()` and appends them to the `DomainEventStore`.
- `DomainEventStore.append(...)` takes an `expected_version`; a mismatch raises
  `EventStreamVersionConflict` (optimistic concurrency).
- A **read model** (the `users` table projection) is maintained separately for queries —
  CQRS-lite. The event stream is never queried to answer an authorization question.
- **`RefreshToken` is deliberately *not* event-sourced**: it is a persisted entity that
  emits events. Current state is the truth; the events exist for audit and
  cross-context notification.

## Consequences

**Easier**
- Full, truthful history of every account transition, by construction rather than by
  remembering to log.
- Optimistic concurrency falls out of the version check, so two concurrent writes to the
  same user cannot silently interleave.
- New projections can be built by replaying history.

**Harder**
- Two representations to keep coherent: the stream and the read model. A projection bug
  shows up as data that is *plausible but wrong*, which is harder to spot than a crash.
- Event schemas are a durable contract. Changing one means versioning it, not editing it
  — see the event catalog in [ADR-0003](0003-transactional-outbox-for-event-delivery.md).
- Reading current state costs a rehydration unless the read model is used.

**Neutral**
- Every future context (Clubs, Courts, Bookings, Matches) must make this choice
  explicitly and record it. Bookings in particular have a strong audit argument *and* a
  strong "current state is what matters" argument — that decision deserves its own ADR
  rather than inheriting this one by default.
