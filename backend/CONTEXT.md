# Rakieta Backend — Technical Vocabulary

This file holds **backend-only technical vocabulary**. It does **not** define domain
language — those terms (User, Authority, Club, Court, Booking, statuses, events) live
once in the shared glossary [`../CONTEXT.md`](../CONTEXT.md), which all three apps obey.
See [`../CONTEXT-MAP.md`](../CONTEXT-MAP.md) for the topology.

> When you name a backend architecture concept, use the term as defined here or in the
> root glossary's **Cross-cutting concepts** section. Don't drift to synonyms.

## Where the architectural terms already live

The core hexagonal / event-sourcing vocabulary — **DomainEvent**, **EventRecorder**,
**DomainEventStore**, **Transactional outbox**, **EventWorker**, **Event catalog**,
**Port / adapter**, **UnitOfWork**, **Read model**, **EventStreamVersionConflict** — is
documented in [`../CONTEXT.md`](../CONTEXT.md) under *Cross-cutting concepts*. Read them
there; they are not repeated here.

## Backend-only terms

- **Module** — a bounded context's vertical slice under `app/modules/<context>/`, split
  into `domain/ application/ infrastructure/ presentation/`. _Avoid_: package, app,
  service (this codebase has exactly one service).
- **Use case** — one class in `application/` with a single `async execute(...)`.
  Constructor-injected ports only. _Avoid_: service, manager, handler (a **handler** is
  specifically an event subscriber, which is a different thing).
- **Handler** — a function subscribed to a domain event, run by the `EventWorker`
  **after commit**. The only place a side effect belongs. _Avoid_: listener, callback.
- **Command** — the input dataclass a use case's `execute` takes. Carries primitives
  from the boundary, not domain value objects.
- **Event-sourced aggregate** vs **persisted-with-events entity** — the two persistence
  shapes in this codebase, and a deliberate per-context choice. `User` is the former
  (state rebuilt from its stream); `RefreshToken` is the latter (current state is the
  truth, events provide audit + cross-context notification). Neither is the default.
- **Durable event name** — the stable `"<context>.<event>"` string plus integer version
  registered in the event catalog, e.g. `users.user_registered` / v1. It is the wire
  contract for stored history and is **independent of the Python class name**.
- **Aggregate repository** — the port a use case loads and saves an **event-sourced
  aggregate** through, e.g. `AssessmentRepository`. It owns the aggregate-type name, the
  replay, the ownership scoping and the optimistic-concurrency bookkeeping, so a use case
  never names the event store. `save` appends and publishes and **does not commit** — the
  `UnitOfWork` stays a use-case dependency, because one transaction can span two
  aggregates. Its adapter keeps a **per-request** identity map of loaded versions, so it
  must be constructed per request from the session. _Avoid_: DAO, store, gateway.
- **Invariant** vs **Unavailability** — the two ways kernel and engine code refuses, and
  they are not interchangeable ([ADR-0022](../docs/adr/0022-kernel-negative-space-and-constant-homes.md)).
  An **invariant** is a broken precondition: `invariant(subject, message)` raises
  `InvariantViolated`, nothing catches it, and it raising in production means a bug
  shipped. An **unavailability** is a legitimate domain state where no answer exists:
  it is *returned* as a `Result` and the caller branches on it. Confusing them forces
  `try` into pure code, or forces every call site to handle a case that cannot happen.
  _Avoid_: "error" for either, unqualified.
- **Result** — a frozen `Ok(value)` or a frozen `Err(reason)`, consumed by pattern match.
  Two `@final` classes with one field each, so there is no third inhabitant: never both,
  never neither. `map` and `and_then` pass a failure's reason through untouched.
- **Reason** — why there is no answer: a stable machine `kind` code and its payload
  fields, **never a sentence**. The clients own the words; a reason crosses the wire as
  `{kind, …payload}`. `Unavailable` is the closed union of them and currently **ships
  empty** — its first member arrives with the kernel's time module. _Avoid_: message,
  detail, error text.
- **Read-model repository** — the port a use case reads *projected current state* through,
  e.g. `UserRepository`. It answers queries against a table, not by replaying a stream, and
  has no version bookkeeping. **The trap:** `UserRepository` is this kind despite its name
  and despite `User` being an event-sourced aggregate — it is the projection side, not the
  write side. It keeps its name; read the shape, not the noun.

Add backend-specific technical terms here as they are resolved. Anything describing the
*domain* belongs in the shared glossary instead.
