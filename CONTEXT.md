# Rakieta — Domain Context

The shared, ubiquitous language for the whole system. When you name a concept — in an
issue, a test, a type, a refactor proposal — use the term as defined here. All three
apps obey this file; see [`CONTEXT-MAP.md`](CONTEXT-MAP.md) for how the vocabulary is
split, and [`docs/adr/`](docs/adr/) for the decisions behind these terms.

Rakieta is a racket-sport platform. Players find and book courts through the
**player app**; clubs manage those courts through the **club web app**; both are served
by one **backend** built on Clean Architecture (hexagonal ports & adapters), DDD, and
event sourcing.

> This is a living document, grown deliberately. Terms are added as decisions are
> actually resolved — not invented ahead of the code. Don't drift to synonyms it avoids.

---

## Part 1 — Implemented bounded contexts

These exist in `backend/app/modules/` today and are the authority for their terms.

### Users (`backend/app/modules/users/`)

Identity and account state.

- **User** — **event-sourced aggregate**: its state is rebuilt from a stream of domain
  events. Constructed only via `User.register(...)` or rehydrated via
  `User.from_history(events)`. Carries an `EventRecorder`; the application layer drains
  pending events with `pull_events()`.
- **Authority** — role enum, `USER` or `ADMIN`.
- **Email** — value object. Trimmed, lower-cased, RFC-ish validated, ≤ 320 chars.
- **Nickname** — value object. Trimmed, 2–64 chars, `[A-Za-z0-9_.-]`.
- **RawPassword** — the plaintext at the boundary; 8–128 chars with ≥1 letter and ≥1
  digit. Carrying it as a type is what prevents hashing an unchecked string.
- **HashedPassword** — non-empty bcrypt hash; the only password form ever persisted.
- **User events** (durable name / version):
  - **UserRegistered** — `users.user_registered` / v1 — first event of every stream.
  - **UserDisabled** — `users.user_disabled` / v1.
  - **UserPromotedToAdmin** — `users.user_promoted_to_admin` / v1.

**Invariants**
- Email and nickname are **unique** — `RegisterUser` reads both before insert and
  raises `EmailAlreadyRegistered` / `NicknameAlreadyTaken` (a domain conflict, not a
  database constraint violation).
- **`disable()` is idempotent** — a no-op on an already-inactive user.
- **An inactive user cannot be promoted** — raises `InactiveUserCannotBePromoted`.
- `promote_to_admin()` is a no-op if already `ADMIN`.

### Auth (`backend/app/modules/auth/`)

Authentication and session lifecycle.

- **RefreshToken** — a **persisted entity that emits events** (not event-sourced).
  Stores the bcrypt `token_hash` and `jti` — **never the plaintext** —
  plus `refresh_expires_at`, `is_valid`, `revoked_at`.
- **Access token** — short-lived JWT for API calls (`ACCESS_TOKEN_EXPIRE_SECONDS`).
- **Refresh token** — longer-lived, **rotating** credential
  (`REFRESH_TOKEN_EXPIRE_SECONDS`).
- **Rotation** — on refresh the old token is revoked and a new one issued atomically
  (`RefreshToken.rotate_to(...)`); reusing a rotated token is rejected (replay
  protection).
- **TokenService** — port for signing/decoding JWTs (`JwtTokenService` adapter).
- **PasswordHasher** — port for bcrypt hashing (`BcryptPasswordHasher` adapter).
- **Auth events** (durable name / version):
  - **RefreshTokenIssued** — `auth.refresh_token_issued` / v1.
  - **RefreshTokenRevoked** — `auth.refresh_token_revoked` / v1.
  - **RefreshTokenRotated** — `auth.refresh_token_rotated` / v1.

**Invariants**
- **Logout is idempotent** and never reveals whether a token existed.
- `revoke()` / `rotate_to()` are no-ops on an already-invalid token.
- Login returns **the same error** for unknown-email and wrong-password
  (`InvalidCredentials`) — no account enumeration.

---

## Part 2 — Planned bounded contexts

The racket-sport domain proper. **These are not modeled yet** — no code, no events, no
committed terms. They are listed so that work lands in the right context from the first
commit, and so nobody invents a fourth name for the same idea.

| Context | Intent | Likely home |
| --- | --- | --- |
| **Clubs** | The tenant: a venue that owns courts, staff, opening hours, pricing. | `backend/app/modules/clubs/` |
| **Courts** | The bookable resource: surface, indoor/outdoor, sport, availability rules. | `backend/app/modules/courts/` |
| **Bookings** | A player's reservation of a court for a time slot. Cancellation, no-shows, payment state. | `backend/app/modules/bookings/` |
| **Matches** | Players organising play: open matches, joining, levels, results. | `backend/app/modules/matches/` |

> **Do not treat this table as settled design.** It records intent and naming, not
> aggregates, invariants, or ownership. Before writing code in one of these, resolve
> its terms into Part 1 above and record the shape in an ADR. In particular, whether a
> given context is **event-sourced** (like `User`) or **persisted-with-events** (like
> `RefreshToken`) is a real decision with real consequences — make it deliberately, per
> context, and write it down.

Open questions that must be answered before Bookings exists — flagged here so they are
not silently assumed away:

- Is a **Booking** owned by the Court, the Club, or standing alone with references?
- Is availability a **projection** over bookings, or its own stored concept?
- What is the **tenancy spine** — `Club → Court → Booking`? Where do players attach?
- Which side owns **cancellation windows and pricing** — Club config or Booking policy?

---

## Cross-cutting concepts

These are real and implemented; they apply across every context.

- **DomainEvent** — frozen dataclass with `occurred_at`; the unit of state change.
- **EventRecorder** — composed into aggregates/entities; collects events until drained.
- **DomainEventStore** — the append-only event log (`event_store` table). `append(...)`
  takes an `expected_version`; a mismatch raises **`EventStreamVersionConflict`**
  (optimistic concurrency).
- **Transactional outbox** — the `event_delivery_queue` table. Use cases enqueue events
  here **in the same transaction** as the state change, so side effects never run
  inline. See [ADR-0003](docs/adr/0003-transactional-outbox-for-event-delivery.md).
- **EventWorker** — the embedded poller that drains the outbox (`SELECT … FOR UPDATE
  SKIP LOCKED`) and dispatches to handlers after commit. Toggle:
  `EVENT_DELIVERY_WORKER_ENABLED`.
- **Event catalog** — registry mapping each event class to a stable durable **name** and
  **version**, so the JSON codec serializes by contract rather than by Python class
  name. Renaming a class must never change the wire format of stored history.
- **Port / adapter** — domain and application depend on `Protocol` ports; infrastructure
  implements them; wiring happens at the FastAPI boundary
  (`backend/app/api/dependencies.py`).
- **UnitOfWork** — the transaction boundary port (`AsyncSqlAlchemyUnitOfWork` adapter).
- **Read model** — the `users` table projection, written via `project_registered`, kept
  separate from the append-only event stream (CQRS-lite).

## Terms the clients must not reinvent

Both frontends describe the same nouns. A concept that exists in this glossary keeps
its name in TypeScript: a `Court` is a `Court`, not a `Venue`, `Facility`, or `Pitch`.
Client-only *technical* vocabulary (wire type, DTO, mapper, BFF route handler, secure
store) belongs in that app's own `CONTEXT.md`, never here.
