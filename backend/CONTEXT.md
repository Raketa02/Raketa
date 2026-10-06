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
- **Stream-answered idempotency** — how a create-once command recognises its own retry:
  the **creating event carries the client's idempotency key**, so *has this exact request
  already been served* is asked of the aggregate rather than of a table beside it. The
  profile commit is the first of these (`CommitPlayerProfile`,
  [ADR-0089](../docs/adr/0089-player-profile-context-event-sourced.md)). The alternative —
  an `idempotency_keys` table written in the same transaction — is a second record of one
  fact and so a second place for it to disagree, which is the dual-write shape
  [ADR-0017](../docs/adr/0017-rating-context-event-sourced.md) rejected. It answers the
  *sequential* retry; two concurrent duplicates collide on version 1 of one stream and the
  loser is told `concurrent_modification`, exactly as two concurrent assessment starts are.
  _Avoid_: "dedupe table", "request log".
- **Event-sourced aggregate** vs **persisted-with-events entity** vs **stored aggregate** —
  the three persistence shapes in this codebase, and a deliberate per-context choice.
  `User` is the first (state rebuilt from its stream); `RefreshToken` is the second (current
  state is the truth, events provide audit + cross-context notification). `SportsmanshipCard`
  is the third and so far the only one: rows, and **no events at all**
  ([ADR-0158](../docs/adr/0158-a-rating-is-one-per-person-and-the-collapse-is-the-key.md)).
  None is the default, and the third is the one that has to be argued for hardest, because
  *state changes emit domain events* is a standing rule here — it earns the exemption by
  having no life story (a card is born answered), no subscriber, and no derived standing
  anybody folds from it. Distinguish it from a **durable ledger** — the matcher's interest,
  pass, decline and deck-reset rows — which is a small fact with no aggregate around it at
  all; this has
  an aggregate, because the card and every answer on it are written together and every rule
  about who may be on it holds across the whole of it.
- **Durable event name** — the stable `"<context>.<event>"` string plus integer version
  registered in the event catalog, e.g. `users.user_registered` / v1. It is the wire
  contract for stored history and is **independent of the Python class name**.
- **Append order** (`sequence_no`) — the position a row took in `event_store`, assigned by
  the database and the **only total order over the whole log**
  ([ADR-0097](../docs/adr/0097-event-store-append-order-is-a-sequence-column.md)). It is
  the table's primary key, and the only column a read that crosses streams may order by.
  It is not a count: identity counters skip numbers on rollback. Distinguish it from
  **version**, which orders one stream and says nothing about how two interleave, and from
  `occurred_at`, the **domain moment** — one commit may append several events sharing an
  instant, so domain time is not a tie-break and must never be used as one.
  _Avoid_: "timestamp", "event number", "offset".
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
- **Outward port** — a port this backend defines and **another context implements**, rather
  than one it implements itself. The three in `modules/matchmaking/domain/ports.py` are the
  matcher's ([ADR-0098](../docs/adr/0098-matcher-demands-as-executable-contracts.md)):
  the matcher names the facts it needs and has no opinion on the provider's aggregates,
  storage or state machines. Distinguish it from a repository port, which this backend both
  defines and adapts. _Avoid_: "external port", "integration".
- **Null object** — an adapter for an outward port whose provider **does not exist**, named
  for the fact it asserts and never for being empty: `NoHoldsExist`, not
  `NullAccountHoldQuery`, because *null* reads as *not wired yet* and these are wired. It is
  not a stub or a fake — it returns what is *true today*, and stops being true on the day its
  provider lands. The rule it obeys is **a gate may be honestly empty; a term may never be
  honestly neutral**, and the test is whether a zero would be **measured** or **invented**.
  _Avoid_: stub, dummy, placeholder, no-op adapter.
- **Register** (`app/bootstrap/matcher_demands.py`) — the list of every implementation of
  every outward port, one row each, read by the **demand suite** in `tests/demands/` and
  by nothing else. It lives in the composition root because choosing implementations is what
  a composition root is for, and because a module may not import `app.bootstrap`. Registering
  an adapter enrols it in the suite; **a port with no row is a red build**, because an empty
  `parametrize` collects as *skipped* and a skipped test is one nobody is watching.
  It is ADR-0098's **contract suite**, and the directory is deliberately not called that:
  [`docs/environments.md`](../docs/environments.md)'s **Contract** tier already means
  `openapi.player.json` drift, and two suites called *contract* is how a green build starts
  being read as the wrong assurance. _Avoid_: registry (the ruleset store and the event
  catalog are already spoken for), provider list.

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
  no domain is registered, so neither has a host or a database. **No placeholder hostname is
  written anywhere**, which is why "configured" can only mean "somebody set it": there is
  nothing to compare a host against. _Avoid_: inventing `api-dev.…`; a config file naming a
  host that does not exist describes infrastructure that does not exist.
- **Deployed environment** — `development`, `staging` and `production`: everything that is
  not somebody's laptop. Selecting one without `APP_HOST`, `WRITER_DB_URL` and `REDIS_URL`
  is a startup refusal naming the missing variable. The set is *deployed* rather than
  *unprovisioned* because what makes those three defaults dangerous is that each is a
  service name out of `docker-compose-local.yml`, and that is as true of `production` as of
  the two nobody has built (#341). _Avoid_: exempting `production` on the grounds that it is
  the real one — it is the one where inheriting a laptop costs most.
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
- **Cohort** — the population behind the named accounts: sixty-odd members generated from
  one seed, committed as `app/seeds/cohort.json` and **inputs only** — never a level, an
  uncertainty or a band, because those are the engine's answers to the questionnaire each
  member sits and a committed copy of an answer is a number nothing keeps honest. It is a
  **development workbench and says so on its own artifact**: a population chosen so that
  every Play screen state is *reachable*, standing for nothing outside itself and
  describing no real market. Every draw is keyed off the member's own handle, so adding one
  changes that row and nobody else's; every coverage rule is a rule over the member's
  position rather than a rate, because at this size a 25% draw is four people on a good day
  and one on a bad one. _Avoid_: reading a rate here as evidence about anything, a μ in the
  artifact, a rule expressed as a percentage.
- **Dev console** — the backend's development surface: surface `dev`, contract
  `openapi.dev.json`, code in `app/api/dev/`. Today it is **one roster route and its gate**;
  its page — a no-build `console.html` at `/dev` that signed in as a seeded player and
  pressed searches, yeses and challenges as them — went with the challenges (#578).
  **[ADR-0194](../docs/adr/0194-the-games-test-console-acts-as-seed-accounts-and-writes-history-never-time.md)
  replaces it** with the games test console (#590), which acts as seed accounts without
  signing in, in `local` only. **It is not a client** — nothing generates types from its
  contract, which is why that document is gated by a *freshness* check and not by
  `check-contract-drift.sh`. `frontend_club/` was *"the club console"* and is gone; this is
  the only console, and saying so here is cheaper than having the collision rediscovered.
  _Avoid_: calling it an app, a second client, an admin panel.
- **Console gate** — `CONSOLE_SERVED` in `app/api/dev/gate.py`: where the dev console is
  served, written out per environment with the same `_undecided` refusal the **Seed guard**
  carries. ADR-0194 narrows it to `local` and makes the data half a refusal
  (#590). **A second table, and never `SEEDABLE`** — the same answer today to a different
  question, and deriving one refusal from another is what `guard.py`'s own comment argues
  against. The refusal sits at the top of `routes.py` rather than in the package's
  `__init__`, which is where the seed system puts its own and is **wrong here**:
  `create_app` reads the table in every environment to decide whether to mount anything, so
  a package that refused on import would make a production deployable crash at startup
  reading its own dev tool. Beside it the data half is a **filter, not a refusal** — a seed
  account is one addressed on the reserved `.example` TLD — so *gated structurally and by
  data* resolves asymmetrically: the structural gate is a check and the data gate is a
  **consequence**, since production has no such accounts. Both hold; only one can fail.
  _Avoid_: deriving it from `SEEDABLE`, putting the refusal where the mount reads it,
  making the roster *refuse* a non-seed address (it would be theatre — the login route any
  browser reaches takes any credential).
- **Served vocabulary** — a closed domain constant the platform owns, held in exactly one
  module of the context that owns it and exposed **read-only** over the player API so no
  client hardcodes it. Two exist: the `Sport` registry at `GET /api/v1/sports`, and the
  Social tag vocabulary — with how many of it a profile must hold, and the Search
  radius bounds — at `GET /api/v1/player-profile/options`. What crosses the wire is
  **ids, grouping and numbers** — never a label, because the backend emits machine codes
  and never display text, and a preformatted string can only be one rendering in one
  language. The rule is
  enforced rather than remembered: a walk over `app/` fails on a string literal equal to a
  tag id anywhere outside the vocabulary module, because the failure it prevents — the
  onboarding picker and the profile editor holding two lists that have drifted — is
  invisible until a player sees a tag the engine has never heard of. _Avoid_: a second
  copy in a client, a served label, shipping the list in an app-store release.

- **Photo storage port** — the seam photo bytes live behind
  (`app/modules/player_profile/domain/ports.py`, [ADR-0091](../docs/adr/0091-photo-storage-behind-a-port.md)).
  One S3-compatible adapter serves both deployments: MinIO on a laptop and AWS S3 deployed
  are the same class with a different endpoint, which is why the deployed answer is a
  setting rather than a migration of live user data. **Every method takes a `PhotoRef` —
  the owner and the photo id together** — so ownership is part of the port's contract
  rather than a check each caller has to remember, and the S3 adapter renders it as a key
  prefix. _Avoid_: a bare photo id in a signature, a second adapter class whose body is a
  copy, bytes in Postgres.
- **Re-encode on receipt** — every uploaded image is decoded to pixels and written back
  out as JPEG at a capped long edge, always, whatever arrived. **This is how EXIF is
  stripped reliably rather than best-effort**: nothing is carried across because nothing
  copies it, where a scrubbing pass is a list of tags somebody has to keep complete. EXIF
  is not a detail — it carries GPS, which the product's privacy rules put in the row
  nobody ever sees. The orientation tag is *applied* before it is dropped, or every phone
  photo is stored sideways. _Avoid_: storing what arrived, a tag-deletion pass, dropping
  orientation without honouring it.
- **Presigned URL** — how a photo is served: a short-lived signature the object store
  honours directly, so bytes never cross this API twice. **Signing is offline
  computation**, not a lookup, so an endpoint that hands one back without checking the
  object exists returns a working-looking URL for a photo that is not there. Two endpoints
  are configured rather than one, because the URL this process *calls* is a
  server-to-server address and the URL a *phone* opens is a public-network one, and SigV4
  signs the host. _Avoid_: a public bucket, a long window, signing before checking, signing
  against the internal endpoint.
- **Photo review port** — the seam the on-court content check sits behind
  (`app/modules/player_profile/domain/ports.py`, [ADR-0091](../docs/adr/0091-photo-storage-behind-a-port.md),
  [ADR-0129](../docs/adr/0129-the-photo-check-is-a-sidecar-the-backend-asks.md)). It runs
  server-side, because a client-side check is trivially bypassed, and it **soft-warns and
  never blocks**: the verdict rides on the stored object as metadata, and a flagged photo
  is still stored. The port says *look at this image and tell me what you conclude*, so
  nothing above it knows whether the answer came from a model, a pass-through, or a queue
  of humans. _Avoid_: a `REJECTED` verdict nothing has earned, a third decision value for
  *the reviewer was unreachable*, copy claiming an enforcement that is not running, a
  client-side check.
- **Photo review sidecar** — the container that holds the model, reached over HTTP
  (`docker/photo-review/`, `ClipSidecarPhotoReview`). It answers **one raw cosine
  similarity per caption** and holds **no policy**: not the captions, not the temperature,
  not the threshold, and no concept of a verdict. Those are the backend's, beside the size
  caps in `player_profile/domain/photos.py`, because they are behaviour a domain test can
  observe — so the rule is re-tunable with no change to the service and the model is
  swappable with no backend release. Keeping `torch` out of the API image is what let the
  check ship ahead of the player card rather than behind it. _Avoid_: a threshold or a
  prompt in `app/core/config.py`, the sidecar returning a decision, the API waiting for the
  container to be ready.
- **Review evidence** — what a verdict records beside its decision, in the `review-note`
  metadata key: the model, the prompt-set fingerprint, the confidence and the raw
  similarity vector — on allowed photos as much as flagged ones. It is what makes today's
  threshold safe to be a **declared placeholder**: a real one is derived later by reading
  stored objects, without re-running inference over the corpus. The fingerprint is derived
  from the captions as asked rather than declared, so it cannot describe a set it does not
  match. _Avoid_: recording only the decision, a hand-maintained prompt-set version, a note
  a player could ever be shown.
- **Fails open** — what the reviewer does when it cannot be asked: `allowed`, with a note
  naming which failure it was, from a closed set (`timeout`, `transport`, `status`,
  `malformed`). A reviewer that turned its own outage into a failed upload would refuse a
  real player's first photo for a reason that is not about the photo. The set is closed
  because *which photos need re-reviewing* has to be a query, not a guess. _Avoid_: an
  upload that fails when the sidecar is down, an unavailability recorded as an ordinary
  allowed verdict, a free-text reason.
- **Decode cap** — the ceiling on an image's *declared* dimensions, read from the header
  before a pixel is allocated, and a **separate question from the byte cap**. Both PNG and
  HEIF compress uniform data enormously, so a file well inside the byte cap can decode to
  tens of gigabytes — the decompression bomb, which the byte cap cannot see because the
  file really is small. Pillow's own guard is pointed at the same number, so the two agree
  by construction rather than by being maintained in step. _Avoid_: one cap standing in for
  both, a warning where a refusal belongs, checking size after decoding.
- **Scheduled job** — work that runs because an interval elapsed, as an `asyncio` loop
  hosted by the API process (`app/infrastructure/jobs/`,
  [ADR-0092](../docs/adr/0092-periodic-jobs-as-embedded-loops.md)). Distinct from the
  **`EventWorker`**, which drains a queue as fast as it fills; they share the loop and
  nothing else. **A job must be idempotent and safe to run beside itself**, because with N
  API processes it runs N times per interval with no lock anywhere — that requirement is
  what let the platform avoid owning a scheduler at all. Registered in
  `app/bootstrap/jobs.py`, built from the composition root, first run at startup rather
  than after the first interval. _Avoid_: cron, beat, a leader election, a job that must
  run exactly once.
- **Uncommitted photo** — a photo the object store holds that no committed profile
  currently names. It is the ordinary state of every upload between the upload and the
  commit, and the permanent state of one whose commit never came; the **sweep** deletes
  those older than the retention window. *Currently* is load-bearing: a photo dropped from
  a profile is as unreachable as one never committed, so it is the same orphan. _Avoid_:
  "orphan" as a status stored anywhere — it is a question asked of the store and the
  stream, never a field.
- **Review standing** — what the metadata on a stored photo says about whether anybody
  ever looked at it, read off the `review-note` key and nothing else
  ([ADR-0132](../docs/adr/0132-a-re-review-is-the-same-reviewer-and-a-stale-prompt-set-is-not-one.md)).
  Three values, because there are three populations: **never asked** (no note — the
  pass-through era, and also any note nothing can parse), **unavailable** (`unavailable=…`
  — the sidecar was down when the photo arrived, and this population keeps growing), and
  **reviewed** (`clip;m=…;p=…;c=…;s=…` — an image was really scored). It is **not** the
  same question as the verdict: a photo is `allowed` both when a model scored it and when
  nothing was asked, which is the confusion that made #197 necessary. _Avoid_: a status
  column, a second table, "reviewed" as a boolean on the object.
- **Re-review backfill** — the scheduled job that asks the reviewer about the photos
  nobody ever asked it about: standings *never asked* and *unavailable*. It re-reviews
  **through the same `PhotoReview` port the upload path holds**, so there is one copy of
  the rule and a batch cannot disagree with an upload about one image; it never rewrites a
  note that is already right, because an S3 metadata update is a copy of the object onto
  itself. _Avoid_: calling it a re-scan or a migration, and calling anything that applies
  its own threshold a backfill.
- **Superseded prompt set** — a photo whose standing is *reviewed*, against a
  `PROMPT_SET_FINGERPRINT` that is no longer the current one. **Counted, never
  re-reviewed**: whether captions that have moved are worth re-running is a judgement
  nobody has made, and the fingerprint exists so that the question is answerable rather
  than so that a job can act on it. _Avoid_: folding it in with the two populations that
  are work.
- **Retention window vs cadence** — the pair that must not swap places. *How old an
  uncommitted photo must be before it is swept* is a rule a domain test can observe and
  lives beside the size caps in `player_profile/domain/photos.py`; *how often the sweep
  runs* is `PHOTO_SWEEP_INTERVAL_SECONDS` and is operational. The **environment may select
  configuration; it may never select behaviour** — and a deletion the environment could
  make happen sooner is exactly that. _Avoid_: a configurable retention window, a cadence
  hard-coded in the domain.

- **Ruleset store** — where the released **Ruleset** dataset lives:
  `app/modules/matchmaking/infrastructure/rulesets/`, a package rather than a table,
  because a ruleset ships embedded with the code and the runtime store is deferred
  ([ADR-0093](../docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md)).
  **The engine owns the shape and the module owns the data**: `Ruleset` and
  `validate_ruleset` are the engine's, the dataset is here, and the day the runtime store
  lands it replaces this package rather than growing beside it. Since the ranking went
  (#580) a ruleset is two sections — the balance rules and each kind of game's level
  tolerance — and one release is carried. _Avoid_: "config", "settings" — the environment
  may select configuration and may never select a ruleset.

- **Ephemeral store** — the process's Redis, holding a room's **live channel** and its
  **typing roster** and nothing else. Every message is a durable row before anything is
  published, so an unreachable store costs a room its liveness and never anybody their
  message ([ADR-0093](../docs/adr/0093-matcher-in-the-backend-with-a-pure-match-fit-engine.md),
  ADR-0147). Its **address** is configuration (`REDIS_URL`). The matcher's exposure and
  suppression ledgers were its first readers and went with the searches (#579). _Avoid_:
  "cache" alone for it — nothing here is recomputed from anything.
- **Nudge** — one of the live channel's **two** frames, and the one that says a room moved:
  `{v, conversation_id, last_seq}`, and never content
  ([ADR-0147](../docs/adr/0147-the-live-channel-carries-a-nudge-and-the-sequence-is-what-cannot-be-swapped.md)
  §3; it was the whole payload until
  [ADR-0156](../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)
  added *somebody is typing* beside it). It rides Redis pub/sub from an append to whichever servers hold an open stream, and
  it rides Server-Sent Events from there to the phone — **the same three fields both hops**,
  which is what makes at-most-once on either leg one harmless risk rather than two. It is
  **news and not a cursor**: the client fetches from *its own* high-water mark through the
  ordinary read path, so a lost frame is repaired by the next one for free and *may the UI
  draw what it did not read from the authoritative path* becomes a thing the wire cannot
  express. `last_seq` is the conversation row's allocator, so publishing costs no second
  read. _Avoid_: calling it an event or a message — it announces that a room moved and says
  nothing about what moved it, and the day it carries an entry the self-healing property is
  gone.
- **Typing heartbeat** — *this player is typing, as of now*, written to Redis with `TYPING_TTL`
  on it and never anywhere durable
  ([ADR-0156](../docs/adr/0156-the-live-channel-carries-presence-and-a-heartbeat-is-the-only-honest-shape.md)).
  **A heartbeat and not a state**: there is no *stopped* call and there will not be one, because
  every way a client can vanish — killed app, lost signal, dropped request — is a way a *stopped*
  fails to arrive, and each of them would leave a room saying somebody is typing for ever. **The
  TTL is what clears it**, which makes the failure mode the indicator *vanishing* rather than
  sticking, and it must exceed `TYPING_CADENCE` or the indicator flickers on somebody still
  typing. _Avoid_: a `typing: bool`, a rate limiter (the TTL is what bounds repetition), or a row
  in Postgres — presence is the one fact here that must not outlive the room it is about.
- **Typing roster** — *who is typing in this room right now*, which is **whatever has not
  expired**. Read once per `TYPING_CHECK` by each open stream, as one keyed lookup: an index set,
  `typing:{conversation}`, names who has typed lately so the read never has to scan the key space
  or know who is *in* the room — and that index is a **hint**, since a member is reported only if
  their own `typing:{conversation}:{player}` key is alive. The read writes nothing. _Avoid_:
  reading it as evidence of anything — there is no *who stopped*, no *since when*, and no way to
  ask about a moment other than this one.
- **Typing frame** — the live channel's second frame, `{v, conversation_id, player_ids}`, named
  `typing` on the SSE `event:` field. **It carries no `last_seq` and moves no sequence**: it is not
  an entry, nothing was appended and the gapless allocator was never asked for a number — the one
  invariant of ADR-0156. `player_ids` is sorted by the sender (ADR-0105) and **never contains the
  reader**, who is filtered out on the way out because only the stream knows whose it is; an empty
  list is how an indicator goes away, and it is the only clear there is. _Avoid_: a discriminator
  inside the JSON — the event name is the kind, so a frame a client has never heard of is dropped
  by the transport rather than by a branch somebody remembered to write; and bumping
  `LIVE_CHANNEL_VERSION`, which would tell every shipped phone the envelope it parses had changed
  when it had not.
- **The conversation channel** — `conversation:{id}`, one Redis pub/sub channel per room,
  subscribed and unsubscribed as streams open and close. Keyed on the **conversation and
  never on a member**: per-user would force *who is in this room* into the append path, and
  membership is derived from whichever record is arranging — a read bought to gain nothing.
  Nothing is retained on it, which is the point: a subscriber that misses a notification
  loses **latency, not data**. _Avoid_: Redis Streams here — durability on this leg buys
  nothing a nudge does not already give away.
- **Publisher soft, subscriber loud** — the two postures of the live channel's **bus**, and their
  asymmetry is the whole degradation story. (Presence is on neither side of it: both typing ports
  fail soft, and ADR-0156 §6 argues the departure — a roster is a courtesy read on the *command*
  client, so failing it loud would let a merely slow store close every healthy stream.) A publish happens **after** the append has
  committed, so `FailSoftNudgePublisher` swallows an outage: a room loses its liveness and
  nobody loses a message. A subscription **is** the liveness, so it is unwrapped and a
  failure closes the stream — **a chat that is not live has to look not-live**, because a
  connection held open delivering nothing looks up to date (ADR-0147 §8). `/health` stays
  about the **process** for the same reason it is safe to close: a health check that pinged
  Redis would take sign-in, onboarding and the games down with the chat. _Avoid_: wrapping
  the subscriber "for symmetry" — the symmetry is what would hide the outage.
- **The subscriber's own client** — the process's **second** Redis client, from
  `create_redis_subscriber_client` and opened by the lifespan beside the command pool.
  Connecting is bounded at `REDIS_CONNECT_TIMEOUT_SECONDS` and reading is not bounded at
  all, because on a subscription **waiting is the operation** and a `socket_timeout` there
  does not reconnect quietly — it raises at the caller every two seconds and loses whatever
  was published in the gap ([#342](https://github.com/Raketa02/Raketa/issues/342)). One
  client per **process**, not per stream: each open stream takes a `PubSub` off it. _Avoid_:
  putting a blocking read on the pool a player's critical path draws commands from.
- **Stream item type** — what a generator route yields, and the thing FastAPI 0.136.1
  detects **once** and loses on every `include_router`. `app/api/streaming.py` puts it back
  on the finished application, which is what makes the live envelope generated into
  `openapi.player.json` rather than documented as an opaque string, and what makes every
  frame validated through the declared model on the way out. **It has a second half since
  ADR-0156**: a route that names its own SSE events must yield a `ServerSentEvent`, which the
  framework reads as *this route declares nothing*, so the shim takes the narrowed `data`
  annotation off a subclass instead — without it, adding the typing event would have deleted
  `LiveNudgeSchema` from `components.schemas`. It is a dated shim with a test that goes red if it
  stops matching. _Avoid_: hand-writing the SSE `itemSchema` in `openapi_extra` — that is the
  mirror of a backend response ADR-0006 exists to forbid.
- **Mail queue** — the `mail_queue` table, and the **second queue** beside the transactional
  outbox ([ADR-0186](../docs/adr/0186-email-goes-through-a-port-and-a-purged-queue.md) §2). A use
  case that sends an email **renders it whole** — recipient, subject, plain text and HTML, link and
  code — and writes it here through the `MailQueue` port **in its own transaction**, so the email
  and the act that caused it commit together. It is the one place a secret sits, for as long as it
  takes to send it. _Avoid_: putting an email on the outbox — the outbox carries domain events,
  and a domain event may never carry a secret.
- **Mail worker** — the `mail-delivery` `PeriodicJob` that drains the mail queue through
  `DeliverQueuedMail`: one message per transaction, claimed `FOR UPDATE SKIP LOCKED`, sent through
  the **Mailer** port, then **purged** — `text_body` and `html_body` cleared, the kind, recipient,
  subject and delivery record kept. A refused send waits on `RETRY_AFTER` and is tried again; once
  the retries are spent it is **given up on and purged all the same**. At least once. _Avoid_:
  treating `MAIL_DELIVERY_ENABLED=false` as *not sending* — it is a table of live secrets nobody
  receives.
- **Mailer** — the port that sends one rendered message (`SmtpMailer`: the dev stack's Mailpit
  locally, a relay once a domain exists). The API suite reads a `RecordingMailer` through the
  `mailbox` fixture, after draining both queues. _Avoid_: calling a mailer from a use case.
- **One-time credential** — a **link token** (256 random bits, in a URL) and an **8-character
  code** issued together, in the `one_time_credentials` table and never in an event
  ([ADR-0184](../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
  §3–§4). **Both are stored hashed** — the token by SHA-256, the code by the password hasher,
  because the code is the one small enough to guess — and **the code is derived from the token**
  (`credential_code.py`), so a page holding the link can show its code without either being
  stored readable. A purpose (`invitation`, `club_reset`, `forgot_password`) sets its lifetime and
  an audience says which surface may use it. Its **standing** — valid, expired, used, locked — is
  folded from the clock and the row, never stored. A newer credential for the same subject
  **retires** the older ones of its purpose — or of every purpose the issuer names: an
  Administrator's `invitation` and `club_reset` retire each other, because both open the same
  page for the same person. One mechanism, `OneTimeCredentials`, for every flow that issues one;
  `verify_code` and `grant_ticket` are its claim split in two, so the invitation's claim can
  answer *sign in to accept* between them, to somebody holding the right code and nobody else.
- **Claim ticket** — what a **right** code is exchanged for: a second random secret, stored hashed
  on the credential, good for `TICKET_LIFETIME` and never past the credential's own deadline. The
  new password is set with it, so guessing is bounded to the claim, which is the one place wrong
  codes are counted. A claim is not a use; claiming again replaces the ticket.
- **Credentials-changed instant** — `users.credentials_changed_at` and
  `club_accounts.credentials_changed_at`: the `occurred_at` of the account's last
  `PasswordChanged` / `ClubAccountPasswordChanged`, on the row each surface already reads per
  request. An access token whose **issue instant** is strictly before it is refused
  (`access_token_revoked`). The issue instant is the token's `iat_us` claim — **microseconds, on
  the application's clock** — because a whole-second `iat` would refuse the very session a reset
  opens, and an instant on another clock than the one that wrote the change would disagree with it
  in every test that moves time. _Avoid_: comparing against `iat`.
- **PasswordAccounts** — the auth port *Forgot password?* recovers through, answered **per
  audience** as `SessionHolders` is: `UserPasswordAccounts` for the player app,
  `ClubPasswordAccounts` for the club website. Each records the change on its own stream.
- **Public surface** — `/api/v1/public`, emitted as `openapi.public.json`, which only the public
  site generates from
  ([ADR-0187](../docs/adr/0187-four-deployables-the-club-website-and-the-public-site-live-in-this-repo.md)
  §4–§5): what a group link, an invitation email or a reset email opens without the app. **No
  route on it takes a session**, and its document carries no bearer scheme —
  `tests/unit/test_public_surface.py` refuses one. It **discloses the least a page needs**: a
  group's row and its club, never anybody in it; an invitation's name — whole, as the club typed
  it (ADR-0171 §4) — club and standing, and its code while it is valid, recomputed from the link;
  a reset's standing and nothing else. A link token travels in a body, a group's code in the
  path. **Its two password routes sign nobody in**: `SetInvitationPasswordWithoutSigningIn` and
  `SetNewPasswordWithoutSigningIn` call the very rules the app's `SetInvitationPassword` and
  `SetNewPassword` call — one class per flow — and commit where those issue a token pair, so the
  page and the app cannot come to two answers about one link. _Avoid_: a second copy of a
  password rule for the web; a token in a public path; a first name cut out of a name.

- **Invitation sender** — `InvitationSender`, where the invite, a resend and the club's reset all
  end, so the three choose **which email** by one rule read off the account at the moment of
  sending and recorded nowhere: an account that can sign in is asked to accept in the app, with
  no credential; anybody else has a password to set and is sent a link and a code — the reset's
  while one is pending, the invitation's otherwise
  ([ADR-0186](../docs/adr/0186-email-goes-through-a-port-and-a-purged-queue.md) §3).
- **Administrator guard** — `AdministratorAtClubDep`: the request dependency every administrator
  operation declares, reading **an active administratorship of this account at the club its own
  path names** on every request, and refusing with `403 not_an_administrator`
  ([ADR-0184](../docs/adr/0184-an-administrator-is-invited-by-a-club-and-a-one-time-credential-never-enters-the-event-store.md)
  §7). It is also the only writer of **last used**, at most once an hour and in its own commit —
  the one column on `administrators` no event carries.
- **AccountHolders** — the Administrators context's demand on `users`: the account behind an
  address, opening one by invitation, setting or clearing its password, and **acts as a player**
  (attested, or holding a Player profile). Every write is `users`' own, on the User's stream
  (`InvitationAccounts`); the adapter only translates.
- **Attested player** — `AttestedPlayerDep`, what starting an assessment and committing a Player
  profile take instead of the current user: the account **refused with `403
  adult_attestation_missing` unless its stream holds the Adult attestation** (ADR-0185 §5). Read
  off the stream, because the `users` row has no column for it — and a `User` read from the row
  carries `adult_attested=None`, meaning *not read here*, never *not attested*.

Add backend-specific technical terms here as they are resolved. Anything describing the
*domain* belongs in the shared glossary instead.
