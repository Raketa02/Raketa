# Raketa — Domain Context

The shared, ubiquitous language for the whole system. When you name a concept — in an
issue, a test, a type, a refactor proposal — use the term as defined here. All three
apps obey this file; see [`CONTEXT-MAP.md`](CONTEXT-MAP.md) for how the vocabulary is
split, and [`docs/adr/`](docs/adr/) for the decisions behind these terms.

Raketa is a racket-sport platform. Today it does one thing end to end: a player signs up,
signs in, and answers a questionnaire that gives them a **Skill rating** per sport. That is
served by the **player app** and one **backend** built on Clean Architecture (hexagonal
ports & adapters), DDD, and event sourcing.

> This is a living document, grown deliberately. Terms are added as decisions are
> actually resolved — not invented ahead of the code. Don't drift to synonyms it avoids.
>
> **It was cut back on 2026-08-25.** The repository was reset to the finished features, and
> every term that named removed code went with it — the club console, the pairing and Match
> Fit engines, the kernel's money module, and the whole planned-context list (Clubs, Courts,
> Bookings, Matches, Money, Now). What remains is what the code actually says. See the
> [ADR index](docs/adr/README.md#the-2026-08-25-reset--why-the-sequence-has-gaps) for why
> the ADR numbers have gaps. Naming something new in the racket-sport domain is now an open
> question again, not a lookup: read [`docs/agents/domain.md`](docs/agents/domain.md) first.

---

## Part 1 — Implemented bounded contexts

These are the authority for their terms. There is no Part 2: after the reset, no term is
committed ahead of *a decision*, and a speculative list of context names is not one. A
context that does not appear below has no vocabulary yet — resolve its terms into this file
before writing it, which is what the last section below is: **Player profile** is settled in
an accepted ADR and is being built, and its terms are here because that is the order this
file asks for, not because the code landed first. Every other section describes code that
exists in `backend/app/` today.

### Skill rating (`backend/app/modules/rating/`)

What the platform believes about how well a player plays one sport, and how sure it is.
A rating is **never only a number**.

- **Skill rating** — an **event-sourced aggregate**, one per (player, sport).
- **Level (μ)** — the current best estimate on a fixed **1,0–5,0** scale. Public. **5,0 does
  not mean professional**; it means at or above the top of the competitive amateur
  population this marketplace exists to match.
- **Uncertainty (σ)** — how unsure the platform is. **Skill and certainty are separate
  variables**: two players both showing 3,0, at ±0,15 and ±0,90, are not the same player,
  and matchmaking reads the record rather than the headline.
- **Confidence** — σ restated as a percentage for the player, `100 × (1 − σ/1,20)`, capped
  at 99. **Never 100** — the platform cannot claim total certainty about anybody.
- **Likely range** — μ ± σ, clamped to the scale. The player's own range, and the only
  range shown to them; a band's numeric edges are not a second range to compare it against.
- **Band** — one of four named ranges, deliberately uneven in width, each with a
  plain-language meaning: **New** 1,0–1,5 · **Developing** 1,6–2,6 · **Established**
  2,7–3,8 · **Advanced** 3,9–5,0.
- **Rating status** — **Initial Estimate** (onboarding output, no counted matches) →
  **Calibrating** (real matches started, still moving) → **Stable**.
- **Volatility** — how fast the estimate currently appears to be moving.
- **Assessment** — an **event-sourced aggregate**: one adaptive questionnaire run, for one
  player and one sport.
- **Transcript** — the answers a run has given, in order, each as a question and the option
  chosen for it. It is what the engine reads and the *only* thing it reads: given the same
  transcript the engine always returns the same next question and the same rating. It is a
  **projection over the assessment's stream**, not a second record beside it, which is why a
  run resumed on a fresh install or a second handset still has all of it.
- **Revision** — changing an answer already given. It **truncates** the transcript at that
  question: every answer after it is discarded, because each was pitched at a difficulty
  chosen from the estimate as it then stood, so an answer that outlived a change to an
  earlier one would mean something the player never said. Re-selecting the option already
  recorded is not a revision and changes nothing.
- **Stop** — the moment the engine judges that no remaining question would meaningfully
  tighten the estimate. The questionnaire ends there and *nothing is rated*: the run sits
  in progress with nothing outstanding, and every answer stays revisable. A stop is a fact
  about the transcript rather than a state anything records, so it is asked of the engine
  and never stored.
- **Completion** — the separate, explicit act that ends an assessment and brings its Skill
  rating into existence. This is the irreversible moment, and the only one — which is what
  lets a player see every answer laid out, still changeable, before it becomes a number.
  Stopping and completing are deliberately two moments and not one.
- **Claim** / **demonstration** — every answer is one or the other. A claim is a statement
  about standing (how often you play, what you compete in, how you do against your usual
  group). A demonstration is a statement about what you do inside a point.
- **Contradiction** — a gap beyond tolerance between fused claims and fused demonstrations.
  *"I regularly compete in strong club matches"* against *"I almost never maintain a basic
  rally"* is one. A strong smash and a weak backhand is not — that is an **uneven profile**,
  and it widens the range without being called a contradiction.
- **Layoff** — declared time away from the sport, asked only of players with a history.
- **Evidence trail** — the account a rating gives of itself: what the platform concluded
  and why. It has two halves and they are deliberately kept apart, because they answer
  different questions. **What moved the level** — each kind of evidence the player gave,
  fused on its own, and where that sits relative to the estimate they were given. **What
  widened the range** — a layoff, a contradiction, an uneven profile, each reporting how
  much uncertainty it actually added. Something that widened the range did not move the
  level, and saying otherwise would describe a different rating than the one produced.
- **Calibration priority** — how urgently a rating wants real matches to settle it. Raised
  when the assessment ended on evidence the questionnaire could not resolve. It is a
  statement about the *estimate*, never about the player, and it changes who they are
  matched with, never where they sit.

**Invariants**
- **A level is proved, never declared.** Not by the player, not by staff, not by a club.
  Manual editing is refused by the domain itself, not guarded by a permission check.
- **Only the rating context writes μ, σ, volatility and status.** Every other engine
  contributes evidence, an information weight, or an anomaly signal — never a rating point.
- **Absence widens, it never lowers.** Layoff and inactivity add to σ and never touch μ. A
  player who was 3,20 two years ago has no obligation to still be 3,20 — and no obligation
  to have got worse. The honest position is *we are less sure*, not *we assume decline*.
- **A contradiction is never resolved by picking a side.** It widens the range and raises
  calibration priority; it never moves the player up or down, and it never accuses them.
  Resolution has no direction, which is what stops under-reporting being profitable.
- **Onboarding cannot produce confidence above 30%.** The questionnaire is the entire
  evidence surface and self-report has an irreducible ceiling, enforced as a floor on σ
  rather than as a display cap. Everyone leaves onboarding as an *Initial Estimate*.
- **A rating explains itself, and the explanation is computed, never authored.** Which way
  a kind of evidence pulled is decided by comparing it against the estimate, and which
  reason is given for the confidence is decided by whichever thing widened the range most.
  Nobody writes down that standing pulled a player up; the arithmetic says so, or it does
  not. Retuning a constant therefore moves the explanation with it, and an explanation
  cannot quietly drift out of step with the number it explains.
- **A rating carries the engine version that produced it.** Every constant in the engine is
  a hypothesis with a measurement that would falsify it — and you cannot falsify one you
  cannot attribute a rating back to.
- **A revision shortens the past; it never edits it.** The change is *appended* to the
  stream and nothing is deleted, so what a player answered first, and what they changed it
  to, are both permanently recoverable. Only the transcript — the projection — gets shorter.
  A player changing their mind is data to learn from rather than a gap
  ([ADR-0020](docs/adr/0020-revisable-assessment-answers.md)).
- **An answer is revisable for as long as its run is, and no longer.** Once a run has
  produced a Skill rating, its answers are settled: the account of a player stops moving at
  the moment the platform starts relying on it. This is the same invariant as *a level is
  proved, never declared*, read from the other end.
- **The questionnaire stopping is not the rating existing.** Stopping is the engine having
  heard enough; completion is a separate act that a player performs, and only completion
  creates a rating. Nothing that ends the questioning — the last answer, or a revision that
  reaches the beginner fast path — may create one as a side effect, because a player must
  be able to see what they said before it becomes a number.
- **There is no *onboarded player*.** Onboarding is not a state a player is in or out of;
  it is how a Skill rating comes to exist, and a rating is per sport. A player can be rated
  at padel and unrated at tennis at the same moment, indefinitely. Anything that needs to
  know "has this player been through onboarding" is really asking "does a rating exist for
  this sport", and must ask it that way — a per-player onboarding flag would be a second,
  coarser truth about the same fact.

  **What this bans is a per-player flag standing in for a per-sport fact** — not per-player
  facts as such. The test is the sentence above: *is this really asking whether a rating
  exists for this sport?* Where the answer is yes, ask it that way. Where the answer is no,
  the fact is genuinely the player's and belongs on the player. A **Player profile** is the
  first thing to return no — tags, photos, a week, a location and a consent are facts about
  a person and have no sport dimension at all — so *does a Player profile exist* is a
  legitimate per-player question, and onboarding's second part is checkpointed on it
  ([ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md)). Everything the invariant
  was written about stands unchanged.

### Users (`backend/app/modules/users/`)

Identity and account state.

- **User** — **event-sourced aggregate**: its state is rebuilt from a stream of domain
  events. Constructed only via `User.register(...)` or rehydrated via
  `User.from_history(events)`. Carries an `EventRecorder`; the application layer drains
  pending events with `pull_events()`.
- **Player** — a User acting in the player app. **Not a separate aggregate and not a
  separate id**: a player's identity *is* the `UserId`. `PlayerId` exists as a distinct
  type so the code reads in the domain's own vocabulary and so the two have one place to
  diverge, but today every `PlayerId` is a `UserId`. There is no `players` table.
  Revisit only if a person can be known to the system as a participant without holding an
  account, or if club staff share this accounts system — neither is true today.
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

### Shared kernel (`backend/app/kernel/`)

The dependency-free ring that every bounded context and every engine reads verbatim and
none may redefine ([ADR-0015](docs/adr/0015-engines-as-a-pure-versioned-layer.md)).

- **Sport** — a **closed enum** of exactly four values: `PADEL`, `TENNIS`, `SQUASH`,
  `BADMINTON`. Adding a sport is a code change and a release, never a row. A club's sport
  list *filters* this registry and never extends or overrides it.
- **SportSpec** — the frozen per-sport facts: `players` (how many the sport is played for)
  and `durations` (the bookable lengths in minutes). Served read-only over the player API at
  `GET /api/v1/sports` so neither client hardcodes it.
- **There is no `Format`.** One rating per sport, one question bank per sport, worded for how
  that sport is actually played — padel and badminton as doubles, tennis and squash as
  singles. *Padel singles* and *tennis doubles* are not terms in this system.

| Sport | players | durations (min) |
| --- | --- | --- |
| PADEL | 4 | 60 / 90 / 120 |
| TENNIS | 2 | 60 / 90 |
| SQUASH | 2 | 45 / 60 / 90 |
| BADMINTON | 4 | 60 / 90 |

**Invariants**
- **A sport's player count is never club-configurable.** No field on any club or court may
  override it; the value is read from exactly one place, everywhere. A club cannot sell a
  two-player padel match because the registry forbids it structurally, not by convention.
- **Reintroducing `Format` would be a new decision, not a gap someone should fill in.**
  Its absence is deliberate and load-bearing: one rating per sport is what let onboarding
  drop cross-sport transfer and the singles/doubles link entirely.

### Player profile (`backend/app/modules/player_profile/`)

Everything a matchmaker needs about a player that a questionnaire cannot infer. Decided by
[ADR-0089](docs/adr/0089-player-profile-context-event-sourced.md); the terms are here ahead
of the code because this file asks for them in that order.

- **Player profile** — an **event-sourced aggregate**, one per player. **The first
  aggregate in the racket-sport domain that is not per sport**: skill is per sport, but
  tags, photos, a week, a location and a consent are facts about a person.
- **Social tag** — one of a **fixed, closed vocabulary** the platform owns, in three groups
  about the game: how a player is *after the match*, what they are like *on the court*, and
  *why they are here*. A player holds **2 to 6**. Never free text, never player-authored,
  never imported from another platform, and never about the person rather than the game —
  age, looks, body and "looking for" are a different product's vocabulary.
- **Availability grid** — a player's ordinary week as **7 days × 3 parts of the day**,
  Monday-first. It is the *only* way time preference is ever expressed, and it is a
  **preference, not a promise** — a ticked slot is never a commitment, a hold, or a bookable
  time.
- **Availability slot** — one cell of the grid: a day and one of **morning**, **afternoon**,
  **evening**. The finest precision the platform holds about when a player wants to play.
- **Availability overlap** — how much of a player's own declared week another player covers.
  Deliberately **asymmetric**: the denominator is *your* slots, because the question it
  answers is *how much of my week does this person cover*.
- **Location area** — where a player plays, held coarsely. The precise fix that produced it
  is never a shareable value.
- **Search radius** — the distance around a player's Location area within which they want to
  find other players. **A filter when the player searches, and a weight when the engine
  proposes** — the same number answering two questions, because who *you* asked to see and
  who the platform *offers* you are different acts.
- **Proposals opt-in** — the player's recorded answer to whether the recommendation engine
  may push games at them. It has **no default**: unanswered is neither yes nor no.
- **Profile photo** — the first of a player's photos, and the one a player card shows. A
  player may hold up to three or none; none is not an absence but a **generated court
  poster**, derived from their identity so it is stable across devices.

**Invariants**
- **A tag id is permanent.** Ids are persisted on accounts, so retiring a tag means hiding
  it from the picker while continuing to honour it — never reusing or renaming it.
- **Blank means "no preference", never "leave me out".** An empty availability grid is a
  valid answer: it scores no overlap and it excludes the player from nothing. An unanswered
  field is never a negative filter.
- **The grid is never shown to anybody as a calendar.** Not to matched players, not as
  free/busy, not exported. Only the *count* of shared slots and the name of the next shared
  one are ever rendered — overlap is a fact about a pair, a calendar is a fact about a
  person.
- **Skipping is not consent.** The proposals opt-in is never pre-answered, and no other act
  in the product may be read as answering it — not a timeout, not a backgrounded app, not
  progress through any other step.
- **Opting out stops the engine pushing, not the player existing.** A player who declines
  receives no engine-generated proposals. They remain findable: search and matchmaking are
  unaffected, and they keep every other part of the product. Over-applying the flag makes a
  ghost account; under-applying it is a consent violation.
- **Consent is evidenced, not asserted.** Every answer is recorded with the moment it was
  given and **the exact copy the player was shown**, because consent gathered against one
  sentence is not consent to a different one. It is as revocable as it was grantable.
- **A profile is one per player, and asking whether one exists is a legitimate question.**
  See the narrowed *there is no onboarded player* invariant above, and
  [ADR-0090](docs/adr/0090-onboarding-per-player-checkpoint.md).

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

## Terms the client must not reinvent

The player app describes the same nouns this file does. A concept that exists in this
glossary keeps its name in TypeScript: an `Assessment` is an `Assessment`, not a `Quiz`,
`Survey`, or `Test`. Client-only *technical* vocabulary (wire type, DTO, mapper, secure
store) belongs in that app's own `CONTEXT.md`, never here.

The client also **renders** the values the backend sends. The backend sends numbers and
machine codes and never display text
([ADR-0022](docs/adr/0022-kernel-negative-space-and-constant-homes.md)), so the client
formats — against one table, in [`docs/value-formatting.md`](docs/value-formatting.md).
That is not a design system and holds no colour or size; it is the exact string a level, a
time or a duration becomes. One client cannot drift from itself, so the table's immediate
value is smaller than it was — it is kept because it is the contract a *second* client
would be held to, and rewriting it from memory later is how two apps end up rendering the
same number two ways. **Copy is not formatting**: the sentence behind an unavailability
code is the app's own.
