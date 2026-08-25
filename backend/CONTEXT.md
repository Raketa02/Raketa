# Raketa Backend — Technical Vocabulary

This file holds **backend-only technical vocabulary**. It does **not** define domain
language — those terms (User, Authority, Email, Sport, Assessment, Skill rating,
statuses, events) live
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
  `{kind, …payload}`. `Unavailable` is the closed union of them, in
  `app/kernel/unavailability.py` — its own module, because it is assembled *from* the
  modules that produce its members while `results.py` knows about none of them. It
  shipped empty (`Never`); its first member is `NonexistentLocalTime`. A function
  declares the reasons it can actually give; only code aggregating over all of them
  names `Unavailable`. _Avoid_: message, detail, error text.
- **Clock** — the `Protocol` in the kernel returning an `Instant`, **passed, never
  imported**. No module reads ambient time (ADR-0015's first purity rule), which is what
  makes scrubbing forwards and backwards, determinism and every fixed-`now` test
  possible. One read per command, captured once and passed on: two reads inside one
  command can disagree. Its wall-clock adapter is `SystemClock` in
  `app/infrastructure/clock.py`, and only a composition root imports it — depending on
  *what a clock is* must not drag a live one into scope.
- **Read-model repository** — the port a use case reads *projected current state* through,
  e.g. `UserRepository`. It answers queries against a table, not by replaying a stream, and
  has no version bookkeeping. **The trap:** `UserRepository` is this kind despite its name
  and despite `User` being an event-sourced aggregate — it is the projection side, not the
  write side. It keeps its name; read the shape, not the noun.

- **Environment** — one of exactly four: `local`, `development`, `staging`, `production`,
  spelled identically by both apps and carried by `APP_ENV`. `local` is a developer's
  own machine — a container on your laptop is still `local`, because the name describes
  *where the software runs*, not whether it is containerised. **The load-bearing rule: the
  environment may select configuration defaults; it may never select behaviour a domain
  test could observe.** No deadline, threshold, validation, status code or response shape
  varies by it. `APP_ENV` rather than `ENV` because the old name collides with an ordinary
  shell variable, so a value inherited from the surrounding environment could decide what
  environment the application thought it was in. _Avoid_: `dev`, `prod`, `test`, `stage` —
  those are the spellings whose synonymy is the bug, and the settings object refuses every
  one of them.
- **Environment profile** — the settings `APP_ENV` supplies defaults for: `DEBUG`,
  `LOG_LEVEL`, `LOG_JSON`. One value replaces three that had to be kept in agreement by
  memory, and the failure that removes is the silent one — nothing goes wrong until the
  deployment where somebody sets two and forgets the third. Each stays **explicitly
  overridable**, because a legitimate one-off (verbose logging in staging while chasing a
  bug) must not require abandoning the mechanism. Implemented with `model_fields_set`, so
  *"was this configured?"* means *"did somebody actually set it"* rather than *"does it
  differ from a sentinel"*. _Avoid_: environment-specific config file, profile inheritance.
- **Startup refusal** — a `ConfigurationError` raised while the settings object is being
  built, for configuration that is dangerous rather than merely wrong. It lives on the
  settings object and not in the application factory, so it holds for a worker, a
  migration or a seed run and not only for a process serving HTTP. Two constraints on the
  message: it **names the offending variable and the reason**, and it **never contains the
  offending value** — a `WRITER_DB_URL` carries a password and a refusal goes straight to a
  log aggregator. `ConfigurationError` is deliberately **not** a `ValueError`: pydantic
  wraps `ValueError` raised inside a validator into a `ValidationError` whose repr carries
  `input_value=…`, which for an after-validator is the entire settings object, signing key
  included. _Avoid_: falling back, warning and continuing, a "strict mode" flag.
- **Unprovisioned environment** — `development` and `staging`. Defined and validated, but
  no domain is registered, so neither has a host or a database. Selecting one without
  `APP_HOST` and `WRITER_DB_URL` is a startup refusal naming the missing variable. **No
  placeholder hostname is written anywhere**, which is why "configured" can only mean
  "somebody set it": there is nothing to compare a host against. _Avoid_: inventing
  `api-dev.…`; a config file naming a host that does not exist describes infrastructure
  that does not exist.
- **Public-network scheme rule** — the platform rule that a URL a browser or a phone
  reaches over the internet is `https://` in every deployed environment, and unconstrained
  in `local`. The backend calls nothing over HTTP, so its only instance is `ALLOW_ORIGINS`:
  a non-`https://` entry there while `APP_ENV` is deployed is a startup refusal, because a
  credentialed CORS grant to a plaintext origin is a browser client's session cookie in the
  clear. The wildcard is not an origin and is skipped; it has its own refusal. Defined once
  for all three apps in [`../docs/environments.md`](../docs/environments.md). _Avoid_:
  extending it to a **server-to-server** address — `http://backend.svc.cluster.local:8000`
  never crosses a public network, and whether that hop is encrypted is a
  deployment-topology question no app can assert.
- **Composition root** — `app/bootstrap/composition.py`, the one place an adapter is
  constructed. One plain function per port, taking a database session and the settings,
  with no web framework in it and no request anywhere near it. Before it, every adapter
  was built inside a `Depends` callable, so anything that is not an HTTP request had two
  options and both were bad: boot the API to create data, or hand-copy the wiring into a
  second root. **A hand-copied composition root drifts silently** — it keeps working, and
  it stops being what production runs. _Avoid_: constructing an adapter anywhere else; a
  walk over the dependency modules refuses it.
- **Declaration vs construction** — the split the composition root buys, and the reason
  `app/api/dependencies.py` still exists. A dependency declaration answers *when* an
  adapter is built and how long it lives — one per request, cached by FastAPI for that
  request, which is what keeps a repository from answering with another request's stream
  versions. The factory answers *what* is built. Sharing is therefore the caller's
  business: every adapter is a stateless wrapper over its session, so a caller outside a
  request that wants one store for two repositories builds it once and passes it on.
- **Configuration boundary** — the line configuration is read at and never crosses. It is
  the composition boundary: `app/bootstrap/`, `app/api/dependencies.py`, `app/core/`,
  `app/main.py` and the adapters. Inward of it — `app/application/`, `app/shared/domain/`
  and every `app/modules/*/domain` and `app/modules/*/application` — the settings module is
  **structurally unreachable**, enforced by an `.importlinter` contract rather than by
  review. That is what makes *the environment may never select behaviour a domain test
  could observe* a checkable claim instead of an aspiration: a use case reading `APP_ENV`
  to pick a deadline is a rule that is true on a laptop and false in production, and the
  domain suite cannot see the difference. `pydantic_settings` and `os` are forbidden beside
  it, because declaring a second settings class or reading `os.environ` is the same rule
  broken by a different import. The two `app/modules/*` arms are **wildcards**, so a
  context created tomorrow is fenced the day it exists — every racket-sport context and
  Matches are all named and none is modelled. A use case that needs a configured value
  takes it as a constructor argument. _Avoid_: importing settings "just for a default",
  a module-level `get_settings()` inside a business layer, an exemption.

- **Seed account** — a deterministic development account created by `app/seeds/`, named
  for the **state it represents** rather than for a person: signing in as
  `assessment-in-progress@raketa.example` is a statement about what you expect to see.
  The address is *derived* from that name, so an account cannot be called one thing and
  reachable at another, and it is on a TLD RFC 2606 reserves so it can never become
  somebody's real mailbox. **`.example` rather than `.test`**, though the same sentence of
  the same RFC reserves both: `EmailStr` at the HTTP boundary is `email-validator`, which
  refuses `test`, `invalid`, `localhost`, `local`, `arpa` and `onion` outright — so a
  `.test` account is one no client can sign in as. _Avoid_: a fixture user, a real domain,
  an address that names a person.
- **Seeding through the write path** — the rule that makes seed data trustworthy: a seed
  executes the same use cases a request executes, wired from the **composition root**, so
  the event stream, the outbox row and the projection are written by the code that
  normally writes them. A row inserted straight into a table produces an aggregate with
  **no history** — it reads correctly until something replays it, and then the seeded data
  and the system's own account of that data disagree; it also skips every handler that
  should have reacted. A structural walk over `app/seeds/` refuses a statement import, an
  ORM model and `session.add`. _Avoid_: fixtures SQL, a factory that builds ORM objects.
- **Seed guard** — the refusal that keeps fabricated accounts out of production, checked
  **on import** of `app/seeds/` and again against the settings `run` is handed. Not in the
  make target: a make target is not what runs inside a container, and a guard that
  `python -m app.seeds` walks around is decoration. Seeding is permitted in `local`,
  `development` and `staging`, written out per environment rather than derived as
  "everything but production", so a fifth environment has to be decided about rather than
  inheriting an answer. _Avoid_: guarding the entry point instead of the module.
- **Seed scenario** — what one seeded account holds, **for one sport**: a run left open, a
  run abandoned, or a run answered through and rated. A closed union, so the runner's
  `match` over it stops typechecking the day a fourth state exists — an unhandled scenario
  would otherwise be an account silently seeded into no state at all. One sport is one
  scenario: two on the same sport describe a state the domain cannot reach, because a
  rated sport refuses a second assessment. _Avoid_: an account that is a person rather
  than a state, a scenario for a context with no aggregate.
- **Answer policy** — how a seed scenario answers whatever the questionnaire asks: an
  index into the question's *own* options counted from the weakest, clamped to the last
  one, with one number for demonstrations and one for everything else. The split is read
  off `Question.tier` — the port's own marker for an execution question — never off a
  question id, which belongs to an engine version. Two small numbers rather than a script
  of option ids, so rewritten copy and renamed options leave it working. _Avoid_: a fixed
  transcript, a per-question-id table, choosing answers by reaching into the engine.
- **Rating claim** — what a seeded account's *name* promises about the rating its run
  produces: a band, and where in that band the Level must sit, as a fraction of the band's
  own width. Checked against the **stored** rating on every run, including one that
  created nothing, so an engine retune that moves `rating-barely-established` into
  Developing stops the seed by name. The band's edges come from the rating rather than
  from a second copy, so a re-cut band moves the claim with it. _Avoid_: a claim written as
  literal Levels, a check that only runs on the account this run happened to create.

Add backend-specific technical terms here as they are resolved. Anything describing the
*domain* belongs in the shared glossary instead.
